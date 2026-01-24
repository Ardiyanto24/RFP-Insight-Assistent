# app.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import os
import streamlit as st

from rfp_insight.ingestion.pdf_loader import load_pdf_pages
from rfp_insight.ingestion.text_cleaner import normalize_text
from rfp_insight.ingestion.language import is_likely_scanned_pdf, detect_language_id_en

from rfp_insight.extraction.analyzer import analyze_whole_document
from rfp_insight.config.settings import settings

st.set_page_config(page_title="RFP Insight", layout="wide")

st.title("RFP Insight — The 10-Second Bid Analyzer")
st.caption("Upload PDF RFP/TOR untuk auto-extraction & chat Q&A (session-only, tidak disimpan).")

st.divider()

st.subheader("1) Upload Dokumen (PDF)")
uploaded = st.file_uploader("Pilih file PDF", type=["pdf"])

if uploaded is None:
    st.info("Silakan upload PDF untuk memulai.")
    st.stop()

file_bytes = uploaded.getvalue()

# 1) Load raw pages
pages = load_pdf_pages(file_bytes)

# 2) Normalize per page (light)
pages_clean = []
for p in pages:
    pages_clean.append(type(p)(page_number=p.page_number, text=normalize_text(p.text)))

# 3) Detect scan + language
scan_like = is_likely_scanned_pdf(pages_clean)
lang = detect_language_id_en(pages_clean)

# 4) UI summary
st.success(f"PDF terbaca: **{len(pages_clean)} halaman** | Bahasa terdeteksi: **{lang.upper()}**")

if scan_like:
    st.warning("Dokumen tampaknya hasil scan gambar. Hasil ekstraksi mungkin tidak akurat tanpa OCR.")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("2) Preview Teks (2–3 halaman)")
    preview_pages = pages_clean[:3]
    for p in preview_pages:
        with st.expander(f"Halaman {p.page_number}", expanded=(p.page_number == 1)):
            st.text(p.text[:4000] if p.text else "[HALAMAN KOSONG / TIDAK ADA TEKS]")

with col2:
    st.subheader("3) Auto-Extraction (Analyzer)")

    # API key: prefer Streamlit secrets, fallback to env
    api_key = os.getenv("GOOGLE_API_KEY")

    # st.secrets bisa melempar error kalau secrets.toml tidak ada → harus try/except
    try:
        secret_key = st.secrets.get("GOOGLE_API_KEY", None)
        if secret_key:
            api_key = secret_key
    except Exception:
        # Tidak ada secrets.toml → abaikan, pakai env var
        pass

    if not api_key:
        st.error(
            "API Key belum di-set. Isi st.secrets['GOOGLE_API_KEY'] "
            "(Streamlit Cloud) atau env GOOGLE_API_KEY (lokal)."
        )
        st.stop()

    run = st.button("Run Auto-Extraction", type="primary", use_container_width=True)

    if run:
        # Gabungkan seluruh halaman menjadi satu konteks
        full_text = "\n\n".join(p.text for p in pages_clean).strip()

        with st.spinner("Menganalisis dokumen (whole-context)..."):
            result, logs = analyze_whole_document(
                full_text=full_text,
                language=lang,
                api_key=api_key,
            )

        st.success("Selesai. Berikut hasil ekstraksi:")

        # JSON output (audit-friendly)
        st.json(result.model_dump())

        st.subheader("Tabel Ringkas")
        st.table(
            {
                "field": [
                    "project_title",
                    "submission_deadline",
                    "budget_limit",
                    "technical_requirements_summary",
                ],
                "value": [
                    result.project_title,
                    result.submission_deadline,
                    result.budget_limit,
                    result.technical_requirements_summary,
                ],
            }
        )

        st.subheader("Log Parsing (attempts)")
        st.write(
            [
                {
                    "attempt": l.attempt,
                    "ok": l.ok,
                    "latency_sec": round(l.latency_sec, 2),
                    "errors": l.errors,
                }
                for l in logs
            ]
        )

        st.caption(f"Model: {settings.GEMINI_MODEL_ANALYZER} | Target latency: < 15 detik")

st.divider()
st.caption("Privacy: Dokumen diproses hanya selama sesi browser aktif. Tidak disimpan permanen.")