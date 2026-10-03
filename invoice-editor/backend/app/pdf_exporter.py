import io
from collections import defaultdict

import fitz

from .models import TextBlock


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
    edits_by_page: dict[int, list[tuple[TextBlock, str]]] = defaultdict(list)
    for edit in edits:
        block = blocks_map.get(edit["block_id"])
        if block is not None:
            edits_by_page[block.page].append((block, edit["new_text"]))

    for page_num, page_edits in edits_by_page.items():
        page = doc[page_num]

        # Phase 1: register all redactions for this page
        for block, _ in page_edits:
            rect = fitz.Rect(block.x0, block.y0, block.x1, block.y1)
            page.add_redact_annot(rect, fill=(1, 1, 1))

        # Phase 2: apply all redactions at once
        page.apply_redactions()

        # Phase 3: insert new text at original baseline
        helv = fitz.Font("helv")
        for block, new_text in page_edits:
            fontsize = block.size
            text_width = helv.text_length(new_text, fontsize=fontsize)
            orig_width = block.x1 - block.x0
            if text_width > orig_width:
                # Clear extra space so longer text isn't hidden behind existing content
                clear_rect = fitz.Rect(block.x0, block.y0, block.x0 + text_width + 2, block.y1)
                page.draw_rect(clear_rect, color=(1, 1, 1), fill=(1, 1, 1))
            page.insert_text(
                (block.x0, block.y1 - 1.0),
                new_text,
                fontname="helv",
                fontsize=fontsize,
                color=block.color,
            )

    buf = io.BytesIO()
    doc.save(buf, garbage=4, deflate=True)
    doc.close()
    return buf.getvalue()
