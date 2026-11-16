"""Grouping of Tesseract word boxes into editable blocks.

Pure data tests: no tesseract binary needed.
"""
import pytest

from app.ocr_parser import _SCALE, blocks_from_tesseract_data

WORD_H = 30  # px at 300 DPI, about the cap height of 10 pt text


def _data(words):
    """words: (text, left, top, width, line_num[, conf]) -> pytesseract-style dict."""
    keys = ("block_num", "par_num", "line_num", "left", "top", "width", "height", "conf", "text")
    rows = []
    for word in words:
        text, left, top, width, line = word[:5]
        conf = word[5] if len(word) > 5 else 90
        rows.append((1, 1, line, left, top, width, WORD_H, conf, text))
    return {key: [row[i] for row in rows] for i, key in enumerate(keys)}


def _texts(blocks):
    return [block.text for block in blocks]


def test_words_with_normal_spacing_stay_in_one_block():
    data = _data([("SEA", 100, 50, 90, 1), ("LAS", 202, 50, 80, 1), ("PERLAS,", 294, 50, 150, 1)])

    assert _texts(blocks_from_tesseract_data(data, page_num=0)) == ["SEA LAS PERLAS,"]


def test_wide_gap_on_same_line_splits_columns():
    # Left and right column text share one visual row, so Tesseract calls it one line.
    data = _data([
        ("SEA", 100, 50, 90, 1), ("LAS", 202, 50, 80, 1),
        ("Fecha:", 1800, 50, 120, 1), ("2026-10-23", 1932, 50, 220, 1),
    ])

    left, right = blocks_from_tesseract_data(data, page_num=0)

    assert (left.text, right.text) == ("SEA LAS", "Fecha: 2026-10-23")
    assert left.x1 < right.x0  # boxes no longer overlap horizontally


def test_table_row_cells_become_separate_blocks():
    data = _data([
        ("204.9", 100, 50, 100, 1),
        ("30", 265, 50, 50, 1), ("-", 327, 50, 20, 1), ("DIESEL", 359, 50, 140, 1),
        ("B/", 1500, 50, 40, 1), ("1,233.50", 1552, 50, 190, 1),
    ])

    assert _texts(blocks_from_tesseract_data(data, page_num=0)) == [
        "204.9",
        "30 - DIESEL",
        "B/ 1,233.50",
    ]


def test_block_bbox_is_scaled_to_pdf_points():
    data = _data([("Total", 300, 150, 150, 1)])

    (block,) = blocks_from_tesseract_data(data, page_num=2)

    assert block.page == 2
    assert block.x0 == pytest.approx(300 * _SCALE)
    assert block.x1 == pytest.approx(450 * _SCALE)
    assert block.y0 == pytest.approx(150 * _SCALE)
    assert block.y1 == pytest.approx(180 * _SCALE)


def test_low_confidence_words_are_dropped():
    data = _data([("noise", 100, 50, 90, 1, 10), ("Total", 212, 50, 100, 1, 95)])

    assert _texts(blocks_from_tesseract_data(data, page_num=0)) == ["Total"]


def test_separate_lines_never_merge():
    data = _data([("A", 100, 50, 30, 1), ("B", 100, 100, 30, 2)])

    assert _texts(blocks_from_tesseract_data(data, page_num=0)) == ["A", "B"]
