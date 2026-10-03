import fitz
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


def extract_blocks(pdf_bytes: bytes) -> list[TextBlock]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    blocks: list[TextBlock] = []
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            raw = page.get_text("rawdict")
            span_counter = 0
            for block_idx, block in enumerate(raw["blocks"]):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = _text_from_span(span).strip()
                        bbox = span["bbox"]
                        blocks.append(TextBlock(
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
