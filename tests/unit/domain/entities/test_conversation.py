"""Conversation 엔티티 테스트 - Aggregate Root"""

import uuid
from datetime import datetime

import pytest

from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.domain.entities.enums import MessageRole


class TestConversation:
    """Conversation 엔티티 테스트"""

    def test_create_conversation_with_defaults(self):
        """기본값으로 Conversation 생성"""
        # When
        conversation = Conversation()

        # Then
        assert conversation.id is not None
        assert conversation.title == ""
        assert conversation.messages == []
        assert isinstance(conversation.created_at, datetime)
        assert isinstance(conversation.updated_at, datetime)

    def test_create_conversation_with_custom_values(self):
        """커스텀 값으로 Conversation 생성"""
        # Given
        custom_id = "conv-123"
        custom_title = "Test Conversation"

        # When
        conversation = Conversation(id=custom_id, title=custom_title)

        # Then
        assert conversation.id == custom_id
        assert conversation.title == custom_title

    def test_conversation_id_is_uuid_format(self):
        """기본 ID는 UUID 형식"""
        # When
        conversation = Conversation()

        # Then
        try:
            uuid.UUID(conversation.id)
            is_valid_uuid = True
        except ValueError:
            is_valid_uuid = False
        assert is_valid_uuid

    def test_add_message_to_conversation(self):
        """메시지 추가"""
        # Given
        conversation = Conversation()
        message = Message.user("Hello")

        # When
        conversation.add_message(message)

        # Then
        assert len(conversation.messages) == 1
        assert conversation.messages[0].content == "Hello"
        assert conversation.messages[0].conversation_id == conversation.id

    def test_add_message_sets_conversation_id(self):
        """메시지 추가 시 conversation_id가 설정됨"""
        # Given
        conversation = Conversation(id="conv-abc")
        message = Message.user("Test")

        # When
        conversation.add_message(message)

        # Then
        assert message.conversation_id == "conv-abc"

    def test_add_message_updates_updated_at(self):
        """메시지 추가 시 updated_at 갱신"""
        # Given
        conversation = Conversation()
        original_updated_at = conversation.updated_at

        # When
        import time
        time.sleep(0.01)  # 시간 차이 보장
        message = Message.user("Hello")
        conversation.add_message(message)

        # Then
        assert conversation.updated_at >= original_updated_at

    def test_add_user_message_generates_title_if_empty(self):
        """첫 사용자 메시지 추가 시 제목이 없으면 자동 생성"""
        # Given
        conversation = Conversation()
        message = Message.user("Hello, how are you today?")

        # When
        conversation.add_message(message)

        # Then
        assert conversation.title != ""
        assert len(conversation.title) <= 50  # 제목은 50자 이하

    def test_add_message_does_not_change_existing_title(self):
        """이미 제목이 있으면 변경하지 않음"""
        # Given
        conversation = Conversation(title="Existing Title")
        message = Message.user("Hello")

        # When
        conversation.add_message(message)

        # Then
        assert conversation.title == "Existing Title"

    def test_add_assistant_message_does_not_generate_title(self):
        """assistant 메시지는 제목 생성하지 않음"""
        # Given
        conversation = Conversation()
        message = Message.assistant("I'm doing great!")

        # When
        conversation.add_message(message)

        # Then
        assert conversation.title == ""

    def test_get_context_messages_returns_recent_messages(self):
        """get_context_messages는 최근 메시지 반환"""
        # Given
        conversation = Conversation()
        for i in range(25):
            conversation.add_message(Message.user(f"Message {i}"))

        # When
        context = conversation.get_context_messages(limit=20)

        # Then
        assert len(context) == 20
        assert context[0].content == "Message 5"  # 5번부터 시작
        assert context[-1].content == "Message 24"  # 24번으로 끝

    def test_get_context_messages_returns_all_if_less_than_limit(self):
        """메시지가 limit보다 적으면 모두 반환"""
        # Given
        conversation = Conversation()
        conversation.add_message(Message.user("First"))
        conversation.add_message(Message.user("Second"))

        # When
        context = conversation.get_context_messages(limit=20)

        # Then
        assert len(context) == 2

    def test_get_context_messages_default_limit(self):
        """기본 limit은 20"""
        # Given
        conversation = Conversation()
        for i in range(30):
            conversation.add_message(Message.user(f"Message {i}"))

        # When
        context = conversation.get_context_messages()

        # Then
        assert len(context) == 20

    def test_message_count_property(self):
        """message_count 프로퍼티"""
        # Given
        conversation = Conversation()
        conversation.add_message(Message.user("One"))
        conversation.add_message(Message.assistant("Two"))
        conversation.add_message(Message.user("Three"))

        # Then
        assert conversation.message_count == 3

    def test_message_count_empty(self):
        """빈 대화의 메시지 수는 0"""
        # Given
        conversation = Conversation()

        # Then
        assert conversation.message_count == 0

    def test_multiple_messages_maintain_order(self):
        """여러 메시지 추가 시 순서 유지"""
        # Given
        conversation = Conversation()

        # When
        conversation.add_message(Message.user("First"))
        conversation.add_message(Message.assistant("Second"))
        conversation.add_message(Message.user("Third"))

        # Then
        assert conversation.messages[0].content == "First"
        assert conversation.messages[1].content == "Second"
        assert conversation.messages[2].content == "Third"


class TestConversationTitleGeneration:
    """제목 자동 생성 테스트"""

    def test_short_message_uses_full_content(self):
        """짧은 메시지는 전체 내용을 제목으로"""
        # Given
        conversation = Conversation()
        message = Message.user("Hi")

        # When
        conversation.add_message(message)

        # Then
        assert conversation.title == "Hi"

    def test_long_message_truncated(self):
        """긴 메시지는 잘림"""
        # Given
        conversation = Conversation()
        long_content = "A" * 100

        # When
        conversation.add_message(Message.user(long_content))

        # Then
        assert len(conversation.title) <= 50
        assert conversation.title.endswith("...")
