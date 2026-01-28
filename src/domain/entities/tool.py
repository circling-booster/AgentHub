"""Tool 엔티티 - MCP 도구 정보

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""

from dataclasses import dataclass, field
from typing import Any

from src.domain.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class Tool:
    """
    MCP 도구 정보

    MCP 서버에서 제공하는 도구의 메타데이터를 담는 불변 객체입니다.
    frozen=True로 불변성을 보장하고, slots=True로 메모리 효율을 높입니다.

    Attributes:
        name: 도구 이름 (고유 식별자)
        description: 도구 설명 (LLM에 제공됨)
        input_schema: JSON Schema 형식의 입력 파라미터 정의
        endpoint_id: 소속 엔드포인트 ID

    Example:
        >>> tool = Tool(
        ...     name="web_search",
        ...     description="Search the web for information",
        ...     input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
        ...     endpoint_id="mcp-server-1"
        ... )
    """

    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    endpoint_id: str = ""

    def __post_init__(self) -> None:
        """생성 후 유효성 검증"""
        if not self.name:
            raise ValidationError("Tool name cannot be empty")
