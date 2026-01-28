"""Message 엔티티 테스트"""

from datetime import datetime

import pytest

from src.domain.entities.enums import MessageRole
from src.domain.entities.message import Message
from src.domain.entities.tool_call import ToolCall
from src.domain.exceptions import ValidationError


class TestMessage:
    """Message 엔티티 테스트"""

    def test_create_message_with_required_fields(self):
        """필수 필드로 Message 생성"""
        # When
        message = Message(role=MessageRole.USER, content="Hello")

        # Then
        assert message.role == MessageRole.USER
        assert message.content == "Hello"
        assert message.id is not None
        assert message.conversation_id == ""
        assert message.tool_calls == []
        assert isinstance(message.created_at, datetime)

    def test_create_message_with_conversation_id(self):
        """conversation_id가 있는 Message 생성"""
        # When
        message = Message(
            role=MessageRole.ASSISTANT,
            content="Hi there!",
            conversation_id="conv-123",
        )

        # Then
        assert message.conversation_id == "conv-123"

    def test_user_factory_method(self):
        """Message.user() 팩토리 메서드"""
        # When
        message = Message.user("Hello, how are you?")

        # Then
        assert message.role == MessageRole.USER
        assert message.content == "Hello, how are you?"

    def test_assistant_factory_method(self):
        """Message.assistant() 팩토리 메서드"""
        # When
        message = Message.assistant("I'm doing well, thanks!")

        # Then
        assert message.role == MessageRole.ASSISTANT
        assert message.content == "I'm doing well, thanks!"

    def test_system_factory_method(self):
        """Message.system() 팩토리 메서드"""
        # When
        message = Message.system("You are a helpful assistant.")

        # Then
        assert message.role == MessageRole.SYSTEM
        assert message.content == "You are a helpful assistant."

    def test_factory_methods_with_conversation_id(self):
        """팩토리 메서드에 conversation_id 전달"""
        # When
        message = Message.user("Hello", conversation_id="conv-456")

        # Then
        assert message.conversation_id == "conv-456"

    def test_add_tool_call_to_assistant_message(self):
        """assistant 메시지에 ToolCall 추가"""
        # Given
        message = Message.assistant("Let me search for that.")
        tool_call = ToolCall(tool_name="search", arguments={"query": "test"})

        # When
        message.add_tool_call(tool_call)

        # Then
        assert len(message.tool_calls) == 1
        assert message.tool_calls[0].tool_name == "search"

    def test_add_tool_call_to_user_message_raises_error(self):
        """user 메시지에 ToolCall 추가 시 에러"""
        # Given
        message = Message.user("Hello")
        tool_call = ToolCall(tool_name="search", arguments={"query": "test"})

        # When / Then
        with pytest.raises(ValidationError) as exc_info:
            message.add_tool_call(tool_call)

        assert "assistant" in str(exc_info.value.message).lower()

    def test_add_multiple_tool_calls(self):
        """여러 ToolCall 추가"""
        # Given
        message = Message.assistant("I'll use multiple tools.")
        tool_call1 = ToolCall(tool_name="search", arguments={"query": "first"})
        tool_call2 = ToolCall(tool_name="calculate", arguments={"expr": "1+1"})

        # When
        message.add_tool_call(tool_call1)
        message.add_tool_call(tool_call2)

        # Then
        assert len(message.tool_calls) == 2

    def test_message_id_is_uuid_format(self):
        """Message ID는 UUID 형식"""
        # When
        message = Message.user("Test")

        # Then
        parts = message.id.split("-")
        assert len(parts) == 5

    def test_tool_role_message(self):
        """TOOL 역할 메시지"""
        # When
        message = Message(role=MessageRole.TOOL, content='{"result": "data"}')

        # Then
        assert message.role == MessageRole.TOOL

    def test_empty_content_is_allowed(self):
        """빈 content 허용 (일부 케이스에서 필요)"""
        # When
        message = Message(role=MessageRole.ASSISTANT, content="")

        # Then
        assert message.content == ""
