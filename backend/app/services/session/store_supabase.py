"""Supabase-backed :class:`SessionStore` (ADR-0008).

Implements the exact :class:`app.services.session.store.SessionStore` protocol
as :class:`.InMemorySessionStore`, so call sites (routes, tests) cannot tell
the implementations apart. Durability now survives restarts; the visibility
filter in ``app.services.session.visibility`` stays pure and unchanged.

The constructor accepts any client exposing the postgrest ``from_()`` surface
(the official ``supabase.Client`` does); tests inject a fake, never the SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.services.access_control.models import Role
from app.services.session.models import Session, SessionMessage
from app.services.session.store import SessionNotFoundError

#: Table names in supabase/schema.sql (ADR-0008).
SESSIONS_TABLE = "sessions"
MESSAGES_TABLE = "session_messages"


def _message_from_row(row: dict) -> SessionMessage:
    """Map a ``session_messages`` row to the domain dataclass."""
    try:
        return SessionMessage(
            message_id=str(row["id"]),
            sender_user_id=str(row["sender_user_id"]),
            sender_role=Role(str(row["sender_role"])),
            question=str(row["question"]),
            answer=str(row["answer"]),
            sources=tuple(dict(source) for source in (row.get("sources") or [])),
            access_levels=frozenset(row.get("access_levels") or []),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"corrupt session_messages row: {exc}") from exc


def _row_from_message(session_id: str, message: SessionMessage) -> dict:
    """Map the domain dataclass to an insertable ``session_messages`` row."""
    return {
        "session_id": session_id,
        "id": message.message_id,
        "sender_user_id": message.sender_user_id,
        "sender_role": message.sender_role.value,
        "question": message.question,
        "answer": message.answer,
        "sources": [dict(source) for source in message.sources],
        "access_levels": sorted(message.access_levels),
    }


def _epoch_from_iso(value: object) -> float | None:
    """Convert a timestamptz string from postgrest to epoch seconds."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError as exc:
        raise ValueError(f"corrupt sessions.created_at value: {value!r}") from exc


class SupabaseSessionStore:
    """Durable shared-session storage backed by Supabase (postgrest)."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def _session_row(self, session_id: str) -> dict | None:
        rows = (
            self._client.from_(SESSIONS_TABLE)
            .select("session_id,created_at")
            .eq("session_id", session_id)
            .execute()
            .data
        )
        return rows[0] if rows else None

    def _messages(self, session_id: str) -> list[SessionMessage]:
        rows = (
            self._client.from_(MESSAGES_TABLE)
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .execute()
            .data
        )
        return [_message_from_row(row) for row in rows]

    def get_or_create(self, session_id: str) -> Session:
        key = (session_id or "").strip()
        if not key:
            raise ValueError("session_id must be a non-empty string")
        row = self._session_row(key)
        if row is None:
            self._client.from_(SESSIONS_TABLE).upsert({"session_id": key}).execute()
            created_at: float | None = None
        else:
            created_at = _epoch_from_iso(row.get("created_at"))
        session = Session(session_id=key, messages=self._messages(key))
        if created_at is not None:
            session.created_at = created_at
        return session

    def get(self, session_id: str) -> Session:
        key = (session_id or "").strip()
        row = self._session_row(key) if key else None
        if row is None:
            raise SessionNotFoundError(f"session not found: {key!r}")
        session = Session(session_id=key, messages=self._messages(key))
        created_at = _epoch_from_iso(row.get("created_at"))
        if created_at is not None:
            session.created_at = created_at
        return session

    def add_message(self, session_id: str, message: SessionMessage) -> Session:
        session = self.get_or_create(session_id)
        self._client.from_(MESSAGES_TABLE).insert(
            _row_from_message(session.session_id, message)
        ).execute()
        session.messages.append(message)
        return session
