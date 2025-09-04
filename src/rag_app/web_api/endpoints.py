import logging
import time
from typing import Optional
from uuid import uuid4

import httpx
import jwt
import uvicorn
from fastapi import FastAPI, Header, UploadFile, File, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

logger = logging.getLogger(__name__)
from rag_app.config import CONFIG
from rag_app.agent.graph import launch_graph, create_graph
from rag_app.agent.graph_configuration import GraphRunConfig
from rag_app.ingestion.pdf_store import PdfSaverData, pdf_saver
from rag_app.logging_setup import setup_logging, RequestContextMiddleware, UVICORN_LOG
from rag_app.web_api.jwt_resolver import JWTBearer, get_user_id


class InputData(BaseModel):
    content: str


class CreateUser(BaseModel):
    email: str
    password: str


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


@app.get("/api/debug/get_user_thread")
def get_user_thread(request: Request,
                    _token: str = Depends(JWTBearer()),
                    x_thread_id: Optional[str] = Header(..., alias="X-Thread-Id")):
    user_id = get_user_id(request)

    cfg: RunnableConfig = {"configurable": {
        "thread_id": x_thread_id,
        "checkpoint_ns": user_id,
        "checkpoint_namespace": user_id,  # compat
    }}
    return create_graph().get_state(config=cfg)  # .values["messages"] holds the history


def _mint_service_jwt() -> str:
    """Create a short-lived service-role JWT for GoTrue admin endpoints."""
    now = int(time.time())
    payload = {
        "sub": "admin-cli",
        "role": "service_role",  # must be allowed by GOTRUE_JWT_ADMIN_ROLES
        "aud": "authenticated",
        "iat": now,
        "exp": now + 3600,
    }
    return jwt.encode(payload, CONFIG.JWT_SECRET, algorithm=CONFIG.JWT_ALG)


@app.delete("/api/admin/delete_user?user_id={user_id}")
async def delete_user_admin(user_id: str):
    """Admin: delete a user in local GoTrue via /admin/users/{id}.
    Requires that CONFIG.JWT_SECRET matches GoTrue's signing secret
    and that `service_role` is included in GOTRUE_JWT_ADMIN_ROLES.
    """
    admin_jwt = _mint_service_jwt()
    url = f"{CONFIG.GOTRUE_URL}/admin/users/{user_id}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.delete(url, headers={
            "Authorization": f"Bearer {admin_jwt}",
        })
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return {"status": "deleted", "user_id": user_id}



@app.post("/api/admin/create_user")
async def create_user_admin(req: CreateUser):
    async with httpx.AsyncClient(base_url=CONFIG.GOTRUE_URL, timeout=10) as client:
        resp = await client.post(
            "/signup",
            json=req.model_dump(),
            headers={"Accept": "application/json"},
        )

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    # GoTrue returns the user/session payload; return or shape as you like
    return {"status": "created", "gotrue": resp.json()}


def main():
    setup_logging()
    logger.info("Ciao")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=UVICORN_LOG)
