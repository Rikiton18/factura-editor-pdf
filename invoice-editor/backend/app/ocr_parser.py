"""
Phase 2 OCR parser for scanned/rasterized PDFs.

Dependencies (not in requirements.txt by default — add when enabling Phase 2):
  pytesseract>=0.3.10
  Pillow>=10.0
  System: tesseract-ocr with 'spa' language pack

Gating: only called when pdf_parser.is_scanned_pdf() returns True.
"""
from __future__ import annotations
import re
import statistics
import uuid
from collections import Counter, defaultdict
from dataclasses import replace

import fitz
from PIL import Image
from .models import BOLD_FONT_NAME, TextBlock

_RENDER_DPI = 300
_PDF_POINTS_PER_INCH = 72.0
_SCALE = _PDF_POINTS_PER_INCH / _RENDER_DPI  # 0.24 — converts pixel coords → PDF points
_MIN_CONFIDENCE = 30
# A gap wider than this many word-heights starts a new block. A normal space is
# about 0.4 word-heights; table/column gaps are 2 or more.
_COLUMN_GAP_FACTOR = 1.2

# Helvetica metrics in em. Invoices are assumed to use Helvetica/Arial-like type,
# which is also what the exporter draws edits with.
_CAP_HEIGHT_EM = 0.718
_X_HEIGHT_EM = 0.523
_DESCENDER_EM = 0.207
_TALL_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789bdfhijklt!?/|$%&@#()áéíóúÁÉÍÓÚÑñ")
_DESCENDING_CHARS = frozenset("gjpqy,;()[]{}_")
_MIN_CHARS_FOR_WIDTH = 5   # shorter text: side bearings make the box width unreliable
_SIZE_DISAGREEMENT = 0.12  # height and width estimates this far apart: trust the width
_SNAP_TOLERANCE = 0.10     # a size this close to a more common one is merged into it
BOLD_STROKE_RATIO = 0.115  # median ink stroke / em: about 0.09 regular, 0.145 bold
_BOLD_FLAG = 16            # PyMuPDF span flag for bold
_INK = 255                 # value of an ink pixel in the binarised crop
_INK_RUN = re.compile(b"\xff+")
_RULE_FRACTION = 0.85      # a row/column inked this much is a table rule, not text
_DENSE_ROW = 0.55          # rows with this share of the peak ink count are letter bodies
_STRETCHED_BOX = 1.25      # a box this much taller than its text's ink includes table borders
_HELVETICA = fitz.Font("helv")


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

            gray = img.convert("L")
            blocks.extend(
                _with_ink_metrics(block, gray)
                for block in blocks_from_tesseract_data(data, page_num)
            )
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
        if float(conf) < _MIN_CONFIDENCE or not _word_text(data, i):
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines[key].append(i)

    blocks: list[TextBlock] = []
    for indices in lines.values():
        for segment in _split_on_wide_gaps(indices, data):
            blocks.append(_segment_to_block(segment, data, page_num))
    return _with_page_sizes(blocks)


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
    text = " ".join(_word_text(data, i) for i in indices)
    x0 = min(data["left"][i] for i in indices) * _SCALE
    y0 = min(data["top"][i] for i in indices) * _SCALE
    x1 = max(data["left"][i] + data["width"][i] for i in indices) * _SCALE
    y1 = max(data["top"][i] + data["height"][i] for i in indices) * _SCALE
    return TextBlock(
        block_id=str(uuid.uuid4()),
        page=page_num,
        x0=x0, y0=y0, x1=x1, y1=y1,
        text=text,
        font="Helvetica",  # OCR cannot identify the typeface; Helvetica is the closest base-14 match
        size=estimate_font_size(text, x1 - x0, y1 - y0),  # refined per page in _with_page_sizes
        color=(0.0, 0.0, 0.0),
        flags=0,
        editable=True,
    )


def _word_text(data: dict, i: int) -> str:
    """Word text without the '|' Tesseract reads from table cell borders."""
    return data["text"][i].strip().strip("|").strip()


def _has_descender(text: str) -> bool:
    return any(char in _DESCENDING_CHARS for char in text)


def _ink_height_em(text: str) -> float:
    """Height of the ink of `text`, in em: caps/ascenders or x-height, plus any descender."""
    top = _CAP_HEIGHT_EM if any(char in _TALL_CHARS for char in text) else _X_HEIGHT_EM
    return top + (_DESCENDER_EM if _has_descender(text) else 0.0)


def estimate_font_size(text: str, width_pt: float, height_pt: float) -> float:
    """Font size (pt) of Helvetica-like text that fills a box of this size.

    From the box height, using the glyph classes present (caps/ascenders and
    descenders set how much of the em the ink covers). From the box width when
    the text is long enough, using Helvetica advance widths. A tall box (table
    borders, accents) disagrees with the width: then the width wins.
    """
    text = text.strip()
    from_height = height_pt / _ink_height_em(text)

    advance_per_pt = _HELVETICA.text_length(text, fontsize=1.0)
    if len(text) < _MIN_CHARS_FOR_WIDTH or advance_per_pt <= 0:
        return from_height
    from_width = width_pt / advance_per_pt
    if abs(from_height - from_width) / from_width > _SIZE_DISAGREEMENT:
        return from_width
    return (from_height + from_width) / 2


def snap_sizes(sizes: list[float]) -> list[float]:
    """Round to 0.5 pt, then merge sizes within 10% into the most common one.

    One page rarely mixes 7.5, 8 and 8.5 pt body text; the spread is estimation
    noise, so the whole cluster takes the dominant size.
    """
    rounded = [round(size * 2) / 2 for size in sizes]
    representatives: list[float] = []
    mapping: dict[float, float] = {}
    for size, _ in Counter(rounded).most_common():
        near = next((rep for rep in representatives if abs(size - rep) / rep <= _SNAP_TOLERANCE), None)
        if near is None:
            representatives.append(size)
            near = size
        mapping[size] = near
    return [mapping[size] for size in rounded]


def _baseline(text: str, y1: float, size: float) -> float:
    return y1 - (_DESCENDER_EM * size if _has_descender(text) else 0.0)


def _with_page_sizes(blocks: list[TextBlock]) -> list[TextBlock]:
    sizes = snap_sizes([block.size for block in blocks])
    return [
        replace(block, size=size, baseline=_baseline(block.text, block.y1, size))
        for block, size in zip(blocks, sizes)
    ]


def ink_stroke_ratio(gray: Image.Image, size_pt: float, dpi: int = _RENDER_DPI) -> float:
    """Median thickness of the ink strokes divided by the em size.

    About 0.09 for regular Helvetica and 0.145 for bold, so it tells the weight
    of scanned text without needing the original font.
    """
    mask, width, height = _ink_mask(gray)
    em_px = size_pt * dpi / _PDF_POINTS_PER_INCH
    longest_stem = 0.6 * _CAP_HEIGHT_EM * em_px  # longer runs are horizontal bars, not stems
    runs = [
        match.end() - match.start()
        for y in range(height)
        for match in _INK_RUN.finditer(mask[y * width:(y + 1) * width])
        if match.end() - match.start() <= longest_stem
    ]
    return statistics.median(runs) / em_px if runs else 0.0


def ink_baseline_row(gray: Image.Image) -> int | None:
    """Row (px from the crop's top) just below the last dense row of text, or None.

    Tesseract boxes can be stretched by table borders, so the baseline is read
    from the ink instead: rules (rows/columns inked across most of the crop) are
    ignored, and so are descenders, which are sparse next to the letter bodies.
    """
    mask, width, height = _ink_mask(gray)
    cleaned = bytearray(mask)
    rule_cols = [x for x in range(width) if mask[x::width].count(_INK) >= _RULE_FRACTION * height]
    for x in rule_cols:
        cleaned[x::width] = bytes(height)
    usable_width = width - len(rule_cols)
    counts = [cleaned[y * width:(y + 1) * width].count(_INK) for y in range(height)]
    counts = [0 if count >= _RULE_FRACTION * usable_width else count for count in counts]
    peak = max(counts, default=0)
    if peak == 0:
        return None
    return max(y for y, count in enumerate(counts) if count >= _DENSE_ROW * peak) + 1


def _ink_mask(gray: Image.Image) -> tuple[bytes, int, int]:
    """Binarise: ink pixels become 255 and the rest 0. Returns (pixels, width, height)."""
    gray = gray.convert("L")
    low, high = gray.getextrema()
    threshold = (low + high) / 2
    mask = gray.point(lambda value: _INK if value < threshold else 0)
    return mask.tobytes(), gray.width, gray.height


def _with_ink_metrics(block: TextBlock, gray: Image.Image) -> TextBlock:
    """Set weight (bold flag and font) and baseline from the block's pixels."""
    px_per_pt = _RENDER_DPI / _PDF_POINTS_PER_INCH
    top_px = int(block.y0 * px_per_pt)
    crop = gray.crop((
        int(block.x0 * px_per_pt), top_px,
        int(block.x1 * px_per_pt) + 1, int(block.y1 * px_per_pt) + 1,
    ))
    updates: dict = {}
    if ink_stroke_ratio(crop, block.size) >= BOLD_STROKE_RATIO:
        updates.update(font=BOLD_FONT_NAME, flags=block.flags | _BOLD_FLAG)
    # A tight box already gives an exact baseline (its bottom, minus any descender).
    # Only a box stretched by table borders needs the baseline read from the ink.
    stretched = block.y1 - block.y0 > _STRETCHED_BOX * _ink_height_em(block.text) * block.size
    row = ink_baseline_row(crop) if stretched else None
    if row is not None:
        measured = (top_px + row) / px_per_pt
        if block.y0 <= measured <= block.y1 + 1.0:  # sanity: the baseline lies inside the box
            updates["baseline"] = measured
    return replace(block, **updates)
