# src/rfp_insight/ingestion/text_cleaner.py
from __future__ import annotations

import re


def normalize_text(text: str) -> str:
    """
    Light normalization only:
    - unify line endings
    - collapse excessive whitespace
    - keep numbers/currency/date strings intact
    """
    if not text:
        return ""

    # normalize newlines
    t = text.replace("\r\n", "\n").replace("\r", "\n")

    # remove trailing spaces on each line
    t = "\n".join(line.rstrip() for line in t.split("\n"))

    # collapse multiple blank lines (>=3 -> 2)
    t = re.sub(r"\n{3,}", "\n\n", t)

    # collapse multiple spaces/tabs
    t = re.sub(r"[ \t]{2,}", " ", t)

    return t.strip()