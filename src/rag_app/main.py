from typing import Optional
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Header, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from starlette import status

from rag_app.config import CONFIG
from rag_app.agent.graph import launch_graph
from rag_app.agent.graph_configuration import GraphRunConfig
from rag_app.ingestion.pdf_store import PdfSaverData, pdf_saver

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CONFIG.ALLOW_ORIGINS],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


class InputData(BaseModel):
    content: str


@app.post("/api/invoke")
async def invoke(
        data: InputData,
        x_thread_id: Optional[str] = Header(..., alias="X-Thread-Id"),
        x_user_id: str = Header(..., alias="X-User-Id")
):
    thread_id = x_thread_id or str(uuid4())  # generate per request if absent
    cfg = GraphRunConfig.from_headers(thread_id=thread_id, user_id=x_user_id)
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
        file: UploadFile = File(...),
        x_user_id: str = Header(..., alias="X-User-Id"),
):
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing x-user-id")
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
            user_id=x_user_id,
            file=file,
            file_name=file.filename)
        result = pdf_saver.upsert(inp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {type(e).__name__}. " + str(e))

    return {"filename": file.filename, "status": "uploaded", "ingested": result}


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
