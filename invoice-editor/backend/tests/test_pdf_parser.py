from app.pdf_parser import extract_blocks, is_scanned_pdf


def test_extract_blocks_returns_text_blocks(minimal_pdf_bytes):
    blocks = extract_blocks(minimal_pdf_bytes)
    assert len(blocks) >= 2
    texts = [b.text for b in blocks]
    assert any("Factura" in t for t in texts)


def test_extract_blocks_have_coordinates(minimal_pdf_bytes):
    blocks = extract_blocks(minimal_pdf_bytes)
    for b in blocks:
        assert b.x1 > b.x0
        assert b.y1 > b.y0
        assert b.page == 0


def test_extract_blocks_have_unique_ids(minimal_pdf_bytes):
    blocks = extract_blocks(minimal_pdf_bytes)
    ids = [b.block_id for b in blocks]
    assert len(ids) == len(set(ids))


def test_is_scanned_pdf_returns_false_for_digital(minimal_pdf_bytes):
    assert is_scanned_pdf(minimal_pdf_bytes) is False


def test_is_scanned_pdf_returns_true_for_image_only(scanned_pdf_bytes):
    assert is_scanned_pdf(scanned_pdf_bytes) is True
