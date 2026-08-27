"""Offline tests for the Supabase composition-root selection (ADR-0008).

``deps._build_user_directory`` / ``deps._build_session_store`` must pick the
Supabase implementations only when both env values are set, fail fast on a
half-set configuration, and otherwise keep the in-memory defaults.
"""

from __future__ import annotations

import pytest
from app.api import deps
from app.config.settings import Settings
from app.database.supabase_client import build_supabase_client, is_supabase_configured
from app.services.access_control.directory import InMemoryUserDirectory
from app.services.access_control.directory_supabase import SupabaseUserDirectory
from app.services.session.store import InMemorySessionStore
from app.services.session.store_supabase import SupabaseSessionStore


def _settings(**overrides: str) -> Settings:
    base = {"chroma_persist_dir": "unused", "documents_dir": "unused"}
    base.update(overrides)
    return Settings(**base)


# --- is_supabase_configured / build_supabase_client ---


@pytest.mark.parametrize(
    ("url", "key", "expected"),
    [("", "", False), ("http://x", "", False), ("", "key", False), ("http://x", "key", True)],
)
def test_configured_requires_both_values(url: str, key: str, expected: bool) -> None:
    assert is_supabase_configured(_settings(supabase_url=url, supabase_service_key=key)) is expected


def test_build_client_fails_fast_when_not_configured() -> None:
    with pytest.raises(ValueError, match="not configured"):
        build_supabase_client(_settings())


def test_build_client_fails_fast_on_half_set_config() -> None:
    with pytest.raises(ValueError, match="incomplete"):
        build_supabase_client(_settings(supabase_url="http://x"))


def test_build_client_offline_construction(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def fake_create_client(url: str, key: str) -> object:
        captured["url"], captured["key"] = url, key
        return object()

    import supabase as supabase_module

    monkeypatch.setattr(supabase_module, "create_client", fake_create_client)
    build_supabase_client(_settings(supabase_url="http://x", supabase_service_key="k"))
    assert captured == {"url": "http://x", "key": "k"}


# --- implementation selection ---


def test_unconfigured_settings_keep_in_memory_stores() -> None:
    settings = _settings()
    assert isinstance(deps._build_user_directory(settings), InMemoryUserDirectory)
    assert isinstance(deps._build_session_store(settings), InMemorySessionStore)


def test_configured_settings_select_supabase_stores(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings(supabase_url="http://x", supabase_service_key="k")
    monkeypatch.setattr(deps, "resolve_supabase_client", lambda _settings: object())
    assert isinstance(deps._build_user_directory(settings), SupabaseUserDirectory)
    assert isinstance(deps._build_session_store(settings), SupabaseSessionStore)


def test_half_set_config_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    """URL without key must fail loudly, never silently downgrade to memory."""
    settings = _settings(supabase_url="http://x")
    with pytest.raises(ValueError, match="incomplete"):
        deps._build_user_directory(settings)
    with pytest.raises(ValueError, match="incomplete"):
        deps._build_session_store(settings)
