"""OrchestratorService - 채팅 조율 서비스 (ChatPort 구현)

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""

from collections.abc import AsyncIterator

from src.domain.entities.conversation import Conversation
from src.domain.entities.stream_chunk import StreamChunk
from src.domain.ports.inbound.chat_port import ChatPort
from src.domain.services.conversation_service import ConversationService


class OrchestratorService(ChatPort):
    """
    채팅 조율 서비스 (ChatPort 구현)

    ChatPort 인터페이스를 구현하여 외부에서 채팅 기능에 접근할 수 있게 합니다.
    내부적으로 ConversationService에 위임합니다.

    Attributes:
        _conversation_service: 대화 관리 서비스
    """

    def __init__(self, conversation_service: ConversationService) -> None:
        """
        Args:
            conversation_service: 대화 관리 서비스
        """
        self._conversation_service = conversation_service

    async def send_message(
        self,
        conversation_id: str | None,
        message: str,
    ) -> AsyncIterator[StreamChunk]:
        """
        메시지 전송 및 스트리밍 응답

        ConversationService.send_message()에 위임합니다.

        Args:
            conversation_id: 대화 ID 또는 None
            message: 사용자 메시지

        Yields:
            StreamChunk 이벤트
        """
        async for chunk in self._conversation_service.send_message(conversation_id, message):
            yield chunk

    async def get_conversation(self, conversation_id: str) -> Conversation:
        """
        대화 조회

        Args:
            conversation_id: 대화 ID

        Returns:
            대화 객체
        """
        return await self._conversation_service.get_conversation(conversation_id)

    async def list_conversations(self, limit: int = 20) -> list[Conversation]:
        """
        대화 목록 조회

        Args:
            limit: 최대 결과 수

        Returns:
            대화 목록 (최신순)
        """
        return await self._conversation_service.list_conversations(limit=limit)

    async def create_conversation(self, title: str = "") -> Conversation:
        """
        새 대화 생성

        Args:
            title: 대화 제목 (선택)

        Returns:
            생성된 대화 객체
        """
        return await self._conversation_service.create_conversation(title=title)

    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        대화 삭제

        Args:
            conversation_id: 삭제할 대화 ID

        Returns:
            삭제 성공 여부
        """
        return await self._conversation_service.delete_conversation(conversation_id)
