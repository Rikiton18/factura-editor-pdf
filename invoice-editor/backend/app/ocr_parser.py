"""
Phase 2 OCR parser for scanned/rasterized PDFs.

Dependencies (not in requirements.txt by default — add when enabling Phase 2):
  pytesseract>=0.3.10
  Pillow>=10.0
  System: tesseract-ocr with 'spa' language pack

Gating: only called when pdf_parser.is_scanned_pdf() returns True.
"""
from __future__ import annotations
import uuid
from collections import defaultdict

import fitz
from .models import TextBlock

_RENDER_DPI = 300
_PDF_POINTS_PER_INCH = 72.0
_SCALE = _PDF_POINTS_PER_INCH / _RENDER_DPI  # 0.24 — converts pixel coords → PDF points


def extract_blocks_ocr(pdf_bytes: bytes) -> list[TextBlock]:
    """Extract text blocks from a scanned PDF via Tesseract OCR.

    Renders each page at 300 DPI, runs Tesseract with Spanish language,
    groups word-level detections into line-level blocks, then scales
    bounding boxes back to PDF point coordinates.
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError as e:
        raise RuntimeError(
            "Phase 2 OCR requires pytesseract and Pillow. "
            "Add them to requirements.txt and install Tesseract."
        ) from e

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    blocks: list[TextBlock] = []

    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            mat = fitz.Matrix(_RENDER_DPI / _PDF_POINTS_PER_INCH, _RENDER_DPI / _PDF_POINTS_PER_INCH)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            data = pytesseract.image_to_data(
                img,
                output_type=pytesseract.Output.DICT,
                lang="spa",
                config="--psm 6",
            )

            # Group words into lines
            lines: dict[tuple, list[int]] = defaultdict(list)
            for i, conf in enumerate(data["conf"]):
                if float(conf) < 30:
                    continue
                key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
                lines[key].append(i)

            for indices in lines.values():
                words = [data["text"][i].strip() for i in indices if data["text"][i].strip()]
                if not words:
                    continue
                text = " ".join(words)
                x_min = min(data["left"][i] for i in indices) * _SCALE
                y_min = min(data["top"][i] for i in indices) * _SCALE
                x_max = max(data["left"][i] + data["width"][i] for i in indices) * _SCALE
                y_max = max(data["top"][i] + data["height"][i] for i in indices) * _SCALE

                blocks.append(TextBlock(
                    block_id=str(uuid.uuid4()),
                    page=page_num,
                    x0=x_min,
                    y0=y_min,
                    x1=x_max,
                    y1=y_max,
                    text=text,
                    font="Helvetica",  # OCR cannot detect original font
                    size=12.0,         # Approximate; OCR does not give exact size
                    color=(0.0, 0.0, 0.0),
                    flags=0,
                    editable=True,
                ))
    finally:
        doc.close()

    return blocks
