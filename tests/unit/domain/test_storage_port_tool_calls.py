"""StoragePort Tool Call 메서드 테스트 - Step 6: Part B

StoragePort에 save_tool_call(), get_tool_calls() 메서드가 정의되었는지 검증
"""

import pytest


def test_storage_port_has_save_tool_call_method():
    """StoragePort에 save_tool_call() 메서드가 정의되어 있어야 함"""
    from src.domain.ports.outbound.storage_port import ConversationStoragePort

    assert hasattr(ConversationStoragePort, "save_tool_call")


def test_storage_port_has_get_tool_calls_method():
    """StoragePort에 get_tool_calls() 메서드가 정의되어 있어야 함"""
    from src.domain.ports.outbound.storage_port import ConversationStoragePort

    assert hasattr(ConversationStoragePort, "get_tool_calls")


@pytest.mark.asyncio
async def test_fake_storage_saves_and_retrieves_tool_calls():
    """Fake Storage가 ToolCall을 저장하고 조회할 수 있어야 함"""
    from src.domain.entities.conversation import Conversation
    from src.domain.entities.message import Message, MessageRole
    from src.domain.entities.tool_call import ToolCall
    from tests.unit.fakes.fake_storage import FakeConversationStorage

    storage = FakeConversationStorage()

    # Given: 대화와 메시지 생성
    conversation = Conversation(id="conv-1", title="Test")
    await storage.save_conversation(conversation)

    message = Message(
        id="msg-1",
        conversation_id="conv-1",
        role=MessageRole.USER,
        content="test",
    )
    await storage.save_message(message)

    # Given: ToolCall 생성
    tool_call = ToolCall(
        id="tc-1",
        tool_name="web_search",
        arguments={"query": "test"},
        result={"results": []},
        duration_ms=150,
    )

    # When: ToolCall 저장 (message_id로 저장)
    await storage.save_tool_call(message_id="msg-1", tool_call=tool_call)

    # Then: conversation_id로 조회 가능
    retrieved = await storage.get_tool_calls("conv-1")
    assert len(retrieved) == 1
    assert retrieved[0].id == "tc-1"
    assert retrieved[0].tool_name == "web_search"
    assert retrieved[0].duration_ms == 150
