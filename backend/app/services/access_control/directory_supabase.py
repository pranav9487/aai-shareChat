"""Supabase-backed :class:`UserDirectory` (ADR-0008).

Same :class:`app.services.access_control.UserDirectory` protocol as
:class:`.InMemoryUserDirectory`: unknown IDs raise :class:`UserNotFoundError`,
which callers turn into the fixed non-leaky 403. The ``app_users`` table is
populated once (via supabase/schema.sql or an insert) — the registry is read
per lookup so role changes take effect without a restart.
"""

from __future__ import annotations

from typing import Any

from app.services.access_control.directory import UserNotFoundError
from app.services.access_control.models import Role, User

#: Table name in supabase/schema.sql (ADR-0008).
USERS_TABLE = "app_users"


class SupabaseUserDirectory:
    """User registry served from the ``app_users`` table."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def get_user(self, user_id: str) -> User:
        key = (user_id or "").strip()
        if not key:
            raise UserNotFoundError("user_id not found: ''")
        rows = (
            self._client.from_(USERS_TABLE)
            .select("user_id,display_name,role")
            .eq("user_id", key)
            .execute()
            .data
        )
        if not rows:
            raise UserNotFoundError(f"user_id not found: {key!r}")
        row = rows[0]
        try:
            return User(
                user_id=str(row["user_id"]),
                display_name=str(row["display_name"]),
                role=Role(str(row["role"])),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"corrupt app_users row: {exc}") from exc
