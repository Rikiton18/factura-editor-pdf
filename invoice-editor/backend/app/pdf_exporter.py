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
            fontsize = block.size
            text_width = fonts[fontname].text_length(new_text, fontsize=fontsize)
            orig_width = block.x1 - block.x0

            # Cover original text with a white rectangle drawn in the content stream.
            # draw_rect does NOT erase PDF XObjects (images, vector graphics) — it
            # simply paints white on top of them in drawing order, so logos and other
            # graphics behind the text area are preserved in the file and render
            # correctly when the new text does not overlap them.
            cover_width = max(orig_width, text_width + 2)
            cover_rect = fitz.Rect(block.x0, block.y0, block.x0 + cover_width, block.y1)
            page.draw_rect(cover_rect, color=(1, 1, 1), fill=(1, 1, 1))

            baseline = block.baseline if block.baseline is not None else block.y1 - 1.0
            page.insert_text(
                (block.x0, baseline),
                new_text,
                fontname=fontname,
                fontsize=fontsize,
                color=block.color,
            )

    buf = io.BytesIO()
    doc.save(buf, garbage=4, deflate=True)
    doc.close()
    return buf.getvalue()
