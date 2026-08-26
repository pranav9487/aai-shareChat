"""API-level tests via FastAPI TestClient with the pipeline dependency overridden."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from app.api.deps import get_pipeline
from app.main import app
from app.services.rag.pipeline import PipelineError, QueryResult
from fastapi.testclient import TestClient


class FakePipeline:
    """Stands in for RAGPipeline behind the /api/dev/query dependency."""

    def __init__(self) -> None:
        self.result = QueryResult(answer="stub answer", sources=[{"source": "a.md"}])
        self.error: Exception | None = None
        self.calls: list[str] = []

    def query(self, question: str) -> QueryResult:
        self.calls.append(question)
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
def client(fake_pipeline: FakePipeline) -> TestClient:
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_query_happy_path(client: TestClient, fake_pipeline: FakePipeline) -> None:
    fake_pipeline.result = QueryResult(
        answer="25 days", sources=[{"source": "hr_vacation_policy.md"}]
    )
    response = client.post("/api/dev/query", json={"question": "vacation days?"})
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "25 days"
    assert body["sources"] == [{"source": "hr_vacation_policy.md"}]
    assert fake_pipeline.calls == ["vacation days?"]


def test_value_error_maps_to_400(client: TestClient, fake_pipeline: FakePipeline) -> None:
    fake_pipeline.error = ValueError("empty question")
    response = client.post("/api/dev/query", json={"question": "x"})
    assert response.status_code == 400
    assert "empty question" in response.json()["detail"]


def test_pipeline_error_maps_to_502(client: TestClient, fake_pipeline: FakePipeline) -> None:
    fake_pipeline.error = PipelineError("groq unreachable")
    response = client.post("/api/dev/query", json={"question": "x"})
    assert response.status_code == 502
    assert "groq unreachable" in response.json()["detail"]


def test_missing_question_field_is_422(client: TestClient) -> None:
    assert client.post("/api/dev/query", json={}).status_code == 422


def test_blank_question_fails_validation_as_422(client: TestClient) -> None:
    assert client.post("/api/dev/query", json={"question": ""}).status_code == 422
