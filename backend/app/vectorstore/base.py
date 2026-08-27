"""Vendor-agnostic vector-store contract shared by every consumer.

The rest of the application (retriever, ingestion, pipeline, LLM chain, FastAPI
composition root) depends only on the ``VectorStore`` protocol and the
:class:`RetrievedChunk` / :data:`EmbedFn` types defined here — never on a
concrete vendor class (ChromaDB, Pinecone, …). That keeps stores swappable and
lets unit tests inject an offline fake while an online implementation is
configured at the composition root.

Two production implementations exist:
- :class:`~app.vectorstore.pinecone_client.PineconeVectorStore` (hosted)
- tests use :class:`~app.vectorstore.inmemory.InMemoryVectorStore`.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field

#: Produces one embedding vector per input text.
EmbedFn = Callable[[Sequence[str]], Sequence[Sequence[float]]]


class RetrievedChunk(BaseModel):
    """A single retrieved chunk plus its metadata and similarity distance.

    ``distance`` is defined so that *smaller means more similar* (a cosine
    distance), matching ChromaDB semantics; hosted stores that return a
    cosine *score* (larger = closer) must map it to this invariant in their
    implementation.
    """

    text: str
    metadata: dict = Field(default_factory=dict)
    distance: float


@runtime_checkable
class VectorStore(Protocol):
    """Minimal persistence/retrieval surface used by the RAG pipeline.

    Consumers rely on exactly these four operations; anything extra (index
    management, namespace plumbing) is an implementation detail behind this
    contract.
    """

    def delete_source(self, source: str) -> None:
        """Delete every chunk that came from *source* (idempotent)."""
        ...

    def upsert_chunks(
        self, texts: Sequence[str], metadatas: Sequence[dict], ids: Sequence[str]
    ) -> int:
        """Store/overwrite *texts* (embedding via the injected ``EmbedFn``).

        Returns how many chunks were written. Re-inserting an existing id
        replaces it, so ingestion stays idempotent.
        """
        ...

    def query(
        self, query_text: str, top_k: int, allowed_levels: Sequence[str] | None = None
    ) -> list[RetrievedChunk]:
        """Return the ``top_k`` most similar chunks, closest (smallest distance) first.

        When *allowed_levels* is given, only chunks whose stored
        ``access_level`` metadata appears in that list are eligible — the
        permission filter must run server-side so forbidden chunks never leave
        the store. An empty *allowed_levels* list denies everything.
        """
        ...

    def count(self) -> int:
        """Total number of stored chunks."""
        ...


class DefaultEmbedder:
    """Local MiniLM-L6-v2 embeddings (384-dim) via the FastEmbed ONNX runtime.

    Wrapped in :class:`EmbedFn` so the rest of the app never imports a specific
    embedding library. The underlying model is only instantiated (and its ONNX
    weights downloaded) on first call, so importing this module never triggers
    network access. The Pinecone index must be created with the matching
    dimension (384) and cosine metric.
    """

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self) -> None:
        self._model = None

    def __call__(self, texts: Sequence[str]) -> list[list[float]]:
        if self._model is None:
            from fastembed import TextEmbedding  # lazily download weights on first use

            self._model = TextEmbedding(model_name=self.MODEL_NAME)
        return [list(float(x) for x in vec) for vec in self._model.embed(list(texts))]


def _require_equal_lengths(
    texts: Sequence[str], metadatas: Sequence[dict], ids: Sequence[str]
) -> None:
    if not (len(texts) == len(metadatas) == len(ids)):
        raise ValueError(
            f"length mismatch: texts={len(texts)} metadatas={len(metadatas)} ids={len(ids)}"
        )
