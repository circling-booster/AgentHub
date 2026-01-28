"""ConversationService - 대화 관리 서비스

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""

from collections.abc import AsyncIterator

from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.domain.exceptions import ConversationNotFoundError
from src.domain.ports.outbound.orchestrator_port import OrchestratorPort
from src.domain.ports.outbound.storage_port import ConversationStoragePort


class ConversationService:
    """
    대화 관리 서비스

    대화 세션의 생성, 조회, 삭제 및 메시지 처리를 담당합니다.
    OrchestratorPort를 통해 LLM과 통신하고,
    ConversationStoragePort를 통해 대화를 저장합니다.

    Attributes:
        _storage: 대화 저장소 포트
        _orchestrator: LLM 오케스트레이터 포트
    """

    def __init__(
        self,
        storage: ConversationStoragePort,
        orchestrator: OrchestratorPort,
    ) -> None:
        """
        Args:
            storage: 대화 저장소 포트
            orchestrator: LLM 오케스트레이터 포트
        """
        self._storage = storage
        self._orchestrator = orchestrator

    async def create_conversation(self, title: str = "") -> Conversation:
        """
        새 대화 생성

        Args:
            title: 대화 제목 (선택)

        Returns:
            생성된 대화 객체
        """
        conversation = Conversation(title=title)
        await self._storage.save_conversation(conversation)
        return conversation

    async def get_conversation(self, conversation_id: str) -> Conversation:
        """
        대화 조회

        Args:
            conversation_id: 대화 ID

        Returns:
            대화 객체

        Raises:
            ConversationNotFoundError: 대화를 찾을 수 없을 때
        """
        conversation = await self._storage.get_conversation(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(f"Conversation not found: {conversation_id}")
        return conversation

    async def list_conversations(self, limit: int = 20) -> list[Conversation]:
        """
        대화 목록 조회

        Args:
            limit: 최대 결과 수

        Returns:
            대화 목록 (최신순)
        """
        return await self._storage.list_conversations(limit=limit)

    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        대화 삭제

        Args:
            conversation_id: 삭제할 대화 ID

        Returns:
            삭제 성공 여부
        """
        return await self._storage.delete_conversation(conversation_id)

    async def get_or_create_conversation(
        self,
        conversation_id: str | None,
    ) -> Conversation:
        """
        대화 조회 또는 생성

        conversation_id가 None이면 새 대화를 생성합니다.
        존재하는 ID면 해당 대화를 반환합니다.

        Args:
            conversation_id: 대화 ID 또는 None

        Returns:
            대화 객체
        """
        if conversation_id is None:
            return await self.create_conversation()
        return await self.get_conversation(conversation_id)

    async def send_message(
        self,
        conversation_id: str | None,
        content: str,
    ) -> AsyncIterator[str]:
        """
        메시지 전송 및 스트리밍 응답

        사용자 메시지를 처리하고 LLM 응답을 스트리밍합니다.
        conversation_id가 None이면 새 대화를 생성합니다.

        Args:
            conversation_id: 대화 ID 또는 None
            content: 사용자 메시지 내용

        Yields:
            LLM 응답 텍스트 조각 (스트리밍)

        Raises:
            ConversationNotFoundError: 존재하지 않는 대화 ID
        """
        # 대화 조회 또는 생성
        if conversation_id is None:
            conversation = await self.create_conversation()
        else:
            # 존재하지 않으면 에러 발생
            conversation = await self._storage.get_conversation(conversation_id)
            if conversation is None:
                raise ConversationNotFoundError(f"Conversation not found: {conversation_id}")

        # 사용자 메시지 저장
        user_message = Message.user(content, conversation.id)
        conversation.add_message(user_message)
        await self._storage.save_message(user_message)
        await self._storage.save_conversation(conversation)

        # LLM 응답 스트리밍
        response_chunks: list[str] = []
        async for chunk in self._orchestrator.process_message(content, conversation.id):
            response_chunks.append(chunk)
            yield chunk

        # 어시스턴트 응답 저장
        full_response = "".join(response_chunks)
        assistant_message = Message.assistant(full_response, conversation.id)
        conversation.add_message(assistant_message)
        await self._storage.save_message(assistant_message)
        await self._storage.save_conversation(conversation)
