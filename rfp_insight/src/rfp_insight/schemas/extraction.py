# src/rfp_insight/schemas/extraction.py
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List


class ExtractionResult(BaseModel):
    """
    CONTRACT: output stabil untuk Analyzer (whole-document extraction).
    IMPORTANT: schema ini dikunci setelah Milestone 0.
    """

    project_title: Optional[str] = Field(
        default=None,
        description="Judul proyek / nama paket pekerjaan sesuai dokumen."
    )

    submission_deadline: Optional[str] = Field(
        default=None,
        description="Deadline pengumpulan proposal/penawaran, tulis persis seperti di dokumen (raw text)."
    )

    budget_limit: Optional[str] = Field(
        default=None,
        description="Batas anggaran/HPS/Owner Estimate, tulis persis seperti di dokumen (raw text)."
    )

    technical_requirements_summary: Optional[str] = Field(
        default=None,
        description="Ringkasan syarat teknis utama (bullet singkat, fact-based)."
    )

    # Optional tapi sangat membantu untuk audit (boleh dipakai nanti, tapi tidak wajib di brief)
    notes: Optional[List[str]] = Field(
        default=None,
        description="Catatan tambahan: misal bagian ambigu, atau lokasi teks penting (opsional)."
    )