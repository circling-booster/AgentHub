"""
AuthConfig domain entity

MCP 서버 인증 설정 (순수 Python, 외부 의존성 없음)
"""

from dataclasses import dataclass, field


@dataclass
class AuthConfig:
    """
    MCP 서버 인증 설정

    지원 인증 타입:
    - none: 인증 없음
    - header: 커스텀 헤더
    - api_key: API Key (Authorization 헤더)
    - oauth2: OAuth 2.0/2.1 (Bearer token)
    """

    auth_type: str = "none"  # "none" | "header" | "api_key" | "oauth2"

    # Header Auth
    headers: dict[str, str] = field(default_factory=dict)

    # API Key Auth
    api_key: str = ""
    api_key_header: str = "Authorization"
    api_key_prefix: str = "Bearer"  # "Bearer", "ApiKey", "" (raw)

    # OAuth 2.0/2.1
    oauth2_client_id: str = ""
    oauth2_client_secret: str = ""
    oauth2_token_url: str = ""
    oauth2_authorize_url: str = ""
    oauth2_scope: str = ""
    oauth2_access_token: str = ""
    oauth2_refresh_token: str = ""
    oauth2_token_expires_at: float = 0.0

    def get_auth_headers(self) -> dict[str, str]:
        """
        인증 타입에 따라 HTTP 헤더 생성

        Returns:
            인증 헤더 딕셔너리 (빈 dict 가능)
        """
        if self.auth_type == "header":
            return dict(self.headers)

        elif self.auth_type == "api_key":
            # 프리픽스가 있으면 "Bearer key", 없으면 "key"
            prefix = f"{self.api_key_prefix} " if self.api_key_prefix else ""
            return {self.api_key_header: f"{prefix}{self.api_key}"}

        elif self.auth_type == "oauth2" and self.oauth2_access_token:
            return {"Authorization": f"Bearer {self.oauth2_access_token}"}

        # auth_type="none" 또는 토큰 없음
        return {}
