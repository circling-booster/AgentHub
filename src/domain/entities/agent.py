"""Agent 엔티티 - AI 에이전트 설정

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""

import uuid
from dataclasses import dataclass, field

from src.domain.exceptions import ValidationError


@dataclass
class Agent:
    """
    AI 에이전트 설정

    LLM 기반 에이전트의 이름, 모델, 지시사항을 정의합니다.

    Attributes:
        name: 에이전트 이름 (필수)
        model: LLM 모델 식별자 (LiteLLM 형식)
        instruction: 시스템 프롬프트
        id: 에이전트 ID (UUID)

    Example:
        >>> agent = Agent(name="Assistant")
        >>> agent.model
        'anthropic/claude-sonnet-4-20250514'
    """

    name: str
    model: str = "anthropic/claude-sonnet-4-20250514"
    instruction: str = "You are a helpful assistant with access to various tools."
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        """생성 후 유효성 검사"""
        if not self.name:
            raise ValidationError("Agent name cannot be empty")
