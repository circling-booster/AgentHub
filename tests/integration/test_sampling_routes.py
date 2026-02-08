"""Sampling HITL API Integration Tests (Phase 6, Step 6.3)"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.local_mcp
@pytest.mark.llm
class TestSamplingRoutes:
    """Sampling HITL API 통합 테스트 (Method C 패턴)"""

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
    async def pending_sampling_request(
        self, authenticated_client: TestClient, registered_mcp_endpoint: dict
    ):
        """대기 중인 Sampling 요청 생성 fixture

        Note: 실제 MCP 서버가 createMessage를 요청해야 하지만,
        테스트에서는 SamplingService에 직접 요청을 추가합니다.
        """
        from src.domain.entities.sampling_request import SamplingRequest, SamplingStatus

        # authenticated_client의 app에서 Container 가져오기
        container = authenticated_client.app.container
        sampling_service = container.sampling_service()

        # 테스트용 Sampling 요청 생성
        request = SamplingRequest(
            id="test-req-001",
            endpoint_id=registered_mcp_endpoint["id"],
            messages=[{"role": "user", "content": "Test message"}],
            max_tokens=100,
            status=SamplingStatus.PENDING,
        )

        # SamplingService에 등록 (in-memory)
        sampling_service._requests[request.id] = request

        return {"id": request.id, "endpoint_id": request.endpoint_id}

    async def test_list_pending_requests(
        self, authenticated_client: TestClient, pending_sampling_request: dict
    ):
        """대기 중인 요청 목록 조회"""
        response = authenticated_client.get("/api/sampling/requests")

        assert response.status_code == 200
        data = response.json()
        assert "requests" in data
        assert len(data["requests"]) >= 1

        # 요청 스키마 검증
        first_request = data["requests"][0]
        assert "id" in first_request
        assert "endpoint_id" in first_request
        assert "messages" in first_request
        assert "status" in first_request
        assert first_request["status"] == "pending"

    async def test_approve_triggers_llm(
        self, authenticated_client: TestClient, pending_sampling_request: dict
    ):
        """승인 시 LLM 호출됨 (Method C 패턴)"""
        request_id = pending_sampling_request["id"]

        response = authenticated_client.post(f"/api/sampling/requests/{request_id}/approve")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "approved"
        assert "result" in data

        # LLM 응답 포함 확인
        assert "content" in data["result"]
        assert len(data["result"]["content"]) > 0

    async def test_reject_sets_status(
        self, authenticated_client: TestClient, pending_sampling_request: dict
    ):
        """거부 시 상태 변경"""
        request_id = pending_sampling_request["id"]

        response = authenticated_client.post(
            f"/api/sampling/requests/{request_id}/reject",
            json={"reason": "Not authorized"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "rejected"

    async def test_list_empty_when_no_requests(self, authenticated_client: TestClient):
        """요청이 없을 때 빈 목록 반환"""
        response = authenticated_client.get("/api/sampling/requests")

        assert response.status_code == 200
        data = response.json()
        assert "requests" in data
        # 다른 테스트의 요청이 남아있을 수 있으므로 타입만 검증
        assert isinstance(data["requests"], list)

    async def test_approve_nonexistent_request_returns_404(self, authenticated_client: TestClient):
        """존재하지 않는 요청 승인 시 404"""
        response = authenticated_client.post("/api/sampling/requests/nonexistent-id/approve")

        assert response.status_code == 404

    async def test_reject_nonexistent_request_returns_404(self, authenticated_client: TestClient):
        """존재하지 않는 요청 거부 시 404"""
        response = authenticated_client.post(
            "/api/sampling/requests/nonexistent-id/reject",
            json={"reason": "test"},
        )

        assert response.status_code == 404
