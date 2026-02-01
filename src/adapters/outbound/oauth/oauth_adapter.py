"""
OAuth Adapter (httpx 기반)

OAuth 2.1 토큰 교환 및 갱신 구현
"""

import httpx

from src.domain.entities.auth_config import AuthConfig
from src.domain.exceptions import OAuthTokenExchangeError, OAuthTokenRefreshError
from src.domain.ports.outbound.oauth_port import OAuthPort, TokenResponse


class HttpxOAuthAdapter(OAuthPort):
    """
    httpx 기반 OAuth 2.1 Adapter

    책임:
    - Authorization Code → Access Token 교환 (POST /token)
    - Refresh Token으로 Access Token 갱신 (POST /token)
    """

    async def exchange_code_for_token(
        self,
        code: str,
        auth_config: AuthConfig,
        redirect_uri: str,
    ) -> TokenResponse:
        """
        Authorization Code를 Access Token으로 교환

        OAuth 2.1 Token Exchange Request:
        POST {token_url}
        grant_type=authorization_code
        code={code}
        redirect_uri={redirect_uri}
        client_id={client_id}
        client_secret={client_secret}

        Args:
            code: Authorization code
            auth_config: OAuth 설정
            redirect_uri: Redirect URI

        Returns:
            TokenResponse

        Raises:
            OAuthTokenExchangeError: 토큰 교환 실패
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    auth_config.oauth2_token_url,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "client_id": auth_config.oauth2_client_id,
                        "client_secret": auth_config.oauth2_client_secret,
                    },
                    headers={"Accept": "application/json"},
                )

                if response.status_code != 200:
                    raise OAuthTokenExchangeError(
                        f"Token exchange failed: {response.status_code} {response.text}"
                    )

                data = response.json()
                return TokenResponse(
                    access_token=data["access_token"],
                    refresh_token=data.get("refresh_token"),
                    expires_in=data.get("expires_in", 3600),
                    token_type=data.get("token_type", "Bearer"),
                )

            except httpx.HTTPError as e:
                raise OAuthTokenExchangeError(f"HTTP error during token exchange: {e}") from e

    async def refresh_access_token(
        self,
        auth_config: AuthConfig,
    ) -> TokenResponse:
        """
        Refresh Token으로 Access Token 갱신

        OAuth 2.1 Token Refresh Request:
        POST {token_url}
        grant_type=refresh_token
        refresh_token={refresh_token}
        client_id={client_id}
        client_secret={client_secret}

        Args:
            auth_config: OAuth 설정 (refresh_token 포함)

        Returns:
            TokenResponse

        Raises:
            OAuthTokenRefreshError: 토큰 갱신 실패
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    auth_config.oauth2_token_url,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": auth_config.oauth2_refresh_token,
                        "client_id": auth_config.oauth2_client_id,
                        "client_secret": auth_config.oauth2_client_secret,
                    },
                    headers={"Accept": "application/json"},
                )

                if response.status_code != 200:
                    raise OAuthTokenRefreshError(
                        f"Token refresh failed: {response.status_code} {response.text}"
                    )

                data = response.json()
                return TokenResponse(
                    access_token=data["access_token"],
                    refresh_token=data.get("refresh_token", auth_config.oauth2_refresh_token),
                    expires_in=data.get("expires_in", 3600),
                    token_type=data.get("token_type", "Bearer"),
                )

            except httpx.HTTPError as e:
                raise OAuthTokenRefreshError(f"HTTP error during token refresh: {e}") from e
