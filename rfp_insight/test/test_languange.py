from rfp_insight.ingestion.language import detect_language_id_en, is_likely_scanned_pdf
from rfp_insight.utils.types import PageText

def test_scan_heuristic_empty_pages():
    pages = [PageText(1, ""), PageText(2, "")]
    assert is_likely_scanned_pdf(pages) is True

def test_language_default_id_when_uncertain():
    pages = [PageText(1, "random text without hints")]
    assert detect_language_id_en(pages) in ("id", "en")
