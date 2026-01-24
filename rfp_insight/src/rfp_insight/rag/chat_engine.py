from __future__ import annotations
from typing import List, Dict, Any
from rfp_insight.utils.types import PageText


def build_chat_index(pages: List[PageText]) -> Any:
    """
    CONTRACT (Milestone 3 akan diisi):
    input: pages with text+page metadata
    output: in-memory vector index / retriever handle
    """
    raise NotImplementedError("Implemented in Milestone 3: indexing for chat")


def answer_question(question: str, chat_index: Any, chat_history: List[Dict[str, str]]) -> str:
    """
    CONTRACT (Milestone 3-4 akan diisi):
    input: question, index handle, session chat history
    output: final answer string (with citations if possible)
    """
    raise NotImplementedError("Implemented in Milestone 3-4: retrieval + response + memory")