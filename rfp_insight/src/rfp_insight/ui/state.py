# src/rfp_insight/ui/state.py
"""
Step 1 — Session State Contract (UI <-> Pipeline)

Tujuan:
- Menyamakan "bahasa" antara UI (Streamlit) dan pipeline (ingestion/extraction/rag).
- Semua key st.session_state terdefinisi di satu tempat.
- App reload tidak error karena state selalu ter-initialize.

Cara pakai di app.py (paling atas):
    from rfp_insight.ui.state import init_state
    init_state()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, TypedDict


# =========================
# Types (ringan, optional)
# =========================

LanguageCode = Literal["id", "en"]


@dataclass(frozen=True)
class PageText:
    """Kontrak hasil ingestion/pdf_loader.py per halaman."""
    page_number: int  # 1-based page number (lebih natural untuk user)
    text: str


class EvidenceItem(TypedDict, total=False):
    """Evidence untuk field analyzer (opsional tapi disiapkan untuk UI Evidence + View Page)."""
    page: int          # 1-based
    snippet: str       # potongan teks bukti
    note: str          # catatan tambahan (opsional)


class ChatCitation(TypedDict, total=False):
    """Citation sederhana untuk chat."""
    page: int          # 1-based
    note: str          # opsional, mis. 'Based on ...'


class ChatTurn(TypedDict, total=False):
    """Riwayat chat, multi-turn. citations opsional."""
    role: Literal["user", "assistant"]
    content: str
    citations: List[ChatCitation]


# =========================
# Session State Keys (CONST)
# =========================

# --- Document / Ingestion ---
SS_DOC_FILE_NAME = "doc_file_name"          # str | None
SS_DOC_FILE_BYTES = "doc_file_bytes"        # bytes | None (untuk render preview page)
SS_DOC_PAGES = "doc_pages"                  # list[PageText] | None
SS_DOC_FULL_TEXT = "doc_full_text"          # str | None
SS_DOC_LANGUAGE = "doc_language"            # "id"|"en"|None
SS_SCAN_WARNING = "scan_warning"            # bool
SS_DOC_META = "doc_meta"                    # dict (pages, size, etc)

# --- Analyzer / Extraction ---
SS_ANALYZER_RUNNING = "analyzer_running"    # bool
SS_EXTRACT_RESULT = "extract_result"        # Pydantic model (ExtractionResult) | None
SS_EXTRACT_JSON = "extract_json"            # dict | None
SS_EXTRACT_EVIDENCE = "extract_evidence"    # dict[str, EvidenceItem] | None
SS_EXTRACT_LAT_MS = "extract_latency_ms"    # int | None

# --- RAG / Index ---
SS_INDEX_BUILDING = "index_building"        # bool
SS_INDEX_READY = "index_ready"              # bool
SS_RAG_INDEX = "rag_index"                  # object | None (LlamaIndex in-memory index)

# --- Chat ---
SS_CHAT_HISTORY = "chat_history"            # list[ChatTurn]

# --- Page Preview Cache ---
SS_PAGE_PREVIEW_CACHE = "page_preview_cache"  # dict[int, bytes]  (page_number -> PNG bytes)

# --- Global / UX ---
SS_LAST_ERROR = "last_error"                # str | None
SS_DEBUG_MODE = "debug_mode"                # bool

SS_PREVIEW_PAGE_NO = "preview_page_no"


# =========================
# Defaults
# =========================

_DEFAULTS: Dict[str, Any] = {
    # Document
    SS_DOC_FILE_NAME: None,
    SS_DOC_FILE_BYTES: None,
    SS_DOC_PAGES: None,
    SS_DOC_FULL_TEXT: None,
    SS_DOC_LANGUAGE: None,
    SS_SCAN_WARNING: False,
    SS_DOC_META: {},

    # Analyzer
    SS_ANALYZER_RUNNING: False,
    SS_EXTRACT_RESULT: None,
    SS_EXTRACT_JSON: None,
    SS_EXTRACT_EVIDENCE: None,
    SS_EXTRACT_LAT_MS: None,

    # RAG / Index
    SS_INDEX_BUILDING: False,
    SS_INDEX_READY: False,
    SS_RAG_INDEX: None,

    # Chat
    SS_CHAT_HISTORY: [],

    # Page preview cache
    SS_PAGE_PREVIEW_CACHE: {},

    # Global
    SS_LAST_ERROR: None,
    SS_DEBUG_MODE: False,

    SS_PREVIEW_PAGE_NO: None,
}


# =========================
# API
# =========================

def init_state() -> None:
    """
    Initialize all required Streamlit session_state keys.

    Exit criteria:
    - App reload tidak error
    - Semua key ada dan punya default value
    """
    import streamlit as st

    for key, default in _DEFAULTS.items():
        if key not in st.session_state:
            # penting: list/dict di defaults harus fresh per session
            if isinstance(default, list):
                st.session_state[key] = list(default)
            elif isinstance(default, dict):
                st.session_state[key] = dict(default)
            else:
                st.session_state[key] = default


def reset_state(keep_debug: bool = True) -> None:
    """
    Reset state ke default (dipakai tombol Reset Session).
    """
    import streamlit as st

    debug_val = st.session_state.get(SS_DEBUG_MODE, False)
    for key in list(_DEFAULTS.keys()):
        if key in st.session_state:
            del st.session_state[key]

    init_state()
    if keep_debug:
        st.session_state[SS_DEBUG_MODE] = debug_val


def append_chat(role: Literal["user", "assistant"], content: str, citations: Optional[List[ChatCitation]] = None) -> None:
    """
    Helper untuk menambahkan chat turn secara konsisten.
    Mapping:
      rag/chat_engine.py -> append chat_history
    """
    import streamlit as st

    turn: ChatTurn = {"role": role, "content": content}
    if citations:
        turn["citations"] = citations

    st.session_state[SS_CHAT_HISTORY].append(turn)


def set_error(message: str) -> None:
    """
    Set last_error (UX layer). Jangan lempar exception ke user-facing UI.
    """
    import streamlit as st

    st.session_state[SS_LAST_ERROR] = message


def clear_error() -> None:
    """
    Clear last_error.
    """
    import streamlit as st

    st.session_state[SS_LAST_ERROR] = None
