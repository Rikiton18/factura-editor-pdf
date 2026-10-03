import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from .config import settings
from .models import Session, TextBlock

_store: dict[str, Session] = {}


def create_session(
    doc_type: str,
    pdf_bytes: bytes,
    blocks: list[TextBlock],
) -> str:
    session_id = str(uuid.uuid4())
    _store[session_id] = Session(
        session_id=session_id,
        doc_type=doc_type,
        pdf_bytes=pdf_bytes,
        blocks=blocks,
    )
    return session_id


def get_session(session_id: str) -> Session | None:
    session = _store.get(session_id)
    if session is not None:
        session.last_accessed = datetime.now(timezone.utc)
    return session


def update_session_edits(session_id: str, edits: dict[str, str]) -> None:
    session = _store.get(session_id)
    if session:
        session.latest_edits = edits


async def cleanup_expired_sessions() -> None:
    while True:
        await asyncio.sleep(600)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.SESSION_TTL_HOURS)
        expired = [sid for sid, s in _store.items() if s.last_accessed < cutoff]
        for sid in expired:
            del _store[sid]
