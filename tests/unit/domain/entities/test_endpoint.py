"""Endpoint 엔티티 테스트"""

import pytest

from src.domain.entities.endpoint import Endpoint
from src.domain.entities.enums import EndpointStatus, EndpointType
from src.domain.entities.tool import Tool
from src.domain.exceptions import InvalidUrlError


class TestEndpoint:
    """Endpoint 엔티티 테스트"""

    def test_create_endpoint_with_required_fields(self):
        """필수 필드로 Endpoint 생성"""
        # When
        endpoint = Endpoint(url="https://example.com/mcp", type=EndpointType.MCP)

        # Then
        assert endpoint.url == "https://example.com/mcp"
        assert endpoint.type == EndpointType.MCP
        assert endpoint.id is not None
        assert endpoint.name == "example.com"  # URL에서 자동 추출
        assert endpoint.enabled is True
        assert endpoint.status == EndpointStatus.UNKNOWN
        assert endpoint.tools == []

    def test_create_endpoint_with_custom_name(self):
        """커스텀 이름으로 Endpoint 생성"""
        # When
        endpoint = Endpoint(
            url="https://example.com/mcp",
            type=EndpointType.MCP,
            name="My MCP Server",
        )

        # Then
        assert endpoint.name == "My MCP Server"

    def test_create_a2a_endpoint(self):
        """A2A 타입 Endpoint 생성"""
        # When
        endpoint = Endpoint(url="https://agent.example.com/a2a", type=EndpointType.A2A)

        # Then
        assert endpoint.type == EndpointType.A2A

    def test_empty_url_raises_error(self):
        """빈 URL은 에러"""
        # When / Then
        with pytest.raises(InvalidUrlError) as exc_info:
            Endpoint(url="", type=EndpointType.MCP)

        assert "cannot be empty" in str(exc_info.value.message).lower()

    def test_invalid_url_scheme_raises_error(self):
        """잘못된 URL 스킴은 에러"""
        # When / Then
        with pytest.raises(InvalidUrlError) as exc_info:
            Endpoint(url="ftp://example.com/mcp", type=EndpointType.MCP)

        assert "invalid url scheme" in str(exc_info.value.message).lower()

    def test_url_without_scheme_raises_error(self):
        """스킴 없는 URL은 에러"""
        # When / Then
        with pytest.raises(InvalidUrlError):
            Endpoint(url="example.com/mcp", type=EndpointType.MCP)

    def test_update_status(self):
        """상태 업데이트"""
        # Given
        endpoint = Endpoint(url="https://example.com/mcp", type=EndpointType.MCP)
        assert endpoint.status == EndpointStatus.UNKNOWN
        assert endpoint.last_health_check is None

        # When
        endpoint.update_status(EndpointStatus.CONNECTED)

        # Then
        assert endpoint.status == EndpointStatus.CONNECTED
        assert endpoint.last_health_check is not None

    def test_enable_disable(self):
        """활성화/비활성화"""
        # Given
        endpoint = Endpoint(url="https://example.com/mcp", type=EndpointType.MCP)
        assert endpoint.enabled is True

        # When / Then
        endpoint.disable()
        assert endpoint.enabled is False

        endpoint.enable()
        assert endpoint.enabled is True

    def test_endpoint_with_tools(self):
        """도구가 있는 Endpoint"""
        # Given
        tools = [
            Tool(name="search", description="Search the web"),
            Tool(name="calculate", description="Calculator"),
        ]

        # When
        endpoint = Endpoint(
            url="https://example.com/mcp",
            type=EndpointType.MCP,
            tools=tools,
        )

        # Then
        assert len(endpoint.tools) == 2
        assert endpoint.tools[0].name == "search"

    def test_extract_name_from_url_with_port(self):
        """포트가 있는 URL에서 이름 추출"""
        # When
        endpoint = Endpoint(url="http://localhost:8080/mcp", type=EndpointType.MCP)

        # Then
        assert endpoint.name == "localhost:8080"

    def test_http_url_is_valid(self):
        """HTTP URL도 유효"""
        # localhost는 HTTP 허용
        endpoint = Endpoint(url="http://localhost:8000/mcp", type=EndpointType.MCP)
        assert endpoint.url == "http://localhost:8000/mcp"

    def test_endpoint_id_is_uuid_format(self):
        """Endpoint ID는 UUID 형식"""
        # When
        endpoint = Endpoint(url="https://example.com/mcp", type=EndpointType.MCP)

        # Then
        parts = endpoint.id.split("-")
        assert len(parts) == 5

    def test_a2a_endpoint_with_agent_card(self):
        """
        Given: A2A 엔드포인트
        When: agent_card를 설정하면
        Then: agent_card 필드가 저장됨
        """
        # Given
        agent_card = {
            "name": "test_agent",
            "description": "Test A2A Agent",
            "version": "1.0.0",
        }

        # When
        endpoint = Endpoint(
            url="http://localhost:9001",
            type=EndpointType.A2A,
            agent_card=agent_card,
        )

        # Then
        assert endpoint.agent_card == agent_card
        assert endpoint.agent_card["name"] == "test_agent"

    def test_mcp_endpoint_agent_card_defaults_to_none(self):
        """
        Given: MCP 엔드포인트
        When: agent_card를 지정하지 않으면
        Then: None
        """
        # When
        endpoint = Endpoint(url="https://example.com/mcp", type=EndpointType.MCP)

        # Then
        assert endpoint.agent_card is None
