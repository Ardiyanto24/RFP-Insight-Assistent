# src/rfp_insight/rag/guardrails.py
from __future__ import annotations

from typing import List
from llama_index.core.schema import NodeWithScore


def should_refuse_answer(
    retrieved: List[NodeWithScore],
    min_score: float = 0.35,
    min_nodes: int = 1,
) -> bool:
    """
    Simple guardrail:
    - refuse if not enough nodes retrieved
    - or top score below threshold
    """
    if len(retrieved) < min_nodes:
        return True
    top = retrieved[0].score or 0.0
    return top < min_score


REFUSAL_TEXT_ID = (
    "Maaf, saya tidak menemukan informasi itu di dokumen ini. "
    "Coba tanyakan hal yang spesifik terkait isi RFP/TOR yang Anda upload."
)

REFUSAL_TEXT_EN = (
    "Sorry — I can’t find that information in the uploaded document. "
    "Try asking something that is explicitly covered by the RFP/TOR."
)