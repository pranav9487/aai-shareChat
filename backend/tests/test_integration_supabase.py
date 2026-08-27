"""Live Supabase round-trip (roadmap Next-v2 acceptance).

Auto-skips unless SUPABASE_URL and SUPABASE_SERVICE_KEY are configured — the
offline suite must never depend on a hosted service (rule 03).
"""

from __future__ import annotations

import os

import pytest
from app.config.settings import Settings
from app.database.supabase_client import build_supabase_client, is_supabase_configured
from app.services.access_control import Role
from app.services.session.models import SessionMessage
from app.services.session.store_supabase import SupabaseSessionStore

pytestmark = pytest.mark.skipif(
    not is_supabase_configured(Settings()), reason="Supabase not configured in .env"
)


def test_session_round_trips_through_supabase() -> None:
    store = SupabaseSessionStore(build_supabase_client(Settings()))
    session_id = f"it_{os.urandom(6).hex()}"
    message = SessionMessage.build(
        sender_user_id="alice",
        sender_role=Role.EMPLOYEE,
        question="integration question",
        answer="integration answer",
        sources=({"access_level": "general", "source": "it.md"},),
    )

    store.add_message(session_id, message)
    reread = store.get(session_id)

    assert reread.session_id == session_id
    assert reread.messages == [message]
