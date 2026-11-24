"""An edit stays anchored where the original text sat in its cell, inside the borders.

Reported on a scanned invoice: a longer number typed in the right-aligned Total
column grew to the right and touched the cell's border line. It must keep the same
gap to the border instead, and never paint over a border.
"""
import fitz
import pytest

from app.models import TextBlock
from app.pdf_exporter import apply_edits

LEFT_RULE, RIGHT_RULE = 100.0, 300.0
SIZE = 8.0
HELV = fitz.Font("helv")
TOO_LONG = "B/ " + "1,234,567," * 6 + "0.00"  # about 270 pt at 8 pt: wider than the 200 pt cell


def _cell_pdf():
    page = fitz.open().new_page(width=612, height=792)
    for x in (LEFT_RULE, RIGHT_RULE):
        page.draw_line((x, 200), (x, 260), width=1)
    return page.parent.tobytes()


def _block(text, *, align="right", x0=None, x1=None):
    width = HELV.text_length(text, fontsize=SIZE)
    if x1 is None:
        x1 = x0 + width
    if x0 is None:
        x0 = x1 - width
    return TextBlock(
        block_id="b1", page=0, x0=x0, y0=222.0, x1=x1, y1=232.0, text=text,
        font="Helvetica", size=SIZE, color=(0.0, 0.0, 0.0), flags=0, editable=True,
        baseline=230.0, align=align, limit_x0=LEFT_RULE, limit_x1=RIGHT_RULE,
    )


def _export(block, new_text):
    out = apply_edits(_cell_pdf(), [{"block_id": "b1", "new_text": new_text}], {"b1": block})
    page = fitz.open(stream=out, filetype="pdf")[0]
    span = next(
        s for b in page.get_text("dict")["blocks"] for line in b.get("lines", [])
        for s in line["spans"] if s["text"] == new_text
    )
    return page, span


# ── anchoring ───────────────────────────────────────────────────────────────

def test_a_longer_right_aligned_edit_keeps_its_right_edge_and_grows_leftwards():
    block = _block("B/ 6.02", x1=290.0)

    _, span = _export(block, "B/ 12,345.67")

    assert span["bbox"][2] == pytest.approx(290.0, abs=0.8)
    assert span["bbox"][0] < block.x0


def test_a_shorter_right_aligned_edit_still_hugs_the_right_edge():
    _, span = _export(_block("B/ 12,345.67", x1=290.0), "B/ 5.00")

    assert span["bbox"][2] == pytest.approx(290.0, abs=0.8)


def test_a_centered_edit_keeps_its_center():
    block = _block("455", align="center", x0=190.0)

    _, span = _export(block, "12345")

    assert (span["bbox"][0] + span["bbox"][2]) / 2 == pytest.approx((block.x0 + block.x1) / 2, abs=0.8)


def test_a_left_aligned_edit_keeps_its_left_edge():
    _, span = _export(_block("Texto", align="left", x0=110.0), "Texto mas largo")

    assert span["bbox"][0] == pytest.approx(110.0, abs=0.8)


# ── staying inside the cell ─────────────────────────────────────────────────

def test_an_edit_too_wide_for_the_cell_shrinks_to_fit_between_its_borders():
    _, span = _export(_block("B/ 6.02", x1=290.0), TOO_LONG)

    assert span["size"] < SIZE
    assert span["bbox"][0] > LEFT_RULE
    assert span["bbox"][2] < RIGHT_RULE


def test_a_shrunk_edit_keeps_the_original_gap_to_the_border():
    _, span = _export(_block("B/ 6.02", x1=290.0), TOO_LONG)

    assert span["bbox"][2] == pytest.approx(290.0, abs=0.8)


def test_an_edit_that_fits_keeps_the_original_size():
    _, span = _export(_block("B/ 6.02", x1=290.0), "B/ 12,345.67")

    assert span["size"] == pytest.approx(SIZE, abs=0.01)


def _dark_pixels_near(page, x, *, scale=4, clip=fitz.Rect(90, 200, 310, 260)):
    pix = page.get_pixmap(dpi=72 * scale, clip=clip)
    column = round((x - clip.x0) * scale)
    row = round((230 - clip.y0) * scale)
    return [pix.pixel(c, row)[0] for c in range(column - 3, column + 4)]


@pytest.mark.parametrize("new_text", ["B/ 12,345.67", TOO_LONG])
def test_the_cell_borders_are_not_painted_over(new_text):
    page, _ = _export(_block("B/ 6.02", x1=290.0), new_text)

    assert min(_dark_pixels_near(page, RIGHT_RULE)) < 128
    assert min(_dark_pixels_near(page, LEFT_RULE)) < 128


def test_a_left_aligned_overflowing_edit_does_not_paint_over_the_right_border():
    page, _ = _export(_block("Texto", align="left", x0=110.0), TOO_LONG)

    assert min(_dark_pixels_near(page, RIGHT_RULE)) < 128


# ── blocks without cell limits behave as before ─────────────────────────────

def test_a_block_without_limits_grows_rightwards_from_its_left_edge():
    block = _block("Texto", align="left", x0=110.0)
    block = TextBlock(**{**block.__dict__, "limit_x0": None, "limit_x1": None})

    _, span = _export(block, TOO_LONG)

    assert span["bbox"][0] == pytest.approx(110.0, abs=0.8)
    assert span["size"] == pytest.approx(SIZE, abs=0.01)
