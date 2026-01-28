"""Conversation 엔티티 - 대화 세션 (Aggregate Root)

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from src.domain.entities.enums import MessageRole

if TYPE_CHECKING:
    from src.domain.entities.message import Message


@dataclass
class Conversation:
    """
    대화 세션 (Aggregate Root)

    사용자와 어시스턴트 간의 대화 컨텍스트를 관리하는 루트 엔티티입니다.
    메시지 추가, 컨텍스트 조회, 제목 자동 생성 등을 담당합니다.

    Attributes:
        id: 대화 ID (UUID)
        title: 대화 제목 (자동 생성 가능)
        messages: 메시지 목록
        created_at: 생성 시각
        updated_at: 마지막 수정 시각

    Example:
        >>> conversation = Conversation()
        >>> conversation.add_message(Message.user("Hello"))
        >>> conversation.message_count
        1
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    messages: list["Message"] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, message: "Message") -> None:
        """
        메시지 추가

        대화에 새 메시지를 추가합니다. 메시지의 conversation_id가 설정되고
        updated_at이 갱신됩니다. 첫 사용자 메시지이고 제목이 없으면 자동 생성합니다.

        Args:
            message: 추가할 메시지
        """
        # conversation_id 설정
        message.conversation_id = self.id

        # 메시지 추가
        self.messages.append(message)

        # updated_at 갱신
        self.updated_at = datetime.utcnow()

        # 첫 사용자 메시지이고 제목이 없으면 자동 생성
        if not self.title and message.role == MessageRole.USER:
            self.title = self._generate_title(message.content)

    def get_context_messages(self, limit: int = 20) -> list["Message"]:
        """
        컨텍스트용 최근 메시지 조회

        LLM에 전달할 컨텍스트로 사용할 최근 메시지를 반환합니다.

        Args:
            limit: 최대 메시지 수 (기본 20)

        Returns:
            최근 메시지 목록 (최대 limit개)
        """
        return self.messages[-limit:]

    @property
    def message_count(self) -> int:
        """
        메시지 수

        Returns:
            현재 대화의 총 메시지 수
        """
        return len(self.messages)

    def _generate_title(self, content: str) -> str:
        """
        메시지 내용으로 제목 생성

        Args:
            content: 메시지 내용

        Returns:
            생성된 제목 (최대 50자, 초과 시 '...' 추가)
        """
        max_length = 50
        if len(content) <= max_length:
            return content
        return content[: max_length - 3] + "..."
