"""Where each text sits in its table cell.

An edit has to keep the text's distance to the cell borders: a number hugging the
right border must keep hugging it however long the new number is.
"""
import fitz
import pytest

from app.alignment import assign_alignment
from app.models import TextBlock
from app.pdf_parser import extract_blocks


def _block(text, x0, x1, *, page=0):
    return TextBlock(
        block_id="%s-%s-%s" % (page, text, x0), page=page,
        x0=x0, y0=300.0, x1=x1, y1=308.0, text=text, font="Helvetica", size=8.0,
        color=(0.0, 0.0, 0.0), flags=0, editable=True,
    )


def _aligned(blocks, rules=()):
    return assign_alignment(blocks, lambda block: list(rules))


# ── a text with a border on each side ───────────────────────────────────────

def test_a_number_hugging_the_right_border_is_right_aligned():
    (block,) = _aligned([_block("B/ 2,739.10", 532, 572)], rules=[465, 580])

    assert block.align == "right"
    assert (block.limit_x0, block.limit_x1) == (465, 580)


def test_text_hugging_the_left_border_is_left_aligned():
    (block,) = _aligned([_block("30 - DIESEL REGULAR", 88, 175)], rules=[70, 360])

    assert block.align == "left"


def test_text_in_the_middle_of_its_cell_is_centered():
    (block,) = _aligned([_block("455", 57, 70)], rules=[45, 82])

    assert block.align == "center"


def test_only_the_nearest_borders_around_the_text_bound_the_cell():
    (block,) = _aligned([_block("B/ 2,739.10", 532, 572)], rules=[10, 465, 520, 580, 900])

    assert (block.limit_x0, block.limit_x1) == (520, 580)


def test_a_border_running_through_the_text_is_not_a_cell_edge():
    (block,) = _aligned([_block("B/ 2,739.10", 532, 572)], rules=[550, 580])

    assert block.limit_x0 is None
    assert block.limit_x1 == 580


# ── a text without borders: the column it belongs to decides ────────────────

def test_a_column_sharing_its_right_edge_is_right_aligned():
    blocks = [_block("B/ 1,233.50", 526, 566), _block("B/ 0.00", 541, 566), _block("B/ 1,233.50", 525, 566)]

    assert {block.align for block in _aligned(blocks)} == {"right"}


def test_equal_width_texts_do_not_prove_a_column_is_right_aligned():
    # Dates or codes of one width share both edges whether they are left or right aligned.
    blocks = [_block("2026-10-23", 445, 485), _block("2026-10-24", 445, 485), _block("2026-10-25", 445, 485)]

    assert {block.align for block in _aligned(blocks)} == {"left"}


def test_a_lone_text_without_borders_stays_left_aligned():
    (block,) = _aligned([_block("Total", 462, 481)])

    assert block.align == "left"


def test_a_shared_left_edge_is_not_right_alignment():
    blocks = [_block("Total", 445, 481), _block("Impuestos", 445, 490), _block("Sub-Total", 445, 500)]

    assert {block.align for block in _aligned(blocks)} == {"left"}


def test_columns_on_other_pages_do_not_count():
    blocks = [_block("1.00", 500, 566, page=0), _block("2.00", 510, 566, page=1), _block("3.00", 520, 566, page=2)]

    assert {block.align for block in _aligned(blocks)} == {"left"}


def test_blocks_keep_everything_else_and_are_not_modified():
    block = _block("455", 57, 70)

    (aligned,) = _aligned([block], rules=[45, 82])

    assert (aligned.text, aligned.x0, aligned.x1) == ("455", 57, 70)
    assert block.align == "left" and block.limit_x0 is None


# ── text PDFs: the rules come from the drawn lines ──────────────────────────

def test_a_text_pdf_table_gets_alignment_and_limits_from_its_drawn_rules():
    page = fitz.open().new_page(width=612, height=792)
    for x in (100, 300):
        page.draw_line((x, 200), (x, 260), width=1)
    amount = "1,234.00"
    page.insert_text((290 - fitz.get_text_length(amount, "helv", 8), 230), amount, fontname="helv", fontsize=8)

    blocks = extract_blocks(page.parent.tobytes())

    (block,) = [b for b in blocks if b.text == amount]
    assert block.align == "right"
    assert block.limit_x0 == pytest.approx(100, abs=1)
    assert block.limit_x1 == pytest.approx(300, abs=1)
