"""Tests for document/user_document_handler.py — Pydantic model validation."""
from datetime import datetime

import pytest

from rag_app.document.user_document_handler import UserDocument


class TestUserDocumentModel:
    def test_valid(self):
        doc = UserDocument(file_name="a.pdf", user_id="u1", document_id="d1", created_at=datetime.now())
        assert doc.file_name == "a.pdf"

    def test_created_at_optional(self):
        doc = UserDocument(file_name="a.pdf", user_id="u1", document_id="d1")
        assert doc.created_at is None

    def test_missing_required_field(self):
        with pytest.raises(Exception):
            UserDocument(user_id="u1", document_id="d1")  # missing file_name
