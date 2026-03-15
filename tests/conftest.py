"""
conftest.py — must set APP_ENV *before* any rag_app module is imported.
This file runs at collection time, before test modules are imported.
"""
import os
import tempfile

# Create the env file immediately (not in a fixture) so that
# `from rag_app.config import CONFIG` works during module collection.
_env_content = """\
DB_HOST=localhost
DB_PORT=5432
DB_USER=test
DB_PWD=test
DOCUMENTS_COLLECTION=test_docs
LEVEL=DEBUG
UVICORN_LEVEL=DEBUG
ALLOW_ORIGINS=http://localhost
CHAT_MODEL=test-model
EMBEDDING_MODEL=test-embed
LLM_HOST=http://localhost:11434
CHUNK_SIZE=500
CHUNK_OVERLAP=50
SEPARATORS=["\\n","  "]
OCR_LANGUANGES=["eng"]
CAMELOT_FLAVOR=lattice
CAMELOT_PAGES=all
STRATEGY=fast
UNSTRUCTURED_MODE=elements
RERANKER_MODEL_NAME=cross-encoder/ms-marco-MiniLM-L-6-v2
RERANKER_TOP_N_RETRIEVED_DOCS=3
JWT_SECRET=test-secret-that-is-at-least-32-characters-long
JWT_ALG=HS256
GOTRUE_URL=http://localhost:9999
"""

_tmpfile = tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False)
_tmpfile.write(_env_content)
_tmpfile.flush()
_tmpfile.close()

os.environ["APP_ENV"] = _tmpfile.name
