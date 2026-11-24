"""Table rules (the long lines of a bordered table) are removed before OCR.

With the rules in place Tesseract can fail to read any text of a bordered table,
for example the lone "455" in a narrow quantity cell. PIL-only image tests, no
tesseract binary.
"""
from PIL import Image, ImageChops, ImageDraw

from app.ocr_parser import remove_table_rules

WIDTH, HEIGHT = 600, 1000
MIN_LEN = round(0.024 * HEIGHT)  # 24 px: a line at least this long is a rule, not a glyph stem


def _page(*boxes):
    """White page with black rectangles (left, top, right, bottom), inclusive."""
    page = Image.new("L", (WIDTH, HEIGHT), 255)
    draw = ImageDraw.Draw(page)
    for box in boxes:
        draw.rectangle(box, fill=0)
    return page


def test_a_vertical_rule_is_removed():
    cleaned = remove_table_rules(_page((100, 200, 102, 500)))

    assert cleaned.getpixel((101, 350)) == 255


def test_a_horizontal_rule_is_removed():
    cleaned = remove_table_rules(_page((100, 300, 500, 302)))

    assert cleaned.getpixel((300, 301)) == 255


def test_a_glyph_sized_stroke_is_kept():
    stem = (100, 300, 103, 300 + MIN_LEN - 3)  # shorter than any rule

    assert remove_table_rules(_page(stem)).getpixel((101, 310)) == 0


def test_a_stroke_longer_than_the_threshold_is_a_rule():
    stem = (100, 300, 103, 300 + MIN_LEN + 5)

    assert remove_table_rules(_page(stem)).getpixel((101, 310)) == 255


def test_text_next_to_a_rule_survives_the_rule_removal():
    rule = (100, 200, 102, 600)
    digit = (110, 300, 113, 312)  # a stem right beside the rule, like "455" beside a cell border

    cleaned = remove_table_rules(_page(rule, digit))

    assert cleaned.getpixel((101, 400)) == 255
    assert cleaned.getpixel((111, 306)) == 0


def test_a_page_without_rules_is_unchanged():
    page = _page((100, 300, 103, 310), (130, 300, 138, 303))  # a stem and a short bar, as in letters

    assert ImageChops.difference(remove_table_rules(page), page).getbbox() is None


def test_the_input_image_is_not_modified():
    page = _page((100, 200, 102, 500))

    remove_table_rules(page)

    assert page.getpixel((101, 350)) == 0


def test_a_whole_table_loses_its_grid_but_keeps_the_numbers():
    frame = [(100, 300, 500, 302), (100, 360, 500, 362), (100, 300, 102, 362), (200, 300, 202, 362), (500, 300, 502, 362)]
    digits = [(140, 320, 143, 332), (150, 320, 153, 332), (160, 320, 163, 332)]  # a lone "455"-like cell

    cleaned = remove_table_rules(_page(*frame, *digits))

    for x, y in ((300, 301), (300, 361), (101, 330), (201, 330), (501, 330)):
        assert cleaned.getpixel((x, y)) == 255
    for x in (141, 151, 161):
        assert cleaned.getpixel((x, 326)) == 0
