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
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from .alignment import assign_alignment
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
_MASK_PADDING_PX = 3            # margin around found words when hiding them for the second pass
_SURE_CONFIDENCE = 60   # below this a read is a guess (logos, frames, rounded corners); real text scores 89+
_RESIDUAL_BLOCK_OFFSET = 10_000  # keeps second-pass block numbers apart from the first pass's
_RULE_LENGTH_FRACTION = 0.024   # of the page size: a straight line this long is a table rule, not a letter stem
_SINGLE_CHAR_MIN_CONFIDENCE = 60  # a lone character below this is usually an arc of a rounded table corner
_HELVETICA = fitz.Font("helv")
_HELVETICA_BOLD = fitz.Font("hebo")


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
            gray = img.convert("L")
            # Tesseract can read none of a bordered table's text while its rules are there.
            rules = find_table_rules(gray)
            clean = remove_table_rules(gray, rules)

            data = pytesseract.image_to_data(
                clean,
                output_type=pytesseract.Output.DICT,
                lang="spa",
                config="--psm 6",
            )

            data = _with_missed_words(clean, data)
            page_blocks = blocks_from_tesseract_data(data, page_num, gray)
            blocks.extend(_with_alignment(page_blocks, rules[0]))
    finally:
        doc.close()

    return blocks


def find_table_rules(gray: Image.Image) -> tuple[Image.Image, Image.Image]:
    """The long straight lines of tables, as two masks (255 on a rule): vertical, horizontal.

    A line this long is far longer than any letter stem at invoice type sizes.
    """
    gray = gray.convert("L")
    ink = gray.point(lambda value: 255 if value < 128 else 0)
    vertical = _straight_runs(ink, max(2, round(_RULE_LENGTH_FRACTION * gray.height)), vertical=True)
    horizontal = _straight_runs(ink, max(2, round(_RULE_LENGTH_FRACTION * gray.width)), vertical=False)
    return vertical, horizontal


def remove_table_rules(
    gray: Image.Image, rules: tuple[Image.Image, Image.Image] | None = None
) -> Image.Image:
    """The page with the long straight lines of tables painted white.

    Tesseract's page analysis can fail on a bordered table and then read none of
    its text, for example the lone "455" of a narrow quantity cell. Removing the
    rules leaves the text intact. Pass `rules` (from find_table_rules) to reuse them.
    """
    gray = gray.convert("L")
    vertical, horizontal = rules if rules is not None else find_table_rules(gray)
    grown = ImageChops.lighter(vertical, horizontal).filter(ImageFilter.MaxFilter(3))  # soft edges too
    return ImageChops.lighter(gray, grown)


def vertical_rule_xs(vertical: Image.Image, y_px: int) -> list[float]:
    """The x (pixels) of the center of each vertical rule crossing row `y_px`."""
    row = vertical.crop((0, y_px, vertical.width, y_px + 1)).tobytes()
    return [(run.start() + run.end() - 1) / 2 for run in _INK_RUN.finditer(row)]


def _straight_runs(ink: Image.Image, length: int, *, vertical: bool) -> Image.Image:
    """The ink pixels that lie on a straight run of at least `length` pixels.

    A morphological opening along one axis (erode, then dilate back), built from
    shifted copies of the image and doubled windows so it stays fast on a full page.
    """
    def shifted(image: Image.Image, amount: int) -> Image.Image:
        return ImageChops.offset(image, 0, amount) if vertical else ImageChops.offset(image, amount, 0)

    eroded, window = ink, 1  # a pixel survives only if the next `length` pixels are all ink
    while window * 2 <= length:
        eroded = ImageChops.darker(eroded, shifted(eroded, -window))
        window *= 2
    eroded = ImageChops.darker(eroded, shifted(eroded, -(length - window)))

    dilated, window = eroded, 1  # spread each survivor back over the run it started
    while window * 2 <= length:
        dilated = ImageChops.lighter(dilated, shifted(dilated, window))
        window *= 2
    return ImageChops.lighter(dilated, shifted(dilated, length - window))


def _is_block_word(data: dict, i: int) -> bool:
    """Whether word i of a Tesseract table becomes part of a block."""
    text = _word_text(data, i)
    if not text:
        return False
    confidence = float(data["conf"][i])
    if confidence < _MIN_CONFIDENCE:
        return False
    return len(text) > 1 or confidence >= _SINGLE_CHAR_MIN_CONFIDENCE


def _is_sure(data: dict, i: int) -> bool:
    """A block word read with high confidence, as opposed to a doubtful guess."""
    return _is_block_word(data, i) and float(data["conf"][i]) >= _SURE_CONFIDENCE


def _boxes_overlap(a: dict, i: int, b: dict, j: int) -> bool:
    """Whether word i of table a and word j of table b have overlapping boxes."""
    return (
        a["left"][i] < b["left"][j] + b["width"][j] and b["left"][j] < a["left"][i] + a["width"][i]
        and a["top"][i] < b["top"][j] + b["height"][j] and b["top"][j] < a["top"][i] + a["height"][i]
    )


def _with_missed_words(img: Image.Image, data: dict) -> dict:
    """Add the words Tesseract skipped on the first pass.

    --psm 6 cannot segment some text, such as a number alone in a bordered table
    cell or a bold heading next to a logo, and that text then cannot be edited.
    Hiding what the first pass found and reading the rest in sparse mode
    (--psm 11) recovers it. Only confident reads are kept, since sparse mode also
    guesses at logos and frames.
    """
    import pytesseract

    residual = pytesseract.image_to_data(
        mask_found_words(img, data),
        output_type=pytesseract.Output.DICT,
        lang="spa",
        config="--psm 11",
    )
    return merge_residual_words(data, residual)


def mask_found_words(img: Image.Image, data: dict) -> Image.Image:
    """A copy of the page with every word that became a block painted white."""
    masked = img.copy()
    draw = ImageDraw.Draw(masked)
    pad = _MASK_PADDING_PX
    for i in range(len(data["conf"])):
        if not _is_sure(data, i):  # doubtful words stay visible so the second pass can reread them
            continue
        left, top = data["left"][i], data["top"][i]
        draw.rectangle(
            (left - pad, top - pad, left + data["width"][i] + pad, top + data["height"][i] + pad),
            fill="white",
        )
    return masked


def merge_residual_words(data: dict, residual: dict) -> dict:
    """The first-pass words plus the sure second-pass words, as one word table.

    A sure second-pass word replaces any doubtful first-pass guess it covers (a scan
    read "DV: 29" as "sosa" at confidence 31). Where the first pass was already
    sure, the second pass adds nothing. Both passes number their blocks from 1, so
    the second pass's block numbers are shifted; otherwise its words would join
    first-pass lines that share a number.
    """
    sure_first = [i for i in range(len(data["conf"])) if _is_sure(data, i)]
    added = [
        j for j, conf in enumerate(residual["conf"])
        if float(conf) >= _SURE_CONFIDENCE and _word_text(residual, j)
        and not any(_boxes_overlap(data, i, residual, j) for i in sure_first)
    ]
    replaced = {
        i for i in range(len(data["conf"]))
        if any(_boxes_overlap(data, i, residual, j) for j in added)
    }
    merged = {
        key: [value for i, value in enumerate(values) if i not in replaced]
        for key, values in data.items()
    }
    for key, values in merged.items():
        picked = [residual[key][j] for j in added]
        if key == "block_num":
            picked = [number + _RESIDUAL_BLOCK_OFFSET for number in picked]
        values.extend(picked)
    return merged


def blocks_from_tesseract_data(
    data: dict, page_num: int, gray: Image.Image | None = None
) -> list[TextBlock]:
    """Turn pytesseract word boxes into editable blocks for one page.

    Words are grouped by Tesseract line, then each line is cut wherever there is
    a wide horizontal gap. With --psm 6 Tesseract calls everything on the same
    visual row one "line", even when it spans several columns; without the cut,
    editing one field would cover (and rewrite) the neighbouring columns too.

    With `gray` (the page image) the weight and, for boxes stretched by table
    borders, the baseline are read from the ink. Weight comes first because bold
    text changes the size estimate, and sizes are then unified across the page.
    """
    lines: dict[tuple, list[int]] = defaultdict(list)
    for i in range(len(data["conf"])):
        if not _is_block_word(data, i):
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines[key].append(i)

    blocks: list[TextBlock] = []
    for indices in lines.values():
        for segment in _split_on_wide_gaps(indices, data):
            blocks.append(_segment_to_block(segment, data, page_num))
    if gray is not None:
        blocks = [_with_weight(block, gray) for block in blocks]
    blocks = _with_page_sizes(blocks)
    if gray is not None:
        blocks = [_with_ink_baseline(block, gray) for block in blocks]
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


def estimate_font_size(text: str, width_pt: float, height_pt: float, *, bold: bool = False) -> float:
    """Font size (pt) of Helvetica-like text that fills a box of this size.

    Bold text is about 7% wider than regular, so `bold` measures it with the
    Helvetica-Bold advance widths; otherwise its size would come out inflated.

    From the box height, using the glyph classes present (caps/ascenders and
    descenders set how much of the em the ink covers). From the box width when
    the text is long enough, using Helvetica advance widths. A tall box (table
    borders, accents) disagrees with the width: then the width wins.
    """
    text = text.strip()
    from_height = height_pt / _ink_height_em(text)

    advance_per_pt = (_HELVETICA_BOLD if bold else _HELVETICA).text_length(text, fontsize=1.0)
    if len(text) < _MIN_CHARS_FOR_WIDTH or advance_per_pt <= 0:
        return from_height
    from_width = width_pt / advance_per_pt
    if abs(from_height - from_width) / from_width > _SIZE_DISAGREEMENT:
        return from_width
    return (from_height + from_width) / 2


def snap_sizes(sizes: list[float]) -> list[float]:
    """Round to whole points, then merge sizes within 10% into the most common one.

    Invoices use whole-point sizes (the reference invoice is 8, 9 and 15 pt), and
    one page rarely mixes 7.5, 8 and 8.5 pt body text; the spread is estimation
    noise, so the whole cluster takes the dominant size.
    """
    rounded = [float(round(size)) for size in sizes]
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


def _with_alignment(blocks: list[TextBlock], vertical_rules: Image.Image) -> list[TextBlock]:
    """Set each block's alignment and cell borders from the vertical rules on its row."""
    px_per_pt = _RENDER_DPI / _PDF_POINTS_PER_INCH

    def rules_at(block: TextBlock) -> list[float]:
        row = int((block.y0 + block.y1) / 2 * px_per_pt)
        row = min(max(row, 0), vertical_rules.height - 1)
        return [x / px_per_pt for x in vertical_rule_xs(vertical_rules, row)]

    return assign_alignment(blocks, rules_at)


def _crop_block(block: TextBlock, gray: Image.Image) -> tuple[Image.Image, int]:
    """The block's pixels from the page image, and the crop's top row in the page."""
    px_per_pt = _RENDER_DPI / _PDF_POINTS_PER_INCH
    top_px = int(block.y0 * px_per_pt)
    crop = gray.crop((
        int(block.x0 * px_per_pt), top_px,
        int(block.x1 * px_per_pt) + 1, int(block.y1 * px_per_pt) + 1,
    ))
    return crop, top_px


def _with_weight(block: TextBlock, gray: Image.Image) -> TextBlock:
    """Flag bold blocks and re-estimate their size with Helvetica-Bold widths."""
    crop, _ = _crop_block(block, gray)
    if ink_stroke_ratio(crop, block.size) < BOLD_STROKE_RATIO:
        return block
    size = estimate_font_size(block.text, block.x1 - block.x0, block.y1 - block.y0, bold=True)
    return replace(block, font=BOLD_FONT_NAME, flags=block.flags | _BOLD_FLAG, size=size)


def _with_ink_baseline(block: TextBlock, gray: Image.Image) -> TextBlock:
    """Read the baseline from the ink when table borders stretched the box.

    A tight box already gives an exact baseline (its bottom, minus any descender).
    """
    if block.y1 - block.y0 <= _STRETCHED_BOX * _ink_height_em(block.text) * block.size:
        return block
    crop, top_px = _crop_block(block, gray)
    row = ink_baseline_row(crop)
    if row is None:
        return block
    measured = (top_px + row) / (_RENDER_DPI / _PDF_POINTS_PER_INCH)
    if not block.y0 <= measured <= block.y1 + 1.0:  # sanity: the baseline lies inside the box
        return block
    return replace(block, baseline=measured)
