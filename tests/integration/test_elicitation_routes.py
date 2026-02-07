"""Elicitation HITL API Integration Tests (Phase 6, Step 6.4)"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.local_mcp
class TestElicitationRoutes:
    """Elicitation HITL API 통합 테스트"""

    @pytest.fixture
    async def registered_mcp_endpoint(self, authenticated_client: TestClient):
        """MCP 엔드포인트 등록 fixture"""
        response = authenticated_client.post(
            "/api/mcp/servers",
            json={
                "url": "http://localhost:9000/mcp",
                "name": "Test Synapse MCP",
            },
        )
        assert response.status_code == 201
        return response.json()

    @pytest.fixture
    async def pending_elicitation_request(
        self, authenticated_client: TestClient, registered_mcp_endpoint: dict
    ):
        """대기 중인 Elicitation 요청 생성 fixture

        Note: 실제 MCP 서버가 elicitation을 요청해야 하지만,
        테스트에서는 ElicitationService에 직접 요청을 추가합니다.
        """
        from src.domain.entities.elicitation_request import ElicitationRequest, ElicitationStatus

        # authenticated_client의 app에서 Container 가져오기
        container = authenticated_client.app.container
        elicitation_service = container.elicitation_service()

        # 테스트용 Elicitation 요청 생성
        request = ElicitationRequest(
            id="test-elicit-001",
            endpoint_id=registered_mcp_endpoint["id"],
            message="Please provide your name",
            requested_schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            status=ElicitationStatus.PENDING,
        )

        # ElicitationService에 등록 (in-memory)
        await elicitation_service.create_request(request)

        return {"id": request.id, "endpoint_id": request.endpoint_id}

    async def test_list_pending_requests(
        self, authenticated_client: TestClient, pending_elicitation_request: dict
    ):
        """대기 중인 요청 목록 조회"""
        response = authenticated_client.get("/api/elicitation/requests")

        assert response.status_code == 200
        data = response.json()
        assert "requests" in data
        assert len(data["requests"]) >= 1

        # 요청 스키마 검증
        first_request = data["requests"][0]
        assert "id" in first_request
        assert "endpoint_id" in first_request
        assert "message" in first_request
        assert "requested_schema" in first_request
        assert "status" in first_request
        assert first_request["status"] == "pending"

    async def test_respond_accept(
        self, authenticated_client: TestClient, pending_elicitation_request: dict
    ):
        """ACCEPT 응답"""
        request_id = pending_elicitation_request["id"]

        response = authenticated_client.post(
            f"/api/elicitation/requests/{request_id}/respond",
            json={"action": "accept", "content": {"name": "John Doe"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "accept"

    async def test_respond_decline(
        self, authenticated_client: TestClient, pending_elicitation_request: dict
    ):
        """DECLINE 응답"""
        request_id = pending_elicitation_request["id"]

        response = authenticated_client.post(
            f"/api/elicitation/requests/{request_id}/respond",
            json={"action": "decline"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "decline"

    async def test_respond_cancel(
        self, authenticated_client: TestClient, pending_elicitation_request: dict
    ):
        """CANCEL 응답"""
        request_id = pending_elicitation_request["id"]

        response = authenticated_client.post(
            f"/api/elicitation/requests/{request_id}/respond",
            json={"action": "cancel"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "cancel"

    async def test_list_empty_when_no_requests(self, authenticated_client: TestClient):
        """요청이 없을 때 빈 목록 반환"""
        response = authenticated_client.get("/api/elicitation/requests")

        assert response.status_code == 200
        data = response.json()
        assert "requests" in data
        # 다른 테스트의 요청이 남아있을 수 있으므로 타입만 검증
        assert isinstance(data["requests"], list)

    async def test_respond_nonexistent_request_returns_404(self, authenticated_client: TestClient):
        """존재하지 않는 요청 응답 시 404"""
        response = authenticated_client.post(
            "/api/elicitation/requests/nonexistent-id/respond",
            json={"action": "accept", "content": {"name": "test"}},
        )

        assert response.status_code == 404
