"""MCP API Request/Response Schemas"""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl

from src.domain.entities.endpoint import EndpointType


class RegisterMcpServerRequest(BaseModel):
    """MCP 서버 등록 요청"""

    url: HttpUrl
    name: str | None = None


class McpServerResponse(BaseModel):
    """MCP 서버 응답"""

    id: str
    url: str
    name: str
    type: EndpointType
    enabled: bool
    registered_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ToolResponse(BaseModel):
    """도구 응답"""

    name: str
    description: str
    input_schema: dict = Field(default_factory=dict)
