import logging
from typing import Optional
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Header, UploadFile, File, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from starlette import status

logger = logging.getLogger(__name__)
from rag_app.config import CONFIG
from rag_app.agent.graph import launch_graph
from rag_app.agent.graph_configuration import GraphRunConfig
from rag_app.ingestion.pdf_store import PdfSaverData, pdf_saver
from rag_app.logging_setup import setup_logging, RequestContextMiddleware, UVICORN_LOG
from rag_app.web_api.jwt_resolver import JWTBearer, get_user_id


class InputData(BaseModel):
    content: str


app = FastAPI()
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CONFIG.ALLOW_ORIGINS],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.post("/api/invoke")
async def invoke(
        data: InputData,
        request: Request,
        x_thread_id: Optional[str] = Header(..., alias="X-Thread-Id"),
        _token: str = Depends(JWTBearer()),
):
    user_id = get_user_id(request)
    thread_id = x_thread_id or str(uuid4())  # generate per request if absent
    cfg = GraphRunConfig.from_headers(thread_id=thread_id, user_id=user_id)
    stream = launch_graph(input_message=data.content, config=cfg)

    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Thread-Id": thread_id,
            "X-User-Id": str(uuid4()),
        }
    )


@app.post("/api/upload")
async def upload_document(
        request: Request,
        file: UploadFile = File(...),
        _token: str = Depends(JWTBearer()),
):
    # check MIME type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    # Optional: small signature check on first bytes (PDFs start with %PDF-)
    head = await file.read(5)
    await file.seek(0)
    if head != b"%PDF-":
        raise HTTPException(status_code=400, detail="File is not a valid PDF")

    try:
        inp = PdfSaverData(
            user_id=get_user_id(request),
            file=file,
            file_name=file.filename)
        result = pdf_saver.upsert(inp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {type(e).__name__}. " + str(e))

    return {"filename": file.filename, "status": "uploaded", "ingested": result}


def main():
    setup_logging()
    logger.info("Ciao")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=UVICORN_LOG)
