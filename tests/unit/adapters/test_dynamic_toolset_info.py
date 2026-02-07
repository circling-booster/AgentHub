"""DynamicToolset.get_registered_info() 테스트

TDD Phase: RED - get_registered_info() 메서드 테스트
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset
from src.domain.entities.endpoint import Endpoint, EndpointType


@pytest.fixture
def dynamic_toolset():
    """DynamicToolset 인스턴스"""
    return DynamicToolset(cache_ttl_seconds=300)


@pytest.fixture
def mock_mcp_endpoint():
    """Mock MCP Endpoint"""
    return Endpoint(
        id="test-mcp-1",
        name="Test MCP Server",
        url="http://localhost:9000/mcp",
        type=EndpointType.MCP,
        enabled=True,
    )


@pytest.fixture
def mock_toolset_with_tools():
    """도구 목록이 있는 Mock MCPToolset"""
    mock_tool1 = MagicMock()
    mock_tool1.name = "test_tool_1"
    mock_tool1.description = "Test tool 1"

    mock_tool2 = MagicMock()
    mock_tool2.name = "test_tool_2"
    mock_tool2.description = "Test tool 2"

    mock_toolset = AsyncMock()
    mock_toolset.get_tools = AsyncMock(return_value=[mock_tool1, mock_tool2])
    mock_toolset.close = AsyncMock()

    return mock_toolset


class TestGetRegisteredInfo:
    """get_registered_info() 메서드 테스트"""

    async def test_get_registered_info_returns_endpoint_tools(
        self, dynamic_toolset, mock_mcp_endpoint, mock_toolset_with_tools
    ):
        """등록된 엔드포인트별 도구 정보를 반환해야 함"""
        # Given: MCP 서버가 등록되어 있음
        dynamic_toolset._mcp_toolsets[mock_mcp_endpoint.id] = mock_toolset_with_tools
        dynamic_toolset._endpoints[mock_mcp_endpoint.id] = mock_mcp_endpoint

        # Mock 캐시 데이터 설정
        mock_tools = await mock_toolset_with_tools.get_tools()
        dynamic_toolset._tool_cache[mock_mcp_endpoint.id] = mock_tools

        # When: get_registered_info() 호출
        info = dynamic_toolset.get_registered_info()

        # Then: 엔드포인트 정보와 도구 목록이 반환됨
        assert mock_mcp_endpoint.id in info
        endpoint_info = info[mock_mcp_endpoint.id]

        assert endpoint_info["name"] == "Test MCP Server"
        assert endpoint_info["url"] == "http://localhost:9000/mcp"
        assert "tools" in endpoint_info
        assert len(endpoint_info["tools"]) == 2
        assert "test_tool_1" in endpoint_info["tools"]
        assert "test_tool_2" in endpoint_info["tools"]

    async def test_get_registered_info_empty_when_no_servers(self, dynamic_toolset):
        """등록된 서버가 없으면 빈 딕셔너리를 반환해야 함"""
        # When: 서버가 등록되지 않은 상태에서 호출
        info = dynamic_toolset.get_registered_info()

        # Then: 빈 딕셔너리 반환
        assert info == {}

    async def test_get_registered_info_multiple_servers(
        self, dynamic_toolset, mock_toolset_with_tools
    ):
        """여러 MCP 서버가 등록된 경우 모두 반환해야 함"""
        # Given: 2개의 MCP 서버가 등록됨
        endpoint1 = Endpoint(
            id="mcp-1",
            name="Server 1",
            url="http://localhost:9001/mcp",
            type=EndpointType.MCP,
            enabled=True,
        )
        endpoint2 = Endpoint(
            id="mcp-2",
            name="Server 2",
            url="http://localhost:9002/mcp",
            type=EndpointType.MCP,
            enabled=True,
        )

        dynamic_toolset._mcp_toolsets[endpoint1.id] = mock_toolset_with_tools
        dynamic_toolset._endpoints[endpoint1.id] = endpoint1

        dynamic_toolset._mcp_toolsets[endpoint2.id] = mock_toolset_with_tools
        dynamic_toolset._endpoints[endpoint2.id] = endpoint2

        # Mock 캐시 데이터
        mock_tools = await mock_toolset_with_tools.get_tools()
        dynamic_toolset._tool_cache[endpoint1.id] = mock_tools
        dynamic_toolset._tool_cache[endpoint2.id] = mock_tools

        # When: get_registered_info() 호출
        info = dynamic_toolset.get_registered_info()

        # Then: 두 서버 모두 반환됨
        assert len(info) == 2
        assert "mcp-1" in info
        assert "mcp-2" in info
        assert info["mcp-1"]["name"] == "Server 1"
        assert info["mcp-2"]["name"] == "Server 2"

    async def test_get_registered_info_handles_empty_cache(
        self, dynamic_toolset, mock_mcp_endpoint, mock_toolset_with_tools
    ):
        """캐시가 비어있는 경우에도 빈 도구 목록을 반환해야 함"""
        # Given: 엔드포인트는 등록되었지만 캐시가 비어있음
        dynamic_toolset._mcp_toolsets[mock_mcp_endpoint.id] = mock_toolset_with_tools
        dynamic_toolset._endpoints[mock_mcp_endpoint.id] = mock_mcp_endpoint
        # 캐시는 비어있음 (add_mcp_server를 통하지 않은 경우)

        # When: get_registered_info() 호출
        info = dynamic_toolset.get_registered_info()

        # Then: 빈 도구 목록과 함께 반환
        assert mock_mcp_endpoint.id in info
        assert info[mock_mcp_endpoint.id]["tools"] == []
