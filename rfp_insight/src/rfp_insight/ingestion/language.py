# src/rfp_insight/ingestion/language.py
from __future__ import annotations

import re
from typing import List
from rfp_insight.utils.types import PageText


_ID_HINT_WORDS = {
    "pengadaan", "pekerjaan", "persyaratan", "penawaran", "jadwal", "dokumen",
    "tanggal", "batas", "anggaran", "nilai", "harga", "evaluasi", "lampiran",
    "penyedia", "kualifikasi", "teknis", "administrasi"
}

_EN_HINT_WORDS = {
    "deadline", "submission", "budget", "requirements", "scope", "proposal",
    "schedule", "evaluation", "annex", "appendix", "technical", "qualification"
}


def is_likely_scanned_pdf(pages: List[PageText], min_chars_per_page: int = 30, empty_ratio_threshold: float = 0.6) -> bool:
    """
    Heuristic:
    - count pages with very low extracted characters
    - if too many pages are "empty", likely scanned/image-only PDF
    """
    if not pages:
        return True

    low_text_pages = sum(1 for p in pages if len((p.text or "").strip()) < min_chars_per_page)
    ratio = low_text_pages / max(1, len(pages))
    return ratio >= empty_ratio_threshold


def detect_language_id_en(pages: List[PageText]) -> str:
    """
    Simple heuristic language detection (ID vs EN).
    Uses keyword hints; if uncertain, defaults to 'id' (since user base likely ID).
    Returns: 'id' or 'en'
    """
    text = "\n".join((p.text or "") for p in pages).lower()

    # quick tokenization-ish
    tokens = set(re.findall(r"[a-zA-Z]{3,}", text))

    id_score = sum(1 for w in _ID_HINT_WORDS if w in tokens)
    en_score = sum(1 for w in _EN_HINT_WORDS if w in tokens)

    return "en" if en_score > id_score else "id"