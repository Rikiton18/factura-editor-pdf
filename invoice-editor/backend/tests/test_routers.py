import base64
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_upload_regular_pdf(minimal_pdf_bytes):
    response = client.post(
        "/api/upload",
        files={"file": ("test.pdf", minimal_pdf_bytes, "application/pdf")},
        data={"doc_type": "regular"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "pdf_base64" in data
    assert "blocks" in data
    assert data["page_count"] == 1
    assert len(data["blocks"]) >= 1
    # Verify pdf_base64 is valid base64
    decoded = base64.b64decode(data["pdf_base64"])
    assert decoded[:4] == b"%PDF"


def test_upload_rejects_invalid_doc_type(minimal_pdf_bytes):
    response = client.post(
        "/api/upload",
        files={"file": ("test.pdf", minimal_pdf_bytes, "application/pdf")},
        data={"doc_type": "unknown"},
    )
    assert response.status_code == 400


def test_upload_block_has_required_fields(minimal_pdf_bytes):
    response = client.post(
        "/api/upload",
        files={"file": ("test.pdf", minimal_pdf_bytes, "application/pdf")},
        data={"doc_type": "regular"},
    )
    block = response.json()["blocks"][0]
    for field in ("block_id", "page", "x0", "y0", "x1", "y1", "text", "font", "size", "color", "flags", "editable"):
        assert field in block, f"Missing field: {field}"


# ── Task 6: export / demo tests ─────────────────────────────────────────────

def _upload(client_fixture, pdf_bytes, doc_type="regular"):
    r = client_fixture.post(
        "/api/upload",
        files={"file": ("t.pdf", pdf_bytes, "application/pdf")},
        data={"doc_type": doc_type},
    )
    return r.json()


def test_export_applies_edits(minimal_pdf_bytes):
    upload_data = _upload(client, minimal_pdf_bytes)
    session_id = upload_data["session_id"]
    block_id = upload_data["blocks"][0]["block_id"]

    response = client.post(
        f"/api/export/{session_id}",
        json={"edits": [{"block_id": block_id, "new_text": "NUEVO"}], "regenerate_qr": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert "pdf_base64" in data
    decoded = base64.b64decode(data["pdf_base64"])
    assert decoded[:4] == b"%PDF"


def test_export_missing_session():
    response = client.post(
        "/api/export/nonexistent",
        json={"edits": [], "regenerate_qr": False},
    )
    assert response.status_code == 404


def test_demo_returns_blocks(minimal_pdf_bytes):
    upload_data = _upload(client, minimal_pdf_bytes)
    session_id = upload_data["session_id"]

    response = client.get(f"/api/demo/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert "blocks" in data


def test_demo_reflects_edits(minimal_pdf_bytes):
    upload_data = _upload(client, minimal_pdf_bytes)
    session_id = upload_data["session_id"]
    block_id = upload_data["blocks"][0]["block_id"]

    # Export with edit
    client.post(
        f"/api/export/{session_id}",
        json={"edits": [{"block_id": block_id, "new_text": "DEMO_TEXT"}], "regenerate_qr": False},
    )

    demo = client.get(f"/api/demo/{session_id}").json()
    texts = [b["text"] for b in demo["blocks"]]
    assert "DEMO_TEXT" in texts
