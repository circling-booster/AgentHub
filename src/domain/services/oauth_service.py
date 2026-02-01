"""
OAuth 2.1 Service (Domain Layer)

순수 Python 도메인 로직 - 외부 의존성 없음
"""

import time
from urllib.parse import urlencode

from src.domain.entities.auth_config import AuthConfig

# 토큰 만료 여유 시간 (초)
# 토큰이 실제 만료되기 전에 갱신 시작
TOKEN_EXPIRY_BUFFER_SECONDS = 30


class OAuthService:
    """
    OAuth 2.1 도메인 서비스

    책임:
    - Authorization URL 생성
    - 토큰 만료 여부 검증
    - 토큰 갱신 필요 여부 판정
    """

    def build_authorize_url(self, auth_config: AuthConfig, state: str) -> str:
        """
        OAuth Authorization URL 생성

        Args:
            auth_config: OAuth 설정 (client_id, authorize_url, scope 포함)
            state: CSRF 방지용 state 파라미터

        Returns:
            Authorization URL (쿼리 파라미터 포함)
        """
        params = {
            "client_id": auth_config.oauth2_client_id,
            "redirect_uri": "http://localhost:8000/oauth/callback",
            "response_type": "code",
            "scope": auth_config.oauth2_scope,
            "state": state,
        }
        return f"{auth_config.oauth2_authorize_url}?{urlencode(params)}"

    def is_token_expired(self, auth_config: AuthConfig) -> bool:
        """
        토큰 만료 여부 검증

        30초 여유를 두고 만료 판정 (갱신 시간 확보)

        Args:
            auth_config: OAuth 설정 (token_expires_at 포함)

        Returns:
            True if 토큰 만료됨 (또는 30초 이내 만료 예정)
        """
        return time.time() > (auth_config.oauth2_token_expires_at - TOKEN_EXPIRY_BUFFER_SECONDS)

    def needs_refresh(self, auth_config: AuthConfig) -> bool:
        """
        토큰 갱신 필요 여부

        조건:
        - 토큰이 만료되었고
        - refresh_token이 존재함

        Args:
            auth_config: OAuth 설정 (access_token, refresh_token, expires_at 포함)

        Returns:
            True if 토큰 갱신 필요
        """
        return self.is_token_expired(auth_config) and bool(auth_config.oauth2_refresh_token)
