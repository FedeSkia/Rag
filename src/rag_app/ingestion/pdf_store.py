from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
import pathlib
import hashlib

from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import PGVector
from langchain_ollama import OllamaEmbeddings

from rag_app.config import CONFIG
from rag_app.ingestion.coalesce import coalesce_elements, CoalesceConfig


def _doc_id_for(path: str) -> str:
    # content-addressable is ideal; as a starter use filename+mtime
    p = pathlib.Path(path)
    base = f"{p.name}-{p.stat().st_mtime}".encode()
    return hashlib.sha1(base).hexdigest()[:16]


@dataclass(frozen=True)
class StorerConfig:
    pg_connection: Optional[str] = field(
        default_factory=lambda: (
            f"postgresql://{CONFIG.DB_USER}:{CONFIG.DB_PWD}@{CONFIG.DB_HOST}:{CONFIG.DB_PORT}/postgres?sslmode=disable"
        )
    )
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
class PdfStorerInput:
    user_id: str
    pdf_path: str


class PdfStore:

    def __init__(self):
        self._config: StorerConfig = StorerConfig()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._config.chunk_size,
            chunk_overlap=self._config.chunk_overlap,
            separators=list(self._config.separators)
        )

    # embeddings
    def _loader_docs(self, pdf_path: str) -> List[Document]:
        loader = UnstructuredPDFLoader(
            pdf_path,
            mode=self._config.unstructured_mode,
            strategy=self._config.strategy,
            languages=self._config.languages,
        )
        try:
            docs = loader.load()
        except Exception as e:
            print("Error while loading PDF")
            raise
        file_name = pathlib.Path(pdf_path).name
        for d in docs:
            d.metadata.update({
                "file_name": file_name,
                "source": pdf_path,
                "page": d.metadata.get("page"),  # keep if provided
            })
        return docs

    def _split(self, docs: List[Document]) -> List[Document]:
        coalesced = coalesce_elements(docs, cfg=CoalesceConfig(
            min_len=80,
            keep_headings_separate=True,
            avoid_cross_page_merge=True,
            hard_types=("Table", "Code", "Figure", "Caption")
        ))
        return self._splitter.split_documents(coalesced)

    def upsert(self, input: PdfStorerInput) -> Dict[str, Any]:
        """Parse the PDF and upsert chunks tagged with user_id & doc_id."""
        doc_id = _doc_id_for(input.pdf_path)
        docs = self._loader_docs(input.pdf_path)
        chunks = self._split(docs)

        # add tenant metadata
        ts = datetime.now().isoformat()
        for c in chunks:
            c.metadata.update({
                "user_id": input.user_id,
                "doc_id": doc_id,
                "ingested_at": ts,
            })

        PGVector.from_documents(
            documents=chunks,
            embedding=self._config.embedding_model,
            collection_name=input.user_id,
            connection_string=self._config.pg_connection,
            pre_delete_collection=False,
        )
        return {"doc_id": doc_id, "chunks": len(chunks)}
