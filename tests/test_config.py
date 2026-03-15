"""Tests for config.py helper functions."""
import os
import pytest


class TestIntEnv:
    def test_valid_int(self, monkeypatch):
        from rag_app.config import _int_env
        monkeypatch.setenv("TEST_INT", "42")
        assert _int_env("TEST_INT") == 42

    def test_missing_raises(self, monkeypatch):
        from rag_app.config import _int_env
        monkeypatch.delenv("TEST_INT_MISSING", raising=False)
        with pytest.raises(ValueError, match="not present"):
            _int_env("TEST_INT_MISSING")

    def test_empty_raises(self, monkeypatch):
        from rag_app.config import _int_env
        monkeypatch.setenv("TEST_INT_EMPTY", "")
        with pytest.raises(ValueError, match="not present"):
            _int_env("TEST_INT_EMPTY")

    def test_non_int_raises(self, monkeypatch):
        from rag_app.config import _int_env
        monkeypatch.setenv("TEST_INT_BAD", "abc")
        with pytest.raises(ValueError, match="must be an integer"):
            _int_env("TEST_INT_BAD")


class TestJsonListEnv:
    def test_valid_list(self, monkeypatch):
        from rag_app.config import _json_list_env
        monkeypatch.setenv("TEST_JSON", '["a", "b"]')
        assert _json_list_env("TEST_JSON") == ["a", "b"]

    def test_missing_raises(self, monkeypatch):
        from rag_app.config import _json_list_env
        monkeypatch.delenv("TEST_JSON_MISSING", raising=False)
        with pytest.raises(ValueError, match="not present"):
            _json_list_env("TEST_JSON_MISSING")

    def test_invalid_json_raises(self, monkeypatch):
        from rag_app.config import _json_list_env
        monkeypatch.setenv("TEST_JSON_BAD", "not json")
        with pytest.raises(ValueError, match="must be valid JSON"):
            _json_list_env("TEST_JSON_BAD")

    def test_non_list_raises(self, monkeypatch):
        from rag_app.config import _json_list_env
        monkeypatch.setenv("TEST_JSON_OBJ", '{"a": 1}')
        with pytest.raises(ValueError, match="must be a JSON list of strings"):
            _json_list_env("TEST_JSON_OBJ")

    def test_list_of_ints_raises(self, monkeypatch):
        from rag_app.config import _json_list_env
        monkeypatch.setenv("TEST_JSON_INTS", "[1, 2]")
        with pytest.raises(ValueError, match="must be a JSON list of strings"):
            _json_list_env("TEST_JSON_INTS")


class TestAppConfig:
    def test_config_loaded(self):
        from rag_app.config import CONFIG
        assert CONFIG.DB_HOST is not None
        assert CONFIG.CHUNK_SIZE > 0
        assert isinstance(CONFIG.SEPARATORS, list)

    def test_to_dict(self):
        from rag_app.config import CONFIG
        d = CONFIG.to_dict()
        assert isinstance(d, dict)
        assert "DB_HOST" in d
        assert "CHUNK_SIZE" in d

    def test_postgres_connection_string(self):
        from rag_app.config import get_postgres_connection_string, CONFIG
        conn = get_postgres_connection_string()
        assert conn.startswith("postgresql://")
        assert CONFIG.DB_USER in conn
        assert CONFIG.DB_HOST in conn
