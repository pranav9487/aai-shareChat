"""Dev-only query routes.

PRE-AUTH DEV STUB — replaced by items 2–3. There is no user identification
or access control here yet, so nothing in this router may be exposed beyond
local development.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_pipeline
from app.api.schemas.query import QueryRequest
from app.services.rag.pipeline import PipelineError, QueryResult, RAGPipeline

router = APIRouter(prefix="/api/dev", tags=["dev"])


@router.post("/query", response_model=QueryResult)
async def dev_query(
    payload: QueryRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> QueryResult:
    # PRE-AUTH DEV STUB — replaced by items 2–3.
    try:
        return pipeline.query(payload.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PipelineError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
