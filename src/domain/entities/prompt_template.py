"""PromptTemplate 엔티티

MCP Prompt Template을 표현합니다. 순수 Python으로 작성됩니다.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PromptArgument:
    """
    Prompt 템플릿 인자

    Attributes:
        name: 인자 이름
        required: 필수 여부
        description: 인자 설명
    """

    name: str
    required: bool = True
    description: str = ""


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    """
    MCP Prompt 템플릿

    MCP 서버가 제공하는 프롬프트 템플릿을 표현합니다.

    Attributes:
        name: 템플릿 이름
        description: 템플릿 설명
        arguments: 템플릿 인자 목록
    """

    name: str
    description: str = ""
    arguments: list[PromptArgument] = field(default_factory=list)
