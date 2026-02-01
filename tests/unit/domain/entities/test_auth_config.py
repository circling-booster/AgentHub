"""
Tests for AuthConfig domain entity

TDD Red Phase: 인증 설정 엔티티 테스트
"""

from src.domain.entities.auth_config import AuthConfig


class TestAuthConfigNone:
    """인증 없음 (auth_type=none)"""

    def test_none_returns_empty_headers(self):
        """인증 타입이 none이면 빈 헤더 반환"""
        # Given
        auth = AuthConfig(auth_type="none")

        # When
        headers = auth.get_auth_headers()

        # Then
        assert headers == {}


class TestAuthConfigHeader:
    """커스텀 헤더 인증 (auth_type=header)"""

    def test_header_returns_custom_headers(self):
        """커스텀 헤더를 그대로 반환"""
        # Given
        auth = AuthConfig(
            auth_type="header",
            headers={"X-API-Key": "secret123", "X-Custom": "value"},
        )

        # When
        headers = auth.get_auth_headers()

        # Then
        assert headers == {"X-API-Key": "secret123", "X-Custom": "value"}

    def test_header_empty_dict_if_no_headers(self):
        """헤더가 없으면 빈 dict 반환"""
        # Given
        auth = AuthConfig(auth_type="header", headers={})

        # When
        headers = auth.get_auth_headers()

        # Then
        assert headers == {}


class TestAuthConfigApiKey:
    """API Key 인증 (auth_type=api_key)"""

    def test_api_key_returns_bearer_header(self):
        """기본 Bearer 프리픽스로 Authorization 헤더 생성"""
        # Given
        auth = AuthConfig(
            auth_type="api_key",
            api_key="my-secret-key",
            api_key_header="Authorization",
            api_key_prefix="Bearer",
        )

        # When
        headers = auth.get_auth_headers()

        # Then
        assert headers == {"Authorization": "Bearer my-secret-key"}

    def test_api_key_custom_header_name(self):
        """커스텀 헤더 이름 사용 가능"""
        # Given
        auth = AuthConfig(
            auth_type="api_key",
            api_key="key123",
            api_key_header="X-API-Key",
            api_key_prefix="",
        )

        # When
        headers = auth.get_auth_headers()

        # Then
        assert headers == {"X-API-Key": "key123"}

    def test_api_key_custom_prefix(self):
        """커스텀 프리픽스 사용 가능"""
        # Given
        auth = AuthConfig(
            auth_type="api_key",
            api_key="abc123",
            api_key_header="Authorization",
            api_key_prefix="ApiKey",
        )

        # When
        headers = auth.get_auth_headers()

        # Then
        assert headers == {"Authorization": "ApiKey abc123"}

    def test_api_key_no_prefix(self):
        """프리픽스 없이 raw key만 전달 가능"""
        # Given
        auth = AuthConfig(
            auth_type="api_key",
            api_key="raw-key",
            api_key_header="X-API-Key",
            api_key_prefix="",
        )

        # When
        headers = auth.get_auth_headers()

        # Then
        assert headers == {"X-API-Key": "raw-key"}


class TestAuthConfigOAuth2:
    """OAuth 2.0 인증 (auth_type=oauth2)"""

    def test_oauth2_returns_access_token_header(self):
        """access_token이 있으면 Bearer 헤더 반환"""
        # Given
        auth = AuthConfig(
            auth_type="oauth2",
            oauth2_access_token="access-token-xyz",
        )

        # When
        headers = auth.get_auth_headers()

        # Then
        assert headers == {"Authorization": "Bearer access-token-xyz"}

    def test_oauth2_no_token_returns_empty(self):
        """access_token이 없으면 빈 헤더 반환"""
        # Given
        auth = AuthConfig(
            auth_type="oauth2",
            oauth2_access_token="",
        )

        # When
        headers = auth.get_auth_headers()

        # Then
        assert headers == {}


class TestAuthConfigDefaults:
    """기본값 테스트"""

    def test_default_auth_type_is_none(self):
        """기본 인증 타입은 none"""
        # Given/When
        auth = AuthConfig()

        # Then
        assert auth.auth_type == "none"
        assert auth.get_auth_headers() == {}

    def test_default_api_key_header_is_authorization(self):
        """기본 API Key 헤더는 Authorization"""
        # Given/When
        auth = AuthConfig()

        # Then
        assert auth.api_key_header == "Authorization"

    def test_default_api_key_prefix_is_bearer(self):
        """기본 API Key 프리픽스는 Bearer"""
        # Given/When
        auth = AuthConfig()

        # Then
        assert auth.api_key_prefix == "Bearer"
