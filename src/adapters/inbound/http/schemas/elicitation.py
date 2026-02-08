"""Elicitation HITL API Response Schemas"""

from typing import Any

from pydantic import BaseModel

from src.domain.entities.elicitation_request import ElicitationRequest


class ElicitationRequestSchema(BaseModel):
    """ElicitationRequest 응답 스키마 (C1 수정: 필드명 일치)"""

    id: str
    endpoint_id: str
    message: str  # "prompt" → "message"
    requested_schema: dict[str, Any]  # "accepted_actions" → "requested_schema"
    status: str
    action: str | None = None  # "user_response" 분리 → "action"
    content: dict[str, Any] | None = None  # "user_response" 분리 → "content"

    @classmethod
    def from_entity(cls, request: ElicitationRequest) -> "ElicitationRequestSchema":
        """Domain Entity → HTTP Response Schema"""
        return cls(
            id=request.id,
            endpoint_id=request.endpoint_id,
            message=request.message,
            requested_schema=request.requested_schema,
            status=request.status.value,
            action=request.action.value if request.action else None,
            content=request.content,
        )


class ElicitationRequestListResponse(BaseModel):
    """Elicitation 요청 목록 응답"""

    requests: list[ElicitationRequestSchema]


class ElicitationRespondRequest(BaseModel):
    """Elicitation 응답 요청 (C2 수정: content 타입)"""

    action: str  # "accept", "decline", "cancel"
    content: dict[str, Any] | None = None  # str → dict


class ElicitationRespondResponse(BaseModel):
    """Elicitation 응답"""

    status: str
