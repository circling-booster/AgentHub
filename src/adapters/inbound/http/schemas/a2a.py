"""A2A Management API Schemas

A2A 에이전트 등록/조회/삭제 Request/Response 모델
"""

from pydantic import BaseModel, HttpUrl


class RegisterA2aAgentRequest(BaseModel):
    """A2A 에이전트 등록 요청"""

    url: HttpUrl
    name: str | None = None


class A2aAgentResponse(BaseModel):
    """A2A 에이전트 응답"""

    id: str
    url: str
    name: str
    type: str  # "a2a"
    enabled: bool
    agent_card: dict | None = None
    registered_at: str
