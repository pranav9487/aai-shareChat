"""Supabase client factory (ADR-0008).

The backend is the trusted party: it connects with the service-role key and
enforces access itself (RBAC visibility filter), so row-level-security
policies are intentionally out of scope. Construction is offline-safe — no
network happens until the first query, mirroring the Pinecone adapter.
"""

from __future__ import annotations

from typing import Any

from app.config.settings import Settings


def is_supabase_configured(settings: Settings) -> bool:
    """True when both Supabase env values are present (trimmed)."""
    return bool((settings.supabase_url or "").strip()) and bool(
        (settings.supabase_service_key or "").strip()
    )


def resolve_supabase_client(settings: Settings) -> Any | None:
    """Return a client when configured, ``None`` when unset, raise when half-set.

    The composition-root selection primitive: blank-blank means "stay in
    memory", both-set means "use Supabase", and exactly one value is a broken
    configuration that must fail fast (rule: bad seeds never silently weaken
    or downgrade persistence).
    """
    if is_supabase_configured(settings):
        return build_supabase_client(settings)
    if (settings.supabase_url or "").strip() or (settings.supabase_service_key or "").strip():
        build_supabase_client(settings)  # raises the actionable ValueError
    return None


def build_supabase_client(settings: Settings) -> Any:
    """Create the Supabase client, failing fast on half-set configuration.

    Returns a ``supabase.Client``; the stores accept any object exposing the
    ``from_()`` postgrest surface so tests can inject a fake.
    """
    url = (settings.supabase_url or "").strip()
    key = (settings.supabase_service_key or "").strip()
    if not url and not key:
        raise ValueError(
            "Supabase is not configured: set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env"
        )
    if not url or not key:
        raise ValueError(
            "Supabase configuration incomplete: SUPABASE_URL and SUPABASE_SERVICE_KEY "
            "must both be set in .env"
        )
    from supabase import create_client  # heavy SDK, imported on use

    return create_client(url, key)
