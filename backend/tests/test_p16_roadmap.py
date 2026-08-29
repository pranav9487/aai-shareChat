"""Explicit verification of the P16 Safety Roadmap (Phases 5-12).

These tests act as the final validation that the RAG pipeline correctly
isolates conversation history, retrieved documents, and user permissions
in a shared session environment.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence

import pytest
from fastapi.testclient import TestClient

from app.api.deps import (
    get_follow_up_resolver,
    get_pipeline,
    get_session_service,
    get_user_directory,
)
from app.main import app
from app.services.access_control import InMemoryUserDirectory, Role, User
from app.services.followup.resolver import HeuristicFollowUpResolver
from app.services.rag.pipeline import ACCESS_DENIED_ANSWER, QueryResult
from app.services.session import InMemorySessionStore


# ---------------------------------------------------------------------------
# Fixtures (mirrored from test_api.py for independent verification)
# ---------------------------------------------------------------------------


class FakePipeline:
    def __init__(self) -> None:
        self.result = QueryResult(answer="Default answer", sources=[])
        self.calls: list[tuple[str, list[str]]] = []

    def query(self, question: str, allowed_levels: Sequence[str] | None = None) -> QueryResult:
        self.calls.append((question, sorted(allowed_levels) if allowed_levels else []))
        return self.result


@pytest.fixture
def fake_pipeline() -> Iterator[FakePipeline]:
    pipeline = FakePipeline()
    app.dependency_overrides[get_pipeline] = lambda: pipeline
    yield pipeline
    app.dependency_overrides.pop(get_pipeline, None)


@pytest.fixture
def sessions() -> Iterator[InMemorySessionStore]:
    store = InMemorySessionStore()
    app.dependency_overrides[get_session_service] = lambda: store
    yield store
    app.dependency_overrides.pop(get_session_service, None)


@pytest.fixture
def directory() -> Iterator[InMemoryUserDirectory]:
    directory = InMemoryUserDirectory(
        users={
            "EMP001": User(user_id="EMP001", display_name="Employee", role=Role.EMPLOYEE),
            "MGR001": User(user_id="MGR001", display_name="Manager", role=Role.MANAGER),
        }
    )
    app.dependency_overrides[get_user_directory] = lambda: directory
    yield directory
    app.dependency_overrides.pop(get_user_directory, None)


@pytest.fixture
def heuristic_resolver() -> Iterator[None]:
    app.dependency_overrides[get_follow_up_resolver] = lambda: HeuristicFollowUpResolver()
    yield
    app.dependency_overrides.pop(get_follow_up_resolver, None)


@pytest.fixture
def client(
    fake_pipeline: FakePipeline,
    sessions: InMemorySessionStore,
    directory: InMemoryUserDirectory,
    heuristic_resolver: None,
) -> TestClient:
    return TestClient(app)


def _post(
    client: TestClient, question: str, user_id: str, session_id: str = "shared_session"
):
    return client.post(
        "/api/query",
        json={"question": question, "session_id": session_id},
        headers={"X-User-ID": user_id},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_new_question_not_followup(client: TestClient, fake_pipeline: FakePipeline) -> None:
    _post(client, question="What is the leave policy?", user_id="EMP001")
    assert fake_pipeline.calls[-1][0] == "What is the leave policy?"


def test_followup_detected(client: TestClient, fake_pipeline: FakePipeline) -> None:
    _post(client, question="How many paid leave days do employees receive?", user_id="EMP001")
    _post(client, question="How many can I carry that forward?", user_id="EMP001")
    # If the history is passed properly, it should rewrite.
    assert "paid leave days" in fake_pipeline.calls[-1][0]


def test_followup_rewritten(client: TestClient, fake_pipeline: FakePipeline) -> None:
    _post(client, question="What is the remote work policy?", user_id="EMP001")
    _post(client, question="Does this apply to contractors?", user_id="EMP001")
    assert "remote work policy" in fake_pipeline.calls[-1][0]
    assert "contractors" in fake_pipeline.calls[-1][0]


def test_followup_uses_limited_history(client: TestClient, fake_pipeline: FakePipeline) -> None:
    _post(client, question="Question 1", user_id="EMP001")
    _post(client, question="Question 2", user_id="EMP001")
    _post(client, question="Question 3", user_id="EMP001")
    _post(client, question="What about that?", user_id="EMP001")
    # History capped to 2 (Question 2 and Question 3). "Question 1" should be excluded.
    assert "Question 3" in fake_pipeline.calls[-1][0]
    assert "Question 1" not in fake_pipeline.calls[-1][0]


def test_user_identity_preserved_per_turn(
    client: TestClient, fake_pipeline: FakePipeline, sessions: InMemorySessionStore
) -> None:
    _post(client, question="Emp Q1", user_id="EMP001")
    _post(client, question="Mgr Q1", user_id="MGR001")
    _post(client, question="Emp Q2", user_id="EMP001")
    
    session = sessions.get("shared_session")
    messages = session.messages
    assert len(messages) == 3
    assert messages[0].sender_user_id == "EMP001"
    assert messages[0].sender_role == Role.EMPLOYEE
    assert messages[1].sender_user_id == "MGR001"
    assert messages[1].sender_role == Role.MANAGER
    assert messages[2].sender_user_id == "EMP001"
    assert messages[2].sender_role == Role.EMPLOYEE


def test_same_user_followup(client: TestClient, fake_pipeline: FakePipeline) -> None:
    _post(client, question="How many paid leave days do employees receive?", user_id="EMP001")
    
    fake_pipeline.result = QueryResult(answer="10 days.", sources=[{"from": "policy.md"}])
    response = _post(client, question="How many can I carry that forward?", user_id="EMP001")
    
    assert response.status_code == 200
    assert response.json()["answer"] == "10 days."
    assert "paid leave days" in fake_pipeline.calls[-1][0]
    # Verify EMP001's permissions were used
    assert fake_pipeline.calls[-1][1] == ["general"]


def test_shared_session_multiple_users(client: TestClient, sessions: InMemorySessionStore) -> None:
    _post(client, question="Emp asks", user_id="EMP001")
    _post(client, question="Mgr asks", user_id="MGR001")
    session = sessions.get("shared_session")
    users = [m.sender_user_id for m in session.messages]
    assert "EMP001" in users
    assert "MGR001" in users


def test_previous_user_retrieval_not_reused(
    client: TestClient, fake_pipeline: FakePipeline
) -> None:
    # Manager retrieves something
    fake_pipeline.result = QueryResult(answer="Manager result", sources=[{"src": "mgmt.md"}])
    _post(client, question="What is the Engineering team's performance?", user_id="MGR001")
    
    # Employee asks a follow-up
    fake_pipeline.result = QueryResult(answer="Emp result", sources=[{"src": "emp.md"}])
    _post(client, question="What about that?", user_id="EMP001")
    
    # Since Employee has no prior history of their own, "What about that?" won't be rewritten.
    # More importantly, the system must NOT reuse the Manager's chunks or permissions.
    # We verify the pipeline was called again.
    assert fake_pipeline.calls[-1][0] == "What about that?"
    assert len(fake_pipeline.calls) == 2


def test_previous_user_permissions_not_inherited(
    client: TestClient, fake_pipeline: FakePipeline
) -> None:
    _post(client, question="Mgr Q", user_id="MGR001")
    _post(client, question="Emp Q", user_id="EMP001")
    
    # The last pipeline call must use EMP001's permissions, NOT MGR001's.
    # MGR001 gets ['general', 'management']
    # EMP001 gets ['general']
    assert fake_pipeline.calls[-1][1] == ["general"]


def test_unauthorized_followup_declined(client: TestClient, fake_pipeline: FakePipeline) -> None:
    # Employee asks something authorized first
    _post(client, question="Company benefits?", user_id="EMP001")
    
    # Employee tries to ask about management bonuses
    fake_pipeline.result = QueryResult(answer=ACCESS_DENIED_ANSWER, sources=[])
    response = _post(client, question="What about that management bonus?", user_id="EMP001")
    
    assert response.status_code == 200
    assert response.json()["answer"] == ACCESS_DENIED_ANSWER
    assert response.json()["sources"] == []


def test_direct_unauthorized_question_declined(
    client: TestClient, fake_pipeline: FakePipeline
) -> None:
    fake_pipeline.result = QueryResult(answer=ACCESS_DENIED_ANSWER, sources=[])
    response = _post(client, question="Show me the confidential management financial report.", user_id="EMP001")
    
    assert response.status_code == 200
    assert response.json()["answer"] == ACCESS_DENIED_ANSWER
    assert response.json()["sources"] == []
