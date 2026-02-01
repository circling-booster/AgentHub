"""
OAuth Port (Outbound)

토큰 교환 및 갱신을 위한 외부 OAuth Provider 연동 인터페이스
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.domain.entities.auth_config import AuthConfig


@dataclass
class TokenResponse:
    """OAuth 토큰 응답"""

    access_token: str
    refresh_token: str | None = None
    expires_in: int = 3600  # 기본 1시간
    token_type: str = "Bearer"


class OAuthPort(ABC):
    """
    OAuth 2.1 외부 연동 Port

    책임:
    - Authorization Code → Access Token 교환
    - Refresh Token으로 Access Token 갱신
    """

    @abstractmethod
    async def exchange_code_for_token(
        self,
        code: str,
        auth_config: AuthConfig,
        redirect_uri: str,
    ) -> TokenResponse:
        """
        Authorization Code를 Access Token으로 교환

        Args:
            code: Authorization code (OAuth provider에서 발급)
            auth_config: OAuth 설정 (client_id, client_secret, token_url)
            redirect_uri: Redirect URI (검증용)

        Returns:
            TokenResponse (access_token, refresh_token, expires_in)

        Raises:
            OAuthTokenExchangeError: 토큰 교환 실패
        """
        pass

    @abstractmethod
    async def refresh_access_token(
        self,
        auth_config: AuthConfig,
    ) -> TokenResponse:
        """
        Refresh Token으로 Access Token 갱신

        Args:
            auth_config: OAuth 설정 (refresh_token, client_id, client_secret, token_url)

        Returns:
            TokenResponse (새 access_token, refresh_token, expires_in)

        Raises:
            OAuthTokenRefreshError: 토큰 갱신 실패
        """
        pass
