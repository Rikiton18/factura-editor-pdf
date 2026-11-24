import fitz
from .alignment import assign_alignment
from .models import TextBlock


def _int_to_rgb(color_int: int) -> tuple[float, float, float]:
    r = ((color_int >> 16) & 0xFF) / 255.0
    g = ((color_int >> 8) & 0xFF) / 255.0
    b = (color_int & 0xFF) / 255.0
    return (r, g, b)


def _text_from_span(span: dict) -> str:
    """Extract text from a rawdict span (uses chars list)."""
    chars = span.get("chars", [])
    if chars:
        return "".join(c.get("c", "") for c in chars)
    # Fallback to "text" key (dict format)
    return span.get("text", "")


_MIN_RULE_LENGTH_PT = 8.0
_MAX_RULE_THICKNESS_PT = 2.0


def _vertical_rules(page) -> list[tuple[float, float, float]]:
    """(x, top, bottom) of the vertical lines drawn on the page: the borders of tables."""
    rules = []
    for drawing in page.get_drawings():
        outlined = drawing.get("fill") is None
        for item in drawing["items"]:
            if item[0] == "l":
                start, end = item[1], item[2]
                if abs(start.x - end.x) < 0.5 and abs(start.y - end.y) >= _MIN_RULE_LENGTH_PT:
                    rules.append(((start.x + end.x) / 2, min(start.y, end.y), max(start.y, end.y)))
            elif item[0] == "re":
                rect = item[1]
                if rect.height < _MIN_RULE_LENGTH_PT:
                    continue
                if rect.width <= _MAX_RULE_THICKNESS_PT:
                    rules.append(((rect.x0 + rect.x1) / 2, rect.y0, rect.y1))
                elif outlined:  # the sides of a table frame
                    rules.extend([(rect.x0, rect.y0, rect.y1), (rect.x1, rect.y0, rect.y1)])
    return rules


def _rules_at(page):
    rules = _vertical_rules(page)

    def at(block: TextBlock) -> list[float]:
        middle = (block.y0 + block.y1) / 2
        return [x for x, top, bottom in rules if top <= middle <= bottom]

    return at


def extract_blocks(pdf_bytes: bytes) -> list[TextBlock]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    blocks: list[TextBlock] = []
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            raw = page.get_text("rawdict")
            span_counter = 0
            page_blocks: list[TextBlock] = []
            for block_idx, block in enumerate(raw["blocks"]):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = _text_from_span(span).strip()
                        bbox = span["bbox"]
                        page_blocks.append(TextBlock(
                            block_id=f"p{page_num}-b{block_idx}-s{span_counter}",
                            page=page_num,
                            x0=float(bbox[0]),
                            y0=float(bbox[1]),
                            x1=float(bbox[2]),
                            y1=float(bbox[3]),
                            text=text,
                            font=span.get("font", "Helvetica"),
                            size=float(span.get("size", 12)),
                            color=_int_to_rgb(span.get("color", 0)),
                            flags=int(span.get("flags", 0)),
                            editable=bool(text),
                        ))
                        span_counter += 1
            blocks.extend(assign_alignment(page_blocks, _rules_at(page)))
    finally:
        doc.close()
    return blocks


def is_scanned_pdf(pdf_bytes: bytes) -> bool:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        for page in doc:
            text_chars = len(page.get_text("text").strip())
            images = page.get_images()
            if text_chars == 0 and len(images) >= 1:
                return True
        return False
    finally:
        doc.close()
