# src/rfp_insight/rag/chat_engine.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field

from rfp_insight.llm.gemini_client import GeminiClient
from rfp_insight.config.settings import settings


LanguageCode = Literal["id", "en"]

# Brief-mandated refusal (ID) must match EXACTLY.
RFP_NOT_FOUND_ID = "Informasi tersebut tidak ditemukan dalam dokumen RFP ini."
# English version (not mandated by brief, but keep consistent)
RFP_NOT_FOUND_EN = "I can't find that information in this RFP document."


@dataclass
class AnswerResult:
    ok: bool
    answer: str
    retrieved: List[Dict[str, Any]]
    citations: List[int]


class ChatAnswer(BaseModel):
    answer: str = Field(..., description="Final answer to the user, based ONLY on provided context.")


def _normalize_ws(s: str) -> str:
    return " ".join((s or "").split()).strip()


def _history_to_text(history: List[Dict[str, Any]], max_turns: int = 6) -> str:
    """
    Convert last N turns into a compact text block.
    history item format: {"role": "user"/"assistant", "content": "...", "citations": [...]}
    """
    turns = history[-max_turns:] if history else []
    lines: List[str] = []
    for m in turns:
        role = (m.get("role") or "").upper()
        content = _normalize_ws(m.get("content") or "")
        if not content:
            continue
        # Keep it compact to control prompt length
        if len(content) > 600:
            content = content[:600] + " …"
        lines.append(f"{role}: {content}")
    return "\n".join(lines).strip()


def _build_rag_prompt(
    language: LanguageCode,
    question: str,
    contexts: List[Dict[str, Any]],
    history: List[Dict[str, Any]],
) -> str:
    """
    Strict prompt:
    - Use ONLY provided CONTEXT
    - If not found, refuse with exact string
    - If answered, include citations via Sources/Sumber
    """
    if language == "en":
        not_found_msg = RFP_NOT_FOUND_EN
        sources_label = "Sources: p."
        instr = (
            "You are a careful assistant. Answer ONLY using the provided CONTEXT.\n"
            f"If the answer is not explicitly in the context, say exactly:\n\"{not_found_msg}\".\n"
            "Do NOT guess.\n"
            "If you refuse, do NOT add sources.\n"
            "If you answer, include a final line: \"Sources: p. <numbers>\" if page numbers are available.\n"
        )
        empty_history = "(empty)"
    else:
        not_found_msg = RFP_NOT_FOUND_ID
        sources_label = "Sumber: Hal."
        instr = (
            "Kamu adalah asisten yang hati-hati. Jawab HANYA menggunakan CONTEXT yang diberikan.\n"
            f"Jika jawabannya tidak ada secara eksplisit di konteks, jawab persis:\n\"{not_found_msg}\".\n"
            "Jangan mengarang.\n"
            "Jika menolak, JANGAN tambahkan sumber.\n"
            "Jika menjawab, sertakan baris terakhir: \"Sumber: Hal. <angka>\" jika nomor halaman tersedia.\n"
        )
        empty_history = "(kosong)"

    history_block = _history_to_text(history, max_turns=6)
    if not history_block:
        history_block = empty_history

    # Build context snippets with page references
    ctx_lines: List[str] = []
    for i, c in enumerate(contexts, start=1):
        page = c.get("page_number")
        page_str = str(page) if isinstance(page, int) else "?"
        text = (c.get("text", "") or "").strip()
        if len(text) > 1800:
            text = text[:1800] + " …"
        ctx_lines.append(f"[{i}] (page {page_str})\n{text}")

    # Explicit refusal template
    template = (
        "REFUSAL RULE:\n"
        f"- If not found, output exactly:\n\"{not_found_msg}\"\n"
        "- and do not add any extra text.\n"
    )

    return (
        f"{instr}\n"
        f"{template}\n\n"
        f"CHAT HISTORY:\n{history_block}\n\n"
        f"QUESTION:\n{question}\n\n"
        f"CONTEXT:\n" + "\n\n".join(ctx_lines) + "\n\n"
        f"ANSWER FORMAT:\n"
        f"- If answering: end with '{sources_label} <numbers>' if possible.\n"
        f"- If refusing: output only the refusal sentence.\n"
    )


def _collect_citations(retrieved: List[Dict[str, Any]], max_pages: int = 5) -> List[int]:
    pages: List[int] = []
    for r in retrieved:
        p = r.get("page_number")
        if isinstance(p, int):
            pages.append(p)
    pages = sorted(set(pages))
    return pages[:max_pages]


def answer_question(
    index,
    question: str,
    language: LanguageCode,
    top_k: int = 3,  # brief default
    api_key: Optional[str] = None,
    history: Optional[List[Dict[str, Any]]] = None,
) -> AnswerResult:
    """
    Retrieval (LlamaIndex) + Generation (GeminiClient).

    - Uses semantic search (top_k) from in-memory index.
    - Uses chat history for multi-turn context.
    - Returns citations derived from retrieved chunks (page_number metadata).

    Note:
    - This function does NOT modify Streamlit session_state directly.
      UI/app layer should append chat turns to session history.
    """
    if not api_key:
        raise ValueError("api_key is required for GeminiClient in answer_question().")

    history = history or []

    # 1) Retrieve top-k nodes (NO LLM)
    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(question)

    retrieved: List[Dict[str, Any]] = []
    for n in nodes:
        md = getattr(n, "metadata", {}) or {}
        try:
            text = n.get_content()
        except Exception:
            text = str(getattr(n, "text", ""))

        page_number = md.get("page_number")
        if isinstance(page_number, str):
            try:
                page_number = int(page_number)
            except Exception:
                pass

        retrieved.append(
            {
                "score": float(getattr(n, "score", 0.0) or 0.0),
                "page_number": page_number,
                "text": text,
            }
        )

    # If no context retrieved -> refuse
    if not retrieved:
        msg = RFP_NOT_FOUND_EN if language == "en" else RFP_NOT_FOUND_ID
        return AnswerResult(ok=False, answer=msg, retrieved=[], citations=[])

    citations = _collect_citations(retrieved)

    # 2) Build strict prompt with history + contexts
    prompt = _build_rag_prompt(
        language=language,
        question=question,
        contexts=retrieved,
        history=history,
    )

    # 3) Generate answer using GeminiClient.generate_structured
    client = GeminiClient(api_key=api_key)
    resp = client.generate_structured(
        model=getattr(settings, "GEMINI_MODEL_CHAT", settings.GEMINI_MODEL_ANALYZER),
        system_instruction=None,
        user_prompt=prompt,
        full_text="",
        schema=ChatAnswer,
        temperature=0.2,
    )
    answer = (resp.answer or "").strip()

    # 4) Determine ok flag based on refusal message (exact)
    lowered = answer.lower()
    not_found = (RFP_NOT_FOUND_EN.lower() in lowered) or (RFP_NOT_FOUND_ID.lower() in lowered)

    return AnswerResult(ok=not not_found, answer=answer, retrieved=retrieved, citations=citations)