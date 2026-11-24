"""Second OCR pass: text Tesseract skips on the first pass must still become blocks.

First pass (--psm 6) misses text it cannot segment, for example a number alone in a
bordered table cell (the "455" of a quantity column). The second pass reads what the
first one did not cover. Pure data/PIL tests, no tesseract binary.
"""
from PIL import Image

from app.ocr_parser import blocks_from_tesseract_data, mask_found_words, merge_residual_words

COLUMNS = (
    "level", "page_num", "block_num", "par_num", "line_num", "word_num",
    "left", "top", "width", "height", "conf", "text",
)


def _words(*rows):
    """rows: (text, left, top, width, height, conf) -> pytesseract-style dict."""
    data = {key: [] for key in COLUMNS}
    for number, (text, left, top, width, height, conf) in enumerate(rows, start=1):
        values = dict(
            level=5, page_num=1, block_num=1, par_num=1, line_num=1, word_num=number,
            left=left, top=top, width=width, height=height, conf=conf, text=text,
        )
        for key in COLUMNS:
            data[key].append(values[key])
    return data


def _texts(data):
    return sorted(block.text for block in blocks_from_tesseract_data(data, page_num=0))


# ── merging the second pass into the first ──────────────────────────────────

def test_a_missed_word_becomes_its_own_block():
    first = _words(("Cantidad", 100, 100, 190, 30, 96))
    missed = _words(("455", 100, 300, 70, 30, 96))

    assert _texts(merge_residual_words(first, missed)) == ["455", "Cantidad"]


def test_both_passes_number_their_lines_from_one_without_fusing_words():
    first = _words(("A", 100, 100, 30, 30, 90))
    missed = _words(("B", 140, 100, 30, 30, 90))  # close enough that one shared line would fuse them

    assert _texts(merge_residual_words(first, missed)) == ["A", "B"]


def test_low_confidence_second_pass_words_are_dropped_as_noise():
    first = _words(("A", 100, 100, 30, 30, 90))
    noise = _words(("x", 300, 100, 30, 30, 45), ("y", 400, 100, 30, 30, 59))

    assert _texts(merge_residual_words(first, noise)) == ["A"]


def test_second_pass_keeps_words_just_above_the_noise_threshold():
    first = _words(("A", 100, 100, 30, 30, 90))
    sure = _words(("DV:", 300, 100, 60, 30, 60))

    assert _texts(merge_residual_words(first, sure)) == ["A", "DV:"]


def test_blank_second_pass_words_are_dropped():
    first = _words(("A", 100, 100, 30, 30, 90))
    blank = _words(("", 300, 100, 30, 30, 96), ("  ", 400, 100, 30, 30, 96))

    assert merge_residual_words(first, blank)["text"] == ["A"]


def test_merging_does_not_modify_its_inputs():
    first = _words(("A", 100, 100, 30, 30, 90))
    missed = _words(("B", 300, 100, 30, 30, 90))

    merge_residual_words(first, missed)

    assert first["text"] == ["A"] and first["block_num"] == [1]
    assert missed["text"] == ["B"] and missed["block_num"] == [1]


# ── hiding what the first pass found ────────────────────────────────────────

def test_masking_wipes_found_words_and_leaves_everything_else():
    page = Image.new("RGB", (200, 100), "white")
    for box in ((50, 30, 80, 50), (150, 30, 170, 50), (10, 70, 30, 90)):
        page.paste((0, 0, 0), box)
    found = _words(("Total", 50, 30, 30, 20, 90), ("noise", 10, 70, 20, 20, 10))

    masked = mask_found_words(page, found)

    assert masked.getpixel((60, 40)) == (255, 255, 255)  # found word is wiped
    assert masked.getpixel((160, 40)) == (0, 0, 0)       # unseen ink stays for the second pass
    assert masked.getpixel((20, 80)) == (0, 0, 0)        # a low-confidence word did not become a block
    assert page.getpixel((60, 40)) == (0, 0, 0)          # the original image is untouched


# ── a sure second-pass read replaces a doubtful first-pass guess ────────────

def test_a_sure_second_pass_word_replaces_a_doubtful_first_pass_guess():
    # Seen on a real scan: the first pass read "DV: 29" as "sosa" (confidence 31).
    first = _words(("sosa", 539, 86, 60, 30, 31))
    second = _words(("DV:", 541, 88, 55, 28, 89))

    assert _texts(merge_residual_words(first, second)) == ["DV:"]


def test_a_sure_first_pass_word_is_never_replaced_or_duplicated():
    first = _words(("Total", 100, 100, 90, 30, 90))
    second = _words(("Totai", 102, 101, 88, 29, 95))

    assert _texts(merge_residual_words(first, second)) == ["Total"]


def test_a_doubtful_first_pass_word_stays_when_nothing_better_covers_it():
    first = _words(("sosa", 539, 86, 60, 30, 31))
    second = _words(("455", 100, 300, 70, 30, 96))

    assert _texts(merge_residual_words(first, second)) == ["455", "sosa"]


def test_masking_leaves_doubtful_words_visible_so_the_second_pass_can_reread_them():
    page = Image.new("RGB", (200, 100), "white")
    page.paste((0, 0, 0), (50, 30, 80, 50))

    masked = mask_found_words(page, _words(("sosa", 50, 30, 30, 20, 45)))

    assert masked.getpixel((60, 40)) == (0, 0, 0)


# ── single characters read from the arcs of rounded table corners ───────────

def test_a_lone_low_confidence_character_is_noise():
    assert _texts(_words(("(", 100, 100, 20, 30, 45))) == []


def test_a_lone_confident_character_is_kept():
    assert _texts(_words(("1", 100, 100, 20, 30, 80))) == ["1"]


def test_a_short_word_with_middling_confidence_is_kept():
    assert _texts(_words(("No", 100, 100, 40, 30, 45))) == ["No"]


def test_masking_ignores_a_lone_low_confidence_character_too():
    page = Image.new("RGB", (200, 100), "white")
    page.paste((0, 0, 0), (50, 30, 60, 50))

    masked = mask_found_words(page, _words(("(", 50, 30, 10, 20, 45)))

    assert masked.getpixel((55, 40)) == (0, 0, 0)  # not a block, so the second pass still sees it
