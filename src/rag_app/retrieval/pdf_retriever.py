from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_postgres import PGVector

from langchain_ollama import OllamaEmbeddings
from rag_app.config import CONFIG, get_postgres_connection_string
from rag_app.ingestion.constants import USER_ID_KEY, DOC_ID_KEY

from sentence_transformers import CrossEncoder

@dataclass(frozen=True)
class RetrieverInput:
    user_id: str
    query: str
    k: int = 8
    doc_id: Optional[str] = None  # optional scoping to a single document


class PdfRetriever:
    def __init__(self):
        self._pg_connection = get_postgres_connection_string()
        self._emb = OllamaEmbeddings(model=CONFIG.EMBEDDING_MODEL)
        self._collection = CONFIG.DOCUMENTS_COLLECTION
        # --- reranker config ---
        self._rerank_top_k = getattr(CONFIG, "RERANK_TOP_K", 20)   # candidates to re-rank
        self._reranker =  CrossEncoder(CONFIG.RERANKER_MODEL_NAME)

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

    def _rerank(self, query: str, docs: list[Document], top_n: int) -> list[Document]:
        pairs = [(query, d.page_content) for d in docs]
        scores = self._reranker.predict(pairs)
        ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
        return [d for d, _ in ranked[:top_n]]

    def similarity(self, inp: RetrieverInput):
        vs = self._pg_vector()
        # retrieve a wider candidate set for better re-ranking
        k_candidates = inp.k
        filt = self._build_filter_query(user_id=inp.user_id, document_id=inp.doc_id)
        candidates = vs.similarity_search(inp.query, k=k_candidates, filter=filt)
        return self._rerank(inp.query, candidates, top_n=inp.k)

    def retriever(self, query: str, user_id: str, k: int = 20, document_id: Optional[str] = None) -> list[Document]:
        assert k > CONFIG.RERANKER_TOP_N_RETRIEVED_DOCS
        pg_vector = self._pg_vector()
        filt = self._build_filter_query(user_id=user_id, document_id=document_id)
        retriever: VectorStoreRetriever = pg_vector.as_retriever(search_kwargs={"k": k, "filter": filt})
        docs = retriever.invoke(query)
        return self._rerank(query, docs, top_n=CONFIG.RERANKER_TOP_N_RETRIEVED_DOCS)

pdf_retriever = PdfRetriever()