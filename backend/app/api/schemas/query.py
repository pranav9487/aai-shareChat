"""Request/response models for the query endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Body for POST /api/query."""

    question: str = Field(
        min_length=1,
        description="Free-text question about the ingested documents.",
    )
