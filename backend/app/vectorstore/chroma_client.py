"""Thin wrapper around a persistent ChromaDB collection.

This layer deliberately contains no business logic: it stores chunks with
metadata and answers similarity queries. Embeddings are produced by an
injected callable (``EmbedFn``) so unit tests can run fully offline with a
deterministic fake instead of downloading the real embedding model.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Sequence

import chromadb
from pydantic import BaseModel, Field

EmbedFn = Callable[[Sequence[str]], Sequence[Sequence[float]]]


class RetrievedChunk(BaseModel):
    """A single retrieved chunk plus its metadata and similarity distance."""

    text: str
    metadata: dict = Field(default_factory=dict)
    distance: float


class DefaultEmbedder:
    """Lazily wraps ChromaDB's default embedding function (MiniLM ONNX).

    The underlying model is only instantiated (and downloaded) on first call,
    so merely importing this module never triggers network access.
    """

    def __init__(self) -> None:
        self._fn = None

    def __call__(self, texts: Sequence[str]) -> list[list[float]]:
        if self._fn is None:
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

            self._fn = DefaultEmbeddingFunction()
        return [[float(x) for x in vec] for vec in self._fn(list(texts))]


def _require_equal_lengths(texts: Sequence[str], metadatas: Sequence[dict], ids: Sequence[str]) -> None:
    if not (len(texts) == len(metadatas) == len(ids)):
        raise ValueError(
            f"length mismatch: texts={len(texts)} metadatas={len(metadatas)} ids={len(ids)}"
        )


class ChromaVectorStore:
    """Persistence-backed vector store over a single ChromaDB collection."""

    def __init__(
        self,
        persist_dir: str | Path,
        collection_name: str = "internal_docs",
        embed_fn: EmbedFn | None = None,
    ) -> None:
        self._embed_fn: EmbedFn = embed_fn or DefaultEmbedder()
        client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def delete_source(self, source: str) -> None:
        """Delete every chunk that came from ``source`` (idempotent)."""
        self._collection.delete(where={"source": source})

    def upsert_chunks(self, texts: Sequence[str], metadatas: Sequence[dict], ids: Sequence[str]) -> int:
        """Upsert chunks (with pre-computed metadata) and return how many were written.

        Embeddings are computed via the configured ``embed_fn`` and passed to
        Chroma explicitly, which keeps storage deterministic and mockable.
        """
        _require_equal_lengths(texts, metadatas, ids)
        if len(texts) == 0:
            return 0
        embeddings = self._embed_fn(texts)
        self._collection.upsert(
            ids=list(ids),
            documents=list(texts),
            metadatas=list(metadatas),
            embeddings=[list(vec) for vec in embeddings],
        )
        return len(texts)

    def query(self, query_text: str, top_k: int) -> list[RetrievedChunk]:
        """Return the ``top_k`` most similar chunks, closest first."""
        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")
        result = self._collection.query(
            query_embeddings=[list(vec) for vec in self._embed_fn([query_text])],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            RetrievedChunk(text=doc, metadata=dict(meta), distance=float(dist))
            for doc, meta, dist in zip(documents, metadatas, distances)
        ]

    def count(self) -> int:
        """Total number of stored chunks."""
        return self._collection.count()
