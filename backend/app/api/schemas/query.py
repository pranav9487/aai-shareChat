"""Request/response models for the query endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    """Body for POST /api/query.

    ``session_id`` identifies the (possibly shared) conversation this question
    belongs to. It is required so every exchange is attributable to a session
    (roadmap §3); the frontend already sends it on every request.
    """

    question: str = Field(
        min_length=1,
        description="Free-text question about the ingested documents.",
    )
    session_id: str = Field(
        min_length=1,
        description="Identifier of the (possibly shared) conversation.",
    )

    @field_validator("session_id")
    @classmethod
    def _session_id_not_blank(cls, value: str) -> str:
        """Reject whitespace-only sessions up front (422) instead of later."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("session_id must not be blank")
        return cleaned
