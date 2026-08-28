"""Adversarial unit tests for safe follow-up handling (roadmap Now §4).

Fully offline: the resolver is pure logic with no vector store, LLM, or
session persistence. Floating masses of deictic/elliptical follow-ups must be
detected and rewritten only from the (caller-supplied) requester history.
"""

from __future__ import annotations

import pytest
from app.services.access_control import Role
from app.services.followup import HeuristicFollowUpResolver
from app.services.session import SessionMessage


def _msg(user_id: str, question: str) -> SessionMessage:
    return SessionMessage.build(
        sender_user_id=user_id,
        sender_role=Role.EMPLOYEE,
        question=question,
        answer="irrelevant",
    )


HISTORY = [_msg("alice", "How many vacation days do employees get?")]
RESOLVER = HeuristicFollowUpResolver()


# --- detection ---


def test_short_deictic_follow_up_is_rewritten() -> None:
    result = RESOLVER.resolve("what about part-time?", HISTORY)
    assert result.follow_up is True
    assert result.rewritten == ("How many vacation days do employees get? what about part-time?")
    assert result.question == "what about part-time?"


def test_elliptical_and_opener_is_rewritten() -> None:
    result = RESOLVER.resolve("and their leave?", HISTORY)
    assert result.follow_up is True
    assert result.question == "and their leave?"
    assert HISTORY[0].question in result.rewritten


def test_pronoun_this_is_detected() -> None:
    result = RESOLVER.resolve("does this apply to contractors?", HISTORY)
    assert result.follow_up is True


def test_standalone_full_question_passes_through_unmodified() -> None:
    question = "How many sick days do contractors get?"
    result = RESOLVER.resolve(question, HISTORY)
    assert result.follow_up is False
    assert result.rewritten == question


def test_long_question_not_treated_as_follow_up() -> None:
    # More than the default 8-word threshold: a self-contained question.
    long_q = "Please explain exactly how the vacation accrual rules work on a calendar basis."
    result = RESOLVER.resolve(long_q, HISTORY)
    assert result.follow_up is False
    assert result.rewritten == long_q


# --- history handling ---


def test_no_history_means_pass_through_even_for_short_question() -> None:
    result = RESOLVER.resolve("what about part-time?", [])
    assert result.follow_up is False
    assert result.rewritten == "what about part-time?"


def test_rewrite_uses_only_the_last_own_question() -> None:
    history = [
        _msg("alice", "first question"),
        _msg("bob", "someone else's question"),
        _msg("alice", "second question"),
    ]
    result = RESOLVER.resolve("and their leave?", history)
    assert "second question" in result.rewritten
    assert "someone else's question" not in result.rewritten


def test_rewrite_never_uses_another_senders_question() -> None:
    """The resolver itself must not inline another sender's question when told
    who the requester is — defense-in-depth beyond the route's own filtering."""
    history = [
        _msg("bob", "foreign secret question"),
        _msg("bob", "another foreign question"),
    ]
    result = RESOLVER.resolve("what about part-time?", history, user_id="alice")
    assert result.follow_up is False  # no *own* prior question -> no rewrite
    assert "foreign secret question" not in result.rewritten


# --- input validation ---


@pytest.mark.parametrize("bad", ["", "   ", "\t\n"])
def test_blank_question_raises(bad: str) -> None:
    with pytest.raises(ValueError, match="non-empty"):
        RESOLVER.resolve(bad, HISTORY)


def test_constructor_rejects_non_positive_threshold() -> None:
    with pytest.raises(ValueError, match="positive"):
        HeuristicFollowUpResolver(max_follow_up_words=0)
