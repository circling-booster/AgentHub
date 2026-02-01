"""DynamicToolset Logging Tests (TDD RED - Step 7)

Phase 4 Part B: Structured Logging for DynamicToolset
"""

import logging
from unittest.mock import AsyncMock

import pytest

from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset
from src.domain.entities.endpoint import Endpoint, EndpointType


@pytest.mark.asyncio
async def test_get_tools_logs_cache_hit_miss(caplog):
    """get_tools()가 캐시 hit/miss를 로깅해야 함"""
    # Given: DynamicToolset with mocked MCPToolset
    toolset = DynamicToolset()

    # Mock MCP server
    mock_mcp = AsyncMock()
    mock_tool = AsyncMock()
    mock_tool.name = "test_tool"
    mock_tool.description = "Test tool"
    mock_tool.input_schema = {}
    mock_mcp.get_tools = AsyncMock(return_value=[mock_tool])
    mock_mcp.close = AsyncMock()

    toolset._mcp_toolsets["endpoint-1"] = mock_mcp

    # When: 첫 번째 호출 (캐시 미스)
    with caplog.at_level(logging.DEBUG):
        await toolset.get_tools()

    # Then: MISS 로그 확인
    assert any("cache MISS" in record.message for record in caplog.records)

    caplog.clear()

    # When: 두 번째 호출 (캐시 히트)
    with caplog.at_level(logging.DEBUG):
        await toolset.get_tools()

    # Then: HIT 로그 확인
    assert any("cache HIT" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_get_tools_logs_total_tool_count(caplog):
    """get_tools()가 총 도구 개수를 INFO 레벨로 로깅해야 함"""
    # Given: DynamicToolset with mocked MCPToolset
    toolset = DynamicToolset()

    # Mock MCP server
    mock_mcp = AsyncMock()
    mock_tools = [AsyncMock(name=f"tool_{i}") for i in range(3)]
    mock_mcp.get_tools = AsyncMock(return_value=mock_tools)
    mock_mcp.close = AsyncMock()

    toolset._mcp_toolsets["endpoint-1"] = mock_mcp

    # When: get_tools() 호출
    with caplog.at_level(logging.INFO):
        result = await toolset.get_tools()

    # Then: 도구 개수 로깅
    assert len(result) == 3
    info_logs = [r for r in caplog.records if r.levelname == "INFO"]
    assert len(info_logs) > 0
    assert any("3 tools" in record.message for record in info_logs)


@pytest.mark.asyncio
async def test_add_mcp_server_logs_endpoint_url_and_tool_count(caplog):
    """add_mcp_server()가 엔드포인트 URL과 도구 개수를 로깅해야 함"""
    # Given: DynamicToolset (실제 MCP 서버 불필요, Mock 사용)
    toolset = DynamicToolset()

    # _create_mcp_toolset을 Mock으로 대체
    mock_mcp = AsyncMock()
    mock_tools = [AsyncMock(name=f"tool_{i}", description="", input_schema={}) for i in range(5)]
    for tool in mock_tools:
        tool.name = tool._mock_name
    mock_mcp.get_tools = AsyncMock(return_value=mock_tools)
    mock_mcp.close = AsyncMock()

    async def mock_create_mcp(url, auth_config=None):
        return mock_mcp

    toolset._create_mcp_toolset = mock_create_mcp

    endpoint = Endpoint(
        id="test-endpoint", name="Test MCP", url="http://localhost:9000/mcp", type=EndpointType.MCP
    )

    # When: add_mcp_server() 호출
    with caplog.at_level(logging.INFO):
        await toolset.add_mcp_server(endpoint)

    # Then: URL과 도구 개수 로깅
    info_logs = [r for r in caplog.records if r.levelname == "INFO"]
    assert len(info_logs) > 0
    assert any("http://localhost:9000/mcp" in record.message for record in info_logs)
    # extra 필드 확인
    log_with_extra = [r for r in info_logs if hasattr(r, "tool_count")]
    assert len(log_with_extra) > 0
    assert log_with_extra[0].tool_count == 5


@pytest.mark.asyncio
async def test_remove_mcp_server_logs_removed_tool_count(caplog):
    """remove_mcp_server()가 제거된 도구 개수를 로깅해야 함"""
    # Given: DynamicToolset with registered endpoint
    toolset = DynamicToolset()

    mock_mcp = AsyncMock()
    mock_tools = [AsyncMock(name=f"tool_{i}", description="", input_schema={}) for i in range(3)]
    for tool in mock_tools:
        tool.name = tool._mock_name
    mock_mcp.get_tools = AsyncMock(return_value=mock_tools)
    mock_mcp.close = AsyncMock()

    async def mock_create_mcp(url, auth_config=None):
        return mock_mcp

    toolset._create_mcp_toolset = mock_create_mcp

    endpoint = Endpoint(
        id="test-endpoint", name="Test MCP", url="http://localhost:9000/mcp", type=EndpointType.MCP
    )

    await toolset.add_mcp_server(endpoint)
    caplog.clear()

    # When: remove_mcp_server() 호출
    with caplog.at_level(logging.INFO):
        removed = await toolset.remove_mcp_server("test-endpoint")

    # Then: 제거 성공 및 도구 개수 로깅
    assert removed is True
    info_logs = [r for r in caplog.records if r.levelname == "INFO"]
    assert len(info_logs) > 0
    assert any("removed" in record.message.lower() for record in info_logs)
