FROM python:3.11-slim

# Tesseract is a system binary: pytesseract alone is not enough. This is why
# the native Render Python runtime cannot do OCR (no apt-get there).
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Render injects $PORT (default 10000); fall back to it for local runs.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
