"""
Workflow API Integration Tests

Tests for Workflow CRUD and execution REST API endpoints.
"""

import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def clear_workflow_storage():
    """각 테스트 전에 workflow storage 초기화"""
    from src.adapters.inbound.http.routes import workflow

    workflow._workflows.clear()
    yield
    workflow._workflows.clear()


@pytest.fixture
def sample_workflow_data():
    """샘플 Workflow 생성 데이터"""
    return {
        "name": "Test Sequential Workflow",
        "workflow_type": "sequential",
        "description": "Echo then Math workflow",
        "steps": [
            {
                "agent_endpoint_id": "echo-agent-id",
                "output_key": "echo_result",
                "instruction": "Echo the user message",
            },
            {
                "agent_endpoint_id": "math-agent-id",
                "output_key": "math_result",
                "instruction": "Calculate based on echo result",
            },
        ],
    }


class TestWorkflowCreation:
    """Workflow 생성 API 테스트"""

    def test_create_workflow_returns_201(
        self, authenticated_client: TestClient, sample_workflow_data
    ):
        """
        Given: Valid workflow data
        When: POST /api/workflows
        Then: 201 Created with workflow ID
        """
        response = authenticated_client.post("/api/workflows", json=sample_workflow_data)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == sample_workflow_data["name"]
        assert data["workflow_type"] == "sequential"
        assert len(data["steps"]) == 2

    def test_create_workflow_with_invalid_type_returns_422(
        self, authenticated_client: TestClient, sample_workflow_data
    ):
        """
        Given: Workflow with invalid workflow_type
        When: POST /api/workflows
        Then: 422 Unprocessable Entity
        """
        sample_workflow_data["workflow_type"] = "invalid_type"
        response = authenticated_client.post("/api/workflows", json=sample_workflow_data)

        assert response.status_code == 422


class TestWorkflowRetrieval:
    """Workflow 조회 API 테스트"""

    def test_list_workflows_returns_empty_list(self, authenticated_client: TestClient):
        """
        Given: No workflows created
        When: GET /api/workflows
        Then: 200 OK with empty list
        """
        response = authenticated_client.get("/api/workflows")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_workflows_returns_created_workflows(
        self, authenticated_client: TestClient, sample_workflow_data
    ):
        """
        Given: 2 workflows created
        When: GET /api/workflows
        Then: 200 OK with 2 workflows
        """
        # Create 2 workflows
        authenticated_client.post("/api/workflows", json=sample_workflow_data)
        sample_workflow_data["name"] = "Second Workflow"
        authenticated_client.post("/api/workflows", json=sample_workflow_data)

        response = authenticated_client.get("/api/workflows")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_workflow_by_id_returns_workflow(
        self, authenticated_client: TestClient, sample_workflow_data
    ):
        """
        Given: Workflow created
        When: GET /api/workflows/{id}
        Then: 200 OK with workflow details
        """
        create_response = authenticated_client.post("/api/workflows", json=sample_workflow_data)
        workflow_id = create_response.json()["id"]

        response = authenticated_client.get(f"/api/workflows/{workflow_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == workflow_id
        assert data["name"] == sample_workflow_data["name"]

    def test_get_nonexistent_workflow_returns_404(self, authenticated_client: TestClient):
        """
        Given: Workflow ID that doesn't exist
        When: GET /api/workflows/{id}
        Then: 404 Not Found
        """
        fake_id = str(uuid4())
        response = authenticated_client.get(f"/api/workflows/{fake_id}")

        assert response.status_code == 404


class TestWorkflowDeletion:
    """Workflow 삭제 API 테스트"""

    def test_delete_workflow_returns_204(
        self, authenticated_client: TestClient, sample_workflow_data
    ):
        """
        Given: Workflow created
        When: DELETE /api/workflows/{id}
        Then: 204 No Content
        """
        create_response = authenticated_client.post("/api/workflows", json=sample_workflow_data)
        workflow_id = create_response.json()["id"]

        response = authenticated_client.delete(f"/api/workflows/{workflow_id}")

        assert response.status_code == 204

        # Verify deletion
        get_response = authenticated_client.get(f"/api/workflows/{workflow_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_workflow_returns_404(self, authenticated_client: TestClient):
        """
        Given: Workflow ID that doesn't exist
        When: DELETE /api/workflows/{id}
        Then: 404 Not Found
        """
        fake_id = str(uuid4())
        response = authenticated_client.delete(f"/api/workflows/{fake_id}")

        assert response.status_code == 404


class TestWorkflowExecution:
    """Workflow 실행 API 테스트 (SSE 스트리밍)"""

    @pytest.mark.skip(reason="Requires actual A2A agents - will be tested in Step 16 E2E tests")
    def test_execute_workflow_streams_sse_events(
        self, authenticated_client: TestClient, sample_workflow_data
    ):
        """
        Given: Workflow created
        When: POST /api/workflows/{id}/execute
        Then: SSE stream with workflow events

        NOTE: This test requires actual A2A agents to be running.
        Full integration testing will be done in Step 16 E2E tests.
        """
        # Create workflow
        create_response = authenticated_client.post("/api/workflows", json=sample_workflow_data)
        workflow_id = create_response.json()["id"]

        # Execute workflow
        response = authenticated_client.post(
            f"/api/workflows/{workflow_id}/execute",
            json={"message": "Test workflow execution"},
            headers={"Accept": "text/event-stream"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        # Parse SSE events
        events = []
        for line in response.text.strip().split("\n\n"):
            if line.startswith("data: "):
                event_data = json.loads(line[6:])  # Remove "data: " prefix
                events.append(event_data)

        # Verify event sequence
        assert len(events) > 0
        assert events[0]["type"] == "workflow_start"
        assert events[0]["workflow_id"] == workflow_id

        # Should have workflow_complete or done event at the end
        last_event = events[-1]
        assert last_event["type"] in ["workflow_complete", "done"]

    def test_execute_nonexistent_workflow_returns_404(self, authenticated_client: TestClient):
        """
        Given: Workflow ID that doesn't exist
        When: POST /api/workflows/{id}/execute
        Then: 404 Not Found
        """
        fake_id = str(uuid4())
        response = authenticated_client.post(
            f"/api/workflows/{fake_id}/execute",
            json={"message": "Test"},
        )

        assert response.status_code == 404
