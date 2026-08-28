"""Deterministic (offline, rule-based) follow-up resolution (ADR-0009).

Roadmap Now §4: detect deictic/elliptical follow-ups in a shared session and
rewrite them into standalone questions so the removed subject is restored for
retrieval. A ``FollowUpResolver`` protocol keeps this swappable for an
LLM-based condense step later. The resolver is pure — it never touches the
vector store, the LLM, or another user's content; the caller (the route)
supplies only the requester's own history.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Protocol

from app.services.followup.models import ResolvedQuestion
from app.services.session.models import SessionMessage

#: Deictic pronouns / connectors that strongly imply a follow-up.
_DEICTIC = frozenset(
    {
        "it",
        "this",
        "that",
        "these",
        "those",
        "they",
        "them",
        "their",
        "there",
    }
)

#: Elliptical openers that start a follow-up ("and", "also", "what about"...).
_OPENERS = (
    "and",
    "also",
    "then",
    "but",
    "what about",
    "how about",
    "too",
    "or",
)

#: Questions that are "short" (likely a follow-up) are those under this many words.
_MAX_FOLLOW_UP_WORDS = 8


class FollowUpResolver(Protocol):
    """Resolve an incoming question against prior history in a shared session."""

    def resolve(
        self, question: str, history: Sequence[SessionMessage], user_id: str | None = None
    ) -> ResolvedQuestion:
        """Return the question to use for retrieval, marking follow-ups."""
        ...


class HeuristicFollowUpResolver:
    """Rule-based follow-up detector; deterministic and fully offline.

    A question is treated as a follow-up when it is short (<= 8 words) and
    either contains a deictic pronoun/connector or begins with an elliptical
    opener. The rewrite inlines the last available prior question. With no
    history, or an explicit full question, the input passes through unchanged.
    """

    _MAX_FOLLOW_UP_WORDS = _MAX_FOLLOW_UP_WORDS

    def __init__(self, max_follow_up_words: int = _MAX_FOLLOW_UP_WORDS) -> None:
        if max_follow_up_words <= 0:
            raise ValueError("max_follow_up_words must be a positive integer")
        self._max_words = max_follow_up_words

    @staticmethod
    def _is_follow_up_internal(question: str, max_words: int) -> bool:
        lowered = question.lower()
        words = lowered.split()
        if len(words) > max_words:
            return False
        if lowered.startswith(_OPENERS):
            return True
        return bool(re.search(r"\b(" + "|".join(_DEICTIC) + r")\b", lowered))

    @staticmethod
    def _last_own_question(history: Sequence[SessionMessage], user_id: str | None) -> str | None:
        """Return the most recent question authored by *user_id* (or any, if None)."""
        for message in reversed(history):
            if user_id is not None and message.sender_user_id != user_id:
                continue
            if message.question and message.question.strip():
                return message.question.strip()
        return None

    def resolve(
        self, question: str, history: Sequence[SessionMessage], user_id: str | None = None
    ) -> ResolvedQuestion:
        """Resolve *question* against *history*.

        When *user_id* is given, only that user's own prior questions are used
        as the rewrite source — another participant's question is never inlined
        (defense-in-depth on top of the route filtering by sender).
        """
        cleaned = question.strip()
        if not cleaned:
            raise ValueError("question must be a non-empty string")

        if not self._is_follow_up_internal(cleaned, self._max_words):
            return ResolvedQuestion(question=cleaned, follow_up=False, rewritten=cleaned)

        prior = self._last_own_question(history, user_id)
        if not prior:
            return ResolvedQuestion(question=cleaned, follow_up=False, rewritten=cleaned)

        rewritten = f"{prior} {cleaned}"
        return ResolvedQuestion(question=cleaned, follow_up=True, rewritten=rewritten)


#: Singleton convenience (matches deps `@lru_cache` pattern).
_HEURISTIC = HeuristicFollowUpResolver()


def get_heuristic_resolver() -> HeuristicFollowUpResolver:
    """Return the shared heuristic resolver instance."""
    return _HEURISTIC
