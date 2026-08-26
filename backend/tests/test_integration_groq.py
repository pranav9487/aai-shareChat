"""Integration test: real ChromaDB embeddings + real Groq call.

Auto-skipped unless ``GROQ_API_KEY`` is set, so plain CI runs (no key) stay
100% green and offline. The first run also downloads the ONNX MiniLM model
used by ChromaDB's default embedder (~80 MB) — that is expected.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

_requires_key = pytest.mark.skipif(
    not os.environ.get("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set; integration tests are skipped",
)


@_requires_key
def test_full_roundtrip_with_real_components(tmp_path: Path) -> None:
    from app.config.settings import Settings
    from app.services.llm.groq_chain import make_generate
    from app.services.rag.ingestion import IngestionService
    from app.services.rag.pipeline import ACCESS_DENIED_ANSWER, RAGPipeline
    from app.services.rag.retriever import Retriever
    from app.vectorstore.chroma_client import ChromaVectorStore

    from documents.generate_test_documents import write_documents

    docs_dir = tmp_path / "docs"
    db_dir = tmp_path / "db"
    write_documents(docs_dir)

    settings = Settings(
        groq_api_key=os.environ["GROQ_API_KEY"],
        groq_model=os.environ.get("GROQ_MODEL", "qwen/qwen3-32b"),
        chroma_persist_dir=db_dir,
        documents_dir=docs_dir,
    )

    store = ChromaVectorStore(persist_dir=db_dir, collection_name=settings.collection_name)
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


@_requires_key
def test_idempotent_reingest_real_store(tmp_path: Path) -> None:
    from app.config.settings import Settings
    from app.services.rag.ingestion import IngestionService
    from app.vectorstore.chroma_client import ChromaVectorStore

    from documents.generate_test_documents import write_documents

    docs_dir = tmp_path / "docs"
    write_documents(docs_dir)
    settings = Settings(chroma_persist_dir=tmp_path / "db", documents_dir=docs_dir)
    store = ChromaVectorStore(persist_dir=settings.chroma_persist_dir)
    service = IngestionService(store, settings)

    first = service.ingest_directory(docs_dir)
    second = service.ingest_directory(docs_dir)
    assert first["files"] == second["files"]
    assert store.count() == first["chunks"] == second["chunks"]
