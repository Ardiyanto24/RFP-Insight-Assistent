# src/rfp_insight/rag/indexing.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from llama_index.core.schema import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import VectorStoreIndex
from llama_index.core.embeddings import BaseEmbedding

from rfp_insight.utils.types import PageText

from google import genai


@dataclass
class ChunkedDoc:
    documents: List[Document]
    stats: Dict[str, Any]


def build_documents_from_pages(pages: List[PageText]) -> ChunkedDoc:
    """
    PageText[] -> LlamaIndex Document[] (1 doc per page) with page_number metadata.
    """
    docs: List[Document] = []
    empty_pages = 0

    for p in pages:
        text = (p.text or "").strip()
        if not text:
            empty_pages += 1
            continue

        docs.append(
            Document(
                text=text,
                metadata={"page_number": p.page_number},
            )
        )

    stats = {
        "n_pages_in": len(pages),
        "n_docs_out": len(docs),
        "empty_pages_skipped": empty_pages,
    }
    return ChunkedDoc(documents=docs, stats=stats)


def chunk_documents(
    documents: List[Document],
    chunk_size: int = 1024,
    chunk_overlap: int = 128,
) -> List[Document]:
    """
    Chunk documents using SentenceSplitter.
    Output: list of Document chunks (text + metadata preserved).
    """
    splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    nodes = splitter.get_nodes_from_documents(documents)

    chunked_docs: List[Document] = []
    for n in nodes:
        md = dict(n.metadata or {})
        chunked_docs.append(Document(text=n.get_content(), metadata=md))

    return chunked_docs


class GoogleGenAIEmbeddingAdapter(BaseEmbedding):
    """
    Adapter embedding model for LlamaIndex using google-genai embeddings.
    Compatible with newer LlamaIndex BaseEmbedding abstract methods.
    """

    def __init__(self, api_key: str, model: str = "gemini-embedding-001"):
        super().__init__()
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def _get_text_embedding(self, text: str) -> List[float]:
        res = self._client.models.embed_content(
            model=self._model,
            contents=[text],
        )
        return res.embeddings[0].values

    def _get_query_embedding(self, query: str) -> List[float]:
        return self._get_text_embedding(query)

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        res = self._client.models.embed_content(
            model=self._model,
            contents=texts,
        )
        return [e.values for e in res.embeddings]

    def get_text_embedding(self, text: str, **kwargs) -> List[float]:
        return self._get_text_embedding(text)

    def get_text_embedding_batch(
        self,
        texts: List[str],
        show_progress: bool = False,
        **kwargs,
    ) -> List[List[float]]:
        return self._get_text_embeddings(texts)


def build_vector_index(
    chunked_docs: List[Document],
    api_key: str,
    embedding_model: str = "gemini-embedding-001",
) -> VectorStoreIndex:
    """Create in-memory VectorStoreIndex using Google embeddings."""
    embed_model = GoogleGenAIEmbeddingAdapter(api_key=api_key, model=embedding_model)
    return VectorStoreIndex.from_documents(chunked_docs, embed_model=embed_model)


def build_rag_index_from_pages(
    pages: List[PageText],
    api_key: str,
    chunk_size: int = 1024,
    chunk_overlap: int = 128,
    embedding_model: str = "gemini-embedding-001",
) -> Tuple[VectorStoreIndex, Dict[str, Any]]:
    """
    Orchestrator for UI button: Build Chat Index.
    Returns: (index, stats)
    """
    docpack = build_documents_from_pages(pages)
    chunks = chunk_documents(docpack.documents, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    index = build_vector_index(chunks, api_key=api_key, embedding_model=embedding_model)

    stats: Dict[str, Any] = {}
    stats.update(docpack.stats)
    stats.update(
        {
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "n_chunks": len(chunks),
            "embedding_model": embedding_model,
        }
    )
    return index, stats