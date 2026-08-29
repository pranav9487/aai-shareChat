"""Similarity retrieval over the ingested document collection."""

from __future__ import annotations

from collections.abc import Sequence

from app.vectorstore.base import RetrievedChunk, VectorStore


class Retriever:
    """Fetches the most similar stored chunks for a free-text query."""

    def __init__(
        self, store: VectorStore, top_k: int = 5, relevance_threshold: float | None = None
    ) -> None:
        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")
        self._store = store
        self.top_k = top_k
        self._relevance_threshold = relevance_threshold

    def retrieve(
        self, query: str, allowed_levels: Sequence[str] | None = None
    ) -> list[RetrievedChunk]:
        """Return up to ``top_k`` chunks closest to *query*, nearest first.

        Whitespace-only queries yield an empty list; an empty corpus also
        yields an empty list instead of querying the store. When
        *allowed_levels* is provided, only chunks from those access tiers can
        come back (the filter runs inside the vector store); an empty
        sequence denies every chunk.

        When a relevance threshold is configured, chunks with a cosine
        distance above the threshold (i.e. low similarity) are discarded.
        This prevents weak, irrelevant matches from bypassing access-denied
        detection in the pipeline.
        """
        if not query or not query.strip():
            return []
        if allowed_levels is not None and not allowed_levels:
            return []
        total = self._store.count()
        if total == 0:
            return []
        effective_k = min(self.top_k, total)
        chunks = self._store.query(query.strip(), effective_k, allowed_levels=allowed_levels)
        if self._relevance_threshold is not None:
            chunks = [c for c in chunks if c.distance <= self._relevance_threshold]
        return chunks
