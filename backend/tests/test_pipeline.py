"""Tests for the RAG pipeline facade (retriever and generator are stubbed)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

import pytest
from app.services.rag.pipeline import (
    ACCESS_DENIED_ANSWER,
    NOT_FOUND_ANSWER,
    PipelineError,
    RAGPipeline,
)
from app.vectorstore.base import RetrievedChunk


class StubRetriever:
    """Scripted retriever: records every call, can simulate tier filtering."""

    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self.chunks = chunks
        self.queries: list[str] = []
        self.levels_seen: list[list[str] | None] = []
        # When set, restricted calls (allowed_levels given) return this list
        # instead of ``chunks`` — simulating server-side access filtering.
        self.restricted_result: list[RetrievedChunk] | None = None

    def retrieve(
        self, query: str, allowed_levels: Sequence[str] | None = None
    ) -> list[RetrievedChunk]:
        self.queries.append(query)
        self.levels_seen.append(list(allowed_levels) if allowed_levels is not None else None)
        if allowed_levels is not None and self.restricted_result is not None:
            return self.restricted_result
        return self.chunks


class RecordingGenerator:
    def __init__(self, answer: str | None = "ok", error: Exception | None = None) -> None:
        self.calls: list[tuple[str, int]] = []
        self.answer = answer
        self.error = error

    def __call__(self, question: str, chunks: Sequence[RetrievedChunk]) -> str:
        self.calls.append((question, len(chunks)))
        if self.error is not None:
            raise self.error
        # No isinstance assert here: a deliberately non-str answer must reach
        # the pipeline's own validation so it raises the domain error.
        return cast(str, self.answer)


def make_chunk(
    source: str = "s.md", level: str = "general", distance: float = 0.2
) -> RetrievedChunk:
    return RetrievedChunk(
        text="chunk text",
        metadata={"source": source, "access_level": level},
        distance=distance,
    )


def test_blank_question_raises_value_error() -> None:
    pipeline = RAGPipeline(retriever=StubRetriever([]), generate=RecordingGenerator())
    with pytest.raises(ValueError):
        pipeline.query("")
    with pytest.raises(ValueError):
        pipeline.query("   \n\t")


def test_no_chunks_returns_canonical_not_found_without_calling_llm() -> None:
    generator = RecordingGenerator()
    pipeline = RAGPipeline(retriever=StubRetriever([]), generate=generator)

    result = pipeline.query("what is the vacation policy?")

    assert result.answer == NOT_FOUND_ANSWER
    assert result.sources == []
    assert generator.calls == [], "LLM must not be called when nothing was retrieved"


def test_successful_query_returns_answer_and_sources() -> None:
    chunks = [make_chunk("a.md", "general"), make_chunk("b.md", "hr")]
    generator = RecordingGenerator(answer="Grounded answer.")
    pipeline = RAGPipeline(retriever=StubRetriever(chunks), generate=generator)

    result = pipeline.query("Tell me about leave.")

    assert result.answer == "Grounded answer."
    assert result.sources == [
        {"source": "a.md", "access_level": "general"},
        {"source": "b.md", "access_level": "hr"},
    ]
    assert generator.calls == [("Tell me about leave.", 2)]


def test_question_is_trimmed_before_retrieval() -> None:
    retriever = StubRetriever([])
    pipeline = RAGPipeline(retriever=retriever, generate=RecordingGenerator())
    pipeline.query("  padded question  ")
    assert retriever.queries == ["padded question"]


def test_generator_exception_is_wrapped_in_pipeline_error() -> None:
    generator = RecordingGenerator(error=RuntimeError("groq down"))
    pipeline = RAGPipeline(retriever=StubRetriever([make_chunk()]), generate=generator)
    with pytest.raises(PipelineError, match="generation failed"):
        pipeline.query("anything")


def test_non_string_generator_output_is_wrapped() -> None:
    generator = RecordingGenerator(answer=None)  # type: ignore[arg-type]
    pipeline = RAGPipeline(retriever=StubRetriever([make_chunk()]), generate=generator)
    with pytest.raises(PipelineError, match="empty or non-string"):
        pipeline.query("anything")


def test_allowed_levels_are_forwarded_to_the_retriever() -> None:
    retriever = StubRetriever([make_chunk("a.md", "general")])
    pipeline = RAGPipeline(retriever=retriever, generate=RecordingGenerator(answer="ans"))

    result = pipeline.query("leave policy?", allowed_levels=["general", "hr"])

    assert result.answer == "ans"
    assert retriever.levels_seen == [["general", "hr"]], "caller tiers must drive filtering"


def test_restricted_query_matching_hidden_material_declines() -> None:
    retriever = StubRetriever([make_chunk("secrets.md", "restricted")])
    retriever.restricted_result = []  # tier filter removes everything
    generator = RecordingGenerator()
    pipeline = RAGPipeline(retriever=retriever, generate=generator)

    result = pipeline.query("what are the salary bands?", allowed_levels=["general"])

    assert result.answer == ACCESS_DENIED_ANSWER
    assert result.sources == [], "denied answers must never expose forbidden sources"
    assert generator.calls == [], "the LLM must never see a denied query"


def test_restricted_query_matching_nothing_says_not_found() -> None:
    retriever = StubRetriever([])  # even the unfiltered probe finds nothing
    generator = RecordingGenerator()
    pipeline = RAGPipeline(retriever=retriever, generate=generator)

    result = pipeline.query("gibberish topic?", allowed_levels=["general"])

    assert result.answer == NOT_FOUND_ANSWER
    assert result.sources == []
    assert generator.calls == []


def test_unrestricted_empty_result_skips_the_denial_probe() -> None:
    retriever = StubRetriever([])
    pipeline = RAGPipeline(retriever=retriever, generate=RecordingGenerator())

    result = pipeline.query("anything")

    assert result.answer == NOT_FOUND_ANSWER
    assert len(retriever.queries) == 1, "no existence probe without an active restriction"
