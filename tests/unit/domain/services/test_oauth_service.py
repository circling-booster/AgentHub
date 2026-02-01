"""
Unit tests for OAuth 2.1 Service

Step 8: OAuth 2.1 Flow - TDD Red Phase
"""

import time

import pytest

from src.domain.entities.auth_config import AuthConfig
from src.domain.services.oauth_service import OAuthService


class TestOAuthService:
    """OAuth 2.1 도메인 서비스 단위 테스트"""

    @pytest.fixture
    def oauth_service(self):
        """OAuthService 인스턴스"""
        return OAuthService()

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
            oauth2_access_token="current-access-token",
            oauth2_refresh_token="current-refresh-token",
            oauth2_token_expires_at=time.time() + 3600,  # 1시간 후
        )

    def test_build_authorize_url(self, oauth_service, auth_config):
        """
        Authorization URL 생성

        Given: OAuth 2.1 AuthConfig와 state 값
        When: build_authorize_url() 호출
        Then: 올바른 Authorization URL 반환 (client_id, redirect_uri, scope, state 포함)
        """
        # Given
        state = "random-state-token"

        # When
        url = oauth_service.build_authorize_url(auth_config, state)

        # Then
        assert url.startswith("https://example.com/oauth/authorize?")
        assert "client_id=test-client-id" in url
        assert "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Foauth%2Fcallback" in url
        assert "response_type=code" in url
        assert "scope=read+write" in url
        assert f"state={state}" in url

    def test_is_token_expired_returns_false_for_valid_token(self, oauth_service, auth_config):
        """
        유효한 토큰은 만료되지 않음

        Given: 1시간 후 만료되는 토큰
        When: is_token_expired() 호출
        Then: False 반환 (30초 여유 고려)
        """
        # When
        result = oauth_service.is_token_expired(auth_config)

        # Then
        assert result is False

    def test_is_token_expired_returns_true_for_expired_token(self, oauth_service):
        """
        만료된 토큰은 만료로 판정

        Given: 1분 전 만료된 토큰
        When: is_token_expired() 호출
        Then: True 반환
        """
        # Given
        expired_config = AuthConfig(
            auth_type="oauth2",
            oauth2_access_token="expired-token",
            oauth2_token_expires_at=time.time() - 60,  # 1분 전
        )

        # When
        result = oauth_service.is_token_expired(expired_config)

        # Then
        assert result is True

    def test_is_token_expired_returns_true_for_near_expiry(self, oauth_service):
        """
        30초 이내 만료 예정 토큰은 만료로 판정 (여유 시간)

        Given: 20초 후 만료되는 토큰
        When: is_token_expired() 호출
        Then: True 반환 (30초 여유)
        """
        # Given
        near_expiry_config = AuthConfig(
            auth_type="oauth2",
            oauth2_access_token="near-expiry-token",
            oauth2_token_expires_at=time.time() + 20,  # 20초 후
        )

        # When
        result = oauth_service.is_token_expired(near_expiry_config)

        # Then
        assert result is True

    def test_needs_refresh_returns_true_when_expired_and_refresh_token_exists(self, oauth_service):
        """
        만료되고 refresh_token이 있으면 갱신 필요

        Given: 만료된 토큰 + refresh_token 존재
        When: needs_refresh() 호출
        Then: True 반환
        """
        # Given
        expired_with_refresh = AuthConfig(
            auth_type="oauth2",
            oauth2_access_token="expired-token",
            oauth2_refresh_token="valid-refresh-token",
            oauth2_token_expires_at=time.time() - 60,  # 1분 전
        )

        # When
        result = oauth_service.needs_refresh(expired_with_refresh)

        # Then
        assert result is True

    def test_needs_refresh_returns_false_when_token_valid(self, oauth_service, auth_config):
        """
        토큰이 유효하면 갱신 불필요

        Given: 유효한 토큰
        When: needs_refresh() 호출
        Then: False 반환
        """
        # When
        result = oauth_service.needs_refresh(auth_config)

        # Then
        assert result is False

    def test_needs_refresh_returns_false_when_no_refresh_token(self, oauth_service):
        """
        refresh_token이 없으면 갱신 불가

        Given: 만료된 토큰 + refresh_token 없음
        When: needs_refresh() 호출
        Then: False 반환 (갱신 불가)
        """
        # Given
        expired_no_refresh = AuthConfig(
            auth_type="oauth2",
            oauth2_access_token="expired-token",
            oauth2_refresh_token="",  # 없음
            oauth2_token_expires_at=time.time() - 60,  # 1분 전
        )

        # When
        result = oauth_service.needs_refresh(expired_no_refresh)

        # Then
        assert result is False
