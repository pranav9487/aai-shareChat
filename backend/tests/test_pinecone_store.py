"""Offline unit tests for the Pinecone vector-store adapter.

No network: ``_ensure`` is monkeypatched to return a fake index that records
calls and returns canned matches, so we can assert the adapter's metadata
filter, score→distance mapping, ordering, idempotent delete and lazy-key
behaviour without touching Pinecone.
"""

from __future__ import annotations

from collections.abc import Sequence

import pytest
from app.vectorstore.pinecone_client import PineconeVectorStore


class _Match:
    def __init__(self, id_: str, score: float, metadata: dict) -> None:
        self.id = id_
        self.score = score
        self.metadata = metadata


class FakeIndex:
    def __init__(self) -> None:
        self.upserts: list[tuple] = []
        self.deletes: list[dict] = []
        self.queries: list[dict] = []
        self.matches: list[_Match] = []
        self.namespaces = {"": {"vector_count": 0}}

    def upsert(self, *, vectors, namespace) -> None:
        self.upserts.append((vectors, namespace))

    def delete(self, *, filter, namespace) -> None:
        self.deletes.append((filter, namespace))

    def query(self, **kwargs) -> object:
        self.queries.append(kwargs)

        class Result:
            matches = self.matches

        return Result()

    def describe_index_stats(self) -> object:
        class Stats:
            namespaces = self.namespaces

        return Stats()


class _StubEmbedder:
    """Returns a deterministic 2-dim vector per text (never used for storage)."""

    def __call__(self, texts: Sequence[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


@pytest.fixture
def store() -> tuple[PineconeVectorStore, FakeIndex]:
    store_ = PineconeVectorStore(
        api_key="test-key",
        index_name="idx",
        namespace="ns",
        dimension=2,
        embed_fn=_StubEmbedder(),
    )
    index = FakeIndex()
    store_._ensure = lambda: index  # noqa: SLF001 - test seam (no network)
    return store_, index


def test_empty_key_raises_only_when_used() -> None:
    store_ = PineconeVectorStore(api_key="", embed_fn=_StubEmbedder())
    # Construction itself must be lazy/offline and never raise on a missing key.
    with pytest.raises(ValueError, match="PINECONE_API_KEY"):
        store_.query("anything", top_k=1)


def test_delete_source_tolerates_missing_namespace(store) -> None:
    """Fresh serverless namespaces 404 on filtered deletes (nothing upserted
    yet); the adapter must treat that as 'nothing to delete' — regression for
    the ingest crash: NotFoundError: [404] Namespace not found."""
    from pinecone import NotFoundError

    store_, index = store

    def _raise(*, filter, namespace) -> None:
        raise NotFoundError("[404] Namespace not found")

    index.delete = _raise
    store_.delete_source("a.md")  # must not raise


def test_upsert_carries_text_in_metadata_and_embeds(store) -> None:
    store_, index = store
    n = store_.upsert_chunks(
        ["A chunk", "B chunk"],
        [
            {"source": "a.md", "access_level": "hr", "chunk_index": 0},
            {"source": "a.md", "access_level": "hr", "chunk_index": 1},
        ],
        ["a.md::0", "a.md::1"],
    )
    assert n == 2
    ((vectors, namespace),) = index.upserts
    assert namespace == "ns"
    assert vectors[0][0] == "a.md::0"
    assert vectors[0][2]["text"] == "A chunk"
    assert vectors[0][2]["access_level"] == "hr"
    assert vectors[1][2]["text"] == "B chunk"


def test_mismatched_lengths_rejected(store) -> None:
    store_, _ = store
    with pytest.raises(ValueError, match="length mismatch"):
        store_.upsert_chunks(
            ["only text"],
            [{"source": "x.md", "access_level": "general", "chunk_index": 0}],
            ["x.md::0", "x.md::1"],
        )


def test_query_builds_access_level_in_filter(store) -> None:
    store_, index = store
    store_.query("question", top_k=5, allowed_levels=["general", "hr"])
    (call,) = index.queries
    assert call["filter"] == {"access_level": {"$in": ["general", "hr"]}}
    assert call["top_k"] == 5
    assert call["include_metadata"] is True
    assert call["namespace"] == "ns"


def test_empty_allowed_levels_denies_without_querying(store) -> None:
    store_, index = store
    assert store_.query("q", top_k=3, allowed_levels=[]) == []
    assert index.queries == [], "must not hit the index for an empty allow-list"


def test_score_mapped_to_distance_and_sorted_nearest_first(store) -> None:
    store_, index = store
    # Pinecone returns higher score = more similar; distance must be reversed.
    index.matches = [
        _Match("far", 0.40, {"text": "far text", "access_level": "general", "source": "f.md"}),
        _Match("near", 0.95, {"text": "near text", "access_level": "general", "source": "n.md"}),
    ]
    results = store_.query("q", top_k=2)
    assert [round(r.distance, 2) for r in results] == [0.05, 0.60]
    # Nearest comes first (smallest distance), and reserved text key is popped.
    assert results[0].text == "near text"
    assert results[0].metadata == {"access_level": "general", "source": "n.md"}
    assert results[1].text == "far text"


def test_delete_source_filters_by_source(store) -> None:
    store_, index = store
    store_.delete_source("a.md")
    ((filter_, namespace),) = index.deletes
    assert filter_ == {"source": "a.md"}
    assert namespace == "ns"


def test_count_reads_namespace_vector_count(store) -> None:
    store_, index = store
    index.namespaces = {"": 5.0, "ns": {"vector_count": 7}}
    assert store_.count() == 7


def test_count_zero_when_namespace_absent(store) -> None:
    store_, index = store
    index.namespaces = {}
    assert store_.count() == 0


def test_count_probes_when_stats_lag_behind_upserts(store) -> None:
    """Serverless describe_index_stats can report 0 right after upserts while
    queries already return matches. Regression for the live bug where the
    retriever's empty-guard short-circuited every query on a fresh index:
    a zero stats report must be double-checked with a direct probe."""
    store_, index = store

    class _ProbeResult:
        matches = [object()]  # one existing vector the stats missed

    def _probe_query(**kwargs) -> object:
        assert kwargs["top_k"] == 1
        assert kwargs["namespace"] == "ns"
        probe_vector = kwargs["vector"]
        assert any(
            v != 0.0 for v in probe_vector
        ), "zero probe vectors are unusable under cosine similarity"
        return _ProbeResult()

    index.namespaces = {}  # stats say empty...
    index.query = _probe_query  # ...but the data is there
    assert store_.count() == 1
