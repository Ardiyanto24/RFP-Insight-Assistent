# src/rfp_insight/ingestion/pdf_loader.py
from __future__ import annotations

from typing import List, Tuple
import fitz  # PyMuPDF

from rfp_insight.utils.types import PageText


def load_pdf_pages(file_bytes: bytes) -> List[PageText]:
    """
    Load PDF bytes and extract text per page.

    Returns:
        List[PageText] where:
          - page_number is 1-indexed (lebih natural untuk user)
          - text is raw extracted text (belum dibersihkan berat)
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages: List[PageText] = []

    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text("text") or ""
        pages.append(PageText(page_number=i + 1, text=text))

    return pages