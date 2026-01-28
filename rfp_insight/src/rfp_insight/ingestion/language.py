# src/rfp_insight/ingestion/language.py
from __future__ import annotations

import re
from typing import List, Any
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


def _safe_page_text(p: Any) -> str:
    """
    Defensive: accept PageText-like objects; ignore invalid items (e.g., Ellipsis).
    """
    try:
        t = getattr(p, "text", "")
        return (t or "").strip()
    except Exception:
        return ""


def is_likely_scanned_pdf(
    pages: List[PageText],
    min_chars_per_page: int = 30,
    empty_ratio_threshold: float = 0.6
) -> bool:
    """
    Heuristic:
    - count pages with very low extracted characters
    - if too many pages are "empty", likely scanned/image-only PDF
    Defensive: skip invalid page objects safely.
    """
    if not pages:
        return True

    low_text_pages = 0
    total = 0

    for p in pages:
        txt = _safe_page_text(p)
        total += 1
        if len(txt) < min_chars_per_page:
            low_text_pages += 1

    ratio = low_text_pages / max(1, total)
    return ratio >= empty_ratio_threshold


def detect_language_id_en(pages: List[PageText]) -> str:
    """
    Simple heuristic language detection (ID vs EN).
    Defensive: skip invalid page objects safely.
    Returns: 'id' or 'en'
    """
    if not pages:
        return "id"

    joined = "\n".join(_safe_page_text(p) for p in pages).lower().strip()
    if not joined:
        return "id"

    tokens = set(re.findall(r"[a-zA-Z]{3,}", joined))

    id_score = sum(1 for w in _ID_HINT_WORDS if w in tokens)
    en_score = sum(1 for w in _EN_HINT_WORDS if w in tokens)

    return "en" if en_score > id_score else "id"