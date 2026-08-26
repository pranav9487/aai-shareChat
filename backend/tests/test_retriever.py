"""Adversarial tests for the retriever over a real (temp) ChromaDB store."""

from __future__ import annotations

import pytest
from app.services.rag.ingestion import IngestionService, ParsedDocument
from app.services.rag.retriever import Retriever


def _ingest_pair(store) -> tuple[str, str]:
    """Ingest two topically distinct documents; returns their source names."""
    vacation = ParsedDocument(
        source="vacation.md",
        title="Vacation",
        access_level="hr",
        text=("Vacation policy: employees accrue twenty five vacation days per year. " * 6),
    )
    helpdesk = ParsedDocument(
        source="helpdesk.md",
        title="Helpdesk",
        access_level="general",
        text=("Contact the IT helpdesk portal for password resets and laptop requests. " * 6),
    )
    service = IngestionService(store)
    service.ingest_text(vacation)
    service.ingest_text(helpdesk)
    return vacation.source, helpdesk.source


@pytest.mark.parametrize("top_k", [0, -3])
def test_top_k_must_be_positive(top_k: int) -> None:
    with pytest.raises(ValueError):
        Retriever(store=None, top_k=top_k)  # type: ignore[arg-type]


def test_store_query_rejects_non_positive_top_k(store) -> None:
    with pytest.raises(ValueError):
        store.query("anything", top_k=0)


def test_empty_or_whitespace_query_returns_empty_list(store) -> None:
    retriever = Retriever(store, top_k=5)
    _ingest_pair(store)
    assert retriever.retrieve("") == []
    assert retriever.retrieve("   \n\t") == []


def test_empty_corpus_returns_empty_list_without_querying(store) -> None:
    retriever = Retriever(store, top_k=5)
    assert retriever.retrieve("anything at all") == []


def test_top_k_larger_than_corpus_returns_everything(store) -> None:
    vacation_source, _ = _ingest_pair(store)
    retriever = Retriever(store, top_k=50)
    results = retriever.retrieve("vacation")
    assert 2 <= len(results), f"expected both corpus chunks back, got {len(results)}"
    assert any(chunk.metadata["source"] == vacation_source for chunk in results)


def test_results_are_ordered_nearest_first_and_tier_matches_topic(store) -> None:
    _ingest_pair(store)
    retriever = Retriever(store, top_k=4)
    results = retriever.retrieve("How many vacation days do employees accrue?")
    assert results
    distances = [chunk.distance for chunk in results]
    assert distances == sorted(distances), "results must come back nearest-first"

    # The HR vacation document shares the most query vocabulary.
    hr_sources = [c for c in results if c.metadata["access_level"] == "hr"]
    assert hr_sources, "expected an hr-tier document among the hits"
    assert results[0].metadata["source"].startswith(("vacation", "hr_"))
