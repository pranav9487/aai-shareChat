"""Integration test: real Pinecone embeddings/index + real Groq call.

Auto-skipped unless both ``PINECONE_API_KEY`` and ``GROQ_API_KEY`` are set, so
plain CI runs (no keys) stay 100% green and offline. The first run also
downloads the ONNX MiniLM model used by the local embedder (~90 MB) — expected.
The test creates/uses a uniquely-named serverless index and cleans up after
itself by deleting the index.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

_requires_keys = pytest.mark.skipif(
    not (os.environ.get("PINECONE_API_KEY") and os.environ.get("GROQ_API_KEY")),
    reason="PINECONE_API_KEY and GROQ_API_KEY not both set; integration tests skipped",
)


def _index_name() -> str:
    """A unique per-run index so concurrent CI runs never collide."""
    return f"aai-sharechat-test-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def indexed_store():
    from app.vectorstore.pinecone_client import PineconeVectorStore

    index_name = _index_name()
    store = PineconeVectorStore(
        api_key=os.environ["PINECONE_API_KEY"],
        index_name=index_name,
        namespace="integration",
        dimension=384,
    )
    try:
        yield store
    finally:
        # Best-effort cleanup: drop the temporary index so concurrent CI runs
        # never collide and no test data is left behind.
        from pinecone import Pinecone

        try:
            Pinecone(api_key=os.environ["PINECONE_API_KEY"]).delete_index(index_name)
        except Exception:
            pass


@_requires_keys
def test_full_roundtrip_with_real_components(tmp_path: Path, indexed_store) -> None:
    from app.config.settings import Settings
    from app.services.llm.groq_chain import make_generate
    from app.services.rag.ingestion import IngestionService
    from app.services.rag.pipeline import ACCESS_DENIED_ANSWER, RAGPipeline
    from app.services.rag.retriever import Retriever

    from documents.generate_test_documents import write_documents

    docs_dir = tmp_path / "docs"
    write_documents(docs_dir)

    settings = Settings(
        groq_api_key=os.environ["GROQ_API_KEY"],
        groq_model=os.environ.get("GROQ_MODEL", "qwen/qwen3-32b"),
        documents_dir=docs_dir,
    )
    store = indexed_store
    summary = IngestionService(store, settings).ingest_directory(docs_dir)
    assert summary["files"] == 12
    assert store.count() >= 12

    retriever = Retriever(store, top_k=5)
    hits = retriever.retrieve("How many vacation days do full time employees accrue per year?")
    assert hits, "expected retrieval hits after ingestion"
    assert any(
        chunk.metadata["access_level"] == "hr" for chunk in hits
    ), f"expected an hr-tier hit, got levels: {[c.metadata['access_level'] for c in hits]}"

    pipeline = RAGPipeline(retriever=retriever, generate=make_generate(settings=settings))
    result = pipeline.query("How many vacation days do full-time employees accrue per year?")

    assert isinstance(result.answer, str)
    assert result.answer.strip()
    assert result.sources, "grounded answers must cite their sources"

    # Roadmap item 2: an employee-tier filter over hr-only matches must yield
    # the canonical security decline, never content and never empty-sources.
    restricted = pipeline.query(
        "How many vacation days do full-time employees accrue per year?",
        allowed_levels=["general"],
    )
    assert restricted.answer == ACCESS_DENIED_ANSWER
    assert restricted.sources == []


@_requires_keys
def test_idempotent_reingest_real_store(tmp_path: Path, indexed_store) -> None:
    from app.config.settings import Settings
    from app.services.rag.ingestion import IngestionService

    from documents.generate_test_documents import write_documents

    docs_dir = tmp_path / "docs"
    write_documents(docs_dir)
    store = indexed_store
    service = IngestionService(store, settings=Settings(documents_dir=docs_dir))

    first = service.ingest_directory(docs_dir)
    second = service.ingest_directory(docs_dir)
    assert first["files"] == second["files"]
    assert store.count() == first["chunks"] == second["chunks"]
