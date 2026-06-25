from __future__ import annotations

from pathlib import Path
from typing import Any


def extract_pdf_pages(pdf_path: str | Path) -> list[dict[str, Any]]:
    path = Path(pdf_path)
    try:
        return _extract_with_pymupdf(path)
    except ImportError:
        return _extract_with_pypdf(path)


def _extract_with_pymupdf(path: Path) -> list[dict[str, Any]]:
    import fitz
    import base64

    pages: list[dict[str, Any]] = []
    with fitz.open(path) as document:
        for index, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            image_list = page.get_images(full=True)
            page_images = []
            
            for img in image_list:
                try:
                    xref = img[0]
                    base_image = document.extract_image(xref)
                    if base_image and "image" in base_image:
                        image_bytes = base_image["image"]
                        
                        # Smart Filtering: Ignore backgrounds and solid artifacts
                        import io
                        from PIL import Image
                        
                        pil_img = Image.open(io.BytesIO(image_bytes))
                        width, height = pil_img.size
                        
                        # 1. Filter out massive background templates
                        if width > 2000 or height > 2000:
                            continue
                            
                        # 2. Filter out solid color blocks (all black or solid borders)
                        extrema = pil_img.convert("L").getextrema()
                        if extrema[0] == extrema[1]:
                            continue
                            
                        if len(image_bytes) < 5_000_000: # Skip if still >5MB
                            page_images.append(base64.b64encode(image_bytes).decode("utf-8"))
                except Exception as e:
                    print(f"Skipped image on page {index} due to error: {e}")
                    continue
                
            pages.append({"page": index, "text": text, "images": page_images})
    return pages


def _extract_with_pypdf(path: Path) -> list[dict[str, Any]]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "Install PyMuPDF for PDF extraction. pypdf may also be installed as a fallback."
        ) from exc

    reader = PdfReader(str(path))
    return [
        {"page": index, "text": (page.extract_text() or "").strip(), "images": []}
        for index, page in enumerate(reader.pages, start=1)
    ]

