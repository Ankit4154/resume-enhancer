from fastapi import APIRouter, UploadFile, File, HTTPException
from services.pdf_service import PDFService
from uuid import uuid4
import os

router = APIRouter()
pdf_service = PDFService()

@router.post("/upload")
async def upload_resume(resume: UploadFile = File(...)):
    print(f"Received file: {resume.filename}, content type: {resume.content_type}")
    if resume.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Must be PDF")
    temp_path=f"/tmp/{uuid4()}.pdf"
    # Extract the directory path from the full file path
    directory = os.path.dirname(temp_path)

    # Create the directory if it does not exist
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    with open(temp_path, "wb") as f:
        f.write(await resume.read())
    text = await pdf_service.extract_text(temp_path)
    await pdf_service.cleanup(temp_path)
    return {"id": str(uuid4()), "text": text}