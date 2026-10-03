import pytest
import fitz
import io


@pytest.fixture
def minimal_pdf_bytes() -> bytes:
    """Creates a minimal 1-page PDF with one line of text."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((100, 100), "Factura 001", fontname="helv", fontsize=12)
    page.insert_text((100, 120), "Total: B/100.00", fontname="helv", fontsize=10)
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


@pytest.fixture
def scanned_pdf_bytes() -> bytes:
    """Creates a PDF that contains only an image (simulates a scanned PDF)."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    # Insert a blank image - no text blocks
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 612, 792))
    pix.clear_with(255)
    page.insert_image(fitz.Rect(0, 0, 612, 792), pixmap=pix)
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()
