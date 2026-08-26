"""Adversarial tests for the text chunker."""

from __future__ import annotations

import pytest
from app.services.rag.ingestion import chunk_text


def test_empty_and_whitespace_only_return_no_chunks() -> None:
    assert chunk_text("") == []
    assert chunk_text("   \n\t  ") == []


def test_tiny_text_is_a_single_chunk() -> None:
    assert chunk_text("hello") == ["hello"]


def test_surrounding_whitespace_is_stripped_from_single_chunk() -> None:
    assert chunk_text("  hi there  ", chunk_size=100, chunk_overlap=10) == ["hi there"]


def test_large_text_chunks_are_bounded_and_cover_content() -> None:
    paragraph = "Sentence one. Sentence two is a bit longer than the first one. "
    big_text = paragraph * 200
    chunks = chunk_text(big_text, chunk_size=800, chunk_overlap=100)
    assert len(chunks) >= 2
    assert all(len(chunk) <= 800 for chunk in chunks)
    assert chunks[0].startswith("Sentence one.")
    # No content lost: first words of the source start the output, and the tail survives.
    assert big_text.strip().endswith(chunks[-1])


def test_consecutive_chunks_share_words_when_overlap_positive() -> None:
    text = ". ".join(f"word{i}" for i in range(300))
    chunks = chunk_text(text, chunk_size=120, chunk_overlap=30)
    assert len(chunks) >= 2
    for prev_chunk, next_chunk in zip(chunks, chunks[1:], strict=False):
        assert set(prev_chunk.split()) & set(
            next_chunk.split()
        ), f"no shared words between consecutive chunks:\n{prev_chunk!r}\n{next_chunk!r}"


def test_unicode_content_is_preserved() -> None:
    text = "Ünïcödé ✓ 日本語のテキスト。Accents éàü everywhere. " * 40
    chunks = chunk_text(text)
    joined = "".join(chunks)
    assert "日本語のテキスト" in joined
    assert "✓" in joined


def test_no_boundaries_hard_splits_within_limit() -> None:
    text = "a" * 2500
    chunks = chunk_text(text, chunk_size=1000, chunk_overlap=100)
    assert all(len(chunk) <= 1000 for chunk in chunks)
    assert len(chunks) == 3  # windows: 0-1000, 900-1900, 1800-2500


@pytest.mark.parametrize(
    ("size", "overlap"),
    [(0, 0), (-5, 0), (10, -1), (10, 10), (10, 15)],
)
def test_invalid_parameters_raise_value_error(size: int, overlap: int) -> None:
    with pytest.raises(ValueError):
        chunk_text("some text", chunk_size=size, chunk_overlap=overlap)
