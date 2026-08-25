"""RAG pipeline facade: retrieve relevant chunks, then generate an answer."""

from __future__ import annotations

from typing import Callable, Sequence

from pydantic import BaseModel, Field

from app.services.rag.retriever import Retriever
from app.vectorstore.chroma_client import RetrievedChunk

NOT_FOUND_ANSWER = "The answer was not found in the documents."


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

    def query(self, question: str) -> QueryResult:
        """Answer *question* from ingested documents.

        Empty questions raise ``ValueError``. When nothing relevant is stored,
        the canonical :data:`NOT_FOUND_ANSWER` is returned without calling the
        LLM, so unanswerable queries stay cheap and deterministic.
        """
        if not question or not question.strip():
            raise ValueError("question must be a non-empty string")
        cleaned = question.strip()

        chunks = self._retriever.retrieve(cleaned)
        # TODO(item-2): per-user access filtering happens inside the Retriever;
        # this facade must stay role-agnostic.
        if not chunks:
            return QueryResult(answer=NOT_FOUND_ANSWER, sources=[])

        try:
            answer = self._generate(cleaned, chunks)
        except Exception as exc:  # noqa: BLE001 - normalized to a domain error
            raise PipelineError(f"generation failed: {exc}") from exc
        if not isinstance(answer, str) or not answer.strip():
            raise PipelineError("generator returned an empty or non-string answer")

        return QueryResult(answer=answer.strip(), sources=[dict(chunk.metadata) for chunk in chunks])
