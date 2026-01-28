# src/rfp_insight/ui/page_preview.py
from __future__ import annotations

import fitz  # PyMuPDF


def render_page_png_bytes(file_bytes: bytes, page_no_1based: int, dpi: int = 150) -> bytes:
    """
    Render a single PDF page into PNG bytes using PyMuPDF.
    page_no_1based: 1-based page number.
    """
    if page_no_1based < 1:
        raise ValueError("page_no_1based must be >= 1")

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        idx = page_no_1based - 1
        if idx < 0 or idx >= len(doc):
            raise ValueError(f"Page {page_no_1based} out of range (1..{len(doc)})")

        page = doc[idx]
        # dpi -> matrix zoom
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return pix.tobytes("png")
    finally:
        doc.close()
