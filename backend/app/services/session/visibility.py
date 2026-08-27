"""Read-time visibility filtering for shared sessions (roadmap §3).

The core security invariant: retrieved context must never be exposed to
another user who lacks access. Because every message records the access tiers
its answer drew from (see :class:`.SessionMessage`), a viewer can be granted
or denied content *without* re-querying the store. Denied messages return a
non-leaky placeholder, never the underlying answer or its sources.
"""

from __future__ import annotations

from collections.abc import Mapping

from app.services.access_control.models import User
from app.services.session.models import HIDDEN_MESSAGE, Session, SessionMessage


def is_message_visible(message: SessionMessage, viewer: User) -> bool:
    """Whether *viewer* may read *message*'s content.

    Rules:
    - The author always sees their own message.
    - A message with no restricted content (a not-found result or a
      security-decline — empty ``access_levels``) is safe for everyone.
    - Otherwise *viewer* must permit every tier the message drew from, i.e.
      the message's ``access_levels`` must be a subset of the viewer's
      ``allowed_tiers``.
    """
    if message.sender_user_id == viewer.user_id:
        return True
    if not message.access_levels:
        return True
    return message.access_levels.issubset(viewer.allowed_tiers)


def _render(message: SessionMessage, viewer: User) -> Mapping[str, object]:
    """Serialize *message* for the wire, hiding the answer when not visible.

    The question is the viewer-typed prompt, not retrieved content, so it stays
    intact. The answer is replaced by a non-leaky placeholder (mirroring the
    ``ACCESS_DENIED_ANSWER`` philosophy), and sources are emptied — the viewer
    learns a restricted answer exists but never its content.
    """
    visible = is_message_visible(message, viewer)
    return {
        "message_id": message.message_id,
        "sender_user_id": message.sender_user_id,
        "sender_role": message.sender_role.value,
        "question": message.question,
        "answer": message.answer if visible else HIDDEN_MESSAGE,
        "sources": list(message.sources) if visible else [],
        "visible": visible,
    }


def visible_messages(
    session: Session, viewer: User, *, order: str = "asc"
) -> list[Mapping[str, object]]:
    """Filter *session*'s messages down to what *viewer* may read, in order.

    *order* accepts ``"asc"`` (oldest-first, the posted order — default) or
    ``"desc"`` (newest-first). Messages the viewer cannot read are still
    returned, but hidden behind a placeholder so the shared session stays
    visibly "shared" without leaking content.
    """
    rendered = [_render(message, viewer) for message in session.messages]
    if order == "desc":
        rendered.reverse()
    return rendered
