# src/rfp_insight/ui/messages.py
"""
Step 2 — Copywriting & Error Messages (UI text)

Tujuan:
- Semua pesan konsisten, manusiawi, sesuai brief.
- Tidak ada hardcoded string tersebar di app.py / components.py.
- Satu pintu untuk label tombol, empty state, dan error messages.

Cara pakai:
    from rfp_insight.ui.messages import UI, ERR, NOTICE, EMPTY, LABEL
"""

from __future__ import annotations

from dataclasses import dataclass


# =========================
# Core: Brief-mandated text
# =========================

# IMPORTANT: This must match EXACTLY the brief requirement.
OUT_OF_CONTEXT_ID = "Informasi tersebut tidak ditemukan dalam dokumen RFP ini."


# =========================
# Labels (Buttons / UI)
# =========================

@dataclass(frozen=True)
class LABEL:
    # Sidebar / actions
    UPLOAD_TITLE: str = "Upload Dokumen (PDF)"
    UPLOAD_HELP: str = "Pilih file PDF RFP/TOR untuk dianalisis."
    BTN_ANALYZE: str = "Analyze (Auto-Extraction)"
    BTN_BUILD_INDEX: str = "Build Chat Index"
    BTN_RESET: str = "Reset Session"

    # Analyzer
    ANALYZER_TITLE: str = "Auto-Extraction (Analyzer)"
    BTN_COPY_JSON: str = "Copy JSON"
    BTN_DOWNLOAD_JSON: str = "Download JSON"
    ANALYZER_RESULTS_TITLE: str = "Hasil Ekstraksi"
    ANALYZER_SUMMARY_TITLE: str = "Ringkasan"

    # Chat
    CHAT_TITLE: str = "Chat Q&A (RAG)"
    CHAT_INPUT_PLACEHOLDER: str = "Tanyakan sesuatu tentang dokumen ini…"
    CHAT_HISTORY_TITLE: str = "Riwayat Chat"

    # Evidence / preview
    EVIDENCE_TITLE: str = "Evidence"
    BTN_VIEW_PAGE: str = "View Page"


# =========================
# Notices / Info
# =========================

@dataclass(frozen=True)
class NOTICE:
    PRIVACY: str = (
        "Privacy: Dokumen hanya diproses selama sesi browser aktif (session-only) dan tidak disimpan permanen."
    )

    SCAN_WARNING: str = (
        "Dokumen tampaknya hasil scan (image-only). Tanpa OCR, akurasi ekstraksi dan chat bisa menurun."
    )

    INDEX_READY_PREFIX: str = "Index ready:"
    LANG_PREFIX: str = "Bahasa:"
    PAGES_PREFIX: str = "PDF terbaca:"


# =========================
# Errors (Human-friendly)
# =========================

@dataclass(frozen=True)
class ERR:
    # Validation
    NON_PDF_MIME: str = "File harus PDF (MIME type bukan application/pdf)."
    NON_PDF_TYPE: str = "File harus PDF."
    TOO_LARGE: str = "Ukuran file terlalu besar."

    # API / runtime
    API_KEY_MISSING: str = "API Key belum di-set. Isi GOOGLE_API_KEY lalu restart."
    QUOTA_EXCEEDED: str = (
        "Layanan sedang penuh atau kuota habis. Coba lagi beberapa saat."
    )
    TIMEOUT: str = (
        "Permintaan memerlukan waktu terlalu lama (timeout). Coba lagi."
    )

    # Chat / RAG
    OUT_OF_CONTEXT_ID: str = OUT_OF_CONTEXT_ID


# =========================
# Empty States
# =========================

@dataclass(frozen=True)
class EMPTY:
    NO_DOCUMENT: str = "Silakan upload PDF untuk memulai."
    NO_INDEX: str = "Index belum siap. Klik 'Build Chat Index' terlebih dahulu."
    NO_EXTRACTION: str = "Belum ada hasil extraction. Klik 'Analyze (Auto-Extraction)'."
    NO_TEXT_PAGE: str = "[HALAMAN KOSONG]"


# =========================
# UI Grouping (optional)
# =========================

@dataclass(frozen=True)
class UI:
    LABEL = LABEL()
    NOTICE = NOTICE()
    ERR = ERR()
    EMPTY = EMPTY()
