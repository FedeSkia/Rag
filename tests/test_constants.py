"""Tests for ingestion/constants.py — verify constant values."""
from rag_app.ingestion.constants import (
    USER_ID_KEY,
    INTERACTION_ID_KEY,
    DOC_ID_KEY,
    FILE_NAME_KEY,
    PAGE_KEY,
    INGESTED_AT_KEY,
)


def test_constant_values():
    assert USER_ID_KEY == "user_id"
    assert INTERACTION_ID_KEY == "interaction_id"
    assert DOC_ID_KEY == "document_id"
    assert FILE_NAME_KEY == "file_name"
    assert PAGE_KEY == "page"
    assert INGESTED_AT_KEY == "ingested_at"


def test_constants_are_strings():
    for c in [USER_ID_KEY, INTERACTION_ID_KEY, DOC_ID_KEY, FILE_NAME_KEY, PAGE_KEY, INGESTED_AT_KEY]:
        assert isinstance(c, str)
