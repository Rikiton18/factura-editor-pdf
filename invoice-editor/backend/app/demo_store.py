"""Persistent demo-data store for QR sessions.

Writes lightweight session snapshots (blocks + edits, no PDF bytes) to
/data/sessions/<session_id>.json so the demo page survives Railway restarts.
The /data directory must be backed by a Railway Volume for true persistence;
without a volume it falls back to the ephemeral filesystem (data lost on restart).
"""

import json
import os
from pathlib import Path

_DATA_DIR = Path(os.getenv("DEMO_DATA_DIR", "/data/sessions"))


def _path(session_id: str) -> Path:
    return _DATA_DIR / f"{session_id}.json"


def save_demo_snapshot(session_id: str, doc_type: str, blocks: list[dict], edits: dict[str, str]) -> None:
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        _path(session_id).write_text(
            json.dumps({"session_id": session_id, "doc_type": doc_type, "blocks": blocks, "edits": edits}),
            encoding="utf-8",
        )
    except OSError:
        pass  # non-fatal: demo will fall back to in-memory session


def load_demo_snapshot(session_id: str) -> dict | None:
    try:
        data = json.loads(_path(session_id).read_text(encoding="utf-8"))
        return data
    except (OSError, json.JSONDecodeError):
        return None
