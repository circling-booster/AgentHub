"""Fake ConversationService - 테스트용 대화 서비스

OrchestratorService 테스트 시 사용하는 Fake 구현입니다.
"""

from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.domain.entities.stream_chunk import StreamChunk
from src.domain.exceptions import ConversationNotFoundError


class FakeConversationService:
    """
    테스트용 대화 서비스

    ConversationService의 Fake 구현입니다.
    OrchestratorService 단위 테스트에서 사용합니다.
    """

    def __init__(
        self,
        responses: list[StreamChunk] | None = None,
    ) -> None:
        """
        Args:
            responses: send_message 시 반환할 StreamChunk 목록
        """
        self.conversations: dict[str, Conversation] = {}
        self.messages: dict[str, list[Message]] = {}
        self.responses: list[StreamChunk] = responses or [
            StreamChunk.text("Hello! "),
            StreamChunk.text("How can I help you?"),
        ]

    async def create_conversation(self, title: str = "") -> Conversation:
        """새 대화 생성"""
        conv = Conversation(title=title)
        self.conversations[conv.id] = conv
        self.messages[conv.id] = []
        return conv

    async def get_conversation(self, conversation_id: str) -> Conversation:
        """대화 조회"""
        if conversation_id not in self.conversations:
            raise ConversationNotFoundError(f"Conversation not found: {conversation_id}")
        return self.conversations[conversation_id]

    async def list_conversations(self, limit: int = 20) -> list[Conversation]:
        """대화 목록 조회"""
        convs = sorted(
            self.conversations.values(),
            key=lambda c: c.updated_at,
            reverse=True,
        )
        return convs[:limit]

    async def delete_conversation(self, conversation_id: str) -> bool:
        """대화 삭제"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            self.messages.pop(conversation_id, None)
            return True
        return False

    async def get_or_create_conversation(
        self,
        conversation_id: str | None,
    ) -> Conversation:
        """대화 조회 또는 생성"""
        if conversation_id is None:
            return await self.create_conversation()
        return await self.get_conversation(conversation_id)

    async def send_message(self, conversation_id: str | None, content: str):
        """메시지 전송 및 스트리밍 응답"""
        if conversation_id is None:
            conv = await self.create_conversation()
            conversation_id = conv.id
        elif conversation_id not in self.conversations:
            raise ConversationNotFoundError(f"Conversation not found: {conversation_id}")

        # 사용자 메시지 저장
        user_msg = Message.user(content, conversation_id)
        self.messages[conversation_id].append(user_msg)

        # 응답 생성
        for chunk in self.responses:
            yield chunk

        # 어시스턴트 메시지 저장 (text 타입만 축적)
        full_response = "".join(c.content for c in self.responses if c.type == "text")
        assistant_msg = Message.assistant(full_response, conversation_id)
        self.messages[conversation_id].append(assistant_msg)

    def clear(self) -> None:
        """모든 데이터 초기화"""
        self.conversations.clear()
        self.messages.clear()
