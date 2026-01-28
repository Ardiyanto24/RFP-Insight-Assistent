# src/rfp_insight/utils/error_handling.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple
import re
import time


@dataclass
class UserFacingError:
    title: str
    message: str
    action: str
    retry_after_sec: Optional[int] = None


def _extract_retry_after_sec(raw: str) -> Optional[int]:
    """
    Try to extract "Please retry in XXs" or retryDelay from Gemini error strings.
    """
    m = re.search(r"retry in\s+([0-9]+(?:\.[0-9]+)?)s", raw, re.IGNORECASE)
    if m:
        return int(float(m.group(1)))
    m = re.search(r"retryDelay'\s*:\s*'([0-9]+)s'", raw)
    if m:
        return int(m.group(1))
    return None


def map_exception_to_user_error(exc: Exception) -> UserFacingError:
    raw = f"{type(exc).__name__}: {exc}"

    # Quota / rate limit (Gemini 429)
    if "429" in raw and ("RESOURCE_EXHAUSTED" in raw or "Quota exceeded" in raw or "rate" in raw.lower()):
        retry = _extract_retry_after_sec(raw)
        return UserFacingError(
            title="Kuota / Rate Limit Tercapai",
            message="Permintaan ke model sedang dibatasi (quota/rate limit). Ini bukan kesalahan aplikasi atau PDF.",
            action="Tunggu beberapa detik lalu coba lagi. Jika sering terjadi, upgrade billing/kuota di Google AI.",
            retry_after_sec=retry,
        )

    # Invalid key (Gemini 400 API_KEY_INVALID)
    if ("API key not valid" in raw) or ("API_KEY_INVALID" in raw) or ("invalid api key" in raw.lower()):
        return UserFacingError(
            title="API Key Tidak Valid",
            message="API key yang dipakai tidak valid/ditolak oleh Gemini API.",
            action="Periksa GOOGLE_API_KEY di .streamlit/secrets.toml atau environment variable, lalu restart app.",
        )

    # Model not found (404)
    if "404" in raw and ("not found" in raw.lower() or "NOT_FOUND" in raw):
        return UserFacingError(
            title="Model Tidak Tersedia",
            message="Nama model yang dipakai tidak tersedia untuk API/version yang kamu gunakan.",
            action="Ganti settings.GEMINI_MODEL_ANALYZER / GEMINI_MODEL_CHAT ke model yang ada (mis. gemini-2.5-flash).",
        )

    # Timeout / network
    if "timeout" in raw.lower() or "deadline exceeded" in raw.lower():
        return UserFacingError(
            title="Timeout",
            message="Permintaan ke API terlalu lama atau koneksi tidak stabil.",
            action="Coba ulang. Jika dokumen sangat panjang, pertimbangkan untuk mengurangi chunk/top_k atau pakai model lebih cepat.",
        )

    # Fallback unknown
    return UserFacingError(
        title="Terjadi Kesalahan",
        message="Terjadi error yang tidak terduga saat memproses permintaan.",
        action="Coba ulang. Jika tetap terjadi, kirim screenshot error ke developer.",
    )


def compute_cooldown_until(retry_after_sec: Optional[int]) -> Optional[float]:
    if retry_after_sec is None:
        return None
    return time.time() + max(1, int(retry_after_sec))


def set_cooldown_until(retry_after_sec: Optional[int]) -> Optional[float]:
    """
    Backward-compatible alias.
    app.py lama mungkin memanggil set_cooldown_until().
    """
    return compute_cooldown_until(retry_after_sec)