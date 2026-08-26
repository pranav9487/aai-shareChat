"""API-level tests via FastAPI TestClient with dependencies overridden.

Covers roadmap item 2 semantics at the HTTP boundary: mandatory identity,
non-leaky failures, per-role tier forwarding, and application-level security
declines.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence

import pytest
from app.api.deps import get_pipeline, get_user_directory
from app.main import app
from app.services.access_control import InMemoryUserDirectory, Role, User
from app.services.rag.pipeline import (
    ACCESS_DENIED_ANSWER,
    NOT_FOUND_ANSWER,
    PipelineError,
    QueryResult,
)
from fastapi.testclient import TestClient


class FakePipeline:
    """Stands in for RAGPipeline behind /api/query; records identity context."""

    def __init__(self) -> None:
        self.result = QueryResult(answer="stub answer", sources=[{"source": "a.md"}])
        self.error: Exception | None = None
        self.calls: list[tuple[str, list[str]]] = []

    def query(self, question: str, allowed_levels: Sequence[str] | None = None) -> QueryResult:
        self.calls.append((question, sorted(allowed_levels) if allowed_levels else []))
        if self.error is not None:
            raise self.error
        return self.result


@pytest.fixture
def fake_pipeline() -> Iterator[FakePipeline]:
    pipeline = FakePipeline()
    app.dependency_overrides[get_pipeline] = lambda: pipeline
    yield pipeline
    app.dependency_overrides.pop(get_pipeline, None)


@pytest.fixture
def directory() -> Iterator[InMemoryUserDirectory]:
    directory = InMemoryUserDirectory(
        users={
            "emp": User(user_id="emp", display_name="Employee", role=Role.EMPLOYEE),
            "hrp": User(user_id="hrp", display_name="HR Person", role=Role.HR),
        }
    )
    app.dependency_overrides[get_user_directory] = lambda: directory
    yield directory
    app.dependency_overrides.pop(get_user_directory, None)


@pytest.fixture
def client(fake_pipeline: FakePipeline, directory: InMemoryUserDirectory) -> TestClient:
    return TestClient(app)


def _post(client: TestClient, question: str = "vacation days?", user_id: str | None = "emp"):
    headers = {"X-User-ID": user_id} if user_id is not None else {}
    return client.post("/api/query", json={"question": question}, headers=headers)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_happy_path_forwards_caller_tiers(client: TestClient, fake_pipeline: FakePipeline) -> None:
    fake_pipeline.result = QueryResult(
        answer="25 days", sources=[{"source": "hr_vacation_policy.md"}]
    )
    response = _post(client)
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "25 days"
    assert body["sources"] == [{"source": "hr_vacation_policy.md"}]
    assert fake_pipeline.calls == [("vacation days?", ["general"])]


def test_hr_role_forwards_both_of_its_tiers(
    client: TestClient, fake_pipeline: FakePipeline
) -> None:
    _post(client, user_id="hrp")
    assert fake_pipeline.calls == [("vacation days?", ["general", "hr"])]


def test_missing_identity_header_is_401_and_never_reaches_pipeline(
    client: TestClient, fake_pipeline: FakePipeline
) -> None:
    response = _post(client, user_id=None)
    assert response.status_code == 401
    assert response.json()["detail"].startswith("Request must identify")
    assert fake_pipeline.calls == [], "unidentified requests must not query documents"


def test_whitespace_identity_header_is_401(client: TestClient) -> None:
    assert _post(client, user_id="   ").status_code == 401


def test_unknown_user_is_403_with_non_leaky_detail(
    client: TestClient, fake_pipeline: FakePipeline
) -> None:
    response = _post(client, user_id="mallory")
    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail == "Access denied: unknown user.", "detail must not echo the attempted ID"
    assert "mallory" not in detail
    assert fake_pipeline.calls == []


def test_security_decline_passes_through_as_application_answer(
    client: TestClient, fake_pipeline: FakePipeline
) -> None:
    fake_pipeline.result = QueryResult(answer=ACCESS_DENIED_ANSWER, sources=[])
    response = _post(client, question="salary bands?")
    assert response.status_code == 200
    assert response.json()["answer"] == ACCESS_DENIED_ANSWER
    assert response.json()["sources"] == []


def test_not_found_passes_through_as_application_answer(
    client: TestClient, fake_pipeline: FakePipeline
) -> None:
    fake_pipeline.result = QueryResult(answer=NOT_FOUND_ANSWER, sources=[])
    response = _post(client, question="gibberish?")
    assert response.status_code == 200
    assert response.json()["answer"] == NOT_FOUND_ANSWER


def test_value_error_maps_to_400(client: TestClient, fake_pipeline: FakePipeline) -> None:
    fake_pipeline.error = ValueError("empty question")
    response = _post(client)
    assert response.status_code == 400
    assert "empty question" in response.json()["detail"]


def test_pipeline_error_maps_to_502(client: TestClient, fake_pipeline: FakePipeline) -> None:
    fake_pipeline.error = PipelineError("groq unreachable")
    response = _post(client)
    assert response.status_code == 502
    assert "groq unreachable" in response.json()["detail"]


def test_missing_question_field_is_422(client: TestClient) -> None:
    response = client.post("/api/query", json={}, headers={"X-User-ID": "emp"})
    assert response.status_code == 422


def test_blank_question_fails_validation_as_422(client: TestClient) -> None:
    response = client.post("/api/query", json={"question": ""}, headers={"X-User-ID": "emp"})
    assert response.status_code == 422
