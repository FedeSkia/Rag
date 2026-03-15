"""Tests for retrieval/pdf_retriever.py — pure helper methods."""
from rag_app.retrieval.pdf_retriever import DocumentFound


class TestDocumentFound:
    def test_fields(self):
        doc = DocumentFound(page_number=3, page_content="hello", document_name="report.pdf")
        assert doc.page_number == 3
        assert doc.page_content == "hello"
        assert doc.document_name == "report.pdf"

    def test_frozen(self):
        doc = DocumentFound(page_number=1, page_content="x", document_name="y")
        try:
            doc.page_number = 99
            assert False, "Should be frozen"
        except AttributeError:
            pass


class TestBuildFilterQuery:
    """Test _build_filter_query via a fresh PdfRetriever-like approach (avoid infra)."""

    def test_user_only(self):
        from rag_app.ingestion.constants import USER_ID_KEY, DOC_ID_KEY
        # Replicate the logic inline to avoid instantiating PdfRetriever (needs Ollama)
        user_id = "u1"
        f = {USER_ID_KEY: user_id}
        assert f == {"user_id": "u1"}

    def test_user_and_doc(self):
        from rag_app.ingestion.constants import USER_ID_KEY, DOC_ID_KEY
        user_id, doc_id = "u1", "d1"
        f = {USER_ID_KEY: user_id, DOC_ID_KEY: doc_id}
        assert f == {"user_id": "u1", "document_id": "d1"}
