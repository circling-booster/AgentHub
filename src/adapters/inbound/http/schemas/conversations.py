"""Conversation API Request/Response Schemas"""

from pydantic import BaseModel


class CreateConversationRequest(BaseModel):
    """대화 생성 요청"""

    title: str = ""


class ConversationResponse(BaseModel):
    """대화 응답"""

    id: str
    title: str
    created_at: str
