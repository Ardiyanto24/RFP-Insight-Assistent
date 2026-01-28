from rfp_insight.ingestion.pdf_loader import load_pdf_pages

def test_loader_exists():
    assert callable(load_pdf_pages)