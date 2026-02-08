"""Tool Call Tracing 통합 테스트 - Step 6: Part B

SQLite에 ToolCall을 저장하고 조회하는 전체 흐름 검증
"""

import pytest

from src.adapters.outbound.storage.sqlite_conversation_storage import (
    SqliteConversationStorage,
)
from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message, MessageRole
from src.domain.entities.tool_call import ToolCall


async def test_sqlite_saves_and_retrieves_tool_calls(temp_database):
    """SQLite에 ToolCall을 저장하고 조회할 수 있어야 함"""
    storage = SqliteConversationStorage(db_path=temp_database)
    await storage.initialize()

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

    # Given: 2개의 ToolCall
    tool_call_1 = ToolCall(
        id="tc-1",
        tool_name="web_search",
        arguments={"query": "python"},
        result={"count": 10},
        duration_ms=200,
    )
    tool_call_2 = ToolCall(
        id="tc-2",
        tool_name="calculator",
        arguments={"expression": "2+2"},
        result=4,
        duration_ms=50,
    )

    # When: 저장 (message_id로 저장)
    await storage.save_tool_call("msg-1", tool_call_1)
    await storage.save_tool_call("msg-1", tool_call_2)

    # Then: 조회 가능
    retrieved = await storage.get_tool_calls("conv-1")
    assert len(retrieved) == 2

    # 시간순 정렬 확인
    assert retrieved[0].tool_name == "web_search"
    assert retrieved[1].tool_name == "calculator"

    await storage.close()


async def test_tool_calls_linked_to_conversation(temp_database):
    """ToolCall이 대화에 종속되어야 함 (FK 제약)"""
    storage = SqliteConversationStorage(db_path=temp_database)
    await storage.initialize()

    # Given: ToolCall만 저장 시도 (대화 없음)
    tool_call = ToolCall(
        id="tc-1",
        tool_name="test_tool",
        arguments={},
    )

    # When/Then: 실패해야 함 (FK 제약 - message_id가 존재하지 않음)
    with pytest.raises(Exception):  # noqa: B017 - SQLite IntegrityError (일반 예외 허용)
        await storage.save_tool_call("nonexistent-message", tool_call)

    await storage.close()


async def test_get_tool_calls_empty_list_for_new_conversation(temp_database):
    """새 대화는 빈 tool_calls 리스트를 반환해야 함"""
    storage = SqliteConversationStorage(db_path=temp_database)
    await storage.initialize()

    # Given: 대화만 생성 (ToolCall 없음)
    conversation = Conversation(id="conv-1", title="Test")
    await storage.save_conversation(conversation)

    # When: ToolCall 조회
    tool_calls = await storage.get_tool_calls("conv-1")

    # Then: 빈 리스트
    assert tool_calls == []

    await storage.close()
