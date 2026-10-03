import base64
from dataclasses import asdict
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
import fitz

from ..pdf_parser import extract_blocks, is_scanned_pdf
from ..session_store import create_session

router = APIRouter()


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
):
    if doc_type not in ("regular", "fiscal"):
        raise HTTPException(status_code=400, detail="doc_type must be 'regular' or 'fiscal'")

    pdf_bytes = await file.read()

    try:
        _doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if _doc.needs_pass:
            _doc.close()
            raise HTTPException(status_code=400, detail="PDF protegido con contraseña no soportado.")
        _doc.close()
    except fitz.FileDataError:
        raise HTTPException(status_code=400, detail="Archivo PDF inválido o corrupto.")

    scanned = is_scanned_pdf(pdf_bytes)

    if scanned:
        # Phase 2 OCR path — gated; falls back to normal parser until pytesseract is installed
        try:
            from ..ocr_parser import extract_blocks_ocr
            blocks = extract_blocks_ocr(pdf_bytes)
        except (ImportError, RuntimeError):
            blocks = extract_blocks(pdf_bytes)
    else:
        blocks = extract_blocks(pdf_bytes)

    session_id = create_session(doc_type, pdf_bytes, blocks)

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_count = len(doc)
    doc.close()

    return {
        "session_id": session_id,
        "pdf_base64": base64.b64encode(pdf_bytes).decode(),
        "blocks": [asdict(b) for b in blocks],
        "page_count": page_count,
        "scanned": scanned,  # frontend can show "Modo OCR" badge
    }
