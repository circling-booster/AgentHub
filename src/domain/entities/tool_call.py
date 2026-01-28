"""ToolCall 엔티티 - 도구 호출 기록

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class ToolCall:
    """
    도구 호출 기록 (Value Object)

    MCP 도구 호출의 입력, 출력, 상태를 기록하는 불변 객체입니다.
    Message 엔티티에 포함되어 대화 이력의 일부로 저장됩니다.

    Attributes:
        tool_name: 호출된 도구 이름
        arguments: 입력 인자 (JSON 직렬화 가능)
        id: 호출 ID (UUID)
        result: 실행 결과 (성공 시)
        error: 에러 메시지 (실패 시)
        duration_ms: 실행 시간 (밀리초)
        created_at: 호출 시각

    Example:
        >>> tool_call = ToolCall(
        ...     tool_name="web_search",
        ...     arguments={"query": "python dataclass"},
        ...     result={"results": [...]},
        ...     duration_ms=250
        ... )
        >>> tool_call.is_success
        True
    """

    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    result: Any = None
    error: str | None = None
    duration_ms: int | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def is_success(self) -> bool:
        """
        실행 성공 여부

        Returns:
            에러가 없으면 True, 있으면 False
        """
        return self.error is None
