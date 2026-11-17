from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

# Font name carried by bold OCR blocks. The exporter draws these in Helvetica-Bold.
BOLD_FONT_NAME = "Helvetica-Bold"


@dataclass
class TextBlock:
    block_id: str
    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    font: str
    size: float
    color: tuple[float, float, float]
    flags: int
    editable: bool
    # y of the text baseline in PDF points. None = derive it from y1 (text PDFs).
    baseline: float | None = None


@dataclass
class Session:
    session_id: str
    doc_type: Literal["regular", "fiscal"]
    pdf_bytes: bytes
    blocks: list[TextBlock]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    latest_edits: dict[str, str] = field(default_factory=dict)
