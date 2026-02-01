"""Usage 엔티티 (순수 Python, 외부 의존성 없음)"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Usage:
    """
    LLM 호출 사용량 엔티티

    LiteLLM 콜백에서 수집한 토큰 사용량 및 비용 정보를 저장합니다.
    """

    model: str  # LLM 모델명 (예: "openai/gpt-4o-mini")
    prompt_tokens: int  # 입력 토큰 수
    completion_tokens: int  # 출력 토큰 수
    total_tokens: int  # 총 토큰 수
    cost_usd: float  # 비용 (USD)
    created_at: datetime = field(default_factory=datetime.now)  # 생성 시간

    def __post_init__(self):
        """검증 로직 (dataclass 초기화 후 실행)"""
        # 토큰 수 검증 (음수 불가)
        if self.prompt_tokens < 0:
            raise ValueError("prompt_tokens must be non-negative")
        if self.completion_tokens < 0:
            raise ValueError("completion_tokens must be non-negative")
        if self.total_tokens < 0:
            raise ValueError("total_tokens must be non-negative")

        # 비용 검증 (음수 불가)
        if self.cost_usd < 0:
            raise ValueError("cost_usd must be non-negative")

        # 총 토큰 일치 검증
        expected_total = self.prompt_tokens + self.completion_tokens
        if self.total_tokens != expected_total:
            raise ValueError(
                f"total_tokens must equal prompt_tokens + completion_tokens "
                f"(expected {expected_total}, got {self.total_tokens})"
            )
