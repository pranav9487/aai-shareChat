"""Unit tests for the LLM-backed follow-up resolver (P16).

All tests are fully offline: a stub rewrite function replaces the real Groq
call, so network access is never needed. The tests verify:

- Standalone questions pass through without an LLM call.
- Detected follow-ups are rewritten by the LLM into standalone form.
- Only the requester's own messages are sent to the LLM.
- LLM failures fall back gracefully to heuristic concatenation.
- The resolver never uses another user's messages for rewriting.
"""

from __future__ import annotations

import pytest
from app.services.access_control.models import Role
from app.services.followup.llm_resolver import LLMFollowUpResolver
from app.services.followup.resolver import HeuristicFollowUpResolver
from app.services.session.models import SessionMessage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class StubRewriteChain:
    """Offline rewrite-chain stub that mimics a LangChain Runnable's .invoke().

    Returns a pre-configured response and records all calls so tests can
    assert what was sent.
    """

    def __init__(self, response: str = "How many paid leave days can be carried forward?"):
        self.response = response
        self.calls: list[dict] = []
        self.should_fail = False

    def invoke(self, input: dict) -> str:
        if self.should_fail:
            raise RuntimeError("LLM unavailable")
        self.calls.append(input)
        return self.response


def _msg(user_id: str, question: str, answer: str = "irrelevant") -> SessionMessage:
    return SessionMessage.build(
        sender_user_id=user_id,
        sender_role=Role.EMPLOYEE,
        question=question,
        answer=answer,
    )


HISTORY = [_msg("alice", "How many paid leave days do employees receive?", "24 days.")]


# ---------------------------------------------------------------------------
# Tests: Follow-up detection passthrough
# ---------------------------------------------------------------------------


def test_new_question_not_followup() -> None:
    """A standalone question passes through with no LLM call."""
    stub = StubRewriteChain()
    resolver = LLMFollowUpResolver(rewrite_fn=stub)
    result = resolver.resolve(
        "What is the company's remote work policy?", HISTORY, user_id="alice"
    )
    assert result.follow_up is False
    assert result.rewritten == "What is the company's remote work policy?"
    assert stub.calls == [], "LLM should NOT be called for standalone questions"


def test_long_question_not_followup() -> None:
    """A question exceeding the word threshold is not treated as follow-up."""
    stub = StubRewriteChain()
    resolver = LLMFollowUpResolver(rewrite_fn=stub)
    long_q = "Please explain exactly how the vacation accrual rules work on a calendar basis."
    result = resolver.resolve(long_q, HISTORY, user_id="alice")
    assert result.follow_up is False
    assert result.rewritten == long_q
    assert stub.calls == []


# ---------------------------------------------------------------------------
# Tests: Follow-up detected and rewritten
# ---------------------------------------------------------------------------


def test_followup_detected_and_rewritten() -> None:
    """A deictic follow-up is detected and rewritten by the LLM."""
    stub = StubRewriteChain(response="How many paid leave days can be carried forward?")
    resolver = LLMFollowUpResolver(rewrite_fn=stub)
    # Uses "that" (a deictic pronoun) to trigger the heuristic.
    result = resolver.resolve("can I carry that forward?", HISTORY, user_id="alice")
    assert result.follow_up is True
    assert result.rewritten == "How many paid leave days can be carried forward?"
    assert result.question == "can I carry that forward?"
    assert len(stub.calls) == 1, "LLM should be called exactly once for a follow-up"


def test_followup_with_opener_rewritten() -> None:
    """An elliptical opener ('what about') triggers LLM rewriting."""
    stub = StubRewriteChain(response="What about part-time employee paid leave allocation?")
    resolver = LLMFollowUpResolver(rewrite_fn=stub)
    result = resolver.resolve("what about part-time?", HISTORY, user_id="alice")
    assert result.follow_up is True
    assert "part-time" in result.rewritten


# ---------------------------------------------------------------------------
# Tests: Limited history / cross-user isolation
# ---------------------------------------------------------------------------


def test_followup_only_sends_own_history_to_llm() -> None:
    """Only the requester's own messages are sent to the LLM for rewriting."""
    mixed_history = [
        _msg("alice", "First question", "First answer"),
        _msg("bob", "Bob's secret question", "Bob's secret answer"),
        _msg("alice", "Second question", "Second answer"),
    ]
    stub = StubRewriteChain()
    resolver = LLMFollowUpResolver(rewrite_fn=stub)
    resolver.resolve("what about that?", mixed_history, user_id="alice")
    assert len(stub.calls) == 1
    # The prompt should NOT contain Bob's question (defense-in-depth)
    prompt_history = stub.calls[0].get("history", "")
    assert "Bob's secret question" not in prompt_history
    assert "Bob's secret answer" not in prompt_history
    # But Alice's messages should be there
    assert "First question" in prompt_history
    assert "Second question" in prompt_history


# ---------------------------------------------------------------------------
# Tests: Graceful fallback
# ---------------------------------------------------------------------------


def test_llm_failure_falls_back_to_concatenation() -> None:
    """When the LLM fails, the resolver degrades to heuristic concatenation."""
    stub = StubRewriteChain()
    stub.should_fail = True
    resolver = LLMFollowUpResolver(rewrite_fn=stub)
    result = resolver.resolve("what about part-time?", HISTORY, user_id="alice")
    assert result.follow_up is True
    # Falls back to the heuristic's naive concatenation
    assert result.rewritten == "How many paid leave days do employees receive? what about part-time?"


def test_llm_returns_empty_falls_back() -> None:
    """When the LLM returns an empty string, fall back to concatenation."""
    stub = StubRewriteChain(response="")
    resolver = LLMFollowUpResolver(rewrite_fn=stub)
    result = resolver.resolve("what about part-time?", HISTORY, user_id="alice")
    assert result.follow_up is True
    # Empty LLM response → falls back to heuristic
    assert "what about part-time?" in result.rewritten


# ---------------------------------------------------------------------------
# Tests: Cross-user safety
# ---------------------------------------------------------------------------


def test_resolver_never_uses_another_users_question() -> None:
    """When the only history belongs to another user, the question passes through."""
    foreign_history = [
        _msg("bob", "What is the executive compensation?", "Confidential info"),
    ]
    stub = StubRewriteChain()
    resolver = LLMFollowUpResolver(rewrite_fn=stub)
    result = resolver.resolve("what about part-time?", foreign_history, user_id="alice")
    assert result.follow_up is False  # No own prior → not a follow-up
    assert "executive compensation" not in result.rewritten
    assert stub.calls == [], "LLM should not be called when no own history exists"


def test_no_history_passes_through() -> None:
    """With empty history, even a deictic question passes through unchanged."""
    stub = StubRewriteChain()
    resolver = LLMFollowUpResolver(rewrite_fn=stub)
    result = resolver.resolve("what about part-time?", [], user_id="alice")
    assert result.follow_up is False
    assert result.rewritten == "what about part-time?"
    assert stub.calls == []


# ---------------------------------------------------------------------------
# Tests: Input validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", ["", "   ", "\t\n"])
def test_blank_question_raises(bad: str) -> None:
    stub = StubRewriteChain()
    resolver = LLMFollowUpResolver(rewrite_fn=stub)
    with pytest.raises(ValueError, match="non-empty"):
        resolver.resolve(bad, HISTORY, user_id="alice")


# ---------------------------------------------------------------------------
# Tests: Think-block stripping
# ---------------------------------------------------------------------------


def test_think_block_stripped_from_rewrite() -> None:
    """Reasoning model <think> blocks are stripped from the rewritten question."""
    stub = StubRewriteChain(
        response="<think>Let me think about this...</think>How many paid leave days can be carried forward?"
    )
    resolver = LLMFollowUpResolver(rewrite_fn=stub)
    # Uses "that" (a deictic pronoun) to trigger the heuristic.
    result = resolver.resolve("can I carry that forward?", HISTORY, user_id="alice")
    assert result.follow_up is True
    assert "<think>" not in result.rewritten
    assert result.rewritten == "How many paid leave days can be carried forward?"
