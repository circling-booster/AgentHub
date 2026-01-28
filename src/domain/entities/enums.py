"""Domain 열거형 정의

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""

from enum import Enum


class MessageRole(str, Enum):
    """메시지 역할

    대화에서 각 메시지의 발신자 역할을 나타냅니다.

    Attributes:
        USER: 사용자 메시지
        ASSISTANT: AI 어시스턴트 응답
        SYSTEM: 시스템 프롬프트
        TOOL: 도구 실행 결과
    """

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class EndpointType(str, Enum):
    """엔드포인트 유형

    AgentHub가 지원하는 외부 서비스 프로토콜 유형입니다.

    Attributes:
        MCP: Model Context Protocol 서버
        A2A: Agent-to-Agent 프로토콜 에이전트
    """

    MCP = "mcp"
    A2A = "a2a"


class EndpointStatus(str, Enum):
    """엔드포인트 연결 상태

    MCP/A2A 서버의 현재 연결 상태를 나타냅니다.

    Attributes:
        CONNECTED: 정상 연결됨
        DISCONNECTED: 연결 끊김
        ERROR: 연결 오류 발생
        UNKNOWN: 상태 확인 전
    """

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    UNKNOWN = "unknown"
