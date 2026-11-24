"""OCR blocks must carry the original text's size, weight and baseline, and the
exporter must draw edits with exactly those. Synthetic data only, no tesseract.
"""
import fitz
import pytest
from PIL import Image

from app.models import TextBlock
from app.ocr_parser import (
    _with_ink_baseline,
    _with_weight,
    BOLD_STROKE_RATIO,
    blocks_from_tesseract_data,
    estimate_font_size,
    ink_baseline_row,
    ink_stroke_ratio,
    snap_sizes,
)
from app.pdf_exporter import apply_edits

DPI = 300
PX_PER_PT = DPI / 72.0
CAP = 0.718  # Helvetica cap height, em
DESC = 0.207  # Helvetica descender, em
HELV = fitz.Font("helv")


def _width_pt(text, size):
    return HELV.text_length(text, fontsize=size)


def _tesseract_word(text, size, *, descender=False, left_px=100, top_px=100, line=1):
    """One word as pytesseract would box it for `text` set in Helvetica at `size` pt."""
    height_pt = (CAP + (DESC if descender else 0.0)) * size
    return {
        "block_num": [1], "par_num": [1], "line_num": [line],
        "left": [left_px], "top": [top_px],
        "width": [round(_width_pt(text, size) * PX_PER_PT)],
        "height": [round(height_pt * PX_PER_PT)],
        "conf": [90], "text": [text],
    }


# ── size estimation ─────────────────────────────────────────────────────────

def test_size_comes_from_box_width_and_height_when_they_agree():
    size = estimate_font_size("Fecha 2026", _width_pt("Fecha 2026", 8), CAP * 8)

    assert size == pytest.approx(8.0, abs=0.3)


def test_inflated_box_height_is_ignored_for_longer_text():
    # Table borders can stretch a word box vertically (seen on "Sub-Total").
    size = estimate_font_size("Sub-Total", _width_pt("Sub-Total", 8), CAP * 13)

    assert size == pytest.approx(8.0, abs=0.4)


def test_short_text_trusts_height_because_bearings_shrink_the_width():
    size = estimate_font_size("1/1", _width_pt("1/1", 8) * 0.75, CAP * 8)

    assert size == pytest.approx(8.0, abs=0.3)


def test_snap_sizes_merges_close_sizes_into_the_dominant_one():
    sizes = [8.0] * 5 + [8.4] * 3 + [7.6] * 2 + [15.4]

    assert snap_sizes(sizes) == [8.0] * 10 + [15.0]


def test_snap_sizes_rounds_to_whole_points_like_real_invoices():
    # Reference invoice: 9 pt "RUC:" and 15 pt "Documento No Fiscal", OCR gave 9.4 and 15.4.
    assert snap_sizes([9.4, 15.4]) == [9.0, 15.0]


# ── blocks carry size and baseline ──────────────────────────────────────────

def test_block_gets_estimated_size_and_default_font():
    (block,) = blocks_from_tesseract_data(_tesseract_word("Total", 8), page_num=0)

    assert block.size == pytest.approx(8.0, abs=0.5)
    assert block.font == "Helvetica"
    assert block.flags == 0


def test_baseline_is_box_bottom_when_text_has_no_descender():
    (block,) = blocks_from_tesseract_data(_tesseract_word("Total", 8), page_num=0)

    assert block.baseline == pytest.approx(block.y1)


def test_baseline_sits_above_box_bottom_when_text_has_descender():
    (block,) = blocks_from_tesseract_data(_tesseract_word("Pago", 8, descender=True), page_num=0)

    assert block.baseline == pytest.approx(block.y1 - DESC * block.size, abs=0.05)


def test_sizes_on_one_page_are_snapped_together():
    word_a = _tesseract_word("Detalle", 8, left_px=100, top_px=100, line=1)
    word_b = _tesseract_word("Cliente", 8.3, left_px=100, top_px=200, line=2)
    word_c = _tesseract_word("Credito", 7.8, left_px=100, top_px=300, line=3)
    data = {key: word_a[key] + word_b[key] + word_c[key] for key in word_a}

    sizes = {block.size for block in blocks_from_tesseract_data(data, page_num=0)}

    assert len(sizes) == 1


# ── bold detection by stroke thickness ──────────────────────────────────────

def _render_gray(text, fontname, size):
    doc = fitz.open()
    page = doc.new_page(width=220, height=40)
    page.insert_text((6, 26), text, fontname=fontname, fontsize=size)
    pix = page.get_pixmap(dpi=DPI)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples).convert("L")


@pytest.mark.parametrize("size", [8, 10, 14])
def test_regular_text_is_below_the_bold_threshold(size):
    assert ink_stroke_ratio(_render_gray("Detalle: Fecha", "helv", size), size) < BOLD_STROKE_RATIO


@pytest.mark.parametrize("size", [8, 10, 14])
def test_bold_text_is_above_the_bold_threshold(size):
    assert ink_stroke_ratio(_render_gray("Detalle: Fecha", "hebo", size), size) > BOLD_STROKE_RATIO


# ── exporter draws with the block's own font, size and baseline ─────────────

def _spans(pdf_bytes):
    page = fitz.open(stream=pdf_bytes, filetype="pdf")[0]
    return [
        span
        for block in page.get_text("dict")["blocks"]
        for line in block.get("lines", [])
        for span in line["spans"]
    ]


def _block(**overrides):
    base = dict(
        block_id="b1", page=0, x0=100.0, y0=90.0, x1=170.0, y1=102.0,
        text="Factura 001", font="Helvetica", size=9.0, color=(0.0, 0.0, 0.0),
        flags=0, editable=True,
    )
    base.update(overrides)
    return TextBlock(**base)


def _new_span(minimal_pdf_bytes, block, font=None):
    edit = {"block_id": "b1", "new_text": "NUEVO"}
    if font is not None:
        edit["font"] = font
    out = apply_edits(minimal_pdf_bytes, [edit], {"b1": block})
    return next(s for s in _spans(out) if s["text"] == "NUEVO")


def test_exporter_draws_bold_blocks_in_helvetica_bold(minimal_pdf_bytes):
    span = _new_span(minimal_pdf_bytes, _block(font="Helvetica-Bold", flags=16))

    assert "bold" in span["font"].lower()
    assert span["size"] == pytest.approx(9.0, abs=0.01)


def test_exporter_keeps_regular_blocks_in_regular_helvetica(minimal_pdf_bytes):
    span = _new_span(minimal_pdf_bytes, _block())

    assert "bold" not in span["font"].lower()


def test_exporter_uses_the_block_baseline_when_given(minimal_pdf_bytes):
    span = _new_span(minimal_pdf_bytes, _block(baseline=99.0))

    assert span["origin"][1] == pytest.approx(99.0, abs=0.05)


def test_exporter_falls_back_to_bottom_minus_one_without_baseline(minimal_pdf_bytes):
    span = _new_span(minimal_pdf_bytes, _block())

    assert span["origin"][1] == pytest.approx(101.0, abs=0.05)


# ── a font picked for the edit wins over the block's detected font ──────────

@pytest.mark.parametrize("font", ["Helvetica", "Helvetica-Bold", "Courier", "Courier-Bold"])
def test_exporter_draws_the_font_chosen_for_the_edit(minimal_pdf_bytes, font):
    span = _new_span(minimal_pdf_bytes, _block(), font=font)

    assert span["font"] == font
    assert span["size"] == pytest.approx(9.0, abs=0.01)


def test_exporter_font_choice_overrides_the_block_font(minimal_pdf_bytes):
    span = _new_span(minimal_pdf_bytes, _block(font="Helvetica-Bold", flags=16), font="Courier")

    assert span["font"] == "Courier"


def test_exporter_falls_back_to_helvetica_for_an_unknown_font_name(minimal_pdf_bytes):
    span = _new_span(minimal_pdf_bytes, _block(), font="Comic-Sans")

    assert span["font"] == "Helvetica"


# ── baseline measured on the image, robust to table rules ───────────────────

BASELINE_ROW_PX = 26 * PX_PER_PT  # text below is drawn with its baseline at y = 26 pt


def _render_baseline_page(text, *, rules=False):
    doc = fitz.open()
    page = doc.new_page(width=220, height=40)
    page.insert_text((6, 26), text, fontname="helv", fontsize=10)
    if rules:
        page.draw_line((0, 3), (220, 3), width=1)  # horizontal rule near the top
        page.draw_line((2, 0), (2, 40), width=1)   # vertical rule at the left edge
    pix = page.get_pixmap(dpi=DPI)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples).convert("L")


@pytest.mark.parametrize("text", ["Fecha 2026", "Pago", "Cliente: Jorge"])
def test_baseline_row_ignores_descenders(text):
    assert ink_baseline_row(_render_baseline_page(text)) == pytest.approx(BASELINE_ROW_PX, abs=2)


def test_baseline_row_ignores_table_rules():
    row = ink_baseline_row(_render_baseline_page("Fecha 2026", rules=True))

    assert row == pytest.approx(BASELINE_ROW_PX, abs=2)


def test_baseline_row_is_none_without_text():
    assert ink_baseline_row(Image.new("L", (200, 40), 255)) is None


# ── image baseline is only used when the box is stretched ───────────────────

def _page_gray(draw):
    doc = fitz.open()
    page = doc.new_page(width=220, height=60)
    draw(page)
    pix = page.get_pixmap(dpi=DPI)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples).convert("L")


def _ink_box_pt(gray, rows=None):
    ink = gray.point(lambda value: 255 if value < 128 else 0)
    left, top, right, bottom = ink.getbbox()
    return left / PX_PER_PT, top / PX_PER_PT, right / PX_PER_PT, bottom / PX_PER_PT


def test_tight_box_keeps_its_geometric_baseline():
    # Stems of "1" span the whole box; they must not be mistaken for table rules.
    gray = _page_gray(lambda page: page.insert_text((10, 40), "1/1", fontname="helv", fontsize=8))
    x0, y0, x1, y1 = _ink_box_pt(gray)
    block = _block(text="1/1", size=8.0, x0=x0, y0=y0, x1=x1, y1=y1, baseline=y1)

    assert _with_ink_baseline(block, gray).baseline == block.baseline


def test_stretched_box_gets_its_baseline_from_the_image():
    def draw(page):
        page.insert_text((10, 40), "Total", fontname="helv", fontsize=8)
        page.draw_line((0, 25), (220, 25), width=0.8)  # table rules around the word
        page.draw_line((0, 48), (220, 48), width=0.8)

    gray = _page_gray(draw)
    block = _block(text="Total", size=8.0, x0=10.0, y0=24.6, x1=34.0, y1=48.4, baseline=48.4)

    assert _with_ink_baseline(block, gray).baseline == pytest.approx(40.0, abs=0.6)


# ── bold text is sized with Helvetica-Bold widths ───────────────────────────

def test_bold_text_width_is_measured_with_bold_metrics():
    bold_width = fitz.Font("hebo").text_length("Descripcion", fontsize=8)

    size = estimate_font_size("Descripcion", bold_width, (CAP + DESC) * 8, bold=True)

    assert size == pytest.approx(8.0, abs=0.3)


def test_weight_pass_flags_bold_and_corrects_the_size():
    gray = _page_gray(lambda page: page.insert_text((10, 40), "Descripcion", fontname="hebo", fontsize=8))
    x0, y0, x1, y1 = _ink_box_pt(gray)
    # 8.6 is what regular-weight widths estimate for this bold text (it is ~7% wider).
    block = _block(text="Descripcion", size=8.6, x0=x0, y0=y0, x1=x1, y1=y1)

    result = _with_weight(block, gray)

    assert result.font == "Helvetica-Bold"
    assert result.flags & 16
    assert result.size == pytest.approx(8.0, abs=0.4)


def test_weight_pass_leaves_regular_text_alone():
    gray = _page_gray(lambda page: page.insert_text((10, 40), "Descripcion", fontname="helv", fontsize=8))
    x0, y0, x1, y1 = _ink_box_pt(gray)
    block = _block(text="Descripcion", size=8.0, x0=x0, y0=y0, x1=x1, y1=y1)

    assert _with_weight(block, gray) == block


# ── table border pipes are not text ─────────────────────────────────────────

def test_table_border_pipe_is_stripped_from_the_text():
    (block,) = blocks_from_tesseract_data(_tesseract_word("|30-", 8), page_num=0)

    assert block.text == "30-"


def test_a_lone_pipe_is_dropped():
    assert blocks_from_tesseract_data(_tesseract_word("|", 8), page_num=0) == []
