"""SamplingRequest 엔티티

MCP Sampling 요청을 표현합니다. 순수 Python으로 작성됩니다.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class SamplingStatus(str, Enum):
    """Sampling 요청 상태"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"


@dataclass
class SamplingRequest:
    """
    MCP Sampling 요청

    MCP 서버가 LLM 호출을 요청할 때 사용됩니다.

    Attributes:
        id: 요청 ID
        endpoint_id: MCP 엔드포인트 ID
        messages: LLM 메시지 목록
        model_preferences: 모델 선호도 (선택)
        system_prompt: 시스템 프롬프트 (선택)
        max_tokens: 최대 토큰 수
        status: 요청 상태
        llm_result: LLM 응답 결과 (승인 후)
        rejection_reason: 거부 사유 (거부 시)
        created_at: 생성 시각 (UTC)
    """

    id: str
    endpoint_id: str
    messages: list[dict[str, Any]]
    model_preferences: dict[str, Any] | None = None
    system_prompt: str | None = None
    max_tokens: int = 1024
    status: SamplingStatus = SamplingStatus.PENDING
    llm_result: dict[str, Any] | None = None
    rejection_reason: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
