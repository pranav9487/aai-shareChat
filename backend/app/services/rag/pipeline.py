"""RAG pipeline facade: retrieve relevant chunks, then generate an answer."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from pydantic import BaseModel, Field

from app.services.rag.retriever import Retriever
from app.vectorstore.base import RetrievedChunk

NOT_FOUND_ANSWER = "The answer was not found in the documents."
ACCESS_DENIED_ANSWER = "Access denied: you do not have permission to view this information."


class QueryResult(BaseModel):
    """Canonical answer payload returned by the pipeline and the API."""

    answer: str
    sources: list[dict] = Field(default_factory=list)


class PipelineError(RuntimeError):
    """Raised when the generation step fails or returns an unusable answer."""


# Contract for a generator callable (see app/services/llm/groq_chain.make_generate).
Generator = Callable[[str, Sequence[RetrievedChunk]], str]


class RAGPipeline:
    """Wires retrieval and generation together behind one method.

    Routes depend only on this class; unit tests can inject fake retrievers
    and generators without touching ChromaDB or Groq.
    """

    def __init__(self, retriever: Retriever, generate: Generator) -> None:
        self._retriever = retriever
        self._generate = generate

    def query(self, question: str, allowed_levels: Sequence[str] | None = None) -> QueryResult:
        """Answer *question* from ingested documents visible at *allowed_levels*.

        Empty questions raise ``ValueError``. ``allowed_levels=None`` means no
        restriction (internal callers/tests only). When permission-filtered
        retrieval comes back empty, one internal unfiltered existence probe
        (its content is discarded) picks between the canonical security
        decline :data:`ACCESS_DENIED_ANSWER` — relevant material exists outside
        the caller's tiers — and :data:`NOT_FOUND_ANSWER`. The LLM is never
        called in either branch, and denied sources are never exposed.
        """
        if not question or not question.strip():
            raise ValueError("question must be a non-empty string")
        cleaned = question.strip()

        chunks = self._retriever.retrieve(cleaned, allowed_levels=allowed_levels)
        if not chunks:
            if allowed_levels is None:
                return QueryResult(answer=NOT_FOUND_ANSWER, sources=[])
            unfiltered = self._retriever.retrieve(cleaned)
            if unfiltered:
                return QueryResult(answer=ACCESS_DENIED_ANSWER, sources=[])
            return QueryResult(answer=NOT_FOUND_ANSWER, sources=[])

        try:
            answer = self._generate(cleaned, chunks)
        except Exception as exc:  # noqa: BLE001 - normalized to a domain error
            raise PipelineError(f"generation failed: {exc}") from exc
        if not isinstance(answer, str) or not answer.strip():
            raise PipelineError("generator returned an empty or non-string answer")

        if answer.strip() == NOT_FOUND_ANSWER and allowed_levels is not None:
            unfiltered = self._retriever.retrieve(cleaned)
            if any(c.metadata.get("access_level") not in allowed_levels for c in unfiltered):
                return QueryResult(answer=ACCESS_DENIED_ANSWER, sources=[])

        sources = [dict(chunk.metadata) for chunk in chunks]
        return QueryResult(answer=answer.strip(), sources=sources)
