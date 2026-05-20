from __future__ import annotations

import io
import re
from fastapi import UploadFile, HTTPException
import PyPDF2
from core.config import logger

MAX_FILE_CHARS = 15000  # Cap extracted text length to protect LLM context window

async def extract_text_from_upload(upload: UploadFile) -> str:
    """
    Extracts text securely from an uploaded file (.txt or .pdf).
    Includes length limits and basic sanitization to protect tokenizers.
    """
    try:
        content = await upload.read()
    except Exception as exc:
        logger.error("Failed to read file buffer: %s", exc)
        raise HTTPException(status_code=400, detail="Unable to read the uploaded file.")

    filename = upload.filename or "unknown"
    
    try:
        if filename.lower().endswith(".pdf"):
            text = _extract_from_pdf(content)
        else:
            # Default to text decoding
            text = content.decode("utf-8", errors="replace")
    except Exception as exc:
        logger.error("Failed to parse document %s: %s", filename, exc)
        raise HTTPException(status_code=400, detail=f"Failed to parse document. Ensure {filename} is a valid text or PDF file.")
        
    text = text.strip()
    
    if not text:
        raise HTTPException(status_code=400, detail="The uploaded document contains no readable text.")

    # Sanitize: Remove null bytes and corrupted invisible control chars
    text = re.sub(r"[\x00\x08\x0b\x0c\x0e-\x1f]", "", text)
    
    # Enforce hard length limit
    if len(text) > MAX_FILE_CHARS:
        logger.warning("Truncated uploaded file %s from %d to %d chars.", filename, len(text), MAX_FILE_CHARS)
        text = text[:MAX_FILE_CHARS] + "\n\n[DOCUMENT TRUNCATED DUE TO LENGTH LIMIT]"
        
    return text

def _extract_from_pdf(content: bytes) -> str:
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
    text_parts = []
    
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
            
        # Fast exit if we already exceeded limit
        if sum(len(p) for p in text_parts) > MAX_FILE_CHARS + 1000:
            break
            
    return "\n\n".join(text_parts)
