"""Similarity retrieval over the ingested document collection."""

from __future__ import annotations

from app.vectorstore.chroma_client import ChromaVectorStore, RetrievedChunk

# TODO(item-2): once roles exist, filter results here by the levels the
# requesting user is allowed to see. Never return another user's context.


class Retriever:
    """Fetches the most similar stored chunks for a free-text query."""

    def __init__(self, store: ChromaVectorStore, top_k: int = 5) -> None:
        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")
        self._store = store
        self.top_k = top_k

    def retrieve(self, query: str) -> list[RetrievedChunk]:
        """Return up to ``top_k`` chunks closest to *query*, nearest first.

        Whitespace-only queries yield an empty list; an empty corpus also
        yields an empty list instead of querying the store.
        """
        if not query or not query.strip():
            return []
        total = self._store.count()
        if total == 0:
            return []
        effective_k = min(self.top_k, total)
        return self._store.query(query.strip(), effective_k)
