import io
from collections import defaultdict

import fitz

from .models import FITZ_FONTS, TextBlock


def apply_edits(
    pdf_bytes: bytes,
    edits: list[dict],
    blocks_map: dict[str, TextBlock],
    doc_type: str = "regular",
) -> bytes:
    """Apply text edits to a PDF via PyMuPDF redact+rewrite pipeline.

    For each edit: covers original text area with a white redaction box,
    then inserts new text at the same position with matching font/size/color.

    Pipeline order per page (as required):
      1. add_redact_annot for all edits on the page
      2. apply_redactions (removes original content under the boxes)
      3. insert_text for each edit at the original baseline
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # Group edits by page so apply_redactions runs once per page
    edits_by_page: dict[int, list[tuple[TextBlock, str, str]]] = defaultdict(list)
    for edit in edits:
        block = blocks_map.get(edit["block_id"])
        if block is not None:
            # The font picked for an edit wins over the block's own; unknown names draw as Helvetica.
            fontname = FITZ_FONTS.get(edit.get("font") or block.font, "helv")
            edits_by_page[block.page].append((block, edit["new_text"], fontname))

    for page_num, page_edits in edits_by_page.items():
        page = doc[page_num]

        fonts = {name: fitz.Font(name) for name in FITZ_FONTS.values()}
        for block, new_text, fontname in page_edits:
            fontsize = _fitted_size(block, new_text, fonts[fontname])
            text_width = fonts[fontname].text_length(new_text, fontsize=fontsize)
            x = _anchored_x(block, text_width)

            # Cover original text with a white rectangle drawn in the content stream.
            # draw_rect does NOT erase PDF XObjects (images, vector graphics) — it
            # simply paints white on top of them in drawing order, so logos and other
            # graphics behind the text area are preserved in the file and render
            # correctly when the new text does not overlap them. The cover never reaches
            # a table border, so the border lines stay intact.
            page.draw_rect(_cover_rect(block, x, text_width), color=(1, 1, 1), fill=(1, 1, 1))

            baseline = block.baseline if block.baseline is not None else block.y1 - 1.0
            page.insert_text(
                (x, baseline),
                new_text,
                fontname=fontname,
                fontsize=fontsize,
                color=block.color,
            )

    buf = io.BytesIO()
    doc.save(buf, garbage=4, deflate=True)
    doc.close()
    return buf.getvalue()


_MIN_CELL_MARGIN_PT = 1.5   # the least gap an edit keeps to a cell border
_BORDER_CLEARANCE_PT = 1.5  # the white cover stops this far from a border


def _cell_margin(block: TextBlock) -> float:
    """The gap the original text left to the border on the side it is anchored to."""
    gap_left = block.x0 - block.limit_x0
    gap_right = block.limit_x1 - block.x1
    gap = {"right": gap_right, "left": gap_left}.get(block.align, min(gap_left, gap_right))
    return max(gap, _MIN_CELL_MARGIN_PT)


def _fitted_size(block: TextBlock, text: str, font: fitz.Font) -> float:
    """The block's size, reduced only if the text would not fit between its cell borders."""
    if block.limit_x0 is None or block.limit_x1 is None:
        return block.size
    available = block.limit_x1 - block.limit_x0 - 2 * _cell_margin(block)
    width = font.text_length(text, fontsize=block.size)
    if available <= 0 or width <= available:
        return block.size
    return block.size * available / width


def _anchored_x(block: TextBlock, width: float) -> float:
    """Where the text starts so it keeps the anchor of the original: left edge, right edge or center."""
    if block.align == "right":
        return block.x1 - width
    if block.align == "center":
        return (block.x0 + block.x1) / 2 - width / 2
    return block.x0


def _cover_rect(block: TextBlock, x: float, width: float) -> fitz.Rect:
    """The white patch over the original text and the new one, held clear of the cell borders."""
    left = min(block.x0, x)
    right = max(block.x1, x + width + 2)
    if block.limit_x0 is not None:
        left = max(left, block.limit_x0 + _BORDER_CLEARANCE_PT)
    if block.limit_x1 is not None:
        right = min(right, block.limit_x1 - _BORDER_CLEARANCE_PT)
    return fitz.Rect(left, block.y0, right, block.y1)
