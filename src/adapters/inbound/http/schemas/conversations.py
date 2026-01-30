"""Conversation API Request/Response Schemas"""

from pydantic import BaseModel, Field


class CreateConversationRequest(BaseModel):
    """대화 생성 요청"""

    title: str = ""


class ConversationResponse(BaseModel):
    """대화 응답"""

    id: str
    title: str
    created_at: str


class ListConversationsQuery(BaseModel):
    """대화 목록 조회 쿼리"""

    limit: int = Field(default=20, ge=1, le=100)
