import asyncio
from dataclasses import asdict
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
import fitz

from ..pdf_parser import extract_blocks, is_scanned_pdf
from ..session_store import create_session

router = APIRouter()


def _validate_pdf(pdf_bytes: bytes) -> None:
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except fitz.FileDataError:
        raise ValueError("corrupt")
    if doc.needs_pass:
        doc.close()
        raise ValueError("password")
    doc.close()


def _get_page_count(pdf_bytes: bytes) -> int:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    n = len(doc)
    doc.close()
    return n


async def _extract_blocks_async(pdf_bytes: bytes, scanned: bool):
    if not scanned:
        return await asyncio.to_thread(extract_blocks, pdf_bytes)
    try:
        from ..ocr_parser import extract_blocks_ocr
        return await asyncio.to_thread(extract_blocks_ocr, pdf_bytes)
    except (ImportError, RuntimeError):
        return await asyncio.to_thread(extract_blocks, pdf_bytes)
    except OSError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "El servidor no tiene OCR disponible, por eso no puede leer PDFs "
                "escaneados. Sube un PDF con texto seleccionable."
            ),
        ) from exc


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
):
    if doc_type not in ("regular", "fiscal"):
        raise HTTPException(status_code=400, detail="doc_type must be 'regular' or 'fiscal'")

    MAX_PDF_BYTES = 20 * 1024 * 1024  # 20 MB
    pdf_bytes = await file.read(MAX_PDF_BYTES + 1)
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF demasiado grande (máximo 20 MB).")

    try:
        await asyncio.to_thread(_validate_pdf, pdf_bytes)
    except ValueError as exc:
        if "password" in str(exc):
            raise HTTPException(status_code=400, detail="PDF protegido con contraseña no soportado.")
        raise HTTPException(status_code=400, detail="Archivo PDF inválido o corrupto.")

    scanned = await asyncio.to_thread(is_scanned_pdf, pdf_bytes)
    blocks = await _extract_blocks_async(pdf_bytes, scanned)
    page_count = await asyncio.to_thread(_get_page_count, pdf_bytes)

    session_id = create_session(doc_type, pdf_bytes, blocks)

    return {
        "session_id": session_id,
        "blocks": [asdict(b) for b in blocks],
        "page_count": page_count,
        "scanned": scanned,
    }
