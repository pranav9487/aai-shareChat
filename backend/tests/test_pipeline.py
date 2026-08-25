"""Tests for the RAG pipeline facade (retriever and generator are stubbed)."""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from app.services.rag.pipeline import NOT_FOUND_ANSWER, PipelineError, RAGPipeline
from app.vectorstore.chroma_client import RetrievedChunk


class StubRetriever:
    """Returns a fixed chunk list; records the queries it received."""

    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self.chunks = chunks
        self.queries: list[str] = []

    def retrieve(self, query: str) -> list[RetrievedChunk]:
        self.queries.append(query)
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
        assert isinstance(self.answer, str)  # narrows type for mypy/ruff
        return self.answer


def make_chunk(source: str = "s.md", level: str = "general") -> RetrievedChunk:
    return RetrievedChunk(text="chunk text", metadata={"source": source, "access_level": level})


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
