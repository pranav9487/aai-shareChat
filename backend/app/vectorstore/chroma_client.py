"""Deprecated compatibility shim (pre-Pinecone migration).

This module previously hosted the ChromaDB-backed ``ChromaVectorStore`` and the
shared embedding/retrieval types. Those types now live in:

- ``app.vectorstore.base`` — ``EmbedFn``, ``RetrievedChunk``, ``VectorStore``,
  ``DefaultEmbedder``
- ``app.vectorstore.pinecone_client`` — ``PineconeVectorStore``
- ``app.vectorstore.inmemory`` — ``InMemoryVectorStore`` (offline tests)

This re-export module is kept only so any external/older import path still
resolves; new code must import from the modules above. It intentionally no
longer imports ``chromadb`` (the project migrated to Pinecone).
"""

from __future__ import annotations

from app.vectorstore.base import (  # noqa: F401 - compatibility re-exports
    DefaultEmbedder,
    EmbedFn,
    RetrievedChunk,
    VectorStore,
)
from app.vectorstore.inmemory import InMemoryVectorStore  # noqa: F401
from app.vectorstore.pinecone_client import PineconeVectorStore  # noqa: F401

