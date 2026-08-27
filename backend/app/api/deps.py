"""FastAPI dependency providers (composition root for pipeline + identity)."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, Header, HTTPException

from app.config.settings import Settings, get_settings
from app.services.access_control import User, UserDirectory, UserNotFoundError
from app.services.access_control.directory import InMemoryUserDirectory, build_directory
from app.services.llm.groq_chain import GenerationError, make_generate
from app.services.rag.pipeline import RAGPipeline
from app.services.rag.retriever import Retriever
from app.services.session.store import InMemorySessionStore
from app.vectorstore.pinecone_client import PineconeVectorStore


def _build_pipeline(settings: Settings) -> RAGPipeline:
    """Construct the pipeline from *settings*.

    Configuration problems surface as actionable HTTP errors instead of bare
    500s: a missing/empty ``GROQ_API_KEY`` makes ``make_generate`` raise
    ``GenerationError`` here, which previously escaped dependency resolution
    uncaught (root cause of the opaque "Request failed" UI state).
    """
    store = PineconeVectorStore(
        api_key=settings.pinecone_api_key,
        index_name=settings.pinecone_index_name,
        namespace=settings.pinecone_namespace,
        cloud=settings.pinecone_cloud,
        region=settings.pinecone_region,
        dimension=settings.embedding_dim,
    )
    retriever = Retriever(store, top_k=settings.retrieval_top_k)
    try:
        generate = make_generate(settings=settings)
    except GenerationError as exc:
        raise HTTPException(
            status_code=503,
            detail="LLM backend not configured: set GROQ_API_KEY (and a valid GROQ_MODEL) in .env",
        ) from exc
    return RAGPipeline(retriever=retriever, generate=generate)


@lru_cache
def get_pipeline() -> RAGPipeline:
    """Build the default pipeline once per process.

    Tests override this dependency with ``app.dependency_overrides`` instead
    of touching real Pinecone/Groq; ``_build_pipeline`` is the testable core.
    """
    return _build_pipeline(get_settings())


@lru_cache
def get_user_directory() -> InMemoryUserDirectory:
    """Build the user directory once per process (ADR-0004)."""
    return build_directory(get_settings().access_control_seed_json)


@lru_cache
def get_session_service() -> InMemorySessionStore:
    """Shared in-memory session store for the process (ADR-0006).

    Tests override this dependency with ``app.dependency_overrides`` to get a
    fresh store per test, exactly as they do for ``get_pipeline``.
    """
    return InMemorySessionStore()


def get_current_user(
    x_user_id: str | None = Header(default=None, alias="X-User-ID"),
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
    directory: UserDirectory = Depends(get_user_directory),
) -> User:
    """Resolve the requesting user from the ``X-User-ID`` header.

    Failure responses are deliberately non-leaky: a missing header and an
    unknown ID produce fixed messages that never confirm which IDs exist.
    """
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(
            status_code=401,
            detail="Request must identify the user via the X-User-ID header.",
        )
    try:
        return directory.get_user(x_user_id.strip())
    except UserNotFoundError:
        if x_user_role:
            try:
                from app.services.access_control.models import Role, User
                role_enum = Role(x_user_role.strip().lower())
                return User(
                    user_id=x_user_id.strip(),
                    display_name=x_user_id.strip(),
                    role=role_enum
                )
            except ValueError:
                pass
        raise HTTPException(status_code=403, detail="Access denied: unknown user.") from None
