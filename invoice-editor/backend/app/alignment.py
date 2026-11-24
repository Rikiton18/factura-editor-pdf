"""Where each text sits in its table cell.

An edit has to keep the text's distance to the cell borders, so a number that hugs
the right border keeps hugging it however long the new number is.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Callable

from .models import TextBlock

_BORDER_CLEARANCE_PT = 0.5   # a border this close to the text edge still lies outside the text
_MIN_GAP_DIFFERENCE_PT = 3.0  # gaps closer than this: the text counts as centered
_SAME_EDGE_PT = 1.0          # right edges this close are the same edge
_MIN_PEERS = 2               # blocks sharing the right edge needed to call a column right-aligned


def assign_alignment(
    blocks: list[TextBlock], rules_at: Callable[[TextBlock], list[float]]
) -> list[TextBlock]:
    """Blocks with `align`, `limit_x0` and `limit_x1` set.

    `rules_at(block)` gives the x of the vertical rules crossing the block's row. The
    nearest rule on each side bounds the cell. With a rule on both sides, the side the
    text hugs decides the alignment; without them, the column decides.
    """
    aligned = []
    for block in blocks:
        rules = rules_at(block)
        left = max((x for x in rules if x <= block.x0 - _BORDER_CLEARANCE_PT), default=None)
        right = min((x for x in rules if x >= block.x1 + _BORDER_CLEARANCE_PT), default=None)
        aligned.append(
            replace(block, align=_alignment(block, left, right, blocks), limit_x0=left, limit_x1=right)
        )
    return aligned


def _alignment(block: TextBlock, left: float | None, right: float | None, blocks: list[TextBlock]) -> str:
    if left is not None and right is not None:
        gap_left, gap_right = block.x0 - left, right - block.x1
        if gap_left - gap_right > _MIN_GAP_DIFFERENCE_PT and gap_right * 2 < gap_left:
            return "right"
        if gap_right - gap_left > _MIN_GAP_DIFFERENCE_PT and gap_left * 2 < gap_right:
            return "left"
        return "center"
    return "right" if _shares_a_right_edge_column(block, blocks) else "left"


def _shares_a_right_edge_column(block: TextBlock, blocks: list[TextBlock]) -> bool:
    """Whether several blocks end at the same x but start at different ones.

    That is how a right-aligned column looks. Texts of one width (dates, codes) share
    both edges whether they are left or right aligned, so they prove nothing.
    """
    peers = [
        other for other in blocks
        if other is not block and other.page == block.page
        and abs(other.x1 - block.x1) <= _SAME_EDGE_PT
    ]
    if len(peers) < _MIN_PEERS:
        return False
    starts = [other.x0 for other in peers] + [block.x0]
    return max(starts) - min(starts) > _SAME_EDGE_PT
