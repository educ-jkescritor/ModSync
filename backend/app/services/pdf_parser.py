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

    pages: list[dict[str, Any]] = []
    with fitz.open(path) as document:
        for index, page in enumerate(document, start=1):
            pages.append({"page": index, "text": page.get_text("text").strip()})
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
        {"page": index, "text": (page.extract_text() or "").strip()}
        for index, page in enumerate(reader.pages, start=1)
    ]

