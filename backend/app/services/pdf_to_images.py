from __future__ import annotations

from pathlib import Path
import fitz

def convert_pdf_to_images(pdf_path: str | Path, dpi: int = 150) -> list[bytes]:
    """Converts a PDF file's pages into a list of PNG image bytes using PyMuPDF."""
    path = Path(pdf_path)
    images: list[bytes] = []
    with fitz.open(path) as doc:
        for page in doc:
            # We use 150 DPI which strikes a good balance between visual detail for OCR/vision and image size.
            pix = page.get_pixmap(dpi=dpi)
            img_bytes = pix.tobytes("png")
            images.append(img_bytes)
    return images
