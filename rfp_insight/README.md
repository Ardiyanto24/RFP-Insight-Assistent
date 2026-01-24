# RFP Insight — The 10-Second Bid Analyzer

A Streamlit app that lets Sales/Bid teams upload an RFP/TOR PDF and:
1) Auto-extract key fields into a structured table (deadline, budget, requirements).
2) Ask questions via document-grounded chat (RAG).

## Scope
- Single PDF upload per session (10–100 pages)
- Whole-document extraction (high accuracy for deadline & budget)
- Chunk-based semantic search for chat (top-k retrieval)
- Session-only (no persistent storage)

## Non-Scope (for now)
- Multi-document knowledge base
- External vector DB (Pinecone/Qdrant)
- User auth / role management
- OCR pipeline (only warning for scanned PDFs)

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py