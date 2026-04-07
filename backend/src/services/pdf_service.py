import pymupdf 
import os
from pathlib import Path

class PDFService:
    async def extract_text(self, file_path: str) -> str:
        doc = pymupdf.open(file_path)
        text = ""
        for page in doc:
            text += str(page.get_text())
        return text

    async def cleanup(self, file_path: str):
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception:
            pass