# src/rfp_insight/extraction/validators.py
from __future__ import annotations

from typing import List, Tuple
from rfp_insight.schemas.extraction import ExtractionResult


def _normalize_for_match(s: str) -> str:
    # ringan saja: unify whitespace for substring check
    return " ".join(s.split()).strip()


def validate_exact_fields(result: ExtractionResult, full_text: str) -> Tuple[bool, List[str]]:
    """
    Returns (ok, errors).
    Rule:
    - If submission_deadline is not None -> must appear in full_text (after light whitespace normalization)
    - If budget_limit is not None -> must appear in full_text (after light whitespace normalization)
    """
    errors: List[str] = []

    ft = _normalize_for_match(full_text)

    if result.submission_deadline:
        needle = _normalize_for_match(result.submission_deadline)
        if needle not in ft:
            errors.append("submission_deadline tidak ditemukan persis di teks dokumen (substring mismatch).")

    if result.budget_limit:
        needle = _normalize_for_match(result.budget_limit)
        if needle not in ft:
            errors.append("budget_limit tidak ditemukan persis di teks dokumen (substring mismatch).")

    return (len(errors) == 0), errors