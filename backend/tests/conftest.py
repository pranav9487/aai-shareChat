"""Shared fixtures: deterministic fake embedder, temp vector stores, stubs.

Unit-test fakes here are fully offline — no ONNX model download, no Groq call,
no Supabase network.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

import pytest
from app.vectorstore.inmemory import InMemoryVectorStore

_DIM = 64


class FakeSupabaseClient:
    """Offline stand-in for the supabase postgrest surface (ADR-0008 tests).

    Records rows per table and supports just the chain the stores use:
    ``from_(t).select(...).eq(...).order(...).execute()`` plus ``upsert`` and
    ``insert``. ``execute()`` returns ``self`` (callers read ``.data``).
    """

    def __init__(self) -> None:
        self.tables: dict[str, list[dict]] = {}
        self._clock = datetime(2026, 1, 1, tzinfo=UTC)

    # -- table handle ------------------------------------------------------
    def from_(self, table: str) -> FakeSupabaseClient:
        self._table = table
        self._filters: list[tuple[str, object]] = []
        self._order_col: str | None = None
        self._order_desc = False
        return self

    def select(self, *_cols: str) -> FakeSupabaseClient:
        return self

    def eq(self, col: str, value: object) -> FakeSupabaseClient:
        self._filters.append((col, value))
        return self

    def order(self, col: str, *, desc: bool = False) -> FakeSupabaseClient:
        self._order_col = col
        self._order_desc = desc
        return self

    # -- writes ------------------------------------------------------------
    def upsert(self, row: dict) -> FakeSupabaseClient:
        rows = self.tables.setdefault(self._table, [])
        key = row.get("session_id") or row.get("user_id")
        for existing in rows:
            if existing.get("session_id") == key or existing.get("user_id") == key:
                existing.update(row)
                break
        else:
            rows.append(self._stamped(dict(row)))
        return self

    def insert(self, row: dict) -> FakeSupabaseClient:
        self.tables.setdefault(self._table, []).append(self._stamped(dict(row)))
        return self

    def _stamped(self, row: dict) -> dict:
        if "created_at" not in row:
            self._clock += timedelta(seconds=1)
            row["created_at"] = self._clock.isoformat()
        return row

    # -- read --------------------------------------------------------------
    def execute(self) -> FakeSupabaseClient:
        rows = [dict(row) for row in self.tables.get(self._table, [])]
        for col, value in self._filters:
            rows = [row for row in rows if row.get(col) == value]
        if self._order_col:
            rows.sort(key=lambda row: row.get(self._order_col) or "", reverse=self._order_desc)
        self.data = rows
        return self


@pytest.fixture
def fake_supabase() -> FakeSupabaseClient:
    return FakeSupabaseClient()


class FakeEmbedder:
    """Deterministic hash-based embedder standing in for the local MiniLM model.

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
def store(fake_embedder: FakeEmbedder) -> InMemoryVectorStore:
    """Fresh offline vector store wired to the fake embedder (no network)."""
    return InMemoryVectorStore(embed_fn=fake_embedder)
