"""Response models for the shared-session read endpoint (roadmap §3)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MessageView(BaseModel):
    """One message in a shared session, as visible to the requesting user.

    When ``visible`` is False, ``question`` and ``answer`` are the canonical
    non-leaky placeholder and ``sources`` is empty — the caller learns the
    message exists but never reads restricted content.
    """

    message_id: str
    sender_user_id: str
    sender_role: str
    question: str
    answer: str
    sources: list[dict] = Field(default_factory=list)
    visible: bool


class SessionView(BaseModel):
    """Shared session metadata plus the filtered transcript."""

    session_id: str
    messages: list[MessageView] = Field(default_factory=list)
