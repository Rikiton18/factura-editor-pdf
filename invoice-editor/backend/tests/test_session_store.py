import pytest
from app.models import TextBlock, Session
from app import session_store


@pytest.fixture(autouse=True)
def clear_store():
    session_store._store.clear()
    yield
    session_store._store.clear()


def make_block() -> TextBlock:
    return TextBlock(
        block_id="b1",
        page=0,
        x0=10.0,
        y0=20.0,
        x1=100.0,
        y1=30.0,
        text="Hola",
        font="Helvetica",
        size=12.0,
        color=(0.0, 0.0, 0.0),
        flags=0,
        editable=True,
    )


def test_create_and_get_session():
    sid = session_store.create_session("regular", b"PDF", [make_block()])
    session = session_store.get_session(sid)
    assert session is not None
    assert session.doc_type == "regular"
    assert len(session.blocks) == 1


def test_get_missing_session():
    assert session_store.get_session("nonexistent") is None


def test_update_edits():
    sid = session_store.create_session("fiscal", b"PDF", [make_block()])
    session_store.update_session_edits(sid, {"b1": "Nuevo texto"})
    session = session_store.get_session(sid)
    assert session.latest_edits == {"b1": "Nuevo texto"}
