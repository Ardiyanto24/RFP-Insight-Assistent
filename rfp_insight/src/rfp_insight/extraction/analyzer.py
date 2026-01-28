# src/rfp_insight/extraction/analyzer.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional, Literal
import time

from rfp_insight.config.settings import settings
from rfp_insight.config.prompts import (
    ANALYZER_SYSTEM_ID,
    ANALYZER_SYSTEM_EN,
    build_analyzer_user_prompt,
)
from rfp_insight.schemas.extraction import ExtractionResult
from rfp_insight.llm.gemini_client import GeminiClient
from rfp_insight.extraction.validators import validate_exact_fields
from rfp_insight.utils.types import PageText  # ✅ add


@dataclass
class AnalyzerLog:
    attempt: int
    ok: bool
    latency_sec: float
    errors: List[str]


def build_full_text(pages_text: List[str]) -> str:
    """Join pages into single context."""
    full = "\n\n".join(pages_text).strip()
    if len(full) > settings.MAX_FULLTEXT_CHARS:
        head = full[: settings.MAX_FULLTEXT_CHARS // 2]
        tail = full[-settings.MAX_FULLTEXT_CHARS // 2 :]
        full = head + "\n\n...[TRUNCATED]...\n\n" + tail
    return full


def build_full_text_from_pages(pages: List[PageText]) -> str:
    """Helper agar nyambung ke output pdf_loader (List[PageText])."""
    return build_full_text([(p.text or "") for p in pages])


def analyze_whole_document(
    full_text: str,
    language: Literal["id", "en"], 
    api_key: str,
) -> Tuple[ExtractionResult, List[AnalyzerLog]]:
    """
    Whole-document extraction with retries + strict validation.

    Success rule:
      - Consider success if returned logs contains ok=True.
      - If all attempts fail, result may be empty schema; UI must show controlled error.
    """
    client = GeminiClient(api_key=api_key)
    logs: List[AnalyzerLog] = []

    system_instruction = ANALYZER_SYSTEM_EN if language == "en" else ANALYZER_SYSTEM_ID
    user_prompt = build_analyzer_user_prompt(language)

    last_result: Optional[ExtractionResult] = None

    for attempt in range(1, settings.ANALYZER_MAX_RETRIES + 2):
        t0 = time.time()
        errors: List[str] = []
        ok = False

        try:
            result = client.generate_structured(
                model=settings.GEMINI_MODEL_ANALYZER,
                system_instruction=system_instruction,
                user_prompt=user_prompt,
                full_text=full_text,
                schema=ExtractionResult,
                temperature=settings.ANALYZER_TEMPERATURE,
            )
            last_result = result

            ok_exact, exact_errors = validate_exact_fields(result, full_text)
            if not ok_exact:
                errors.extend(exact_errors)
            else:
                ok = True

        except Exception as e:
            errors.append(f"LLM/parse error: {type(e).__name__}: {e}")

        latency = time.time() - t0
        logs.append(AnalyzerLog(attempt=attempt, ok=ok, latency_sec=latency, errors=errors))

        if ok:
            return last_result, logs

    return (last_result or ExtractionResult()), logs
