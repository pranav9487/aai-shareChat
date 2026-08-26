"""Similarity retrieval over the ingested document collection."""

from __future__ import annotations

from collections.abc import Sequence

from app.vectorstore.chroma_client import ChromaVectorStore, RetrievedChunk


class Retriever:
    """Fetches the most similar stored chunks for a free-text query."""

    def __init__(self, store: ChromaVectorStore, top_k: int = 5) -> None:
        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")
        self._store = store
        self.top_k = top_k

    def retrieve(
        self, query: str, allowed_levels: Sequence[str] | None = None
    ) -> list[RetrievedChunk]:
        """Return up to ``top_k`` chunks closest to *query*, nearest first.

        Whitespace-only queries yield an empty list; an empty corpus also
        yields an empty list instead of querying the store. When
        *allowed_levels* is provided, only chunks from those access tiers can
        come back (the filter runs inside the vector store); an empty
        sequence denies every chunk.
        """
        if not query or not query.strip():
            return []
        if allowed_levels is not None and not allowed_levels:
            return []
        total = self._store.count()
        if total == 0:
            return []
        effective_k = min(self.top_k, total)
        return self._store.query(query.strip(), effective_k, allowed_levels=allowed_levels)
