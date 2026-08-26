"""Authenticated document query routes (roadmap item 2).

Every request must identify its user via the ``X-User-ID`` header; retrieval
is filtered server-side to that user's permitted access tiers, and denied
topics receive the canonical security-decline answer rather than content.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user, get_pipeline
from app.api.schemas.query import QueryRequest
from app.services.access_control import User
from app.services.rag.pipeline import PipelineError, QueryResult, RAGPipeline

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_model=QueryResult)
async def query_documents(
    payload: QueryRequest,
    user: User = Depends(get_current_user),
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> QueryResult:
    """Answer *question* using only documents the identified user may read."""
    try:
        return pipeline.query(payload.question, allowed_levels=sorted(user.allowed_tiers))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PipelineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
