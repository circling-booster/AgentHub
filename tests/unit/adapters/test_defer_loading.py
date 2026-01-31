"""DynamicToolset Defer Loading 테스트 (Step 11: Part D)

RED Phase: Defer Loading 기능 테스트
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from google.adk.tools import BaseTool

from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset
from src.config.settings import Settings
from src.domain.entities.endpoint import Endpoint, EndpointType


class TestDeferLoading:
    """Defer Loading 기능 테스트"""

    @pytest.fixture
    def settings(self):
        """Settings with defer_loading_threshold=30, max_active_tools=100"""
        settings = Settings()
        settings.mcp.defer_loading_threshold = 30
        settings.mcp.max_active_tools = 100
        return settings

    @pytest.fixture
    def dynamic_toolset(self, settings):
        return DynamicToolset(settings=settings)

    @pytest.mark.asyncio
    async def test_max_active_tools_increased_to_100(self, dynamic_toolset):
        """
        RED: MAX_ACTIVE_TOOLS가 100으로 증가

        Given: 100개 도구를 등록 시도
        When: add_mcp_server() 호출
        Then: ToolLimitExceededError 발생하지 않음 (기존 30 → 100)
        """
        # Given: 100개 도구를 가진 Mock MCP 서버
        endpoint = Endpoint(
            id="test-mcp",
            url="http://test.com/mcp",
            type=EndpointType.MCP,
        )

        # Mock MCPToolset with 100 tools
        mock_toolset = AsyncMock()
        mock_tools = []
        for i in range(100):
            mock_tool = MagicMock(spec=BaseTool)
            mock_tool.name = f"tool_{i}"
            mock_tool.description = f"Tool {i}"
            mock_tools.append(mock_tool)

        mock_toolset.get_tools = AsyncMock(return_value=mock_tools)
        mock_toolset.close = AsyncMock()

        # Patch _create_mcp_toolset
        original_create = dynamic_toolset._create_mcp_toolset
        dynamic_toolset._create_mcp_toolset = AsyncMock(return_value=mock_toolset)

        # When: 100개 도구 등록
        try:
            tools = await dynamic_toolset.add_mcp_server(endpoint)
            # Then: 성공 (ToolLimitExceededError 발생 안 함)
            assert len(tools) == 100
        finally:
            dynamic_toolset._create_mcp_toolset = original_create

    @pytest.mark.asyncio
    async def test_defer_loading_activates_above_threshold(self, dynamic_toolset):
        """
        RED: defer_loading_threshold 초과 시 Defer Loading 활성화

        Given: 총 40개 도구 (threshold=30 초과)
        When: get_tools() 호출
        Then: DeferredToolProxy 반환 (메타데이터만 로드)
        """
        # Given: 40개 도구 등록
        for i in range(2):  # 2개 서버, 각 20개 도구
            endpoint = Endpoint(
                id=f"mcp-{i}",
                url=f"http://test{i}.com/mcp",
                type=EndpointType.MCP,
            )
            mock_toolset = AsyncMock()
            mock_tools = []
            for j in range(20):
                mock_tool = MagicMock(spec=BaseTool)
                mock_tool.name = f"tool_{i}_{j}"
                mock_tool.description = f"Tool {i}-{j}"
                mock_tools.append(mock_tool)

            mock_toolset.get_tools = AsyncMock(return_value=mock_tools)
            mock_toolset.close = AsyncMock()

            dynamic_toolset._create_mcp_toolset = AsyncMock(return_value=mock_toolset)
            await dynamic_toolset.add_mcp_server(endpoint)

        # When: get_tools() 호출
        tools = await dynamic_toolset.get_tools()

        # Then: DeferredToolProxy 반환 (메타데이터만)
        assert len(tools) == 40
        # DeferredToolProxy는 name, description만 가지고 input_schema는 lazy
        for tool in tools:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            # Full tool이 아닌 proxy 확인 (type name check)
            assert type(tool).__name__ == "DeferredToolProxy"

    @pytest.mark.asyncio
    async def test_normal_mode_below_threshold(self, dynamic_toolset):
        """
        RED: defer_loading_threshold 이하 시 Normal Mode

        Given: 총 20개 도구 (threshold=30 이하)
        When: get_tools() 호출
        Then: 풀 도구 반환 (BaseTool)
        """
        # Given: 20개 도구 등록
        endpoint = Endpoint(
            id="mcp-1",
            url="http://test.com/mcp",
            type=EndpointType.MCP,
        )
        mock_toolset = AsyncMock()
        mock_tools = []
        for i in range(20):
            mock_tool = MagicMock(spec=BaseTool)
            mock_tool.name = f"tool_{i}"
            mock_tool.description = f"Tool {i}"
            mock_tools.append(mock_tool)

        mock_toolset.get_tools = AsyncMock(return_value=mock_tools)
        mock_toolset.close = AsyncMock()

        dynamic_toolset._create_mcp_toolset = AsyncMock(return_value=mock_toolset)
        await dynamic_toolset.add_mcp_server(endpoint)

        # When: get_tools() 호출
        tools = await dynamic_toolset.get_tools()

        # Then: BaseTool 반환 (풀 도구)
        assert len(tools) == 20
        for tool in tools:
            # Normal mode: BaseTool 또는 MagicMock (not DeferredToolProxy)
            assert type(tool).__name__ != "DeferredToolProxy"

    @pytest.mark.asyncio
    async def test_deferred_tool_lazy_loads_on_execution(self, dynamic_toolset):
        """
        RED: DeferredToolProxy 실행 시 풀 스키마 lazy load

        Given: Defer mode (40개 도구)
        When: DeferredToolProxy.run_async() 호출
        Then: 실행 시 풀 도구 lazy load 후 정상 실행
        """
        # Given: 40개 도구 (defer mode)
        for i in range(2):
            endpoint = Endpoint(
                id=f"mcp-{i}",
                url=f"http://test{i}.com/mcp",
                type=EndpointType.MCP,
            )
            mock_toolset = AsyncMock()
            mock_tools = []
            for j in range(20):
                mock_tool = MagicMock(spec=BaseTool)
                mock_tool.name = f"test_tool_{i}_{j}"
                mock_tool.description = f"Test Tool {i}-{j}"
                mock_tool.run_async = AsyncMock(return_value="result")
                mock_tools.append(mock_tool)

            mock_toolset.get_tools = AsyncMock(return_value=mock_tools)
            mock_toolset.close = AsyncMock()

            dynamic_toolset._create_mcp_toolset = AsyncMock(return_value=mock_toolset)
            await dynamic_toolset.add_mcp_server(endpoint)

        # When: DeferredToolProxy 실행
        tools = await dynamic_toolset.get_tools()
        assert len(tools) == 40

        # Deferred tool 실행
        result = await tools[0].run_async({"arg": "value"}, None)

        # Then: lazy load 후 정상 실행
        assert result == "result"
