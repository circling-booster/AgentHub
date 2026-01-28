"""
Integration tests for /health endpoint

TDD Phase: RED - Tests written before implementation
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """GET /health 통합 테스트 (토큰 불필요, 서버 상태 확인)"""

    @pytest.fixture
    def client(self, http_client):
        """TestClient fixture"""
        return http_client

    def test_health_endpoint_returns_200(self, client):
        """Health endpoint가 200 OK 반환"""
        response = client.get("/health")

        assert response.status_code == 200

    def test_health_returns_status_and_version(self, client):
        """Health endpoint가 status와 version 정보 포함"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] in ["healthy", "ok"]
        assert "version" in data
        assert isinstance(data["version"], str)

    def test_health_no_token_required(self, client):
        """Health endpoint는 토큰 없이 접근 가능"""
        response = client.get(
            "/health",
            headers={},  # X-Extension-Token 없음
        )

        assert response.status_code == 200

    def test_health_with_invalid_token_still_works(self, client):
        """Health endpoint는 잘못된 토큰이 있어도 동작"""
        response = client.get(
            "/health",
            headers={"X-Extension-Token": "invalid-token"},
        )

        assert response.status_code == 200

    def test_health_response_format(self, client):
        """Health 응답이 올바른 JSON 형식"""
        response = client.get("/health")

        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)
