from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from langchain_community.vectorstores import PGVector
from langchain_ollama import OllamaEmbeddings
from rag_app.config import CONFIG


@dataclass
class PdfRetriever:
    user_id: str
    collection_name: str
    pg_connection: Optional[str] = None
    embedding_model: str = CONFIG.EMBEDDING_MODEL

    def _vs(self) -> PGVector:
        return PGVector(
            embedding_function=OllamaEmbeddings(model=self.embedding_model),
            collection_name=self.collection_name,
            connection_string=self.pg_connection or f"postgresql://{CONFIG.DB_USER}:{CONFIG.DB_PWD}@{CONFIG.DB_HOST}:{CONFIG.DB_PORT}/postgres?sslmode=disable",
        )

    def _filter(self, doc_id: Optional[str] = None, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        f: Dict[str, Any] = {"user_id": self.user_id}
        if doc_id:
            f["doc_id"] = doc_id
        if extra:
            f.update(extra)
        return f

    def similarity(self, query: str, k: int = 8, doc_id: Optional[str] = None):
        vs = self._vs()
        # For LC PGVector, pass metadata filter as 'filter='
        return vs.similarity_search(query, k=k, filter=self._filter(doc_id))

    def retriever(self, k: int = 8, doc_id: Optional[str] = None):
        vs = self._vs()
        return vs.as_retriever(search_kwargs={"k": k, "filter": self._filter(doc_id)})
