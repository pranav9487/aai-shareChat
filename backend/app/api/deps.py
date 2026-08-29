"""FastAPI dependency providers (composition root for pipeline + identity)."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, Header, HTTPException

from app.config.settings import Settings, get_settings
from app.database.supabase_client import resolve_supabase_client
from app.services.access_control import User, UserDirectory, UserNotFoundError
from app.services.access_control.directory import build_directory
from app.services.access_control.directory_supabase import SupabaseUserDirectory
from app.services.followup import FollowUpResolver, get_heuristic_resolver
from app.services.llm.groq_chain import GenerationError, make_generate
from app.services.rag.pipeline import RAGPipeline
from app.services.rag.retriever import Retriever
from app.services.session.store import InMemorySessionStore, SessionStore
from app.services.session.store_supabase import SupabaseSessionStore
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
def get_follow_up_resolver() -> FollowUpResolver:
    """Shared follow-up resolver (ADR-0009).

    Uses the LLM-based resolver for high-quality standalone rewriting when
    ``GROQ_API_KEY`` is set; falls back to the deterministic heuristic
    resolver otherwise (dev/test environments without network).
    """
    settings = get_settings()
    if (settings.groq_api_key or "").strip():
        try:
            from langchain_groq import ChatGroq

            from app.services.followup.llm_resolver import (
                LLMFollowUpResolver,
                make_rewrite_fn,
            )

            llm = ChatGroq(
                model=settings.groq_model,
                api_key=settings.groq_api_key,
                temperature=0,
            )
            chain = make_rewrite_fn(llm)
            return LLMFollowUpResolver(rewrite_fn=chain)
        except Exception:  # noqa: BLE001 — fall back to heuristic
            pass
    return get_heuristic_resolver()


def _build_user_directory(settings: Settings) -> UserDirectory:
    """Select the directory implementation from *settings* (ADR-0008)."""
    client = resolve_supabase_client(settings)
    if client is not None:
        return SupabaseUserDirectory(client)
    return build_directory(settings.access_control_seed_json)


def _build_session_store(settings: Settings) -> SessionStore:
    """Select the session-store implementation from *settings* (ADR-0008)."""
    client = resolve_supabase_client(settings)
    if client is not None:
        return SupabaseSessionStore(client)
    return InMemorySessionStore()


@lru_cache
def get_user_directory() -> UserDirectory:
    """Build the user directory once per process (ADR-0004 / ADR-0008).

    Served from Supabase when configured, else from the in-memory seed
    registry; both implement the same protocol.
    """
    return _build_user_directory(get_settings())


@lru_cache
def get_session_service() -> SessionStore:
    """Shared session store for the process (ADR-0006 / ADR-0008).

    Durable Supabase-backed store when configured, else the in-memory store;
    both implement the same protocol, so tests keep overriding this dependency
    with a fresh in-memory store per test.
    """
    return _build_session_store(get_settings())


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
                    user_id=x_user_id.strip(), display_name=x_user_id.strip(), role=role_enum
                )
            except ValueError:
                pass
        raise HTTPException(status_code=403, detail="Access denied: unknown user.") from None
