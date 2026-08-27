"""Session persistence behind a stable :class:`SessionStore` protocol.

V1 ships an in-memory implementation (ADR-0006); the Supabase-backed
implementation planned for roadmap Next-v2 will implement the same protocol so
nothing above this layer changes — the exact pattern used for
:class:`UserDirectory` in ADR-0004.
"""

from __future__ import annotations

import threading
from collections.abc import Mapping
from typing import Protocol

from app.services.session.models import Session, SessionMessage


class SessionNotFoundError(LookupError):
    """Raised when a lookup references a session that does not exist."""


class SessionStore(Protocol):
    """Anything that can create and update shared sessions."""

    def get_or_create(self, session_id: str) -> Session: ...

    def get(self, session_id: str) -> Session: ...

    def add_message(self, session_id: str, message: SessionMessage) -> Session: ...


class InMemorySessionStore:
    """Thread-safe, in-process session storage; safe default for v1/dev.

    Not durable across restarts — acceptable until Supabase lands. Concurrent
    clients sharing one store are serialized on a lock so a message posted by
    one user is atomically visible to the next read.
    """

    def __init__(self, sessions: Mapping[str, Session] | None = None) -> None:
        self._sessions: dict[str, Session] = (
            {sid: self._copy(session) for sid, session in sessions.items()}
            if sessions
            else {}
        )
        self._lock = threading.RLock()

    @staticmethod
    def _copy(session: Session) -> Session:
        """Return a fresh Session carrying the same messages."""
        return Session(
            session_id=session.session_id,
            messages=list(session.messages),
            created_at=session.created_at,
        )

    def get_or_create(self, session_id: str) -> Session:
        key = (session_id or "").strip()
        if not key:
            raise ValueError("session_id must be a non-empty string")
        with self._lock:
            if key not in self._sessions:
                self._sessions[key] = Session(session_id=key)
            return self._sessions[key]

    def get(self, session_id: str) -> Session:
        key = (session_id or "").strip()
        if not key or key not in self._sessions:
            raise SessionNotFoundError(f"session not found: {key!r}")
        return self._sessions[key]

    def add_message(self, session_id: str, message: SessionMessage) -> Session:
        session = self.get_or_create(session_id)
        with self._lock:
            self._sessions[session.session_id].messages.append(message)
        return self._sessions[session.session_id]