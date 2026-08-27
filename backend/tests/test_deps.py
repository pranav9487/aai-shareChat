"""Regression tests for pipeline construction failure handling.

Root cause being guarded: a missing/empty GROQ_API_KEY made ``make_generate``
raise ``GenerationError`` inside dependency resolution, which no handler
caught — every query returned a bare 500 and the UI showed "Request failed".
The contract now is an actionable HTTP 503.
"""

from __future__ import annotations

import pytest
from app.api.deps import _build_pipeline
from app.config.settings import Settings
from fastapi import HTTPException


def _settings(tmp_path, groq_api_key: str) -> Settings:
    # NOTE: tests construct PipelineVectorStore lazily, so no Pinecone key or
    # network is required at build time.
    return Settings(
        groq_api_key=groq_api_key,
        groq_model="test-model",
    )


def test_missing_api_key_becomes_actionable_503(tmp_path) -> None:
    with pytest.raises(HTTPException) as excinfo:
        _build_pipeline(_settings(tmp_path, groq_api_key=""))

    assert excinfo.value.status_code == 503
    assert "GROQ_API_KEY" in excinfo.value.detail


def test_whitespace_api_key_is_treated_as_missing(tmp_path) -> None:
    # The current code only treats truly empty keys as 503; whitespace-only
    # keys are passed to make_generate which raises GenerationError only
    # for empty strings. This test documents the actual behaviour.
    with pytest.raises(HTTPException) as excinfo:
        _build_pipeline(_settings(tmp_path, groq_api_key="   "))

    # The current implementation treats only the empty string as 503;
    # a whitespace-only key is truthy for the Settings model.
    assert excinfo.value.status_code == 503


def test_valid_config_builds_pipeline_without_network(tmp_path) -> None:
    """Construction itself must stay offline (no Groq call at build time)."""
    pipeline = _build_pipeline(_settings(tmp_path, groq_api_key="test-key"))

    assert pipeline is not None
