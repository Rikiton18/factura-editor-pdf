import base64
import io

import fitz
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..config import settings
from ..pdf_exporter import apply_edits
from ..qr_generator import replace_qr_in_doc
from ..session_store import get_session, update_session_edits

router = APIRouter()


class EditItem(BaseModel):
    block_id: str
    new_text: str


class ExportRequest(BaseModel):
    edits: list[EditItem]
    regenerate_qr: bool = False


@router.post("/export/{session_id}")
async def export_pdf(session_id: str, req: ExportRequest):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    blocks_map = {b.block_id: b for b in session.blocks}
    edit_dicts = [{"block_id": e.block_id, "new_text": e.new_text} for e in req.edits]

    pdf_bytes = apply_edits(session.pdf_bytes, edit_dicts, blocks_map, doc_type=session.doc_type)

    if session.doc_type == "fiscal" and req.regenerate_qr:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        replace_qr_in_doc(doc, session_id, settings.BASE_URL)
        buf = io.BytesIO()
        doc.save(buf)
        doc.close()
        pdf_bytes = buf.getvalue()

    # Persist edits so the demo page can read them
    update_session_edits(session_id, {e.block_id: e.new_text for e in req.edits})

    return {"pdf_base64": base64.b64encode(pdf_bytes).decode()}
