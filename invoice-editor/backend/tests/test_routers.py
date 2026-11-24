import base64
import fitz
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
    # Upload must NOT echo the PDF back: a base64 body made the response
    # large enough to hit Render's HTTP timeout (frontend uses a blob URL).
    assert "pdf_base64" not in data
    assert "blocks" in data
    assert data["page_count"] == 1
    assert len(data["blocks"]) >= 1


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


# ── Browser-visible errors ──────────────────────────────────────────────────
# A bare 500 has no CORS headers, so the browser reports it as "Network Error"
# and the UI wrongly says the backend is still starting up.

_ORIGIN = {"Origin": "https://factura-editor-pdf.vercel.app"}


def test_upload_scanned_pdf_without_tesseract_returns_503_with_cors(scanned_pdf_bytes, monkeypatch):
    def _tesseract_missing(_pdf_bytes):
        # pytesseract.TesseractNotFoundError subclasses OSError
        raise OSError("tesseract is not installed or it's not in your PATH")

    monkeypatch.setattr("app.ocr_parser.extract_blocks_ocr", _tesseract_missing)

    response = client.post(
        "/api/upload",
        files={"file": ("scan.pdf", scanned_pdf_bytes, "application/pdf")},
        data={"doc_type": "regular"},
        headers=_ORIGIN,
    )

    assert response.status_code == 503
    assert "OCR" in response.json()["detail"]
    assert response.headers["access-control-allow-origin"] == "*"


def test_unhandled_error_returns_json_500_with_cors(minimal_pdf_bytes, monkeypatch):
    def _boom(_pdf_bytes):
        raise ValueError("kaboom")

    monkeypatch.setattr("app.routers.upload.extract_blocks", _boom)
    lenient_client = TestClient(app, raise_server_exceptions=False)

    response = lenient_client.post(
        "/api/upload",
        files={"file": ("t.pdf", minimal_pdf_bytes, "application/pdf")},
        data={"doc_type": "regular"},
        headers=_ORIGIN,
    )

    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == "*"
    assert "detail" in response.json()


# ── font chosen per edit ────────────────────────────────────────────────────

def _export_with_font(minimal_pdf_bytes, font):
    upload_data = _upload(client, minimal_pdf_bytes)
    block_id = upload_data["blocks"][0]["block_id"]
    return client.post(
        f"/api/export/{upload_data['session_id']}",
        json={
            "edits": [{"block_id": block_id, "new_text": "NUEVO", "font": font}],
            "regenerate_qr": False,
        },
    )


def test_export_draws_the_font_chosen_for_an_edit(minimal_pdf_bytes):
    response = _export_with_font(minimal_pdf_bytes, "Courier-Bold")

    assert response.status_code == 200
    page = fitz.open(stream=base64.b64decode(response.json()["pdf_base64"]), filetype="pdf")[0]
    fonts = {
        span["font"]
        for block in page.get_text("dict")["blocks"]
        for line in block.get("lines", [])
        for span in line["spans"]
        if span["text"] == "NUEVO"
    }
    assert fonts == {"Courier-Bold"}


def test_export_rejects_a_font_that_is_not_offered(minimal_pdf_bytes):
    assert _export_with_font(minimal_pdf_bytes, "Comic-Sans").status_code == 422


def test_export_still_works_without_a_font(minimal_pdf_bytes):
    upload_data = _upload(client, minimal_pdf_bytes)
    block_id = upload_data["blocks"][0]["block_id"]

    response = client.post(
        f"/api/export/{upload_data['session_id']}",
        json={"edits": [{"block_id": block_id, "new_text": "NUEVO"}], "regenerate_qr": False},
    )

    assert response.status_code == 200
