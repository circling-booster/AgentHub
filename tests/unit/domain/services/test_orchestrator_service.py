"""OrchestratorService 테스트 (ChatPort 구현)"""

import pytest

from src.domain.exceptions import ConversationNotFoundError
from src.domain.services.orchestrator_service import OrchestratorService
from tests.unit.fakes import FakeConversationService


class TestOrchestratorService:
    """OrchestratorService 테스트"""

    @pytest.fixture
    def conversation_service(self):
        return FakeConversationService()

    @pytest.fixture
    def service(self, conversation_service):
        return OrchestratorService(conversation_service=conversation_service)

    @pytest.mark.asyncio
    async def test_send_message(self, service):
        """메시지 전송 - ChatPort.send_message 구현"""
        # When
        chunks = []
        async for chunk in service.send_message(None, "Hello"):
            chunks.append(chunk)

        # Then
        assert len(chunks) == 2
        assert "".join(chunks) == "Hello! How can I help you?"

    @pytest.mark.asyncio
    async def test_send_message_to_existing_conversation(self, service, conversation_service):
        """기존 대화에 메시지 전송"""
        # Given
        conv = await conversation_service.create_conversation()

        # When
        chunks = []
        async for chunk in service.send_message(conv.id, "Hi"):
            chunks.append(chunk)

        # Then
        assert len(chunks) == 2

    @pytest.mark.asyncio
    async def test_send_message_nonexistent_conversation(self, service):
        """존재하지 않는 대화에 메시지 전송"""
        # When / Then
        with pytest.raises(ConversationNotFoundError):
            async for _ in service.send_message("nonexistent", "Hello"):
                pass

    @pytest.mark.asyncio
    async def test_get_conversation(self, service, conversation_service):
        """대화 조회"""
        # Given
        conv = await conversation_service.create_conversation(title="Test")

        # When
        result = await service.get_conversation(conv.id)

        # Then
        assert result.id == conv.id
        assert result.title == "Test"

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, service):
        """존재하지 않는 대화 조회"""
        # When / Then
        with pytest.raises(ConversationNotFoundError):
            await service.get_conversation("nonexistent")

    @pytest.mark.asyncio
    async def test_list_conversations(self, service, conversation_service):
        """대화 목록 조회"""
        # Given
        await conversation_service.create_conversation(title="Conv 1")
        await conversation_service.create_conversation(title="Conv 2")
        await conversation_service.create_conversation(title="Conv 3")

        # When
        result = await service.list_conversations(limit=2)

        # Then
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_create_conversation(self, service):
        """새 대화 생성"""
        # When
        conv = await service.create_conversation(title="New Chat")

        # Then
        assert conv.title == "New Chat"

    @pytest.mark.asyncio
    async def test_delete_conversation(self, service, conversation_service):
        """대화 삭제"""
        # Given
        conv = await conversation_service.create_conversation()

        # When
        result = await service.delete_conversation(conv.id)

        # Then
        assert result is True
        assert conv.id not in conversation_service.conversations

    @pytest.mark.asyncio
    async def test_delete_nonexistent_conversation(self, service):
        """존재하지 않는 대화 삭제"""
        # When
        result = await service.delete_conversation("nonexistent")

        # Then
        assert result is False
