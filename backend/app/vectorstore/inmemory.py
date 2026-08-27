"""Offline :class:`VectorStore` implementation used by unit tests.

Because the production store (Pinecone) is hosted, plain unit tests must not
touch the network. This module mirrors the same ``VectorStore`` contract with a
pure in-process implementation (cosine distance over the injected embedder), so
the retriever, ingestion, pipeline and API tests run instantly and offline while
exercising identical semantics (idempotent re-ingest, nearest-first ordering,
server-side-style access filtering).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from app.vectorstore.base import (
    EmbedFn,
    RetrievedChunk,
    VectorStore,
    _require_equal_lengths,  # noqa: PLC2701 - shared helper
)


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity of two vectors (assumes same length)."""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


class InMemoryVectorStore(VectorStore):
    """In-process store: ``id -> (text, metadata, vector)``."""

    def __init__(self, embed_fn: EmbedFn) -> None:
        self._embed_fn = embed_fn
        self._chunks: dict[str, tuple[str, dict, list[float]]] = {}

    def delete_source(self, source: str) -> None:
        doomed = [cid for cid, (_, meta, _) in self._chunks.items() if meta.get("source") == source]
        for cid in doomed:
            del self._chunks[cid]

    def upsert_chunks(
        self, texts: Sequence[str], metadatas: Sequence[dict], ids: Sequence[str]
    ) -> int:
        _require_equal_lengths(texts, metadatas, ids)
        if len(texts) == 0:
            return 0
        vectors = [list(vec) for vec in self._embed_fn(texts)]
        for cid, text, meta, vec in zip(ids, texts, metadatas, vectors, strict=True):
            self._chunks[str(cid)] = (str(text), dict(meta), vec)
        return len(texts)

    def query(
        self, query_text: str, top_k: int, allowed_levels: Sequence[str] | None = None
    ) -> list[RetrievedChunk]:
        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")
        if allowed_levels is not None and not allowed_levels:
            return []
        qv = [list(vec) for vec in self._embed_fn([query_text])][0]
        if allowed_levels is not None:
            allowed = set(allowed_levels)
            candidates = [
                (t, m, v) for t, m, v in self._chunks.values() if m.get("access_level") in allowed
            ]
        else:
            candidates = list(self._chunks.values())

        scored = [(1.0 - _cosine(qv, v), t, m) for t, m, v in candidates]
        scored.sort(key=lambda item: item[0])
        return [
            RetrievedChunk(text=t, metadata=dict(m), distance=float(d))
            for d, t, m in scored[:top_k]
        ]

    def count(self) -> int:
        return len(self._chunks)
