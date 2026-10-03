import io

import fitz
import qrcode


def generate_qr_bytes(url: str) -> bytes:
    """Generate a QR code PNG from a URL, returned as bytes."""
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def replace_qr_in_doc(doc: fitz.Document, session_id: str, base_url: str) -> None:
    """Replace the QR image on page 0 of a fiscal PDF.

    Locates the largest image in the upper-right quadrant of page 0
    (x > 50% page width, y < 40% page height) and replaces it with a
    new QR code pointing to the demo page.
    """
    url = f"{base_url}/demo/{session_id}"
    qr_png_bytes = generate_qr_bytes(url)

    page = doc[0]
    page_rect = page.rect
    upper_right_x = page_rect.width * 0.5
    upper_right_y = page_rect.height * 0.4

    best_xref: int | None = None
    best_rect: fitz.Rect | None = None
    best_area: float = 0.0

    for img_info in page.get_images(full=True):
        xref = img_info[0]
        for rect in page.get_image_rects(xref):
            if rect.x0 > upper_right_x and rect.y1 < upper_right_y:
                area = rect.width * rect.height
                if area > best_area:
                    best_area = area
                    best_xref = xref
                    best_rect = rect

    if best_xref is not None and best_rect is not None:
        # Cover original image with white, then draw new QR on top
        page.draw_rect(best_rect, color=(1, 1, 1), fill=(1, 1, 1))
        page.insert_image(best_rect, stream=qr_png_bytes)
