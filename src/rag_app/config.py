# src/rag_app/config.py
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import os, json, pathlib
from dotenv import load_dotenv


def _load_env_file() -> Optional[str]:
    """
    Decide which .env file to load.
    - If APP_ENV is set and points to a file, load that.
    - Else if ./.env exists, load it.
    - Else load nothing (env already present).
    """
    app_env = os.getenv("APP_ENV")
    if app_env and pathlib.Path(app_env).is_file():
        load_dotenv(dotenv_path=app_env)
        return app_env
    else:
        raise FileNotFoundError(f"No .env file found at {app_env}")


def _int_env(name: str) -> int:
    v = os.getenv(name)
    if v is None or v == "":
        raise ValueError(f"{name} is not present in .env file")
    try:
        return int(v)
    except ValueError:
        raise ValueError(f"{name} must be an integer, got {v!r}")


def _json_list_env(name: str) -> List[str]:
    v = os.getenv(name)
    if not v:
        raise ValueError(f"{name} is not present in .env file")
    try:
        parsed = json.loads(v)
    except json.JSONDecodeError as e:
        raise ValueError(f"{name} must be valid JSON (e.g., '[\"\\\\n# \", \"\\\\n\"]'): {e}") from e
    if not isinstance(parsed, list) or not all(isinstance(x, str) for x in parsed):
        raise ValueError(f"{name} must be a JSON list of strings, got: {parsed!r}")
    return parsed


def get_postgres_connection_string() -> str:
    return f"postgresql://{CONFIG.DB_USER}:{CONFIG.DB_PWD}@{CONFIG.DB_HOST}:{CONFIG.DB_PORT}/postgres?sslmode=disable"


@dataclass
class AppConfig:
    # ---- DB ----
    DB_HOST: Optional[str]
    DB_PORT: int
    DB_USER: Optional[str]
    DB_PWD: Optional[str]
    DOCUMENTS_COLLECTION: Optional[str]

    # ---- API ----
    ALLOW_ORIGINS: Optional[str]  # keep as string; parse as CSV if you prefer

    # ---- LLM ----
    CHAT_MODEL: Optional[str]
    EMBEDDING_MODEL: Optional[str]
    LLM_HOST: Optional[str]

    # ---- PDF PARSER ----
    CHUNK_SIZE: int
    CHUNK_OVERLAP: int
    SEPARATORS: List[str]
    OCR_LANGUANGES: List[str]
    CAMELOT_FLAVOR: str
    CAMELOT_PAGES: str
    STRATEGY: str
    UNSTRUCTURED_MODE: str
    RERANKER_MODEL_NAME: str
    RERANKER_TOP_N_RETRIEVED_DOCS: int

    # ---- AUTH
    JWT_SECRET: str
    JWT_ALG: str

    # Which env file was loaded (informational)
    loaded_env_file: Optional[str] = field(default=None, repr=False)

    @classmethod
    def from_env(cls) -> "AppConfig":
        loaded = _load_env_file()

        return cls(
            loaded_env_file=loaded,
            # DB
            DB_HOST=os.getenv("DB_HOST"),
            DB_PORT=_int_env("DB_PORT"),
            DB_USER=os.getenv("DB_USER"),
            DB_PWD=os.getenv("DB_PWD"),
            DOCUMENTS_COLLECTION=os.getenv("DOCUMENTS_COLLECTION"),
            # API
            ALLOW_ORIGINS=os.getenv("ALLOW_ORIGINS"),
            # LLM
            CHAT_MODEL=os.getenv("CHAT_MODEL"),
            EMBEDDING_MODEL=os.getenv("EMBEDDING_MODEL"),
            LLM_HOST=os.getenv("LLM_HOST"),
            # PDF PARSER
            CHUNK_SIZE=_int_env("CHUNK_SIZE"),
            CHUNK_OVERLAP=_int_env("CHUNK_OVERLAP"),
            SEPARATORS=_json_list_env("SEPARATORS"),
            OCR_LANGUANGES=_json_list_env("OCR_LANGUANGES"),
            CAMELOT_FLAVOR=os.getenv("CAMELOT_FLAVOR"),
            CAMELOT_PAGES=os.getenv("CAMELOT_PAGES"),
            STRATEGY=os.getenv("STRATEGY"),
            UNSTRUCTURED_MODE=os.getenv("UNSTRUCTURED_MODE"),
            RERANKER_MODEL_NAME=os.getenv("RERANKER_MODEL_NAME"),
            RERANKER_TOP_N_RETRIEVED_DOCS=int(os.getenv("RERANKER_TOP_N_RETRIEVED_DOCS")),
            JWT_SECRET=os.getenv("JWT_SECRET"),
            JWT_ALG=os.getenv("JWT_ALG"),
        )

    # Helpers
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Don't include loaded_env_file in dumps if you prefer:
        # d.pop("loaded_env_file", None)
        return d

    def pretty_print(self) -> None:
        print("Loaded configuration:")
        if self.loaded_env_file:
            print(f"  (env file: {self.loaded_env_file})")
        for k, v in self.to_dict().items():
            if k == "loaded_env_file":
                continue
            print(f"{k:16} = {v}")


CONFIG = AppConfig.from_env()
CONFIG.pretty_print()