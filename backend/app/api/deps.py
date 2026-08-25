"""FastAPI dependency providers (single composition root for the pipeline)."""

from __future__ import annotations

from functools import lru_cache

from app.config.settings import get_settings
from app.services.llm.groq_chain import make_generate
from app.services.rag.pipeline import RAGPipeline
from app.services.rag.retriever import Retriever
from app.vectorstore.chroma_client import ChromaVectorStore


@lru_cache
def get_pipeline() -> RAGPipeline:
    """Build the default pipeline once per process.

    Tests override this dependency with ``app.dependency_overrides`` instead
    of touching real ChromaDB/Groq.
    """
    settings = get_settings()
    store = ChromaVectorStore(
        persist_dir=settings.chroma_persist_dir,
        collection_name=settings.collection_name,
    )
    retriever = Retriever(store, top_k=settings.retrieval_top_k)
    return RAGPipeline(retriever=retriever, generate=make_generate(settings=settings))
