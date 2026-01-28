# src/rfp_insight/ui/components.py
"""
Step 3 — Layout Dasar Dashboard (2 kolom)

Tujuan:
- UI sudah “berbentuk” (dashboard corporate) walau logic belum lengkap.
- app.py cukup memanggil:
    - render_header()
    - render_sidebar()
    - render_dashboard_columns()

Catatan:
- File ini hanya UI rendering + baca session_state.
- Logic berat (ingestion/analyzer/index/chat) tetap di app.py/service layer.

Output:
- header, sidebar controls, placeholders untuk kolom Analyzer & Chat.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
from rfp_insight.ui.page_preview import render_page_png_bytes

import streamlit as st

from rfp_insight.ui.messages import LABEL, NOTICE, ERR, EMPTY
from rfp_insight.ui.state import (
    SS_DOC_FILE_NAME,
    SS_DOC_META,
    SS_DOC_LANGUAGE,
    SS_SCAN_WARNING,
    SS_INDEX_READY,
    SS_ANALYZER_RUNNING,
    SS_INDEX_BUILDING,
    SS_LAST_ERROR,
    SS_DOC_FILE_BYTES,
    SS_EXTRACT_EVIDENCE,
    SS_PAGE_PREVIEW_CACHE,
    SS_PREVIEW_PAGE_NO,
)


# =========================
# UI Actions (return from sidebar)
# =========================

@dataclass(frozen=True)
class SidebarActions:
    analyze_clicked: bool
    build_index_clicked: bool
    reset_clicked: bool


# =========================
# Header
# =========================

def render_header() -> None:
    """
    Corporate header: title + status chips.
    """
    st.title("RFP Insight — 10-Second Bid Analyzer")
    st.caption(NOTICE.PRIVACY)
    st.divider()

    # Status chips line (simple, corporate)
    meta = st.session_state.get(SS_DOC_META) or {}
    doc_loaded = bool(st.session_state.get(SS_DOC_FILE_NAME))
    lang = st.session_state.get(SS_DOC_LANGUAGE)
    scan_warning = bool(st.session_state.get(SS_SCAN_WARNING))
    index_ready = bool(st.session_state.get(SS_INDEX_READY))
    analyzer_running = bool(st.session_state.get(SS_ANALYZER_RUNNING))
    index_building = bool(st.session_state.get(SS_INDEX_BUILDING))

    c1, c2, c3, c4, c5 = st.columns([1.2, 1, 1, 1, 1.2])

    with c1:
        st.markdown(f"**Document:** {'Loaded ✅' if doc_loaded else 'Empty ⬜'}")
    with c2:
        st.markdown(f"**Lang:** {str(lang).upper() if lang else '—'}")
    with c3:
        st.markdown(f"**Scan:** {'⚠️' if scan_warning else 'OK'}")
    with c4:
        st.markdown(f"**Index:** {'Ready ✅' if index_ready else ('Building…' if index_building else 'Not ready ⬜')}")
    with c5:
        st.markdown(f"**Analyzer:** {'Running…' if analyzer_running else 'Idle'}")

    # Optional: show compact doc info if available
    if doc_loaded and meta:
        name = st.session_state.get(SS_DOC_FILE_NAME) or "-"
        n_pages = meta.get("n_pages")
        size_mb = meta.get("size_mb")
        st.caption(f"Dokumen: **{name}** | Halaman: **{n_pages if n_pages is not None else '-'}** | Size: **{size_mb if size_mb is not None else '-'} MB**")

    # Show last error (if any)
    last_err = st.session_state.get(SS_LAST_ERROR)
    if last_err:
        st.warning(last_err)

    st.divider()


# =========================
# Sidebar
# =========================

def render_sidebar() -> SidebarActions:
    """
    Sidebar controls:
    - Upload handled in app.py (logic + validation), but sidebar shows actions.
    - Buttons: Analyze, Build Index, Reset
    """
    with st.sidebar:
        st.header("Controls")

        # Upload area placeholder (actual uploader remains in app.py for now)
        st.subheader(LABEL.UPLOAD_TITLE)
        st.caption(LABEL.UPLOAD_HELP)

        _render_doc_summary()

        st.divider()

        analyze_clicked = st.button(LABEL.BTN_ANALYZE, use_container_width=True)
        build_index_clicked = st.button(LABEL.BTN_BUILD_INDEX, use_container_width=True)
        reset_clicked = st.button(LABEL.BTN_RESET, use_container_width=True)

        st.divider()
        st.caption(NOTICE.PRIVACY)

    return SidebarActions(
        analyze_clicked=analyze_clicked,
        build_index_clicked=build_index_clicked,
        reset_clicked=reset_clicked,
    )


def _render_doc_summary() -> None:
    """
    Step 4 — Document summary after upload.
    """
    name = st.session_state.get(SS_DOC_FILE_NAME)
    meta = st.session_state.get(SS_DOC_META) or {}
    lang = st.session_state.get(SS_DOC_LANGUAGE)
    scan_warning = st.session_state.get(SS_SCAN_WARNING, False)

    if not name:
        st.info(EMPTY.NO_DOCUMENT)
        return

    st.success("Document loaded ✅")

    with st.container(border=True):
        st.markdown(f"**File:** {name}")
        st.markdown(f"**Pages:** {meta.get('n_pages', '-')}")
        st.markdown(f"**Language:** {str(lang).upper() if lang else '-'}")

        if scan_warning:
            st.warning(NOTICE.SCAN_WARNING)


# =========================
# Dashboard Columns (placeholders)
# =========================

def render_dashboard_columns() -> Dict[str, Any]:
    """
    Render main dashboard 2 columns:
    - Left: Analyzer cards (placeholder)
    - Right: Chat card (placeholder)

    Returns: dict of placeholders (optional) to let app.py insert logic later.
    """
    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        st.subheader(LABEL.ANALYZER_TITLE)
        render_evidence_panel()

    with right:
        st.subheader(LABEL.CHAT_TITLE)
        render_analyzer_panel()

    return {"left": left, "right": right}


def _render_analyzer_placeholder() -> None:
    """
    Placeholder cards for Analyzer.
    """
    with st.container(border=True):
        st.markdown("#### Key Fields")
        st.caption("Hasil auto-extraction akan muncul di sini (Project Title, Deadline, Budget, Requirements).")
        st.info("Placeholder: belum ada hasil extraction.")
        st.divider()
        st.markdown("#### Actions")
        cols = st.columns(2)
        with cols[0]:
            st.button(LABEL.BTN_COPY_JSON, disabled=True, use_container_width=True)
        with cols[1]:
            st.button(LABEL.BTN_DOWNLOAD_JSON, disabled=True, use_container_width=True)

    st.divider()

    with st.container(border=True):
        st.markdown(f"#### {LABEL.EVIDENCE_TITLE}")
        st.caption("Bukti dari halaman dokumen (tombol View Page) akan muncul di sini.")
        st.info("Placeholder: evidence belum tersedia.")
        st.button(LABEL.BTN_VIEW_PAGE, disabled=True)


def render_evidence_panel() -> None:
    """
    Step 6 — Evidence + View Page preview (on-demand, cached).
    """
    file_bytes = st.session_state.get(SS_DOC_FILE_BYTES)
    evidence = st.session_state.get(SS_EXTRACT_EVIDENCE) or {}
    cache = st.session_state.get(SS_PAGE_PREVIEW_CACHE) or {}
    selected_page = st.session_state.get(SS_PREVIEW_PAGE_NO)

    with st.container(border=True):
        st.markdown(f"#### {LABEL.EVIDENCE_TITLE}")
        st.caption("Klik View Page untuk melihat halaman bukti. Preview di-cache agar cepat.")

        if not file_bytes:
            st.info("Upload dokumen terlebih dahulu.")
            return

        if not evidence:
            st.info("Evidence belum tersedia. Jalankan **Analyze** dulu.")
            return

        def row(label: str, key: str):
            item = evidence.get(key)
            page = item.get("page") if isinstance(item, dict) else None
            snippet = item.get("snippet") if isinstance(item, dict) else None

            c1, c2, c3 = st.columns([1.2, 0.6, 0.6])
            with c1:
                st.markdown(f"**{label}**")
                if page:
                    st.caption(f"Page: {page}")
                else:
                    st.caption("Page: —")
            with c2:
                if page:
                    if st.button("View Page", key=f"view_{key}", use_container_width=True):
                        st.session_state[SS_PREVIEW_PAGE_NO] = int(page)
                else:
                    st.button("View Page", key=f"view_{key}", disabled=True, use_container_width=True)
            with c3:
                # show snippet short
                if snippet:
                    st.caption((snippet[:160] + "…") if len(snippet) > 160 else snippet)
                else:
                    st.caption("Snippet: —")

        row("Submission Deadline", "submission_deadline")
        st.divider()
        row("Budget Limit", "budget_limit")

    # Preview area
    if selected_page:
        with st.expander(f"Preview — Halaman {selected_page}", expanded=True):
            # cache hit?
            png_bytes = cache.get(selected_page)
            if png_bytes is None:
                with st.spinner("Rendering halaman..."):
                    png_bytes = render_page_png_bytes(file_bytes, selected_page, dpi=150)
                    # store back to session cache
                    st.session_state[SS_PAGE_PREVIEW_CACHE][selected_page] = png_bytes

            st.image(png_bytes, caption=f"Halaman {selected_page}", use_container_width=True)


def render_analyzer_panel() -> None:
    """
    Step 5 — Analyzer output panel.
    Menampilkan:
    - latency
    - tabel key fields
    - JSON output
    - actions: copy / download (UI only)
    """
    result = st.session_state.get("extract_result")
    extract_json = st.session_state.get("extract_json")
    latency = st.session_state.get("extract_latency_ms")
    running = st.session_state.get("analyzer_running", False)

    with st.container(border=True):
        st.markdown("#### Key Fields")

        if running:
            st.info("Analyzer sedang berjalan...")
            return

        if result is None:
            st.info("Belum ada hasil analisis. Klik **Analyze**.")
            return

        # Latency
        if latency is not None:
            st.caption(f"Latency: **{latency} ms**")

        # Key fields table
        st.table(
            {
                "Field": [
                    "Project Title",
                    "Submission Deadline",
                    "Budget Limit",
                    "Technical Requirements Summary",
                ],
                "Value": [
                    getattr(result, "project_title", None),
                    getattr(result, "submission_deadline", None),
                    getattr(result, "budget_limit", None),
                    getattr(result, "technical_requirements_summary", None),
                ],
            }
        )

    # JSON output
    with st.container(border=True):
        st.markdown("#### Raw JSON Output")

        if extract_json:
            st.json(extract_json)

            cols = st.columns(2)
            with cols[0]:
                st.button(LABEL.BTN_COPY_JSON, use_container_width=True)
            with cols[1]:
                st.download_button(
                    LABEL.BTN_DOWNLOAD_JSON,
                    data=str(extract_json),
                    file_name="analyzer_output.json",
                    mime="application/json",
                    use_container_width=True,
                )


def _render_chat_placeholder() -> None:
    """
    Placeholder card for Chat.
    """
    with st.container(border=True):
        st.markdown("#### Chat")
        st.caption("Tanya jawab berbasis dokumen (RAG).")
        st.info(EMPTY.NO_INDEX)
        st.text_input("Preview input (disabled)", value="", disabled=True)

    st.divider()

    with st.container(border=True):
        st.markdown("#### Status")
        doc_loaded = bool(st.session_state.get(SS_DOC_FILE_NAME))
        index_ready = bool(st.session_state.get(SS_INDEX_READY))
        st.write(
            {
                "document_loaded": doc_loaded,
                "index_ready": index_ready,
            }
        )
