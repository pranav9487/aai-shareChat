"""Unit tests for shared-session storage and read-time visibility filtering.

Fully offline: no network, no ChromaDB, no Groq — the store and filter are pure
in-process logic (rule 03, adversarial).
"""

from __future__ import annotations

import pytest
from app.services.access_control import Role, User
from app.services.session import (
    HIDDEN_MESSAGE,
    InMemorySessionStore,
    Session,
    SessionMessage,
    SessionNotFoundError,
    is_message_visible,
    visible_messages,
)
from app.services.session.store_supabase import SupabaseSessionStore


def _make_user(user_id: str, role: Role) -> User:
    return User(user_id=user_id, display_name=user_id, role=role)


EMPLOYEE = _make_user("alice", Role.EMPLOYEE)
MANAGER = _make_user("carlos", Role.MANAGER)
EXECUTIVE = _make_user("dana", Role.EXECUTIVE)


def _msg(
    sender: User,
    *,
    answer: str = "answer",
    levels: set[str] | None = None,
    question: str = "q",
) -> SessionMessage:
    """Build a message whose answer draws from ``levels`` (management by default)."""
    used = levels if levels is not None else {"management"}
    sources = tuple({"access_level": level} for level in used)
    return SessionMessage.build(
        sender_user_id=sender.user_id,
        sender_role=sender.role,
        question=question,
        answer=answer,
        sources=sources,
    )


# --- SessionMessage.build derived metadata ---


def test_build_derives_access_levels_from_sources() -> None:
    message = SessionMessage.build(
        sender_user_id="carlos",
        sender_role=Role.MANAGER,
        question="q",
        answer="a",
        sources=({"access_level": "management"}, {"access_level": "general"}, {"x": 1}),
    )
    assert message.access_levels == {"management", "general"}


def test_build_without_sources_has_no_access_levels() -> None:
    message = SessionMessage.build(
        sender_user_id="carlos", sender_role=Role.MANAGER, question="q", answer="a"
    )
    assert message.access_levels == frozenset()


# --- SessionStore protocol conformance (ADR-0008) ---
# Every behavioral test below runs against BOTH implementations: the in-memory
# default and the Supabase-backed store with an offline fake client. The two
# must be indistinguishable from the callers' perspective.


@pytest.fixture(params=["inmemory", "supabase"])
def store(request, fake_supabase):  # noqa: ANN001, ANN202 - pytest fixtures
    if request.param == "inmemory":
        return InMemorySessionStore()
    return SupabaseSessionStore(fake_supabase)


def test_get_or_create_returns_stable_session(store) -> None:
    first = store.get_or_create("s1")
    second = store.get_or_create("s1")
    assert first.session_id == second.session_id == "s1"


def test_get_unknown_session_raises(store) -> None:
    with pytest.raises(SessionNotFoundError):
        store.get("missing")


def test_add_message_appends_to_the_session(store) -> None:
    message = _msg(MANAGER)
    store.add_message("s1", message)
    session = store.get("s1")
    assert session.messages == [message]


def test_add_message_is_visible_on_fresh_read(store) -> None:
    """Round-trip fidelity: a re-read reconstructs the exact domain objects."""
    message = _msg(MANAGER, answer="bonus formula", levels={"management"})
    store.add_message("s1", message)
    reread = store.get_or_create("s1").messages
    assert reread == [message]
    assert reread[0].sender_role is Role.MANAGER
    assert reread[0].access_levels == {"management"}
    assert reread[0].sources == ({"access_level": "management"},)


def test_blank_session_id_is_rejected(store) -> None:
    with pytest.raises(ValueError):
        store.get_or_create("   ")
    with pytest.raises(ValueError):
        store.add_message("", _msg(MANAGER))


def test_store_isolates_sessions(store) -> None:
    store.add_message("s1", _msg(EMPLOYEE))
    store.add_message("s2", _msg(MANAGER, levels={"management"}))
    assert len(store.get("s1").messages) == 1
    assert len(store.get("s2").messages) == 1


def test_messages_keep_chronological_order(store) -> None:
    first = _msg(EMPLOYEE, question="first")
    second = _msg(MANAGER, question="second")
    store.add_message("s1", first)
    store.add_message("s1", second)
    assert [m.question for m in store.get("s1").messages] == ["first", "second"]


# --- Visibility rules ---


def test_author_always_reads_their_own_restricted_message() -> None:
    message = _msg(MANAGER)  # management content
    assert is_message_visible(message, MANAGER) is True


def test_restricted_message_hidden_from_lower_privilege_viewer() -> None:
    message = _msg(MANAGER)
    assert is_message_visible(message, EMPLOYEE) is False


def test_restricted_message_visible_to_superior_role() -> None:
    message = _msg(MANAGER)
    assert is_message_visible(message, EXECUTIVE) is True


def test_message_without_restricted_content_visible_to_everyone() -> None:
    message = _msg(EMPLOYEE, levels=set())  # e.g. not-found / security-decline
    assert message.access_levels == frozenset()
    assert is_message_visible(message, EXECUTIVE) is True
    assert is_message_visible(message, EMPLOYEE) is True


def test_hidden_view_never_leaks_content_or_sources() -> None:
    message = _msg(MANAGER, answer="the secret bonus formula")
    views = visible_messages(Session(session_id="s1", messages=[message]), viewer=EMPLOYEE)
    assert len(views) == 1
    view = views[0]
    assert view["visible"] is False
    # The question (the viewer-typed prompt) stays, but the answer never leaks.
    assert view["question"] == "q"
    assert view["answer"] == HIDDEN_MESSAGE
    assert view["sources"] == []
    assert "bonus formula" not in view["answer"]


def test_author_view_keeps_full_content() -> None:
    message = _msg(MANAGER, answer="bonus formula", levels={"management"})
    views = visible_messages(Session(session_id="s1", messages=[message]), viewer=MANAGER)
    assert views[0]["visible"] is True
    assert views[0]["answer"] == "bonus formula"
    assert views[0]["sources"] == [{"access_level": "management"}]


def test_visible_messages_preserves_asc_order_and_supports_desc() -> None:
    first = _msg(EMPLOYEE, levels=set())
    second = _msg(MANAGER, levels={"management"})
    session = Session(session_id="s1", messages=[first, second])

    asc = visible_messages(session, viewer=EXECUTIVE, order="asc")
    desc = visible_messages(session, viewer=EXECUTIVE, order="desc")
    assert [v["message_id"] for v in asc] == [first.message_id, second.message_id]
    assert [v["message_id"] for v in desc] == [second.message_id, first.message_id]


def test_mixed_session_filters_per_message() -> None:
    general_msg = _msg(EMPLOYEE, levels={"general"})
    restricted_msg = _msg(MANAGER, levels={"management"})
    session = Session(session_id="s1", messages=[general_msg, restricted_msg])

    views = visible_messages(session, viewer=EMPLOYEE)
    # Employee authored general_msg and reads it; manager's msg is author-hidden.
    assert [v["visible"] for v in views] == [True, False]
