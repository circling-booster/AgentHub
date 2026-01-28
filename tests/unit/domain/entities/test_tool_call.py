"""ToolCall 엔티티 테스트"""

from datetime import datetime

import pytest

from src.domain.entities.tool_call import ToolCall


class TestToolCall:
    """ToolCall 엔티티 테스트"""

    def test_create_tool_call_with_required_fields(self):
        """필수 필드로 ToolCall 생성"""
        # When
        tool_call = ToolCall(tool_name="search")

        # Then
        assert tool_call.tool_name == "search"
        assert tool_call.arguments == {}
        assert tool_call.id is not None
        assert tool_call.result is None
        assert tool_call.error is None
        assert tool_call.duration_ms is None
        assert isinstance(tool_call.created_at, datetime)

    def test_create_tool_call_with_all_fields(self):
        """모든 필드로 ToolCall 생성"""
        # Given
        arguments = {"query": "test query", "limit": 10}
        result = {"items": [{"title": "Result 1"}]}
        created = datetime(2026, 1, 28, 12, 0, 0)

        # When
        tool_call = ToolCall(
            tool_name="search",
            arguments=arguments,
            id="call-123",
            result=result,
            error=None,
            duration_ms=150,
            created_at=created,
        )

        # Then
        assert tool_call.tool_name == "search"
        assert tool_call.arguments == arguments
        assert tool_call.id == "call-123"
        assert tool_call.result == result
        assert tool_call.error is None
        assert tool_call.duration_ms == 150
        assert tool_call.created_at == created

    def test_tool_call_is_success_when_no_error(self):
        """에러가 없으면 성공"""
        # Given
        tool_call = ToolCall(tool_name="search", result={"data": "value"})

        # Then
        assert tool_call.is_success is True

    def test_tool_call_is_not_success_when_error(self):
        """에러가 있으면 실패"""
        # Given
        tool_call = ToolCall(tool_name="search", error="Connection failed")

        # Then
        assert tool_call.is_success is False

    def test_tool_call_is_immutable(self):
        """ToolCall은 불변(frozen) 객체"""
        # Given
        tool_call = ToolCall(tool_name="search")

        # When / Then
        with pytest.raises(AttributeError):
            tool_call.tool_name = "new_name"  # type: ignore

    def test_tool_call_id_is_uuid_format(self):
        """ToolCall ID는 UUID 형식"""
        # When
        tool_call = ToolCall(tool_name="search")

        # Then
        # UUID format: 8-4-4-4-12 hex digits
        parts = tool_call.id.split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4

    def test_tool_call_equality(self):
        """동일한 값을 가진 ToolCall은 동등함"""
        # Given
        created = datetime(2026, 1, 28, 12, 0, 0)
        tool_call1 = ToolCall(tool_name="search", id="same-id", created_at=created)
        tool_call2 = ToolCall(tool_name="search", id="same-id", created_at=created)

        # Then
        assert tool_call1 == tool_call2

    def test_tool_call_with_error_and_result(self):
        """에러와 결과가 모두 있는 경우 (부분 성공)"""
        # 일부 MCP 도구는 경고와 함께 결과를 반환할 수 있음
        tool_call = ToolCall(
            tool_name="search",
            result={"partial_data": "value"},
            error="Rate limit warning",
        )

        # error가 있으면 is_success는 False
        assert tool_call.is_success is False
        assert tool_call.result is not None
