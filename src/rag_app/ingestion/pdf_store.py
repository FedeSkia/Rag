from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal, Dict, Any, IO, Final

from fastapi import UploadFile
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredFileIOLoader
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVector

from rag_app.config import CONFIG, get_postgres_connection_string
from rag_app.ingestion.coalesce import coalesce_elements, CoalesceConfig


USER_ID_KEY: Final[str] = "user_id"
DOC_ID_KEY: Final[str] = "document_id"
FILE_NAME_KEY: Final[str] = "file_name"
PAGE_KEY: Final[str] = "page"
INGESTED_AT_KEY: Final[str] = "ingested_at"


def generate_doc_id_from_bytesio(f: IO[bytes]) -> str:
    pos = f.tell()
    f.seek(0)
    h = hashlib.sha1()
    for chunk in iter(lambda: f.read(1024 * 1024), b""):
        h.update(chunk)
    f.seek(pos)
    return h.hexdigest()[:16]


def create_document_filter(user_id: str, document_id: str) -> Dict[str, Any]:
    """Filter documents by user id and document id."""
    return {
        "$and": [
            {USER_ID_KEY: {"$eq": user_id}},
            {DOC_ID_KEY: {"$eq": document_id}},
        ]
    }

def create_parser_additional_metadata(file_name: str, page) -> Dict[str, Any]:
    return {
        FILE_NAME_KEY: file_name,
        PAGE_KEY: page,
    }

@dataclass(frozen=True)
class StorerConfig:
    pg_connection: str = get_postgres_connection_string()
    # OCR / loader
    languages: str = field(default_factory=lambda: CONFIG.OCR_LANGUANGES)
    strategy: Literal["hi_res", "auto"] = field(default_factory=lambda: CONFIG.STRATEGY)
    unstructured_mode: Literal["elements", "single"] = field(default_factory=lambda: CONFIG.UNSTRUCTURED_MODE)

    # Chunking
    chunk_size: int = field(default_factory=lambda: CONFIG.CHUNK_SIZE)
    chunk_overlap: int = field(default_factory=lambda: CONFIG.CHUNK_OVERLAP)
    separators: List[str] = field(default_factory=lambda: list(CONFIG.SEPARATORS))

    # Embeddings
    embedding_model: OllamaEmbeddings = field(default_factory=lambda: OllamaEmbeddings(model=CONFIG.EMBEDDING_MODEL))


@dataclass(frozen=True)
class PdfSaverData:
    user_id: str
    file: UploadFile
    file_name: str


def _from_uploadfile_to_io(upload: UploadFile) -> IO[bytes]:
    upload.file.seek(0)
    return upload.file  # SpooledTemporaryFile, behaves as IO[bytes]


class PdfSaver:

    def __init__(self):
        self._config: StorerConfig = StorerConfig()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._config.chunk_size,
            chunk_overlap=self._config.chunk_overlap,
            separators=list(self._config.separators)
        )
        self._emb = OllamaEmbeddings(model=CONFIG.EMBEDDING_MODEL)
        self._collection = CONFIG.DOCUMENTS_COLLECTION

    # embeddings
    def _loader_docs(self, file: IO[bytes], file_name: str) -> List[Document]:
        loader = UnstructuredFileIOLoader(
            file=file,
            mode=self._config.unstructured_mode,
            strategy=self._config.strategy,
            languages=self._config.languages,
        )

        try:
            docs = loader.load()
        except Exception as e:
            print("Error while loading PDF")
            raise

        for d in docs:
            d.metadata.update(create_parser_additional_metadata(file_name, d.metadata.get("page")))
        return docs

    def _split(self, docs: List[Document]) -> List[Document]:
        coalesced = coalesce_elements(docs, cfg=CoalesceConfig(
            min_len=80,
            keep_headings_separate=True,
            avoid_cross_page_merge=True,
            hard_types=("Table", "Code", "Figure", "Caption")
        ))
        return self._splitter.split_documents(coalesced)

    def _get_pg_vector(self) -> PGVector:
        return PGVector(
            embeddings=self._config.embedding_model,
            collection_name=self._collection,
            connection=self._config.pg_connection,
        )

    def upsert(self, inp: PdfSaverData) -> Dict[str, Any]:
        """Parse the PDF and upsert chunks tagged with user_id & doc_id."""
        file_as_io = _from_uploadfile_to_io(inp.file)
        document_id = generate_doc_id_from_bytesio(file_as_io)

        documents_already_exists = self._get_pg_vector().similarity_search(
            "probe",
            k=1,
            filter=create_document_filter(inp.user_id, document_id)
        )
        if documents_already_exists:
            raise Exception("Document ID already exists")

        docs = self._loader_docs(file_as_io, inp.file_name)
        chunks = self._split(docs)

        # add tenant metadata
        ts = datetime.now().isoformat()
        for c in chunks:
            c.metadata.update({
                USER_ID_KEY: inp.user_id,
                INGESTED_AT_KEY: ts,
                DOC_ID_KEY: document_id,
            })

        PGVector.from_documents(
            documents=chunks,
            embedding=self._config.embedding_model,
            collection_name=CONFIG.DOCUMENTS_COLLECTION,
            connection=self._config.pg_connection,
            pre_delete_collection=False,
        )
        return {"file_name": inp.file_name, "chunks": len(chunks)}


pdf_saver = PdfSaver()
