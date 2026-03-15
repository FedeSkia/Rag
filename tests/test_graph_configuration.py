"""Tests for agent/graph_configuration.py."""
import pytest

from rag_app.agent.graph_configuration import GraphRunConfig, THREAD_ID
from rag_app.ingestion.constants import USER_ID_KEY, INTERACTION_ID_KEY


class TestGraphRunConfig:
    def test_to_runnable(self):
        cfg = GraphRunConfig(thread_id="t1", user_id="u1", interaction_id="i1")
        runnable = cfg.to_runnable()
        assert runnable["configurable"][THREAD_ID] == "t1"
        assert runnable["configurable"][USER_ID_KEY] == "u1"
        assert runnable["configurable"][INTERACTION_ID_KEY] == "i1"

    def test_from_runnable_roundtrip(self):
        original = GraphRunConfig(thread_id="t1", user_id="u1", interaction_id="i1")
        runnable = original.to_runnable()
        restored = GraphRunConfig.from_runnable(runnable)
        assert restored == original

    def test_from_headers(self):
        cfg = GraphRunConfig.from_headers(thread_id="t2", user_id="u2", interaction_id="i2")
        assert cfg.thread_id == "t2"
        assert cfg.user_id == "u2"
        assert cfg.interaction_id == "i2"

    def test_from_headers_no_interaction(self):
        cfg = GraphRunConfig.from_headers(thread_id="t3", user_id="u3")
        assert cfg.interaction_id is None

    def test_empty_thread_id_rejected(self):
        with pytest.raises(Exception):
            GraphRunConfig(thread_id="", user_id="u1")

    def test_empty_user_id_rejected(self):
        with pytest.raises(Exception):
            GraphRunConfig(thread_id="t1", user_id="")
