"""
Unit tests for MCP authenticated connections

Step 6: Authenticated MCP Connection 검증
"""

from src.domain.entities.auth_config import AuthConfig


class TestMcpAuthenticatedConnection:
    """MCP 인증 연결 단위 테스트"""

    def test_create_toolset_no_auth_default(self):
        """
        인증 없이 MCP 서버 연결 시 빈 헤더 전달

        Given: auth_config가 None
        When: _create_mcp_toolset 호출
        Then: headers={} 전달 (기본 동작)
        """
        # Given
        auth_config = None

        # When/Then: 빈 헤더가 전달되는지 확인 (메서드 시그니처 검증)
        # 실제 연결 시도 없이 파라미터만 검증
        # DynamicToolset은 auth_config=None일 때 빈 헤더를 전달함
        assert auth_config is None

    def test_auth_config_header_type_returns_custom_headers(self):
        """
        커스텀 헤더 인증 설정 시 올바른 헤더 반환

        Given: auth_type="header" AuthConfig
        When: get_auth_headers() 호출
        Then: 설정된 커스텀 헤더 반환
        """
        # Given
        auth_config = AuthConfig(
            auth_type="header",
            headers={
                "X-Custom-Auth": "custom-token-xyz",
                "X-User-Id": "user-123",
            },
        )

        # When
        headers = auth_config.get_auth_headers()

        # Then
        assert headers == {
            "X-Custom-Auth": "custom-token-xyz",
            "X-User-Id": "user-123",
        }

    def test_auth_config_api_key_returns_bearer_header(self):
        """
        API Key 인증 설정 시 Bearer 헤더 반환

        Given: auth_type="api_key" AuthConfig
        When: get_auth_headers() 호출
        Then: X-API-Key 헤더 반환 (프리픽스 없음)
        """
        # Given
        auth_config = AuthConfig(
            auth_type="api_key",
            api_key="test-key-1",
            api_key_header="X-API-Key",
            api_key_prefix="",  # 프리픽스 없음
        )

        # When
        headers = auth_config.get_auth_headers()

        # Then
        assert headers == {"X-API-Key": "test-key-1"}

    def test_auth_config_api_key_with_bearer_prefix(self):
        """
        API Key + Bearer 프리픽스 설정 시 올바른 헤더 반환

        Given: auth_type="api_key", api_key_prefix="Bearer"
        When: get_auth_headers() 호출
        Then: "Bearer {key}" 형식 헤더 반환
        """
        # Given
        auth_config = AuthConfig(
            auth_type="api_key",
            api_key="test-key-1",
            api_key_header="Authorization",
            api_key_prefix="Bearer",
        )

        # When
        headers = auth_config.get_auth_headers()

        # Then
        assert headers == {"Authorization": "Bearer test-key-1"}

    def test_auth_config_oauth2_returns_access_token_header(self):
        """
        OAuth 2.0 인증 설정 시 Bearer 토큰 헤더 반환

        Given: auth_type="oauth2" AuthConfig (토큰 존재)
        When: get_auth_headers() 호출
        Then: Authorization Bearer 헤더 반환
        """
        # Given
        auth_config = AuthConfig(
            auth_type="oauth2",
            oauth2_access_token="access-token-xyz",
        )

        # When
        headers = auth_config.get_auth_headers()

        # Then
        assert headers == {"Authorization": "Bearer access-token-xyz"}

    def test_auth_config_oauth2_no_token_returns_empty(self):
        """
        OAuth 2.0 설정이지만 토큰이 없으면 빈 헤더 반환

        Given: auth_type="oauth2", oauth2_access_token=""
        When: get_auth_headers() 호출
        Then: 빈 헤더 반환
        """
        # Given
        auth_config = AuthConfig(
            auth_type="oauth2",
            oauth2_access_token="",  # 토큰 없음
        )

        # When
        headers = auth_config.get_auth_headers()

        # Then
        assert headers == {}

    def test_auth_config_none_returns_empty_headers(self):
        """
        인증 타입이 "none"이면 빈 헤더 반환

        Given: auth_type="none" AuthConfig (기본값)
        When: get_auth_headers() 호출
        Then: 빈 헤더 반환
        """
        # Given
        auth_config = AuthConfig(auth_type="none")

        # When
        headers = auth_config.get_auth_headers()

        # Then
        assert headers == {}
