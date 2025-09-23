import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi import UploadFile, File
from pydantic import BaseModel, Field

from rag_app.config import CONFIG
from rag_app.document.user_document_handler import list_user_documents, UserDocument, delete_user_document

logger = logging.getLogger(__name__)
from rag_app.ingestion.pdf_store import PdfSaverData, pdf_saver
from rag_app.web_api.jwt_resolver import JWTBearer

document_router = APIRouter(prefix="/document")

class DocumentDeleted(BaseModel):
    file_name: str = Field(...)
    user_id: str = Field(...)
    status: str = Field(...)
    document_id: str = Field(...)

@document_router.post("/upload")
async def upload_document(
        file: UploadFile = File(...),
        user_id: str = Depends(JWTBearer()),
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
            user_id=user_id,
            file=file,
            file_name=file.filename)
        result = pdf_saver.upsert(inp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {type(e).__name__}. " + str(e))

    return {"filename": file.filename, "status": "uploaded", "ingested": result}


@document_router.get("/retrieve_documents", dependencies=[Depends(JWTBearer())])
def list_my_documents(user_id: str = Depends(JWTBearer())) -> List[UserDocument]:
    return list_user_documents(user_id=user_id)

@document_router.delete("/{document_id}")
def delete_document(document_id: str, user_id: str = Depends(JWTBearer())) -> DocumentDeleted:
    deleted = delete_user_document(user_id=user_id, document_id=document_id)
    #more than 0 chunks have been deleted
    if deleted > 0:
        return DocumentDeleted(document_id=document_id, user_id=user_id, status="deleted")
    raise HTTPException(status_code=404, detail="Document not found")
