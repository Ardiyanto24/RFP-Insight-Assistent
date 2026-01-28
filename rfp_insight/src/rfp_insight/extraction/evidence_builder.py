# src/rfp_insight/extraction/evidence_builder.py
from __future__ import annotations

from typing import Dict, Optional

from rfp_insight.ui.state import EvidenceItem
from rfp_insight.utils.types import PageText


def _find_in_pages(pages: list[PageText], needle: str, window: int = 180) -> Optional[EvidenceItem]:
    """
    Find first occurrence of needle in pages, return page + snippet.
    window: chars around match for snippet.
    """
    if not needle:
        return None

    needle_l = needle.lower().strip()
    for p in pages:
        text = (p.text or "")
        text_l = text.lower()
        idx = text_l.find(needle_l)
        if idx >= 0:
            start = max(0, idx - window)
            end = min(len(text), idx + len(needle) + window)
            snippet = text[start:end].strip()
            return {"page": p.page_number, "snippet": snippet}
    return None


def build_extract_evidence(pages: list[PageText], extract_result) -> Dict[str, EvidenceItem]:
    """
    Build minimal evidence map for demo:
    - submission_deadline
    - budget_limit

    Evidence is best-effort. If not found, key may be omitted.
    """
    ev: Dict[str, EvidenceItem] = {}

    deadline = getattr(extract_result, "submission_deadline", None)
    budget = getattr(extract_result, "budget_limit", None)

    # Try exact string match first (fast, deterministic)
    if isinstance(deadline, str) and deadline.strip():
        found = _find_in_pages(pages, deadline.strip())
        if found:
            ev["submission_deadline"] = found

    if isinstance(budget, str) and budget.strip():
        found = _find_in_pages(pages, budget.strip())
        if found:
            ev["budget_limit"] = found

    return ev