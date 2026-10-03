from fastapi import APIRouter, HTTPException

from ..session_store import get_session
from ..demo_extractor import get_demo_data
from ..demo_store import load_demo_snapshot

router = APIRouter()


@router.get("/demo/{session_id}")
async def get_demo(session_id: str):
    session = get_session(session_id)
    if session:
        return get_demo_data(session)

    # Session not in memory (Railway restart) — try persistent snapshot
    snapshot = load_demo_snapshot(session_id)
    if snapshot:
        return {
            "session_id": snapshot["session_id"],
            "doc_type": snapshot["doc_type"],
            "blocks": snapshot["blocks"],
        }

    raise HTTPException(status_code=404, detail="Session not found")
