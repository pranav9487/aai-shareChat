"""User directory: resolution of user IDs to users, behind a stable interface.

V1 uses an in-memory seed registry (ADR-0004); the Supabase-backed
implementation planned for later items will implement the same
:class:`UserDirectory` protocol, so nothing above this layer changes.
"""

from __future__ import annotations

import json
from typing import Protocol

from app.services.access_control.models import Role, User


class UserNotFoundError(LookupError):
    """Raised when a directory lookup does not match any known user."""


class UserDirectory(Protocol):
    """Anything that can resolve a raw user ID into a :class:`User`."""

    def get_user(self, user_id: str) -> User: ...


def _build_default_users() -> dict[str, User]:
    """Deterministic demo registry used until real persistence exists."""
    users = [
        User(user_id="alice", display_name="Alice (Employee)", role=Role.EMPLOYEE),
        User(user_id="priya", display_name="Priya (HR)", role=Role.HR),
        User(user_id="carlos", display_name="Carlos (Manager)", role=Role.MANAGER),
        User(user_id="dana", display_name="Dana (Executive)", role=Role.EXECUTIVE),
        # Low-privilege catch-all that mirrors the frontend DEMO_USERS list.
        # Kept last so the four role-demonstrating users stay the canonical examples.
        User(user_id="guest", display_name="Guest (Employee)", role=Role.EMPLOYEE),
    ]
    return {user.user_id: user for user in users}


class InMemoryUserDirectory:
    """Fixed mapping of user ID → user; safe default for v1/dev."""

    def __init__(self, users: dict[str, User] | None = None) -> None:
        self._users: dict[str, User] = _build_default_users() if users is None else dict(users)

    def get_user(self, user_id: str) -> User:
        """Return the user for *user_id*.

        Raises :class:`UserNotFoundError` for blank/unknown IDs; callers turn
        that into non-leaky API responses (never confirming which IDs exist).
        """
        key = (user_id or "").strip()
        if not key or key not in self._users:
            raise UserNotFoundError(f"user_id not found: {key!r}")
        return self._users[key]


def build_directory(seed_json: str = "") -> InMemoryUserDirectory:
    """Build a directory from the optional ``ACCESS_CONTROL_SEED_JSON`` setting.

    Blank input yields the built-in demo registry. Invalid JSON, missing
    fields, unknown roles, or an empty seed raise ``ValueError`` so a broken
    configuration fails fast at startup instead of silently weakening access
    control.
    """
    if not seed_json.strip():
        return InMemoryUserDirectory()
    try:
        raw = json.loads(seed_json)
        users = [
            User(
                user_id=str(item["user_id"]).strip(),
                display_name=str(item.get("display_name") or item["user_id"]),
                role=Role(str(item["role"]).strip().lower()),
            )
            for item in raw
        ]
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid ACCESS_CONTROL_SEED_JSON: {exc}") from exc
    if not users:
        raise ValueError("invalid ACCESS_CONTROL_SEED_JSON: seed must define at least one user")
    return InMemoryUserDirectory({user.user_id: user for user in users})
