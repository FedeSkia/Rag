import logging

from fastapi import UploadFile, File, HTTPException, Depends, APIRouter

logger = logging.getLogger(__name__)
from rag_app.ingestion.pdf_store import PdfSaverData, pdf_saver
from rag_app.web_api.jwt_resolver import JWTBearer

document_router = APIRouter(prefix="/document")


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
