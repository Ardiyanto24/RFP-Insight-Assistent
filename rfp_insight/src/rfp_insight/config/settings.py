# src/rfp_insight/config/settings.py
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # Model IDs (Gemini Developer API / GenAI SDK)
    GEMINI_MODEL_ANALYZER: str = "models/gemini-2.5-flash"
    # Analyzer harus deterministic
    ANALYZER_TEMPERATURE: float = 0.0

    # Guardrails & performance
    ANALYZER_MAX_RETRIES: int = 2  # total attempts = 1 + retries
    ANALYZER_TIMEOUT_SEC: int = 20  # target brief < 15s, tapi kasih buffer kecil

    # Truncation guard (long PDF)
    MAX_FULLTEXT_CHARS: int = 1_500_000  # long context; tetap batasi biar aman

    def get_api_key(self) -> str | None:
        # Local dev: .env -> os.environ
        # Streamlit Cloud: st.secrets["GOOGLE_API_KEY"] (kita handle di app)
        return os.getenv("GOOGLE_API_KEY")


settings = Settings()