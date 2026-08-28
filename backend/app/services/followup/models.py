"""Follow-up handling domain types (roadmap Now §4)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResolvedQuestion:
    """The question to drive retrieval, plus whether it was rewritten.

    ``follow_up`` is True only when the incoming question was rewritten from
    a prior question in the same session; ``rewritten`` is the full standalone
    question used for retrieval (identical to ``question`` for pass-throughs).
    """

    question: str
    follow_up: bool
    rewritten: str
