from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Literal
from datetime import datetime
import os
import pathlib

import camelot
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import PGVector
from langchain_ollama import OllamaEmbeddings

from rag_app.config import CONFIG
from rag_app.ingestion.coalesce import coalesce_elements, CoalesceConfig


@dataclass
class RobustPDFToPgVector:
    # Required
    pdf_path: str
    collection_name: str  # table/collection in pgvector
    pg_connection: Optional[str] = field(
        default_factory=lambda: (
            f"postgresql://{CONFIG.DB_USER}:{CONFIG.DB_PWD}@{CONFIG.DB_HOST}:{CONFIG.DB_PORT}/postgres?sslmode=disable"
        )
    )
    # OCR / loader
    ocr_languages: str = field(default_factory=lambda: CONFIG.OCR_LANGUANGES)
    strategy: Literal["hi_res", "auto"] = field(default_factory=lambda: CONFIG.STRATEGY)
    unstructured_mode: Literal["elements", "single"] = field(default_factory=lambda: CONFIG.UNSTRUCTURED_MODE)

    # Chunking
    chunk_size: int = field(default_factory=lambda: CONFIG.CHUNK_SIZE)
    chunk_overlap: int = field(default_factory=lambda: CONFIG.CHUNK_OVERLAP)
    separators: List[str] = field(default_factory=lambda: list(CONFIG.SEPARATORS))

    # Embeddings
    embedding_model_name: str = field(default_factory=lambda: CONFIG.EMBEDDING_MODEL)
    _embedding: OllamaEmbeddings = field(init=False, repr=False)
    # Tables
    extract_tables: bool = False
    camelot_flavor: Literal["lattice", "stream"] = field(default_factory=lambda: CONFIG.CAMELOT_FLAVOR)
    camelot_pages: str = field(default_factory=lambda: CONFIG.CAMELOT_PAGES)

    # PGVector build options
    pre_delete_collection: bool = False  # drop & recreate collection on build

    # Internal
    _coalesced_docs: List[Document] = field(default_factory=list, init=False)
    _chunks: List[Document] = field(default_factory=list, init=False)
    _vector_store: Optional[PGVector] = field(default=None, init=False)

    def __post_init__(self):
        # Instantiate the embedder per instance
        self._embedding = OllamaEmbeddings(model=self.embedding_model_name)

    # ---------------- Public API ---------------- #

    def build(self) -> "RobustPDFToPgVector":
        """End-to-end: load -> coalesce -> chunk -> (tables) -> embed+upsert into pgvector."""
        conn = self.pg_connection
        if not conn:
            raise ValueError("Provide pg_connection")

        docs = self._load_pdf()
        chunks = self._split(docs)

        if self.extract_tables:
            chunks += self._extract_tables()

        # Tag provenance
        for chunk in chunks:
            chunk.metadata.setdefault("source", self.pdf_path)
            chunk.metadata.setdefault("file_name", pathlib.Path(self.pdf_path).name)
            chunk.metadata.setdefault("ingested_at", datetime.utcnow().isoformat())

        self._chunks = chunks
        self._vector_store = self._upsert_into_pgvector(chunks, conn)
        return self

    def retriever(self, k: int = 8, search_type: str = "similarity", **kwargs):
        """Return a LangChain retriever backed by pgvector."""
        if not self._vector_store:
            raise RuntimeError("Vector store not built. Call build() or load_collection() first.")
        return self._vector_store.as_retriever(search_type=search_type, search_kwargs={"k": k, **kwargs})

    def similarity_search(self, query: str, k: int = 5):
        if not self._vector_store:
            raise RuntimeError("Vector store not built. Call build() or load_collection() first.")
        return self._vector_store.similarity_search(query, k=k)

    def load_collection(self, pg_connection: Optional[str] = None):
        """Attach to an existing pgvector collection (no ingestion)."""
        conn = pg_connection or self.pg_connection or os.getenv("PG_CONN_STR")
        if not conn:
            raise ValueError("Provide pg_connection or set PG_CONN_STR env var.")

        self._vector_store = PGVector(
            embedding_function=self._embedding,
            collection_name=self.collection_name,
            connection_string=conn,
        )
        return self

    # ---------------- Steps ---------------- #

    def _load_pdf(self) -> List[Document]:
        loader = UnstructuredPDFLoader(
            self.pdf_path,
            mode=self.unstructured_mode,  # "elements" recommended
            strategy=self.strategy,  # "hi_res" triggers OCR when needed
            languages=self.ocr_languages,
        )
        try:
            docs = loader.load()
        except Exception as e:
            print("Error while loading PDF")
            raise

        file_name = pathlib.Path(self.pdf_path).name
        for doc in docs:
            doc.metadata.update({
                "file_name": file_name,
                "source": self.pdf_path,
                "ingested_at": datetime.now().isoformat(),
            })
        coalesced_docs = coalesce_elements(docs, cfg=CoalesceConfig(
            min_len=80,
            keep_headings_separate=True,
            avoid_cross_page_merge=True,
            hard_types=("Table", "Code", "Figure", "Caption")
        ))

        self._coalesced_docs = coalesced_docs
        return coalesced_docs

    def _split(self, docs: List[Document]) -> List[Document]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
        )
        return splitter.split_documents(docs)

    def _extract_tables(self) -> List[Document]:
        """Optional: extract vector-based tables via Camelot and index them as Markdown."""
        tables = camelot.read_pdf(
            self.pdf_path,
            flavor=self.camelot_flavor,
            pages=self.camelot_pages
        )
        docs: List[Document] = []
        for i, t in enumerate(tables):
            md = t.df.to_markdown(index=False)
            docs.append(Document(
                page_content=f"Table #{i + 1}\n{md}",
                metadata={
                    "source": self.pdf_path,
                    "file_name": pathlib.Path(self.pdf_path).name,
                    "type": "table",
                    "table_index": i
                }
            ))
        return docs

    def _upsert_into_pgvector(self, docs: List[Document], conn: str) -> PGVector:

        # If collection doesn’t exist, this will create it. If it exists:
        # - pre_delete_collection=True will drop/recreate (clean build)
        # - otherwise, we add/append to the same collection
        vs = PGVector.from_documents(
            documents=docs,
            embedding=self._embedding,
            collection_name=self.collection_name,
            connection_string=conn,
            pre_delete_collection=self.pre_delete_collection,
        )
        return vs


# ---------------- Example usage ----------------
if __name__ == "__main__":

    ingestor = RobustPDFToPgVector(
        pdf_path="/Users/federicoconoci/Downloads/Octo Fissa 12M Gas Domestico-26-1.pdf",
        collection_name="contracts_v1",
        extract_tables=True,
        pre_delete_collection=False  # set True to rebuild the collection each run
    ).build()

    retriever = ingestor.retriever(k=8)
    results = ingestor.similarity_search("Quali sono i termini di garanzia?", k=5)
    for d in results:
        print(d.metadata.get("file_name"), d.metadata.get("page"), d.metadata.get("type"), "\n",
              d.page_content[:180], "\n---\n")
