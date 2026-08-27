"""FastAPI application entrypoint.

Run locally (repo root)::

    uvicorn app.main:app --reload --app-dir backend
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.query import router as query_router
from app.config.settings import get_settings
from app.services.rag.ingestion import ensure_corpus
from app.vectorstore.pinecone_client import PineconeVectorStore

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Auto-provision the document corpus so a fresh checkout is answerable."""
    settings = get_settings()
    try:
        store = PineconeVectorStore(
            api_key=settings.pinecone_api_key,
            index_name=settings.pinecone_index_name,
            namespace=settings.pinecone_namespace,
            cloud=settings.pinecone_cloud,
            region=settings.pinecone_region,
            dimension=settings.embedding_dim,
        )
        summary = ensure_corpus(store, settings)
        if summary is not None:
            logger.info("auto-ingested corpus on startup: %s", summary)
    except Exception as exc:  # noqa: BLE001 - startup provisioning must not kill the app
        logger.warning("corpus auto-provisioning skipped: %s", exc)
    yield


app = FastAPI(
    title="aai-share-chat backend",
    version="0.2.0",
    description=(
        "Secure employee RAG chat — authenticated, permission-filtered "
        "document queries (roadmap items 1–3) with shared-session transcripts "
        "filtered per viewer."
    ),
    lifespan=lifespan,
)

app.include_router(query_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}
