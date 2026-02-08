"""
Unit tests for security components (TokenProvider, ExtensionAuthMiddleware)

TDD Phase: RED - Tests written before implementation
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import Request, Response
from fastapi.responses import JSONResponse


class TestTokenProvider:
    """TokenProvider 단위 테스트 (보안 토큰 생성 및 관리)"""

    def test_token_is_generated_on_first_access(self):
        """첫 접근 시 토큰이 자동 생성됨"""
        from adapters.inbound.http.security import TokenProvider

        provider = TokenProvider()
        token = provider.get_token()

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_is_cryptographically_secure(self):
        """생성된 토큰이 암호학적으로 안전한 길이를 가짐 (43+ chars)"""
        from adapters.inbound.http.security import TokenProvider

        provider = TokenProvider()
        token = provider.get_token()

        # secrets.token_urlsafe(32)는 43-44 chars 생성
        assert len(token) >= 43
        # URL-safe characters만 포함 (a-zA-Z0-9_-)
        assert all(c.isalnum() or c in "_-" for c in token)

    def test_token_is_consistent_during_session(self):
        """세션 중 동일한 토큰 반환 (싱글톤 동작)"""
        from adapters.inbound.http.security import TokenProvider

        provider = TokenProvider()
        token1 = provider.get_token()
        token2 = provider.get_token()

        assert token1 == token2

    def test_reset_allows_token_injection(self):
        """reset() 메서드로 테스트용 토큰 주입 가능"""
        from adapters.inbound.http.security import TokenProvider

        provider = TokenProvider()
        original_token = provider.get_token()

        test_token = "test-token-12345"
        provider.reset(test_token)

        assert provider.get_token() == test_token
        assert provider.get_token() != original_token

    def test_reset_without_value_generates_new_token(self):
        """reset() 인자 없이 호출 시 새 토큰 생성"""
        from adapters.inbound.http.security import TokenProvider

        provider = TokenProvider()
        token1 = provider.get_token()

        provider.reset()
        token2 = provider.get_token()

        assert token1 != token2
        assert len(token2) >= 43


class TestExtensionAuthMiddleware:
    """ExtensionAuthMiddleware 단위 테스트 (/api/* 경로 토큰 검증)"""

    @pytest.fixture
    def mock_token_provider(self):
        """TokenProvider Mock"""
        with patch("adapters.inbound.http.security.get_extension_token") as mock:
            mock.return_value = "valid-test-token"
            yield mock

    @pytest.fixture
    def mock_settings(self):
        """Settings Mock - DEV_MODE를 False로 설정하여 토큰 검증 강제"""
        mock_settings_instance = Mock()
        mock_settings_instance.dev_mode = False
        with patch("src.config.settings.Settings") as mock_settings_cls:
            mock_settings_cls.return_value = mock_settings_instance
            yield mock_settings_instance

    @pytest.fixture
    def middleware(self, mock_token_provider, mock_settings):
        """Middleware 인스턴스"""
        from adapters.inbound.http.security import ExtensionAuthMiddleware

        app_mock = Mock()
        return ExtensionAuthMiddleware(app_mock)

    async def test_api_request_without_token_returns_403(self, middleware):
        """토큰 없이 /api/* 요청 시 403 반환"""
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/chat/stream"
        mock_request.headers.get = Mock(return_value=None)

        call_next = AsyncMock()

        response = await middleware.dispatch(mock_request, call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 403
        call_next.assert_not_called()

    async def test_api_request_with_invalid_token_returns_403(self, middleware):
        """잘못된 토큰으로 /api/* 요청 시 403 반환"""
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/mcp/servers"
        mock_request.headers.get = Mock(return_value="invalid-token")

        call_next = AsyncMock()

        response = await middleware.dispatch(mock_request, call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 403
        call_next.assert_not_called()

    async def test_api_request_with_valid_token_passes(self, middleware):
        """올바른 토큰으로 /api/* 요청 시 통과"""
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/chat/stream"
        mock_request.headers.get = Mock(return_value="valid-test-token")

        expected_response = Response(status_code=200)
        call_next = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert response == expected_response
        call_next.assert_called_once_with(mock_request)

    @pytest.mark.parametrize(
        "path",
        [
            "/health",
            "/auth/token",
            "/docs",
            "/redoc",
            "/openapi.json",
        ],
    )
    async def test_excluded_paths_bypass_auth(self, middleware, path):
        """제외 경로는 토큰 검증 생략"""
        mock_request = Mock(spec=Request)
        mock_request.url.path = path
        mock_request.headers.get = Mock(return_value=None)  # 토큰 없음

        expected_response = Response(status_code=200)
        call_next = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert response == expected_response
        call_next.assert_called_once_with(mock_request)

    async def test_non_api_path_bypasses_auth(self, middleware):
        """/api/* 아닌 경로는 토큰 검증 생략"""
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/some/other/path"
        mock_request.headers.get = Mock(return_value=None)

        expected_response = Response(status_code=200)
        call_next = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert response == expected_response
        call_next.assert_called_once_with(mock_request)

    async def test_error_response_includes_json_body(self, middleware):
        """403 응답이 올바른 JSON 구조 포함"""
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/tools/call"
        mock_request.headers.get = Mock(return_value=None)

        call_next = AsyncMock()

        response = await middleware.dispatch(mock_request, call_next)

        assert isinstance(response, JSONResponse)
        # body는 bytes로 인코딩되므로 디코드 필요
        import json

        body = json.loads(response.body.decode())
        assert "error" in body
        assert body["error"] == "Unauthorized"
        assert "message" in body
