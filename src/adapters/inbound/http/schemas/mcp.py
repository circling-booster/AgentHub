"""MCP API Request/Response Schemas"""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl

from src.domain.entities.endpoint import EndpointType


class AuthConfigSchema(BaseModel):
    """MCP 서버 인증 설정 스키마"""

    auth_type: str = "none"
    headers: dict[str, str] = Field(default_factory=dict)
    api_key: str = ""
    api_key_header: str = "Authorization"
    api_key_prefix: str = "Bearer"

    # OAuth 2.0/2.1 (Step 8에서 사용)
    oauth2_client_id: str = ""
    oauth2_client_secret: str = ""
    oauth2_token_url: str = ""
    oauth2_authorize_url: str = ""
    oauth2_scope: str = ""
    oauth2_access_token: str = ""
    oauth2_refresh_token: str = ""
    oauth2_token_expires_at: float = 0.0


class RegisterMcpServerRequest(BaseModel):
    """MCP 서버 등록 요청"""

    url: HttpUrl
    name: str | None = None
    auth: AuthConfigSchema | None = None  # Phase 5-B Step 7


class McpServerResponse(BaseModel):
    """MCP 서버 응답"""

    id: str
    url: str
    name: str
    type: EndpointType
    enabled: bool
    registered_at: datetime
    tools: list["ToolResponse"] = Field(default_factory=list)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ToolResponse(BaseModel):
    """도구 응답"""

    name: str
    description: str
    input_schema: dict = Field(default_factory=dict)
