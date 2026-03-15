"""Tests for ingestion/coalesce.py — pure logic, no infra needed."""
import pytest
from langchain.schema import Document

from rag_app.ingestion.coalesce import (
    CoalesceConfig,
    category,
    page,
    merge_adjacent_by_category,
    ensure_min_length,
    coalesce_elements,
)


def _doc(text: str, cat: str | None = None, pg: int | None = None) -> Document:
    meta = {}
    if cat:
        meta["category"] = cat
    if pg is not None:
        meta["page_number"] = pg
    return Document(page_content=text, metadata=meta)


class TestHelpers:
    def test_category_from_category_key(self):
        assert category(Document(page_content="", metadata={"category": "Table"})) == "Table"

    def test_category_from_type_key(self):
        assert category(Document(page_content="", metadata={"type": "Code"})) == "Code"

    def test_category_none(self):
        assert category(Document(page_content="", metadata={})) is None

    def test_page_from_page_number(self):
        assert page(Document(page_content="", metadata={"page_number": 3})) == 3

    def test_page_from_page_key(self):
        assert page(Document(page_content="", metadata={"page": 5})) == 5

    def test_page_none(self):
        assert page(Document(page_content="", metadata={})) is None


class TestMergeAdjacentByCategory:
    def test_same_category_same_page_merged(self):
        docs = [_doc("a", "NarrativeText", 1), _doc("b", "NarrativeText", 1)]
        result = merge_adjacent_by_category(docs, cfg=CoalesceConfig())
        assert len(result) == 1
        assert "a\nb" == result[0].page_content

    def test_different_category_not_merged(self):
        docs = [_doc("a", "NarrativeText", 1), _doc("b", "Table", 1)]
        result = merge_adjacent_by_category(docs, cfg=CoalesceConfig())
        assert len(result) == 2

    def test_cross_page_not_merged_by_default(self):
        docs = [_doc("a", "NarrativeText", 1), _doc("b", "NarrativeText", 2)]
        result = merge_adjacent_by_category(docs, cfg=CoalesceConfig(avoid_cross_page_merge=True))
        assert len(result) == 2

    def test_cross_page_merged_when_allowed(self):
        docs = [_doc("a", "NarrativeText", 1), _doc("b", "NarrativeText", 2)]
        result = merge_adjacent_by_category(docs, cfg=CoalesceConfig(avoid_cross_page_merge=False))
        assert len(result) == 1

    def test_empty_input(self):
        assert merge_adjacent_by_category([], cfg=CoalesceConfig()) == []

    def test_single_element(self):
        docs = [_doc("only one")]
        result = merge_adjacent_by_category(docs, cfg=CoalesceConfig())
        assert len(result) == 1
        assert result[0].page_content == "only one"


class TestEnsureMinLength:
    def test_short_fragments_merged(self):
        docs = [_doc("hi"), _doc("there")]
        result = ensure_min_length(docs, cfg=CoalesceConfig(min_len=50))
        assert len(result) == 1
        assert "hi\nthere" == result[0].page_content

    def test_hard_type_blocks_merge(self):
        docs = [_doc("short"), _doc("table data", "Table")]
        result = ensure_min_length(docs, cfg=CoalesceConfig(min_len=50))
        assert len(result) == 2

    def test_heading_blocks_merge(self):
        docs = [_doc("short", "Title"), _doc("body text")]
        result = ensure_min_length(docs, cfg=CoalesceConfig(min_len=50, keep_headings_separate=True))
        assert len(result) == 2

    def test_heading_merge_allowed_when_disabled(self):
        docs = [_doc("short", "Title"), _doc("body")]
        result = ensure_min_length(docs, cfg=CoalesceConfig(min_len=50, keep_headings_separate=False))
        assert len(result) == 1

    def test_long_fragments_not_merged(self):
        docs = [_doc("a" * 100), _doc("b" * 100)]
        result = ensure_min_length(docs, cfg=CoalesceConfig(min_len=50))
        assert len(result) == 2

    def test_empty_input(self):
        assert ensure_min_length([], cfg=CoalesceConfig()) == []


class TestCoalesceElements:
    def test_full_pipeline(self):
        docs = [
            _doc("intro", "NarrativeText", 1),
            _doc("more", "NarrativeText", 1),
            _doc("Chapter 2", "Title", 2),
            _doc("body of chapter 2 with enough text to pass min length threshold easily", "NarrativeText", 2),
        ]
        result = coalesce_elements(docs, cfg=CoalesceConfig(min_len=20))
        # "intro" + "more" merged (same cat, same page), Title stays separate, body stays separate
        assert len(result) == 3
        assert "intro\nmore" == result[0].page_content

    def test_preserves_layout_categories_metadata(self):
        docs = [_doc("a", "NarrativeText", 1), _doc("b", "NarrativeText", 1)]
        result = coalesce_elements(docs, cfg=CoalesceConfig())
        assert "layout_categories" in result[0].metadata
        assert "NarrativeText" in result[0].metadata["layout_categories"]
