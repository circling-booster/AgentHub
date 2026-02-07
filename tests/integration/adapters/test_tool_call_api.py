"""Tool Call API 엔드포인트 테스트 - Step 6: Part B

GET /api/conversations/{id}/tool-calls 검증
"""

import pytest

from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message, MessageRole
from src.domain.entities.tool_call import ToolCall
from tests.integration.conftest import TEST_EXTENSION_TOKEN


async def test_get_tool_calls_api_returns_list(http_client):
    """GET /api/conversations/{id}/tool-calls가 ToolCall 리스트를 반환해야 함"""
    # Given: http_client의 Container에서 storage 가져오기
    storage = http_client.app.container.conversation_storage()

    # Given: 대화, 메시지, ToolCall 생성
    conversation = Conversation(id="conv-1", title="Test")
    await storage.save_conversation(conversation)

    message = Message(
        id="msg-1",
        conversation_id="conv-1",
        role=MessageRole.USER,
        content="test",
    )
    await storage.save_message(message)

    tool_call = ToolCall(
        id="tc-1",
        tool_name="web_search",
        arguments={"query": "test"},
        result={"count": 5},
        duration_ms=100,
    )
    await storage.save_tool_call("msg-1", tool_call)

    # When: API 호출 (인증 토큰 포함)
    response = http_client.get(
        "/api/conversations/conv-1/tool-calls",
        headers={"X-Extension-Token": TEST_EXTENSION_TOKEN},
    )

    # Then: 성공 응답
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "tc-1"
    assert data[0]["tool_name"] == "web_search"
    assert data[0]["duration_ms"] == 100


async def test_get_tool_calls_api_404_for_nonexistent_conversation(http_client):
    """존재하지 않는 대화 ID로 조회 시 404 반환"""
    # When: 존재하지 않는 대화 조회 (인증 토큰 포함)
    response = http_client.get(
        "/api/conversations/nonexistent/tool-calls",
        headers={"X-Extension-Token": TEST_EXTENSION_TOKEN},
    )

    # Then: 404 Not Found
    assert response.status_code == 404
