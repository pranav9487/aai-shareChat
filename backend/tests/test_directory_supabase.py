"""Adversarial offline tests for the Supabase-backed user directory (ADR-0008).

The fake client carries a seeded ``app_users`` table mirroring
supabase/schema.sql; no network anywhere.
"""

from __future__ import annotations

import pytest
from app.services.access_control import Role, User, UserNotFoundError
from app.services.access_control.directory_supabase import SupabaseUserDirectory

SEED_USERS = [
    {"user_id": "alice", "display_name": "Alice (Employee)", "role": "employee"},
    {"user_id": "priya", "display_name": "Priya (HR)", "role": "hr"},
    {"user_id": "guest", "display_name": "Guest (Employee)", "role": "employee"},
]


@pytest.fixture
def directory(fake_supabase) -> SupabaseUserDirectory:
    fake_supabase.tables["app_users"] = [dict(row) for row in SEED_USERS]
    return SupabaseUserDirectory(fake_supabase)


def test_known_user_maps_to_domain_object(directory) -> None:
    user = directory.get_user("priya")
    assert user == User(user_id="priya", display_name="Priya (HR)", role=Role.HR)
    assert user.allowed_tiers == {"general", "hr"}


def test_lookup_is_trimmed_but_case_sensitive(directory) -> None:
    assert directory.get_user("  guest ").user_id == "guest"
    with pytest.raises(UserNotFoundError):
        directory.get_user("Guest")


def test_unknown_user_raises_non_leaky_lookup_error(directory) -> None:
    with pytest.raises(UserNotFoundError):
        directory.get_user("mallory")


def test_blank_user_id_raises(directory) -> None:
    for bad in ("", "   "):
        with pytest.raises(UserNotFoundError):
            directory.get_user(bad)


def test_corrupt_role_fails_loudly(directory) -> None:
    """A corrupted row must not silently masquerade as a valid identity."""
    directory._client.tables["app_users"][0]["role"] = "superadmin"  # noqa: SLF001
    with pytest.raises(ValueError, match="corrupt app_users row"):
        directory.get_user("alice")
