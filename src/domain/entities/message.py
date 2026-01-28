"""Message 엔티티 - 대화 메시지

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from src.domain.entities.enums import MessageRole
from src.domain.exceptions import ValidationError

if TYPE_CHECKING:
    from src.domain.entities.tool_call import ToolCall


@dataclass
class Message:
    """
    대화 메시지

    대화에서 주고받는 개별 메시지를 나타냅니다.
    사용자, 어시스턴트, 시스템, 도구 응답 등 다양한 역할을 가질 수 있습니다.

    Attributes:
        role: 발신자 역할 (user, assistant, system, tool)
        content: 메시지 내용
        conversation_id: 소속 대화 ID
        id: 메시지 ID (UUID)
        tool_calls: 도구 호출 기록 (assistant 메시지만)
        created_at: 생성 시각

    Example:
        >>> message = Message.user("Hello, how are you?")
        >>> message.role
        <MessageRole.USER: 'user'>
    """

    role: MessageRole
    content: str
    conversation_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool_calls: list["ToolCall"] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_tool_call(self, tool_call: "ToolCall") -> None:
        """
        도구 호출 기록 추가

        assistant 메시지에만 ToolCall을 추가할 수 있습니다.

        Args:
            tool_call: 추가할 도구 호출 기록

        Raises:
            ValidationError: assistant가 아닌 메시지에 추가 시도 시
        """
        if self.role != MessageRole.ASSISTANT:
            raise ValidationError("Only assistant messages can have tool calls")
        self.tool_calls.append(tool_call)

    @classmethod
    def user(cls, content: str, conversation_id: str = "") -> "Message":
        """
        사용자 메시지 팩토리

        Args:
            content: 메시지 내용
            conversation_id: 대화 ID (선택)

        Returns:
            새로운 사용자 메시지
        """
        return cls(
            role=MessageRole.USER,
            content=content,
            conversation_id=conversation_id,
        )

    @classmethod
    def assistant(cls, content: str, conversation_id: str = "") -> "Message":
        """
        어시스턴트 메시지 팩토리

        Args:
            content: 메시지 내용
            conversation_id: 대화 ID (선택)

        Returns:
            새로운 어시스턴트 메시지
        """
        return cls(
            role=MessageRole.ASSISTANT,
            content=content,
            conversation_id=conversation_id,
        )

    @classmethod
    def system(cls, content: str, conversation_id: str = "") -> "Message":
        """
        시스템 메시지 팩토리

        Args:
            content: 메시지 내용
            conversation_id: 대화 ID (선택)

        Returns:
            새로운 시스템 메시지
        """
        return cls(
            role=MessageRole.SYSTEM,
            content=content,
            conversation_id=conversation_id,
        )
