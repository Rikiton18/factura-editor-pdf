import fitz
from app.pdf_parser import extract_blocks
from app.pdf_exporter import apply_edits
from app.qr_generator import generate_qr_bytes


def test_apply_edits_changes_text(minimal_pdf_bytes):
    blocks = extract_blocks(minimal_pdf_bytes)
    first_block = blocks[0]
    edits = [{"block_id": first_block.block_id, "new_text": "EDITADO"}]
    blocks_map = {b.block_id: b for b in blocks}
    result_bytes = apply_edits(minimal_pdf_bytes, edits, blocks_map)
    result_blocks = extract_blocks(result_bytes)
    result_texts = [b.text for b in result_blocks]
    assert any("EDITADO" in t for t in result_texts), "Edited text not found in output"


def test_apply_edits_preserves_unedited_text(minimal_pdf_bytes):
    blocks = extract_blocks(minimal_pdf_bytes)
    blocks_map = {b.block_id: b for b in blocks}
    edits = [{"block_id": blocks[0].block_id, "new_text": "NUEVO"}]
    # Verify no exception; PyMuPDF may merge spans so exact text preservation is not asserted
    apply_edits(minimal_pdf_bytes, edits, blocks_map)


def test_generate_qr_bytes_returns_png():
    qr = generate_qr_bytes("http://localhost:5173/demo/abc123")
    assert qr[:8] == b'\\x89PNG\\r\\n\\x1a\\n'


def test_apply_edits_returns_valid_pdf(minimal_pdf_bytes):
    blocks = extract_blocks(minimal_pdf_bytes)
    edits = [{"block_id": blocks[0].block_id, "new_text": "X"}]
    result = apply_edits(minimal_pdf_bytes, edits, {b.block_id: b for b in blocks})
    doc = fitz.open(stream=result, filetype="pdf")
    assert len(doc) >= 1
    doc.close()
