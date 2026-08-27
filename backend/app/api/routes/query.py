"""Authenticated document query + shared-session read routes (items 2–3).

Every request must identify its user via the ``X-User-ID`` header; retrieval
is filtered server-side to that user's permitted access tiers, and denied
topics receive the canonical security-decline answer rather than content.

Item 3 (shared-session safety): each answer is logged against the caller's
``session_id`` with the author's role and the access tiers the answer actually
drew from. A separate read endpoint returns that transcript filtered per the
requesting viewer's permissions, so a participant never sees content another
participant retrieved outside their own access — the core project invariant.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import (
    get_current_user,
    get_pipeline,
    get_session_service,
)
from app.api.schemas.query import QueryRequest
from app.api.schemas.session import SessionView
from app.services.access_control import User
from app.services.rag.pipeline import PipelineError, QueryResult, RAGPipeline
from app.services.session import (
    SessionMessage,
    SessionNotFoundError,
    SessionStore,
    visible_messages,
)

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_model=QueryResult)
async def query_documents(
    payload: QueryRequest,
    user: User = Depends(get_current_user),
    pipeline: RAGPipeline = Depends(get_pipeline),
    sessions: SessionStore = Depends(get_session_service),
) -> QueryResult:
    """Answer *question* using only documents the identified user may read.

    The fresh, permission-filtered retrieval never consults another user's
    stored context; the resulting answer is then logged to the shared session
    for later, equally permission-filtered reads.
    """
    try:
        result = pipeline.query(payload.question, allowed_levels=sorted(user.allowed_tiers))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PipelineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    sessions.add_message(
        payload.session_id,
        SessionMessage.build(
            sender_user_id=user.user_id,
            sender_role=user.role,
            question=payload.question,
            answer=result.answer,
            sources=tuple(result.sources),
        ),
    )
    return result


@router.get("/sessions/{session_id}", response_model=SessionView)
async def get_session(
    session_id: str,
    user: User = Depends(get_current_user),
    sessions: SessionStore = Depends(get_session_service),
) -> SessionView:
    """Return *session_id*'s transcript filtered to what *user* may read.

    A missing session produces a non-leaky 404. Restricted messages are shown
    with the canonical placeholder (``HIDDEN_MESSAGE``) rather than content.
    """
    try:
        session = sessions.get(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found.") from None
    return SessionView(
        session_id=session.session_id,
        messages=[
            {
                "message_id": view["message_id"],
                "sender_user_id": view["sender_user_id"],
                "sender_role": view["sender_role"],
                "question": view["question"],
                "answer": view["answer"],
                "sources": view["sources"],
                "visible": view["visible"],
            }
            for view in visible_messages(session, viewer=user)
        ],
    )
