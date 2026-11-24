"""End to end: every text of a scanned bordered table becomes an editable block.

Needs the tesseract binary, so it is skipped on machines without it and runs in the
Docker image (mount the tests folder to run it there). The scan is synthetic: header
and body cells with a number alone in each, all enclosed by the table's rules.
"""
import shutil

import fitz
import pytest

from app.ocr_parser import extract_blocks_ocr

pytestmark = pytest.mark.skipif(
    shutil.which("tesseract") is None,
    reason="needs the tesseract binary (available inside the Docker image)",
)

COLUMNS = [40, 100, 300, 400, 480, 570]
TOP, ROW_HEIGHT = 250, 30
HEADER = ["Cant.", "Descripcion", "Precio", "Desc.", "Total"]
BODY = ["455", "DIESEL REGULAR", "6.02", "0.00", "2,739.10"]


def _scanned_table(rows):
    page = fitz.open().new_page(width=612, height=792)
    for r in range(len(rows) + 1):
        page.draw_line((COLUMNS[0], TOP + r * ROW_HEIGHT), (COLUMNS[-1], TOP + r * ROW_HEIGHT), width=1)
    for x in COLUMNS:
        page.draw_line((x, TOP), (x, TOP + len(rows) * ROW_HEIGHT), width=1)
    for r, texts in enumerate(rows):
        for (x0, x1), text in zip(zip(COLUMNS, COLUMNS[1:]), texts):
            width = fitz.get_text_length(text, "helv", 8)
            page.insert_text(((x0 + x1) / 2 - width / 2, TOP + r * ROW_HEIGHT + 19), text, fontname="helv", fontsize=8)
    scan = fitz.open()
    scan.new_page(width=612, height=792).insert_image(fitz.Rect(0, 0, 612, 792), pixmap=page.get_pixmap(dpi=300))
    return scan.tobytes(deflate=True)


def test_every_cell_of_a_bordered_table_is_editable():
    texts = {block.text for block in extract_blocks_ocr(_scanned_table([HEADER, BODY]))}

    assert set(HEADER + BODY) <= texts


def test_a_lone_number_in_a_narrow_cell_is_editable():
    texts = {block.text for block in extract_blocks_ocr(_scanned_table([HEADER, ["455", "x", "x", "x", "x"]]))}

    assert "455" in texts
