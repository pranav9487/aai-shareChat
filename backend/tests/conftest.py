"""Shared fixtures: deterministic fake embedder, temp vector stores, stubs.

Unit-test fakes here are fully offline — no ONNX model download, no Groq call.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from pathlib import Path

import pytest
from app.vectorstore.chroma_client import ChromaVectorStore

_DIM = 64


class FakeEmbedder:
    """Deterministic hash-based embedder standing in for ChromaDB's MiniLM.

    Tokens map to signed unit contributions by SHA-256, so texts sharing
    vocabulary end up close in cosine distance — enough for realistic
    nearest-neighbour ordering in tests while staying instant.
    """

    def __call__(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vec = [0.0] * _DIM
            for token in text.lower().split():
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                idx = int.from_bytes(digest[:4], "big") % _DIM
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                vec[idx] += sign
            norm = sum(v * v for v in vec) ** 0.5 or 1.0
            vectors.append([v / norm for v in vec])
        return vectors


@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def store(tmp_path: Path, fake_embedder: FakeEmbedder) -> ChromaVectorStore:
    """Fresh persistent-in-tmp vector store wired to the fake embedder."""
    return ChromaVectorStore(
        persist_dir=tmp_path / "chroma",
        collection_name="test_docs",
        embed_fn=fake_embedder,
    )
