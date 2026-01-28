"""Tool 엔티티 테스트"""

import pytest

from src.domain.entities.tool import Tool
from src.domain.exceptions import ValidationError


class TestTool:
    """Tool 엔티티 테스트"""

    def test_create_tool_with_required_fields(self):
        """필수 필드로 Tool 생성"""
        # When
        tool = Tool(name="search", description="Search the web")

        # Then
        assert tool.name == "search"
        assert tool.description == "Search the web"
        assert tool.input_schema == {}
        assert tool.endpoint_id == ""

    def test_create_tool_with_all_fields(self):
        """모든 필드로 Tool 생성"""
        # Given
        schema = {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        }

        # When
        tool = Tool(
            name="search",
            description="Search the web",
            input_schema=schema,
            endpoint_id="endpoint-123",
        )

        # Then
        assert tool.name == "search"
        assert tool.description == "Search the web"
        assert tool.input_schema == schema
        assert tool.endpoint_id == "endpoint-123"

    def test_tool_name_cannot_be_empty(self):
        """빈 이름으로 Tool 생성 시 에러"""
        # When / Then
        with pytest.raises(ValidationError) as exc_info:
            Tool(name="", description="Some description")

        assert "name cannot be empty" in str(exc_info.value.message).lower()

    def test_tool_is_immutable(self):
        """Tool은 불변(frozen) 객체"""
        # Given
        tool = Tool(name="search", description="Search the web")

        # When / Then
        with pytest.raises(AttributeError):
            tool.name = "new_name"  # type: ignore

    def test_tool_equality(self):
        """동일한 값을 가진 Tool은 동등함"""
        # Given
        tool1 = Tool(name="search", description="Search the web")
        tool2 = Tool(name="search", description="Search the web")

        # Then
        assert tool1 == tool2

    def test_tool_with_complex_schema(self):
        """복잡한 JSON Schema를 가진 Tool"""
        # Given
        schema = {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "default": 10},
                "filters": {
                    "type": "object",
                    "properties": {"category": {"type": "string"}},
                },
            },
            "required": ["query"],
        }

        # When
        tool = Tool(name="advanced_search", description="Advanced search", input_schema=schema)

        # Then
        assert tool.input_schema["properties"]["query"]["type"] == "string"
        assert tool.input_schema["properties"]["limit"]["default"] == 10

    def test_tool_repr(self):
        """Tool은 repr로 표현 가능"""
        # Given
        tool = Tool(name="search", description="Search the web")

        # When
        repr_str = repr(tool)

        # Then
        assert "Tool" in repr_str
        assert "search" in repr_str
