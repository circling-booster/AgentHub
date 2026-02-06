"""
Integration tests for /auth/token endpoint

TDD Phase: RED - Tests written before implementation
"""

import pytest


class TestAuthTokenEndpoint:
    """POST /auth/token 통합 테스트 (Origin 검증, 토큰 반환)"""

    @pytest.fixture
    def client(self, http_client):
        """TestClient fixture"""
        return http_client

    def test_valid_chrome_extension_origin_returns_token(self, client):
        """올바른 chrome-extension:// Origin으로 요청 시 토큰 반환"""
        response = client.post(
            "/auth/token",
            json={"extension_id": "test-extension-id"},
            headers={"Origin": "chrome-extension://abcdefghijklmnop"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert isinstance(data["token"], str)
        # Token length: TEST_EXTENSION_TOKEN = "test-extension-token" (20 chars)
        assert len(data["token"]) >= 20

    def test_invalid_origin_returns_403(self, client):
        """웹 Origin으로 요청 시 403 반환 (Drive-by RCE 방지)"""
        response = client.post(
            "/auth/token",
            json={"extension_id": "test-extension-id"},
            headers={"Origin": "https://evil.com"},
        )

        assert response.status_code == 403
        data = response.json()
        assert "error" in data or "detail" in data

    def test_missing_origin_returns_403(self, client):
        """Origin 헤더 누락 시 403 반환"""
        response = client.post(
            "/auth/token",
            json={"extension_id": "test-extension-id"},
        )

        assert response.status_code == 403

    def test_empty_origin_returns_403(self, client):
        """빈 Origin 헤더 시 403 반환"""
        response = client.post(
            "/auth/token",
            json={"extension_id": "test-extension-id"},
            headers={"Origin": ""},
        )

        assert response.status_code == 403

    def test_token_format_is_valid(self, client):
        """반환된 토큰이 올바른 형식 (URL-safe base64)"""
        response = client.post(
            "/auth/token",
            json={"extension_id": "test-extension-id"},
            headers={"Origin": "chrome-extension://valid-id"},
        )

        assert response.status_code == 200
        token = response.json()["token"]

        # URL-safe characters만 포함
        assert all(c.isalnum() or c in "_-" for c in token)

    def test_http_origin_chrome_extension_allowed(self, client):
        """http://localhost에서 chrome-extension 스킴 Origin 허용"""
        response = client.post(
            "/auth/token",
            json={"extension_id": "test-ext"},
            headers={"Origin": "chrome-extension://anothervalidid"},
        )

        assert response.status_code == 200

    def test_missing_extension_id_returns_422(self, client):
        """extension_id 누락 시 422 Unprocessable Entity"""
        response = client.post(
            "/auth/token",
            json={},
            headers={"Origin": "chrome-extension://valid-id"},
        )

        assert response.status_code == 422

    def test_different_extension_ids_return_same_token(self, client):
        """서버당 1개 토큰만 존재 (extension_id 무관)"""
        response1 = client.post(
            "/auth/token",
            json={"extension_id": "ext-1"},
            headers={"Origin": "chrome-extension://id1"},
        )

        response2 = client.post(
            "/auth/token",
            json={"extension_id": "ext-2"},
            headers={"Origin": "chrome-extension://id2"},
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        token1 = response1.json()["token"]
        token2 = response2.json()["token"]

        # 동일 서버 인스턴스에서는 동일 토큰
        assert token1 == token2
