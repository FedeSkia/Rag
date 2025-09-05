import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rag_app.web_api.admin import admin_router
from rag_app.web_api.chat_history_web import chat_router
from rag_app.web_api.documents import document_router

logger = logging.getLogger(__name__)
from rag_app.config import CONFIG
from rag_app.logging_setup import setup_logging, RequestContextMiddleware, UVICORN_LOG

app = FastAPI()
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CONFIG.ALLOW_ORIGINS],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(document_router, prefix="/api", tags=["document"])
app.include_router(admin_router, prefix="/api", tags=["admin"])


def main():
    setup_logging()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=UVICORN_LOG)
