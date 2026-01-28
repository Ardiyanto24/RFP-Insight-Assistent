# app.py
import sys
from pathlib import Path
import time
import os
import hashlib
import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rfp_insight.ingestion.pdf_loader import load_pdf_pages
from rfp_insight.ingestion.text_cleaner import normalize_text
from rfp_insight.ingestion.language import is_likely_scanned_pdf, detect_language_id_en
from rfp_insight.extraction.evidence_builder import build_extract_evidence

from rfp_insight.extraction.analyzer import analyze_whole_document

from rfp_insight.rag.indexing import (
    build_rag_index_from_pages,  # ✅ Step 7 orchestrator
)
from rfp_insight.rag.chat_engine import answer_question

# === M5: Error handling utilities ===
from rfp_insight.utils.error_handling import (
    map_exception_to_user_error,
    set_cooldown_until,
)

# === Step 2: UI messages ===
from rfp_insight.ui.messages import LABEL, NOTICE, ERR, EMPTY

# === Step 3: UI components ===
from rfp_insight.ui.components import (
    render_header,
    render_sidebar,
)

# === Step 1: Session State Contract ===
from rfp_insight.ui.state import (
    init_state,
    reset_state,
    append_chat,
    set_error,
    clear_error,
    SS_DOC_FILE_NAME,
    SS_DOC_FILE_BYTES,
    SS_DOC_PAGES,
    SS_DOC_FULL_TEXT,
    SS_DOC_LANGUAGE,
    SS_SCAN_WARNING,
    SS_DOC_META,
    SS_EXTRACT_RESULT,
    SS_EXTRACT_JSON,
    SS_EXTRACT_EVIDENCE,
    SS_EXTRACT_LAT_MS,
    SS_ANALYZER_RUNNING,
    SS_RAG_INDEX,
    SS_INDEX_READY,
    SS_INDEX_BUILDING,
    SS_CHAT_HISTORY,
    SS_LAST_ERROR,
)

init_state()

# ---------------------------
# Page config + Header/Sidebar
# ---------------------------
st.set_page_config(page_title="RFP Insight", layout="wide")
render_header()
actions = render_sidebar()

# ---------------------------
# Helper: cooldown guard (M5)
# ---------------------------
def in_cooldown() -> bool:
    until = st.session_state.get("cooldown_until")
    return until is not None and time.time() < until

def cooldown_remaining_sec() -> int:
    until = st.session_state.get("cooldown_until")
    if until is None:
        return 0
    return max(0, int(until - time.time()))

# ---------------------------
# 0) API key (global)
# ---------------------------
api_key = os.getenv("GOOGLE_API_KEY")
try:
    secret_key = st.secrets.get("GOOGLE_API_KEY", None)
    if secret_key:
        api_key = secret_key
except Exception:
    pass

# ---------------------------
# Sidebar: Upload PDF + validation (Step 3)
# ---------------------------
with st.sidebar:
    uploaded = st.file_uploader("Pilih file PDF", type=["pdf"])

if uploaded is None:
    st.info(EMPTY.NO_DOCUMENT)
    # still render dashboard placeholders
    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        st.subheader(LABEL.ANALYZER_TITLE)
        st.info(EMPTY.NO_EXTRACTION)
    with right:
        st.subheader(LABEL.CHAT_TITLE)
        st.info(EMPTY.NO_INDEX)
    st.stop()

# MIME type validation
if getattr(uploaded, "type", None) != "application/pdf":
    st.error(ERR.NON_PDF_MIME)
    st.stop()

file_bytes = uploaded.getvalue()

# Size guard
MAX_MB = 25
size_mb = len(file_bytes) / (1024 * 1024)
if size_mb > MAX_MB:
    st.error(f"{ERR.TOO_LARGE} ({size_mb:.1f} MB). Maksimal {MAX_MB} MB.")
    st.stop()

# Save to session (needed for Step 6 page preview)
st.session_state[SS_DOC_FILE_NAME] = uploaded.name
st.session_state[SS_DOC_FILE_BYTES] = file_bytes

# Fingerprint document; if changed, reset contract state
doc_fp = hashlib.sha256(file_bytes).hexdigest()
prev_fp = (st.session_state.get(SS_DOC_META) or {}).get("doc_fp")
if prev_fp != doc_fp:
    reset_state(keep_debug=True)
    st.session_state[SS_DOC_FILE_NAME] = uploaded.name
    st.session_state[SS_DOC_FILE_BYTES] = file_bytes
    st.session_state[SS_DOC_META] = {"doc_fp": doc_fp}

# ---------------------------
# 1) Load + normalize pages (fills Step 1 contract)
# ---------------------------
pages = load_pdf_pages(file_bytes)
pages_clean = [type(p)(page_number=p.page_number, text=normalize_text(p.text)) for p in pages]
pages_clean = [p for p in pages_clean if hasattr(p, "text")]

scan_like = is_likely_scanned_pdf(pages_clean)
lang = detect_language_id_en(pages_clean)

st.session_state[SS_DOC_PAGES] = pages_clean
st.session_state[SS_DOC_FULL_TEXT] = "\n\n".join((p.text or "") for p in pages_clean).strip()
st.session_state[SS_DOC_LANGUAGE] = lang
st.session_state[SS_SCAN_WARNING] = scan_like

st.session_state[SS_DOC_META] = {
    **(st.session_state.get(SS_DOC_META) or {}),
    "doc_fp": doc_fp,
    "n_pages": len(pages_clean),
    "size_mb": round(size_mb, 2),
    "mime": getattr(uploaded, "type", None),
}

# ---------------------------
# 2) Trigger actions from Sidebar (Analyze / Build Index / Reset)
# ---------------------------
if actions.reset_clicked:
    reset_state(keep_debug=True)
    st.success("Session di-reset. Silakan upload ulang.")
    st.stop()

# Analyze (Step 5) + Evidence build (Step 6)
if actions.analyze_clicked:
    if not api_key:
        st.error(ERR.API_KEY_MISSING)
    else:
        clear_error()
        st.session_state[SS_ANALYZER_RUNNING] = True
        t0 = time.time()
        try:
            with st.spinner("Menganalisis dokumen..."):
                result, logs = analyze_whole_document(
                    full_text=st.session_state[SS_DOC_FULL_TEXT],
                    language=st.session_state[SS_DOC_LANGUAGE],
                    api_key=api_key,
                )

            st.session_state[SS_EXTRACT_RESULT] = result
            st.session_state[SS_EXTRACT_JSON] = result.model_dump()
            st.session_state[SS_EXTRACT_LAT_MS] = int((time.time() - t0) * 1000)

            st.session_state[SS_EXTRACT_EVIDENCE] = build_extract_evidence(
                st.session_state[SS_DOC_PAGES],
                result,
            )

            st.session_state[SS_DOC_META] = {
                **(st.session_state.get(SS_DOC_META) or {}),
                "analyzer_logs": logs,
            }

        except Exception as e:
            uerr = map_exception_to_user_error(e)
            set_error(f"{uerr.title}: {uerr.message}")
            st.error(f"{uerr.title}: {uerr.message}")
            st.caption(f"Aksi: {uerr.action}")
            if uerr.retry_after_sec:
                st.session_state["cooldown_until"] = set_cooldown_until(uerr.retry_after_sec)

        finally:
            st.session_state[SS_ANALYZER_RUNNING] = False

# Build Chat Index (Step 7) — on demand
if actions.build_index_clicked:
    if not api_key:
        st.error(ERR.API_KEY_MISSING)
    else:
        if not st.session_state[SS_INDEX_READY]:
            st.session_state[SS_INDEX_BUILDING] = True
            try:
                with st.spinner("Membangun chat index (RAG)..."):
                    index, stats = build_rag_index_from_pages(
                        st.session_state[SS_DOC_PAGES],
                        api_key=api_key,
                        chunk_size=1024,
                        chunk_overlap=128,
                        embedding_model="gemini-embedding-001",
                    )
                    st.session_state[SS_RAG_INDEX] = index
                    st.session_state[SS_INDEX_READY] = True
                    st.session_state[SS_DOC_META] = {
                        **(st.session_state.get(SS_DOC_META) or {}),
                        "rag_stats": stats,
                    }
            finally:
                st.session_state[SS_INDEX_BUILDING] = False

# ---------------------------
# 3) Dashboard Layout (2 columns)
# ---------------------------
left, right = st.columns([1.05, 0.95], gap="large")

# LEFT: Analyzer
with left:
    st.subheader(LABEL.ANALYZER_TITLE)

    st.success(
        f"{NOTICE.PAGES_PREFIX} **{len(pages_clean)} halaman** | {NOTICE.LANG_PREFIX} **{lang.upper()}**"
    )
    if scan_like:
        st.warning(NOTICE.SCAN_WARNING)

    with st.expander("Preview Teks (3 halaman pertama)", expanded=False):
        for p in pages_clean[:3]:
            st.markdown(f"**Halaman {p.page_number}**")
            st.text(p.text[:2000] if p.text else EMPTY.NO_TEXT_PAGE)
            st.divider()

    if st.session_state.get(SS_LAST_ERROR):
        st.warning(st.session_state[SS_LAST_ERROR])

    if st.session_state.get(SS_EXTRACT_RESULT) is None:
        st.info(EMPTY.NO_EXTRACTION)
    else:
        result = st.session_state[SS_EXTRACT_RESULT]
        st.success(
            f"{LABEL.ANALYZER_RESULTS_TITLE} (latency: {st.session_state.get(SS_EXTRACT_LAT_MS)} ms)"
        )
        st.json(st.session_state.get(SS_EXTRACT_JSON))
        st.subheader(LABEL.ANALYZER_SUMMARY_TITLE)
        st.table(
            {
                "field": [
                    "project_title",
                    "submission_deadline",
                    "budget_limit",
                    "technical_requirements_summary",
                ],
                "value": [
                    getattr(result, "project_title", None),
                    getattr(result, "submission_deadline", None),
                    getattr(result, "budget_limit", None),
                    getattr(result, "technical_requirements_summary", None),
                ],
            }
        )

# RIGHT: Chat (Step 7)
with right:
    st.subheader(LABEL.CHAT_TITLE)

    if not api_key:
        st.warning(ERR.API_KEY_MISSING)

    rag_stats = (st.session_state.get(SS_DOC_META) or {}).get("rag_stats")
    st.caption(f"{NOTICE.INDEX_READY_PREFIX} {rag_stats if rag_stats else '—'}")

    if in_cooldown():
        st.warning(f"Kena rate limit. Coba lagi dalam {cooldown_remaining_sec()} detik.")

    if not st.session_state[SS_INDEX_READY]:
        st.info(EMPTY.NO_INDEX)

    # Render chat history
    for msg in st.session_state[SS_CHAT_HISTORY]:
        if msg.get("role") == "user":
            st.chat_message("user").write(msg.get("content", ""))
        else:
            st.chat_message("assistant").write(msg.get("content", ""))
            cits = msg.get("citations") or []
            if cits:
                pages = [c.get("page") for c in cits if isinstance(c, dict) and c.get("page") is not None]
                pages = [p for p in pages if isinstance(p, int)]
                if pages:
                    st.caption("Sumber: " + ", ".join([f"Hal. {p}" for p in pages]))

    # Chat input enabled only if index ready and not cooldown
    chat_disabled = in_cooldown() or (not st.session_state[SS_INDEX_READY]) or (not api_key)
    q = st.chat_input(LABEL.CHAT_INPUT_PLACEHOLDER, disabled=chat_disabled)

    if q and q.strip():
        user_q = q.strip()
        append_chat("user", user_q)

        try:
            with st.spinner("Menjawab..."):
                ans = answer_question(
                    st.session_state[SS_RAG_INDEX],
                    user_q,
                    language=st.session_state[SS_DOC_LANGUAGE],
                    top_k=3,  # ✅ Step 7 requirement
                    api_key=api_key,
                    history=st.session_state[SS_CHAT_HISTORY],
                )

            append_chat(
                "assistant",
                ans.answer,
                citations=[{"page": p} for p in (ans.citations or [])] if ans.citations else None,
            )

            st.session_state[SS_DOC_META] = {
                **(st.session_state.get(SS_DOC_META) or {}),
                "last_retrieved": ans.retrieved,
            }

            st.rerun()

        except Exception as e:
            uerr = map_exception_to_user_error(e)
            st.error(f"{uerr.title}: {uerr.message}")
            st.caption(f"Aksi: {uerr.action}")
            if uerr.retry_after_sec:
                st.session_state["cooldown_until"] = set_cooldown_until(uerr.retry_after_sec)
                

with st.status("Processing document...", expanded=True) as status:
    status.update(label="📄 Loading PDF", state="running")
    pages = load_pdf_pages(file_bytes)

    status.update(label="🧹 Normalizing text", state="running")
    pages_clean = [...]

    status.update(label="🌐 Detecting language", state="running")
    lang = detect_language_id_en(pages_clean)

    status.update(label="✅ Document ready", state="complete")

# Footer
st.divider()
st.caption(NOTICE.PRIVACY)

# Debug (optional)
with st.expander("Debug: retrieved chunks (jawaban terakhir)"):
    st.write((st.session_state.get(SS_DOC_META) or {}).get("last_retrieved", []))