from fastapi import APIRouter, HTTPException

from ..session_store import get_session
from ..demo_extractor import get_demo_data

router = APIRouter()


@router.get("/demo/{session_id}")
async def get_demo(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return get_demo_data(session)
