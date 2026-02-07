"""
MCP Registration API with Authentication - Integration Tests
"""

import pytest


class TestMcpAuthApi:
    """MCP 서버 등록 API 인증 테스트"""

    @pytest.mark.skip(
        reason="Known MCP SDK bug: anyio cancel scope error with authenticated servers. "
        "See: https://github.com/modelcontextprotocol/python-sdk/issues/521, "
        "https://github.com/google/adk-python/issues/2196"
    )
    async def test_register_mcp_with_api_key_via_api(self, authenticated_client):
        """
        API Key 인증으로 MCP 서버 등록

        Given: API Key 인증 설정
        When: MCP 서버 등록 요청
        Then: auth_config가 포함된 엔드포인트 생성

        Note: Skipped due to MCP SDK anyio cancel scope bug when connecting to
        authenticated servers (port 9001). This causes "RuntimeError: No response
        returned" and "Attempted to exit cancel scope in a different task" errors.
        Will be re-enabled when MCP SDK fixes the issue.
        """
        client = authenticated_client
        # Given
        request_data = {
            "url": "http://127.0.0.1:9001/mcp",
            "name": "Auth MCP Server",
            "auth": {
                "auth_type": "api_key",
                "api_key": "test-key-1",  # Synapse conftest의 실제 API Key
                "api_key_header": "X-API-Key",
                "api_key_prefix": "",
            },
        }

        # When
        response = client.post("/api/mcp/servers", json=request_data)

        # Then
        assert response.status_code == 201  # HTTP 201 Created
        data = response.json()
        assert data["url"] == "http://127.0.0.1:9001/mcp"
        assert data["name"] == "Auth MCP Server"
        # auth_config는 응답에 포함되지 않음 (보안상)

        # 등록된 서버 목록에서 확인
        response = client.get("/api/mcp/servers")
        assert response.status_code == 200
        servers = response.json()
        assert len(servers) == 1
        assert servers[0]["url"] == "http://127.0.0.1:9001/mcp"

    async def test_register_mcp_with_custom_headers_via_api(self, authenticated_client):
        """
        커스텀 헤더 인증으로 MCP 서버 등록

        Given: 커스텀 헤더 인증 설정
        When: MCP 서버 등록 요청
        Then: auth_config가 포함된 엔드포인트 생성
        """
        client = authenticated_client
        # Given
        # Port 9000 (무인증)에 커스텀 헤더 추가 테스트
        # 실제로는 무시되지만, AuthConfig 구조 검증용
        request_data = {
            "url": "http://127.0.0.1:9000/mcp",
            "name": "Custom Header MCP",
            "auth": {
                "auth_type": "header",
                "headers": {
                    "X-Custom-Auth": "custom-token-xyz",
                    "X-User-Id": "user-123",
                },
            },
        }

        # When
        response = client.post("/api/mcp/servers", json=request_data)

        # Then
        assert response.status_code == 201  # HTTP 201 Created
        data = response.json()
        assert data["url"] == "http://127.0.0.1:9000/mcp"
        assert data["name"] == "Custom Header MCP"

    async def test_register_mcp_without_auth_backwards_compatible(self, authenticated_client):
        """
        인증 없는 MCP 서버 등록 (하위 호환성)

        Given: auth 필드 없는 요청
        When: MCP 서버 등록 요청
        Then: 정상적으로 등록 (auth_type="none")
        """
        client = authenticated_client
        # Given
        request_data = {
            "url": "http://127.0.0.1:9000/mcp",
            "name": "No Auth MCP Server",
            # auth 필드 없음 (하위 호환성)
        }

        # When
        response = client.post("/api/mcp/servers", json=request_data)

        # Then
        assert response.status_code == 201  # HTTP 201 Created
        data = response.json()
        assert data["url"] == "http://127.0.0.1:9000/mcp"
        assert data["name"] == "No Auth MCP Server"
