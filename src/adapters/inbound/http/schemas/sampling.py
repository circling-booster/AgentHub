"""Sampling HITL API Response Schemas (Phase 6, Step 6.3)"""

from typing import Any

from pydantic import BaseModel

from src.domain.entities.sampling_request import SamplingRequest


class SamplingRequestSchema(BaseModel):
    """SamplingRequest 응답 스키마"""

    id: str
    endpoint_id: str
    messages: list[dict[str, Any]]
    model_preferences: dict[str, Any] | None = None
    system_prompt: str | None = None
    max_tokens: int
    status: str
    llm_result: dict[str, Any] | None = None
    rejection_reason: str = ""

    @classmethod
    def from_entity(cls, request: SamplingRequest) -> "SamplingRequestSchema":
        """Domain Entity → HTTP Response Schema"""
        return cls(
            id=request.id,
            endpoint_id=request.endpoint_id,
            messages=request.messages,
            model_preferences=request.model_preferences,
            system_prompt=request.system_prompt,
            max_tokens=request.max_tokens,
            status=request.status.value,
            llm_result=request.llm_result,
            rejection_reason=request.rejection_reason,
        )


class SamplingRequestListResponse(BaseModel):
    """Sampling 요청 목록 응답"""

    requests: list[SamplingRequestSchema]


class SamplingApproveResponse(BaseModel):
    """Sampling 승인 응답"""

    status: str
    result: dict[str, Any]


class SamplingRejectRequest(BaseModel):
    """Sampling 거부 요청"""

    reason: str = ""


class SamplingRejectResponse(BaseModel):
    """Sampling 거부 응답"""

    status: str
