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
_MIN_CONFIDENCE = 30
# A gap wider than this many word-heights starts a new block. A normal space is
# about 0.4 word-heights; table/column gaps are 2 or more.
_COLUMN_GAP_FACTOR = 1.2


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

            blocks.extend(blocks_from_tesseract_data(data, page_num))
    finally:
        doc.close()

    return blocks


def blocks_from_tesseract_data(data: dict, page_num: int) -> list[TextBlock]:
    """Turn pytesseract word boxes into editable blocks for one page.

    Words are grouped by Tesseract line, then each line is cut wherever there is
    a wide horizontal gap. With --psm 6 Tesseract calls everything on the same
    visual row one "line", even when it spans several columns; without the cut,
    editing one field would cover (and rewrite) the neighbouring columns too.
    """
    lines: dict[tuple, list[int]] = defaultdict(list)
    for i, conf in enumerate(data["conf"]):
        if float(conf) < _MIN_CONFIDENCE or not data["text"][i].strip():
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines[key].append(i)

    blocks: list[TextBlock] = []
    for indices in lines.values():
        for segment in _split_on_wide_gaps(indices, data):
            blocks.append(_segment_to_block(segment, data, page_num))
    return blocks


def _split_on_wide_gaps(indices: list[int], data: dict) -> list[list[int]]:
    """Split one line's word indices into runs.

    A run ends at a column-sized gap, or right after a label (a word ending in
    ":"), so a field value can be edited without retyping its label.
    """
    ordered = sorted(indices, key=lambda i: data["left"][i])
    heights = sorted(data["height"][i] for i in ordered)
    max_gap = _COLUMN_GAP_FACTOR * heights[len(heights) // 2]  # median word height

    segments = [[ordered[0]]]
    for prev, cur in zip(ordered, ordered[1:]):
        gap = data["left"][cur] - (data["left"][prev] + data["width"][prev])
        ends_label = data["text"][prev].strip().endswith(":")
        if gap > max_gap or ends_label:
            segments.append([cur])
        else:
            segments[-1].append(cur)
    return segments


def _segment_to_block(indices: list[int], data: dict, page_num: int) -> TextBlock:
    return TextBlock(
        block_id=str(uuid.uuid4()),
        page=page_num,
        x0=min(data["left"][i] for i in indices) * _SCALE,
        y0=min(data["top"][i] for i in indices) * _SCALE,
        x1=max(data["left"][i] + data["width"][i] for i in indices) * _SCALE,
        y1=max(data["top"][i] + data["height"][i] for i in indices) * _SCALE,
        text=" ".join(data["text"][i].strip() for i in indices),
        font="Helvetica",  # OCR cannot detect original font
        size=12.0,         # Approximate; OCR does not give exact size
        color=(0.0, 0.0, 0.0),
        flags=0,
        editable=True,
    )
