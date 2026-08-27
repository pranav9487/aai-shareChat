"""Groq-backed generation chain built with LangChain LCEL.

The system prompt forces grounded answers: the model must answer only from
the retrieved context and reply with the canonical not-found message
(:data:`app.services.rag.pipeline.NOT_FOUND_ANSWER`) otherwise.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from app.config.settings import Settings, get_settings
from app.services.rag.pipeline import NOT_FOUND_ANSWER
from app.vectorstore.base import RetrievedChunk


class GenerationError(RuntimeError):
    """Raised when response generation fails."""


def make_generate(
    llm: Runnable | None = None, settings: Settings | None = None
) -> Callable[[str, Sequence[RetrievedChunk]], str]:
    """Build a ``(question, chunks) -> answer`` callable.

    ``llm`` is injectable so tests can pass any LangChain ``Runnable``
    (e.g. a stub) without network access. By default a ``ChatGroq`` client is
    constructed from settings; that requires ``GROQ_API_KEY`` to be present at
    first use, never at import time.
    """
    resolved = settings or get_settings()
    if llm is None:
        if not (resolved.groq_api_key or "").strip():
            raise GenerationError("GROQ_API_KEY is not set; cannot create the Groq chat model")
        from langchain_groq import ChatGroq  # lazy import: heavy dependency + key-gated

        llm = ChatGroq(model=resolved.groq_model, api_key=resolved.groq_api_key, temperature=0)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an assistant for internal company documents. "
                "Answer ONLY using the context provided. "
                f'If the context does not contain the answer, reply exactly: "{NOT_FOUND_ANSWER}"',
            ),
            ("human", "Context:\n{context}\n\nQuestion: {question}"),
        ]
    )
    chain = prompt | llm | StrOutputParser()

    def generate(question: str, chunks: Sequence[RetrievedChunk]) -> str:
        try:
            return str(chain.invoke({"context": format_context(chunks), "question": question}))
        except Exception as exc:  # noqa: BLE001 - wrapped into a domain error on purpose
            raise GenerationError(f"generation failed: {exc}") from exc

    return generate


def format_context(chunks: Sequence[RetrievedChunk]) -> str:
    """Join retrieved chunks into one labelled context block for the prompt."""
    if not chunks:
        return "(no retrieved documents)"
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        source = chunk.metadata.get("source", "unknown")
        level = chunk.metadata.get("access_level", "unknown")
        parts.append(f"[{i}] ({level}) {source}:\n{chunk.text}")
    return "\n\n".join(parts)
