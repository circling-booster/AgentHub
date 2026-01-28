"""ConversationService 테스트"""

import pytest

from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.domain.entities.enums import MessageRole
from src.domain.exceptions import ConversationNotFoundError
from src.domain.services.conversation_service import ConversationService


class FakeConversationStorage:
    """테스트용 Fake ConversationStorage"""

    def __init__(self):
        self.conversations: dict[str, Conversation] = {}
        self.messages: dict[str, list[Message]] = {}

    async def save_conversation(self, conversation: Conversation) -> None:
        self.conversations[conversation.id] = conversation

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        return self.conversations.get(conversation_id)

    async def list_conversations(
        self, limit: int = 20, offset: int = 0
    ) -> list[Conversation]:
        convs = sorted(
            self.conversations.values(),
            key=lambda c: c.updated_at,
            reverse=True,
        )
        return convs[offset : offset + limit]

    async def delete_conversation(self, conversation_id: str) -> bool:
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            self.messages.pop(conversation_id, None)
            return True
        return False

    async def save_message(self, message: Message) -> None:
        if message.conversation_id not in self.messages:
            self.messages[message.conversation_id] = []
        self.messages[message.conversation_id].append(message)

    async def get_messages(
        self, conversation_id: str, limit: int | None = None
    ) -> list[Message]:
        messages = self.messages.get(conversation_id, [])
        if limit:
            return messages[-limit:]
        return messages


class FakeOrchestrator:
    """테스트용 Fake Orchestrator"""

    def __init__(self, responses: list[str] | None = None):
        self.responses = responses or ["Hello! ", "How can I help you?"]
        self.initialized = False
        self.closed = False

    async def initialize(self) -> None:
        self.initialized = True

    async def process_message(self, message: str, conversation_id: str):
        for chunk in self.responses:
            yield chunk

    async def close(self) -> None:
        self.closed = True


class TestConversationService:
    """ConversationService 테스트"""

    @pytest.fixture
    def storage(self):
        return FakeConversationStorage()

    @pytest.fixture
    def orchestrator(self):
        return FakeOrchestrator()

    @pytest.fixture
    def service(self, storage, orchestrator):
        return ConversationService(storage=storage, orchestrator=orchestrator)

    @pytest.mark.asyncio
    async def test_create_conversation(self, service):
        """새 대화 생성"""
        # When
        conversation = await service.create_conversation()

        # Then
        assert conversation.id is not None
        assert conversation.title == ""

    @pytest.mark.asyncio
    async def test_create_conversation_with_title(self, service):
        """제목과 함께 새 대화 생성"""
        # When
        conversation = await service.create_conversation(title="Test Chat")

        # Then
        assert conversation.title == "Test Chat"

    @pytest.mark.asyncio
    async def test_get_conversation(self, service, storage):
        """대화 조회"""
        # Given
        conv = Conversation(id="conv-123", title="Existing")
        storage.conversations["conv-123"] = conv

        # When
        result = await service.get_conversation("conv-123")

        # Then
        assert result.id == "conv-123"
        assert result.title == "Existing"

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, service):
        """존재하지 않는 대화 조회"""
        # When / Then
        with pytest.raises(ConversationNotFoundError):
            await service.get_conversation("non-existent")

    @pytest.mark.asyncio
    async def test_list_conversations(self, service, storage):
        """대화 목록 조회"""
        # Given
        for i in range(5):
            storage.conversations[f"conv-{i}"] = Conversation(
                id=f"conv-{i}", title=f"Chat {i}"
            )

        # When
        result = await service.list_conversations(limit=3)

        # Then
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_delete_conversation(self, service, storage):
        """대화 삭제"""
        # Given
        storage.conversations["conv-123"] = Conversation(id="conv-123")

        # When
        result = await service.delete_conversation("conv-123")

        # Then
        assert result is True
        assert "conv-123" not in storage.conversations

    @pytest.mark.asyncio
    async def test_send_message_to_new_conversation(self, service, storage):
        """새 대화에 메시지 전송"""
        # When
        chunks = []
        conversation_id = None
        async for chunk in service.send_message(None, "Hello"):
            chunks.append(chunk)
            if conversation_id is None:
                # 첫 청크에서 conversation_id를 얻을 수 있어야 함
                pass

        # Then
        assert len(chunks) == 2  # "Hello! " + "How can I help you?"
        assert "".join(chunks) == "Hello! How can I help you?"

    @pytest.mark.asyncio
    async def test_send_message_to_existing_conversation(self, service, storage):
        """기존 대화에 메시지 전송"""
        # Given
        conv = Conversation(id="conv-123")
        storage.conversations["conv-123"] = conv

        # When
        chunks = []
        async for chunk in service.send_message("conv-123", "Hi there"):
            chunks.append(chunk)

        # Then
        assert len(chunks) == 2

    @pytest.mark.asyncio
    async def test_send_message_saves_user_message(self, service, storage):
        """메시지 전송 시 사용자 메시지 저장"""
        # Given
        conv = Conversation(id="conv-123")
        storage.conversations["conv-123"] = conv

        # When
        async for _ in service.send_message("conv-123", "Test message"):
            pass

        # Then
        messages = storage.messages.get("conv-123", [])
        user_messages = [m for m in messages if m.role == MessageRole.USER]
        assert len(user_messages) == 1
        assert user_messages[0].content == "Test message"

    @pytest.mark.asyncio
    async def test_send_message_saves_assistant_response(self, service, storage):
        """메시지 전송 시 어시스턴트 응답 저장"""
        # Given
        conv = Conversation(id="conv-123")
        storage.conversations["conv-123"] = conv

        # When
        async for _ in service.send_message("conv-123", "Test"):
            pass

        # Then
        messages = storage.messages.get("conv-123", [])
        assistant_messages = [m for m in messages if m.role == MessageRole.ASSISTANT]
        assert len(assistant_messages) == 1
        assert assistant_messages[0].content == "Hello! How can I help you?"

    @pytest.mark.asyncio
    async def test_send_message_to_nonexistent_conversation(self, service):
        """존재하지 않는 대화에 메시지 전송 시 에러"""
        # When / Then
        with pytest.raises(ConversationNotFoundError):
            async for _ in service.send_message("nonexistent", "Hello"):
                pass

    @pytest.mark.asyncio
    async def test_get_or_create_conversation_creates_new(self, service, storage):
        """get_or_create_conversation - 새 대화 생성"""
        # When
        conv = await service.get_or_create_conversation(None)

        # Then
        assert conv.id is not None
        assert conv.id in storage.conversations

    @pytest.mark.asyncio
    async def test_get_or_create_conversation_returns_existing(self, service, storage):
        """get_or_create_conversation - 기존 대화 반환"""
        # Given
        existing = Conversation(id="conv-123", title="Existing")
        storage.conversations["conv-123"] = existing

        # When
        conv = await service.get_or_create_conversation("conv-123")

        # Then
        assert conv.id == "conv-123"
        assert conv.title == "Existing"
