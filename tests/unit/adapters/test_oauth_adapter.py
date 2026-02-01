"""
Unit tests for OAuth Adapter

Step 8: OAuth 2.1 Flow - Adapter TDD
"""

from unittest.mock import MagicMock, patch

import pytest

from src.adapters.outbound.oauth.oauth_adapter import HttpxOAuthAdapter
from src.domain.entities.auth_config import AuthConfig
from src.domain.exceptions import OAuthTokenExchangeError, OAuthTokenRefreshError


class TestHttpxOAuthAdapter:
    """httpx 기반 OAuth Adapter 단위 테스트"""

    @pytest.fixture
    def oauth_adapter(self):
        """OAuthAdapter 인스턴스"""
        return HttpxOAuthAdapter()

    @pytest.fixture
    def auth_config(self):
        """OAuth 2.1 AuthConfig 테스트 데이터"""
        return AuthConfig(
            auth_type="oauth2",
            oauth2_client_id="test-client-id",
            oauth2_client_secret="test-client-secret",
            oauth2_token_url="https://example.com/oauth/token",
            oauth2_authorize_url="https://example.com/oauth/authorize",
            oauth2_scope="read write",
            oauth2_refresh_token="current-refresh-token",
        )

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(self, oauth_adapter, auth_config):
        """
        Authorization Code → Access Token 교환 성공

        Given: 유효한 authorization code
        When: exchange_code_for_token() 호출
        Then: Access Token 반환
        """
        # Given
        code = "valid-auth-code"
        redirect_uri = "http://localhost:8000/oauth/callback"

        mock_response = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

        # When
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json = MagicMock(return_value=mock_response)
            mock_post.return_value = mock_resp

            result = await oauth_adapter.exchange_code_for_token(
                code=code,
                auth_config=auth_config,
                redirect_uri=redirect_uri,
            )

        # Then
        assert result.access_token == "new-access-token"
        assert result.refresh_token == "new-refresh-token"
        assert result.expires_in == 3600
        assert result.token_type == "Bearer"

        # HTTP 요청 검증
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://example.com/oauth/token"
        assert call_args[1]["data"]["code"] == code
        assert call_args[1]["data"]["client_id"] == "test-client-id"
        assert call_args[1]["data"]["client_secret"] == "test-client-secret"
        assert call_args[1]["data"]["redirect_uri"] == redirect_uri

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_failure(self, oauth_adapter, auth_config):
        """
        Authorization Code 교환 실패 (401 Unauthorized)

        Given: 잘못된 authorization code
        When: exchange_code_for_token() 호출
        Then: OAuthTokenExchangeError 발생
        """
        # Given
        code = "invalid-code"
        redirect_uri = "http://localhost:8000/oauth/callback"

        # When/Then
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 401
            mock_resp.text = "Unauthorized"
            mock_post.return_value = mock_resp

            with pytest.raises(OAuthTokenExchangeError):
                await oauth_adapter.exchange_code_for_token(
                    code=code,
                    auth_config=auth_config,
                    redirect_uri=redirect_uri,
                )

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, oauth_adapter, auth_config):
        """
        Refresh Token으로 Access Token 갱신 성공

        Given: 유효한 refresh_token
        When: refresh_access_token() 호출
        Then: 새 Access Token 반환
        """
        # Given
        mock_response = {
            "access_token": "refreshed-access-token",
            "refresh_token": "refreshed-refresh-token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

        # When
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json = MagicMock(return_value=mock_response)
            mock_post.return_value = mock_resp

            result = await oauth_adapter.refresh_access_token(auth_config)

        # Then
        assert result.access_token == "refreshed-access-token"
        assert result.refresh_token == "refreshed-refresh-token"
        assert result.expires_in == 3600

        # HTTP 요청 검증
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://example.com/oauth/token"
        assert call_args[1]["data"]["grant_type"] == "refresh_token"
        assert call_args[1]["data"]["refresh_token"] == "current-refresh-token"
        assert call_args[1]["data"]["client_id"] == "test-client-id"

    @pytest.mark.asyncio
    async def test_refresh_access_token_failure(self, oauth_adapter, auth_config):
        """
        Refresh Token 갱신 실패 (400 Bad Request)

        Given: 만료되거나 잘못된 refresh_token
        When: refresh_access_token() 호출
        Then: OAuthTokenRefreshError 발생
        """
        # When/Then
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 400
            mock_resp.text = "Invalid refresh token"
            mock_post.return_value = mock_resp

            with pytest.raises(OAuthTokenRefreshError):
                await oauth_adapter.refresh_access_token(auth_config)
