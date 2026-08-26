"""Adversarial tests for access control: roles, tiers, directory, seed config."""

from __future__ import annotations

import pytest
from app.services.access_control import (
    ROLE_ALLOWED_TIERS,
    AccessTier,
    InMemoryUserDirectory,
    Role,
    User,
    UserNotFoundError,
)
from app.services.access_control.directory import build_directory
from app.services.rag.ingestion import ALLOWED_ACCESS_LEVELS


def test_tier_vocabulary_matches_ingestion_metadata() -> None:
    """RBAC tiers and stored chunk metadata must never drift apart."""
    assert {tier.value for tier in AccessTier} == set(ALLOWED_ACCESS_LEVELS)


def test_every_role_has_a_nonempty_tier_mapping() -> None:
    for role in Role:
        assert ROLE_ALLOWED_TIERS[role], f"role {role} must map to at least one tier"


def test_role_to_tier_mapping_boundaries() -> None:
    assert User("e", "E", Role.EMPLOYEE).allowed_tiers == {"general"}
    assert User("h", "H", Role.HR).allowed_tiers == {"general", "hr"}
    # A manager must NOT read hr or restricted material.
    assert "hr" not in User("m", "M", Role.MANAGER).allowed_tiers
    assert "restricted" not in User("m", "M", Role.MANAGER).allowed_tiers
    assert User("x", "X", Role.EXECUTIVE).allowed_tiers == {
        "general",
        "hr",
        "restricted",
        "management",
    }


def test_user_allowed_tiers_are_plain_strings_for_store_filters() -> None:
    user = User("u", "U", Role.HR)
    assert all(isinstance(tier, str) for tier in user.allowed_tiers)


class TestInMemoryUserDirectory:
    def test_known_ids_resolve_to_expected_roles(self) -> None:
        directory = InMemoryUserDirectory()
        assert directory.get_user("alice").role == Role.EMPLOYEE
        assert directory.get_user("priya").role == Role.HR
        assert directory.get_user("carlos").role == Role.MANAGER
        assert directory.get_user("dana").role == Role.EXECUTIVE

    def test_unknown_id_raises_lookup_error(self) -> None:
        directory = InMemoryUserDirectory()
        with pytest.raises(UserNotFoundError):
            directory.get_user("mallory")

    def test_blank_or_whitespace_id_raises(self) -> None:
        directory = InMemoryUserDirectory()
        for bad in ("", "   ", None):
            with pytest.raises(UserNotFoundError):
                directory.get_user(bad)  # type: ignore[arg-type]

    def test_ids_are_case_sensitive_and_trimmed_input_matches(self) -> None:
        directory = InMemoryUserDirectory(users={"alice": User("alice", "A", Role.HR)})
        assert directory.get_user("  alice ").user_id == "alice"
        with pytest.raises(UserNotFoundError):
            directory.get_user("Alice")

    def test_custom_registry_replaces_defaults_entirely(self) -> None:
        directory = InMemoryUserDirectory(users={"solo": User("solo", "S", Role.EXECUTIVE)})
        assert directory.get_user("solo").role == Role.EXECUTIVE
        with pytest.raises(UserNotFoundError):
            directory.get_user("alice")


class TestBuildDirectoryFromSeed:
    def test_blank_seed_returns_default_registry(self) -> None:
        directory = build_directory("")
        assert directory.get_user("alice").role == Role.EMPLOYEE

    def test_valid_seed_overrides_users(self) -> None:
        seed = """
        [
          {"user_id": "bob", "display_name": "Bob B", "role": "manager"},
          {"user_id": "eve", "role": "HR"}
        ]
        """
        directory = build_directory(seed)
        assert directory.get_user("bob").role == Role.MANAGER
        eve = directory.get_user("eve")
        assert eve.role == Role.HR, "role parsing must be case-insensitive"
        assert eve.display_name == "eve", "missing display_name falls back to user_id"

    @pytest.mark.parametrize(
        "seed",
        [
            "not json at all",
            '{"user_id": "solo", "role": "employee"}',  # JSON object, not array
            '[{"role": "employee"}]',  # missing user_id
            '[{"user_id": "x", "role": "superadmin"}]',  # unknown role
            '["just-a-string"]',  # wrong item shape
            "[]",  # empty seed
        ],
    )
    def test_invalid_seeds_fail_fast_with_value_error(self, seed: str) -> None:
        with pytest.raises(ValueError, match="ACCESS_CONTROL_SEED_JSON"):
            build_directory(seed)

    def test_broken_seed_never_silently_weakens_access(self) -> None:
        """A failing build must not return a directory missing default users."""
        with pytest.raises(ValueError):
            build_directory('[{"user_id": "x", "role": "nope"}]')
