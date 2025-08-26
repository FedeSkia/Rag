from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any
from langchain_postgres import PGVector

from langchain_ollama import OllamaEmbeddings
from rag_app.config import CONFIG, get_postgres_connection_string


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

    def _vs(self) -> PGVector:
        return PGVector(
            embeddings=self._emb,
            collection_name=self._collection,
            connection=self._pg_connection,
        )

    def _filter(self, *, user_id: str, doc_id: Optional[str] = None,
                extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        f: Dict[str, Any] = {"user_id": user_id}
        if doc_id:
            f["doc_id"] = doc_id
        if extra:
            f.update(extra)
        return f

    def similarity(self, inp: RetrieverInput):
        vs = self._vs()
        filt = self._filter(user_id=inp.user_id, doc_id=inp.doc_id)
        return vs.similarity_search(inp.query, k=inp.k, filter=filt)

    def retriever(self, *, user_id: str, k: int = 8, doc_id: Optional[str] = None):
        vs = self._vs()
        filt = self._filter(user_id=user_id, doc_id=doc_id)
        return vs.as_retriever(search_kwargs={"k": k, "filter": filt})