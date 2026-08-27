"""Session domain types for shared conversations.

A :class:`Session` groups the messages of everyone who participates in a shared
chat. Each message records *who* asked and the access role at the time of the
question, so read-time visibility filtering (roadmap §3) can decide what a
different participant is allowed to see without re-retrieving anything.

This layer is deliberately persistence-agnostic (ADR-0006): an
:class:`.InMemorySessionStore` implements the :class:`.SessionStore` protocol
today, and a future Supabase-backed store implements the same protocol so
call sites do not change.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Final

from app.services.access_control.models import Role

#: Canonical, non-leaky replacement for a message whose content the viewer is
#: not permitted to read (mirrors how ACCESS_DENIED_ANSWER avoids exposing
#: forbidden content instead of showing "not found").
HIDDEN_MESSAGE: Final[
    str
] = "This message is not visible under your access permissions."


@dataclass(frozen=True)
class SessionMessage:
    """A single logged exchange inside a shared session.

    ``access_levels`` is the set of document tiers the author's answer actually
    drew from (derived from the chunk metadata in ``sources``). A viewer may
    read the message only if every one of those tiers is within the viewer's
    own permitted tiers (or the viewer authored it). Empty access_levels (a
    not-found or a security-decline) carries no restricted content and is safe
    for everyone.
    """

    message_id: str
    sender_user_id: str
    sender_role: Role
    question: str
    answer: str
    sources: tuple[dict, ...] = ()
    access_levels: frozenset[str] = frozenset()

    @classmethod
    def build(
        cls,
        *,
        sender_user_id: str,
        sender_role: Role,
        question: str,
        answer: str,
        sources: tuple[dict, ...] = (),
    ) -> "SessionMessage":
        """Construct a message, deriving ``access_levels`` from *sources*."""
        levels = frozenset(
            str(source.get("access_level"))
            for source in sources
            if source.get("access_level")
        )
        return cls(
            message_id=uuid.uuid4().hex,
            sender_user_id=sender_user_id,
            sender_role=sender_role,
            question=question,
            answer=answer,
            sources=sources,
            access_levels=levels,
        )


@dataclass
class Session:
    """A shared conversation identified by a ``session_id``.

    Participants are not listed separately: anyone who posted a message is a
    participant. Membership is deliberately open (any identified user may join),
    because the visibility filter — not membership — is what prevents leakage.
    """

    session_id: str
    messages: list[SessionMessage] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)