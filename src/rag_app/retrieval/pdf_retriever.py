from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any

from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_postgres import PGVector

from langchain_ollama import OllamaEmbeddings
from rag_app.config import CONFIG, get_postgres_connection_string
from rag_app.ingestion.constants import USER_ID_KEY, DOC_ID_KEY


@dataclass(frozen=True)
class RetrieverInput:
    user_id: str
    query: str
    k: int = 8
    doc_id: Optional[str] = None  # optional scoping to a single document


class PdfRetriever:
    """Holds only dependencies; no mutable runtime state."""
    def __init__(self):
        self._pg_connection = get_postgres_connection_string()
        self._emb = OllamaEmbeddings(model=CONFIG.EMBEDDING_MODEL)
        self._collection = CONFIG.DOCUMENTS_COLLECTION

    def _pg_vector(self) -> PGVector:
        return PGVector(
            embeddings=self._emb,
            collection_name=self._collection,
            connection=self._pg_connection,
        )

    def _build_filter_query(self, *, user_id: str, document_id: Optional[str] = None,
                            extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        f: Dict[str, Any] = {USER_ID_KEY: user_id}
        if document_id:
            f[DOC_ID_KEY] = document_id
        if extra:
            f.update(extra)
        return f

    def similarity(self, inp: RetrieverInput):
        vs = self._pg_vector()
        filt = self._build_filter_query(user_id=inp.user_id, document_id=inp.doc_id)
        return vs.similarity_search(inp.query, k=inp.k, filter=filt)

    def retriever(self, query: str, user_id: str, k: int = 8, document_id: Optional[str] = None) -> list[Document]:
        pg_vector = self._pg_vector()
        filt = self._build_filter_query(user_id=user_id, document_id=document_id)
        retriever: VectorStoreRetriever = pg_vector.as_retriever(search_kwargs={"k": k, "filter": filt})
        return retriever.invoke(query)

pdf_retriever = PdfRetriever()