"""ChatPort - 채팅 인터페이스

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from src.domain.entities.stream_chunk import StreamChunk

if TYPE_CHECKING:
    from src.domain.entities.conversation import Conversation


class ChatPort(ABC):
    """
    채팅 포트 (Driving/Inbound Port)

    외부에서 도메인으로 들어오는 채팅 요청을 처리하는 인터페이스입니다.
    HTTP API, CLI 등 다양한 진입점에서 이 포트를 통해 채팅 기능에 접근합니다.

    구현체 예시:
    - OrchestratorService (도메인 서비스)
    """

    @abstractmethod
    async def send_message(
        self,
        conversation_id: str | None,
        message: str,
    ) -> AsyncIterator[StreamChunk]:
        """
        메시지 전송 및 스트리밍 응답

        사용자 메시지를 처리하고 AI 응답을 스트리밍합니다.
        conversation_id가 None이면 새 대화를 생성합니다.

        Args:
            conversation_id: 대화 ID (None이면 새 대화 생성)
            message: 사용자 메시지

        Yields:
            StreamChunk 이벤트 (text, tool_call, tool_result, agent_transfer, error, done)

        Raises:
            ConversationNotFoundError: 존재하지 않는 대화 ID
            LlmRateLimitError: API Rate Limit 초과
        """
        pass

    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> "Conversation":
        """
        대화 조회

        Args:
            conversation_id: 대화 ID

        Returns:
            대화 객체

        Raises:
            ConversationNotFoundError: 대화를 찾을 수 없을 때
        """
        pass

    @abstractmethod
    async def list_conversations(self, limit: int = 20) -> list["Conversation"]:
        """
        대화 목록 조회

        Args:
            limit: 최대 결과 수

        Returns:
            대화 목록 (최신순)
        """
        pass

    @abstractmethod
    async def create_conversation(self, title: str = "") -> "Conversation":
        """
        새 대화 생성

        Args:
            title: 대화 제목 (선택)

        Returns:
            생성된 대화 객체
        """
        pass

    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        대화 삭제

        Args:
            conversation_id: 삭제할 대화 ID

        Returns:
            삭제 성공 여부
        """
        pass
