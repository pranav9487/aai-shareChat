"""FastAPI application entrypoint.

Run locally (repo root)::

    uvicorn backend.app.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI

from app.api.routes.query import router as query_router

app = FastAPI(
    title="aai-share-chat backend",
    version="0.1.0",
    description="Secure employee RAG chat — core pipeline (roadmap item 1).",
)

# PRE-AUTH DEV STUB router — replaced by items 2–3.
app.include_router(query_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}
