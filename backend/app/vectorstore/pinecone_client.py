"""Pinecone-backed implementation of the :class:`VectorStore` protocol.

Construction is deliberately lazy and offline: no Pinecone client is built
until the first actual upsert/query/count call. This keeps the FastAPI
composition root (``app.api.deps._build_pipeline``) network-free at import
time, matching the project rule that plain construction must never perform a
network call, and lets unit tests construct the store safely.

Pinecone stores only metadata per vector (it has no separate "document" field
like ChromaDB), so the chunk text is carried inside metadata under the reserved
``text`` key and popped back out into :class:`RetrievedChunk.text` on query.
Pinecone's cosine query returns a *score* (higher = more similar); the rest of
the pipeline expects :class:`RetrievedChunk.distance` with *smaller = more
similar*, so scores are mapped as ``distance = 1 - score``.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.vectorstore.base import (
    DefaultEmbedder,
    EmbedFn,
    RetrievedChunk,
    VectorStore,
    _require_equal_lengths,  # noqa: PLC2701 - shared helper
)

#: Reserved metadata key carrying the chunk text (Pinecone has no separate field).
TEXT_KEY = "text"


class PineconeVectorStore(VectorStore):
    """Persists chunks to a hosted Pinecone index (single namespace)."""

    def __init__(
        self,
        api_key: str = "",
        *,
        index_name: str = "internal-docs",
        namespace: str = "",
        cloud: str = "aws",
        region: str = "us-east-1",
        dimension: int = 384,
        embed_fn: EmbedFn | None = None,
    ) -> None:
        # No network / validation here on purpose — construction stays offline.
        self._api_key = api_key
        self._index_name = index_name
        self._namespace = namespace
        self._cloud = cloud
        self._region = region
        self._dimension = dimension
        self._embed_fn: EmbedFn = embed_fn or DefaultEmbedder()
        self._index = None

    # -- lazy connect -----------------------------------------------------
    def _ensure(self):
        """Return a connected ``Pinecone.Index``, creating the index if needed."""
        if self._index is not None:
            return self._index
        if not (self._api_key or "").strip():
            raise ValueError("PINECONE_API_KEY is not set; cannot connect to Pinecone")
        from pinecone import Pinecone, ServerlessSpec  # heavy SDK, imported on use

        client = Pinecone(api_key=self._api_key)
        existing = set(client.list_indexes().names())
        if self._index_name not in existing:
            client.indexes.create(
                name=self._index_name,
                dimension=self._dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud=self._cloud, region=self._region),
            )
        self._index = client.index(self._index_name)
        return self._index

    # -- VectorStore protocol ---------------------------------------------
    def delete_source(self, source: str) -> None:
        from pinecone import NotFoundError  # lazy: SDK is only imported on use

        try:
            self._ensure().delete(filter={"source": source}, namespace=self._namespace)
        except NotFoundError:
            # Fresh serverless namespaces return 404 for filtered deletes when
            # nothing has been upserted yet — that is "nothing to delete".
            return

    def upsert_chunks(
        self, texts: Sequence[str], metadatas: Sequence[dict], ids: Sequence[str]
    ) -> int:
        _require_equal_lengths(texts, metadatas, ids)
        if len(texts) == 0:
            return 0
        embeddings = [list(vec) for vec in self._embed_fn(texts)]
        vectors = [
            (
                str(i),
                vec,
                {**dict(meta), TEXT_KEY: text},  # carry text inside metadata
            )
            for i, vec, text, meta in zip(ids, embeddings, texts, metadatas, strict=True)
        ]
        self._ensure().upsert(vectors=vectors, namespace=self._namespace)
        return len(texts)

    def query(
        self, query_text: str, top_k: int, allowed_levels: Sequence[str] | None = None
    ) -> list[RetrievedChunk]:
        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")
        if allowed_levels is not None and not allowed_levels:
            return []
        query_vector = [list(vec) for vec in self._embed_fn([query_text])][0]
        filter_ = (
            {"access_level": {"$in": list(allowed_levels)}} if allowed_levels is not None else None
        )
        result = self._ensure().query(
            vector=query_vector,
            top_k=top_k,
            filter=filter_,
            include_metadata=True,
            namespace=self._namespace,
        )
        chunks: list[RetrievedChunk] = []
        for match in result.matches:
            meta = dict(match.metadata or {})
            text = str(meta.pop(TEXT_KEY, ""))
            chunks.append(
                RetrievedChunk(
                    text=text,
                    metadata=meta,
                    distance=float(1.0 - match.score),
                )
            )
        # ``distance`` ascending == most similar first (matches Chroma semantics).
        chunks.sort(key=lambda c: c.distance)
        return chunks

    def count(self) -> int:
        index = self._ensure()
        stats_ns = (index.describe_index_stats().namespaces or {}).get(self._namespace) or {}
        reported = int(stats_ns.get("vector_count", 0))
        if reported:
            return reported
        # Serverless index stats lag behind recent upserts; double-check a zero
        # report with a direct probe so fresh data is never mistaken for empty.
        # The probe vector must be non-zero: cosine similarity is undefined for
        # the zero vector and Pinecone returns no matches for it.
        probe_vector = [1.0] + [0.0] * (self._dimension - 1)
        probe = index.query(vector=probe_vector, top_k=1, namespace=self._namespace)
        return len(probe.matches or [])
