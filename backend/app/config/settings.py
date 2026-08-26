"""Application configuration loaded from environment variables / .env.

Secrets never live in source code (rule 01-security): everything is read via
pydantic-settings from the repo-root ``.env`` file or process environment.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root: this file is <root>/backend/app/config/settings.py
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Runtime settings for the RAG pipeline."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM (Groq) ---
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3-32b"

    # --- Storage / data locations (defaults resolved against repo root) ---
    chroma_persist_dir: Path = PROJECT_ROOT / "chroma_db"
    documents_dir: Path = PROJECT_ROOT / "documents" / "generated_test_documents"

    # --- Ingestion / retrieval tuning ---
    collection_name: str = "internal_docs"
    chunk_size: int = 800
    chunk_overlap: int = 100
    retrieval_top_k: int = 5

    # --- Access control (ADR-0004) ---
    # Optional JSON seed overriding the built-in demo user registry:
    # '[{"user_id": "alice", "display_name": "Alice", "role": "employee"}, ...]'
    access_control_seed_json: str = ""


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
