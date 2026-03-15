"""Tests for ingestion/pdf_store.py — pure functions only."""
import io

from rag_app.ingestion.pdf_store import (
    generate_doc_id_from_bytesio,
    create_document_filter,
    create_parser_additional_metadata,
)


class TestGenerateDocId:
    def test_deterministic(self):
        data = b"hello world pdf content"
        f = io.BytesIO(data)
        id1 = generate_doc_id_from_bytesio(f)
        id2 = generate_doc_id_from_bytesio(f)
        assert id1 == id2

    def test_length_is_16(self):
        f = io.BytesIO(b"some bytes")
        assert len(generate_doc_id_from_bytesio(f)) == 16

    def test_different_content_different_id(self):
        id1 = generate_doc_id_from_bytesio(io.BytesIO(b"content A"))
        id2 = generate_doc_id_from_bytesio(io.BytesIO(b"content B"))
        assert id1 != id2

    def test_preserves_file_position(self):
        f = io.BytesIO(b"abcdef")
        f.seek(3)
        generate_doc_id_from_bytesio(f)
        assert f.tell() == 3


class TestCreateDocumentFilter:
    def test_structure(self):
        filt = create_document_filter("user-1", "doc-abc")
        assert "$and" in filt
        conditions = filt["$and"]
        assert len(conditions) == 2
        assert conditions[0] == {"user_id": {"$eq": "user-1"}}
        assert conditions[1] == {"document_id": {"$eq": "doc-abc"}}


class TestCreateParserAdditionalMetadata:
    def test_keys(self):
        meta = create_parser_additional_metadata("report.pdf", 5)
        assert meta["file_name"] == "report.pdf"
        assert meta["page"] == 5

    def test_none_page(self):
        meta = create_parser_additional_metadata("doc.pdf", None)
        assert meta["page"] is None
