"""Unit tests for the Groq generation chain using an injected stub LLM."""

from __future__ import annotations

import pytest
from app.config.settings import Settings
from app.services.llm.groq_chain import GenerationError, format_context, make_generate
from app.vectorstore.base import RetrievedChunk
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda


class EchoLLM(RunnableLambda):
    """Stub LLM echoing the fully rendered prompt back as the answer."""

    def __init__(self) -> None:
        super().__init__(func=lambda value: AIMessage(content=f"ECHO::{value.to_string()}"))


class ExplodingLLM(RunnableLambda):
    def __init__(self) -> None:
        super().__init__(func=lambda value: (_ for _ in ()).throw(RuntimeError("api down")))


class ThinkingLLM(RunnableLambda):
    """Mimics qwen3-style reasoning models that prefix a <think> block."""

    def __init__(self) -> None:
        super().__init__(
            func=lambda value: AIMessage(
                content="<think>\ninternal reasoning must never leak\n</think>\nFinal answer."
            )
        )


CHUNKS = [
    RetrievedChunk(
        text="Employees accrue 25 vacation days.",
        metadata={"source": "hr_vacation_policy.md", "access_level": "hr"},
        distance=0.12,
    ),
    RetrievedChunk(
        text="Helpdesk handles password resets.",
        metadata={"source": "general_it_helpdesk.md", "access_level": "general"},
        distance=0.34,
    ),
]


def test_prompt_contains_labelled_context_and_question() -> None:
    generate = make_generate(llm=EchoLLM(), settings=Settings(groq_api_key="", groq_model="m"))
    answer = generate("How many vacation days?", CHUNKS)

    assert answer.startswith("ECHO::")
    assert "[1] (hr) hr_vacation_policy.md" in answer
    assert "[2] (general) general_it_helpdesk.md" in answer
    assert "Question: How many vacation days?" in answer


def test_empty_chunk_list_produces_no_documents_sentinel() -> None:
    generate = make_generate(llm=EchoLLM(), settings=Settings(groq_api_key="", groq_model="m"))
    answer = generate("Anything?", [])
    assert "(no retrieved documents)" in answer


def test_format_context_joins_chunks_with_metadata_labels() -> None:
    context = format_context(CHUNKS)
    assert context.count("[") == 2
    assert "accrue 25 vacation days" in context


def test_missing_api_key_without_injected_llm_raises_generation_error() -> None:
    with pytest.raises(GenerationError, match="GROQ_API_KEY"):
        make_generate(settings=Settings(groq_api_key="", groq_model="m"))


def test_llm_failure_is_wrapped_in_generation_error() -> None:
    generate = make_generate(llm=ExplodingLLM(), settings=Settings(groq_api_key="", groq_model="m"))
    with pytest.raises(GenerationError, match="generation failed"):
        generate("question", CHUNKS)


def test_reasoning_model_think_block_is_stripped_from_answers() -> None:
    generate = make_generate(llm=ThinkingLLM(), settings=Settings(groq_api_key="", groq_model="m"))
    answer = generate("question", CHUNKS)
    assert answer == "Final answer."
    assert "<think>" not in answer, "raw chain-of-thought must never reach users"
