"""DynamicToolset Integration Tests

TDD Phase: RED - 테스트 먼저 작성
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.adapters.outbound.adk.dynamic_toolset import (
    DynamicToolset,
    ToolLimitExceededError,
)
from src.config.settings import McpSettings, Settings
from src.domain.entities.endpoint import Endpoint, EndpointType


@pytest.fixture
def dynamic_toolset():
    """DynamicToolset 인스턴스 (캐시 TTL 1초로 설정)"""
    settings = Settings()
    settings.mcp = McpSettings(
        max_active_tools=30,
        cache_ttl_seconds=1,  # 테스트용 짧은 TTL
        max_retries=2,
        retry_backoff_seconds=1.0,
    )
    return DynamicToolset(settings=settings)


@pytest.fixture
def mock_mcp_server():
    """Mock MCP 서버 엔드포인트"""
    return Endpoint(
        url="http://localhost:9000/mcp",
        type=EndpointType.MCP,
        name="Test MCP Server",
    )


class TestDynamicToolsetBasics:
    """기본 동작 검증"""

    async def test_get_tools_empty(self, dynamic_toolset):
        """등록된 서버가 없을 때 빈 리스트 반환"""
        # When: 서버 없이 get_tools 호출
        tools = await dynamic_toolset.get_tools()

        # Then: 빈 리스트
        assert tools == []

    async def test_add_mcp_server_streamable_http(self, dynamic_toolset, mock_mcp_server):
        """MCP 서버 추가 (Streamable HTTP)"""
        # Given: Mock MCPToolset
        mock_toolset = AsyncMock()
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test tool"
        mock_tool.input_schema = {"type": "object"}
        mock_toolset.get_tools = AsyncMock(return_value=[mock_tool])

        with patch(
            "src.adapters.outbound.adk.dynamic_toolset.MCPToolset",
            return_value=mock_toolset,
        ):
            # When: 서버 추가
            tools = await dynamic_toolset.add_mcp_server(mock_mcp_server)

            # Then: 도구 목록 반환
            assert len(tools) == 1
            assert tools[0].name == "test_tool"
            assert tools[0].endpoint_id == mock_mcp_server.id

    async def test_add_mcp_server_sse_fallback(self, dynamic_toolset, mock_mcp_server):
        """Streamable HTTP 실패 시 SSE 폴백"""
        # Given: Streamable HTTP 실패, SSE 성공
        mock_toolset = AsyncMock()
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test tool"
        mock_tool.input_schema = {"type": "object"}
        mock_toolset.get_tools = AsyncMock(return_value=[mock_tool])

        call_count = 0

        def create_toolset(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # 첫 번째 시도 (Streamable HTTP) 실패
                raise ConnectionError("Streamable HTTP failed")
            # 두 번째 시도 (SSE) 성공
            return mock_toolset

        with patch(
            "src.adapters.outbound.adk.dynamic_toolset.MCPToolset",
            side_effect=create_toolset,
        ):
            # When: 서버 추가
            tools = await dynamic_toolset.add_mcp_server(mock_mcp_server)

            # Then: SSE 폴백으로 성공
            assert len(tools) == 1

    async def test_remove_mcp_server(self, dynamic_toolset, mock_mcp_server):
        """MCP 서버 제거"""
        # Given: 서버 추가
        mock_toolset = AsyncMock()
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_toolset.get_tools = AsyncMock(return_value=[mock_tool])
        mock_toolset.close = AsyncMock()

        with patch(
            "src.adapters.outbound.adk.dynamic_toolset.MCPToolset",
            return_value=mock_toolset,
        ):
            await dynamic_toolset.add_mcp_server(mock_mcp_server)

            # When: 서버 제거
            result = await dynamic_toolset.remove_mcp_server(mock_mcp_server.id)

            # Then: 제거 성공
            assert result is True
            mock_toolset.close.assert_called_once()

    async def test_remove_nonexistent_server(self, dynamic_toolset):
        """존재하지 않는 서버 제거 시 False"""
        # When: 없는 서버 제거
        result = await dynamic_toolset.remove_mcp_server("nonexistent-id")

        # Then: False 반환
        assert result is False


class TestDynamicToolsetCaching:
    """캐싱 동작 검증"""

    async def test_cache_hit(self, dynamic_toolset, mock_mcp_server):
        """캐시 히트 시 MCP 서버 호출 스킵"""
        # Given: 서버 추가
        mock_toolset = AsyncMock()
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_toolset.get_tools = AsyncMock(return_value=[mock_tool])

        with patch(
            "src.adapters.outbound.adk.dynamic_toolset.MCPToolset",
            return_value=mock_toolset,
        ):
            await dynamic_toolset.add_mcp_server(mock_mcp_server)
            mock_toolset.get_tools.reset_mock()

            # When: get_tools 2회 호출 (캐시 TTL 내)
            tools1 = await dynamic_toolset.get_tools()
            tools2 = await dynamic_toolset.get_tools()

            # Then: 캐시 히트, MCPToolset.get_tools() 호출 없음
            assert len(tools1) == 1
            assert len(tools2) == 1
            mock_toolset.get_tools.assert_not_called()

    async def test_cache_miss_after_ttl(self, dynamic_toolset, mock_mcp_server):
        """TTL 경과 후 캐시 미스"""
        # Given: 서버 추가 (캐시 TTL 1초)
        mock_toolset = AsyncMock()
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_toolset.get_tools = AsyncMock(return_value=[mock_tool])

        with patch(
            "src.adapters.outbound.adk.dynamic_toolset.MCPToolset",
            return_value=mock_toolset,
        ):
            await dynamic_toolset.add_mcp_server(mock_mcp_server)
            mock_toolset.get_tools.reset_mock()

            # When: 1초 대기 후 get_tools 호출
            await asyncio.sleep(1.1)
            tools = await dynamic_toolset.get_tools()

            # Then: 캐시 미스, MCPToolset.get_tools() 재호출
            assert len(tools) == 1
            mock_toolset.get_tools.assert_called_once()

    async def test_cache_invalidation(self, dynamic_toolset, mock_mcp_server):
        """수동 캐시 무효화"""
        # Given: 서버 추가
        mock_toolset = AsyncMock()
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_toolset.get_tools = AsyncMock(return_value=[mock_tool])

        with patch(
            "src.adapters.outbound.adk.dynamic_toolset.MCPToolset",
            return_value=mock_toolset,
        ):
            await dynamic_toolset.add_mcp_server(mock_mcp_server)
            mock_toolset.get_tools.reset_mock()

            # When: 캐시 무효화 후 get_tools
            dynamic_toolset.invalidate_cache(mock_mcp_server.id)
            tools = await dynamic_toolset.get_tools()

            # Then: 캐시 미스, 재호출
            assert len(tools) == 1
            mock_toolset.get_tools.assert_called_once()


class TestDynamicToolsetContextExplosion:
    """Context Explosion 방지 검증"""

    async def test_tool_limit_exceeded(self, dynamic_toolset):
        """도구 개수 제한 초과 시 에러"""
        # Given: 30개 도구 추가
        mock_toolset = AsyncMock()
        mock_tools = [
            MagicMock(name=f"tool_{i}", description="", input_schema={}) for i in range(30)
        ]
        mock_toolset.get_tools = AsyncMock(return_value=mock_tools)

        with patch(
            "src.adapters.outbound.adk.dynamic_toolset.MCPToolset",
            return_value=mock_toolset,
        ):
            endpoint1 = Endpoint(url="http://localhost:9000/mcp", type=EndpointType.MCP)
            await dynamic_toolset.add_mcp_server(endpoint1)

            # When: 1개 도구를 더 추가 시도 (총 31개)
            endpoint2 = Endpoint(url="http://localhost:9001/mcp", type=EndpointType.MCP)
            mock_toolset2 = AsyncMock()
            mock_toolset2.get_tools = AsyncMock(return_value=[MagicMock(name="tool_31")])
            mock_toolset2.close = AsyncMock()

            with patch(
                "src.adapters.outbound.adk.dynamic_toolset.MCPToolset",
                return_value=mock_toolset2,
            ):
                # Then: ToolLimitExceededError 발생
                with pytest.raises(ToolLimitExceededError) as exc_info:
                    await dynamic_toolset.add_mcp_server(endpoint2)

                assert "exceed limit (30)" in str(exc_info.value)
                mock_toolset2.close.assert_called_once()


class TestDynamicToolsetCleanup:
    """리소스 정리 검증"""

    async def test_close_all_connections(self, dynamic_toolset):
        """close() 시 모든 MCP 연결 종료"""
        # Given: 2개 서버 추가
        mock_toolset1 = AsyncMock()
        mock_toolset1.get_tools = AsyncMock(return_value=[])
        mock_toolset1.close = AsyncMock()

        mock_toolset2 = AsyncMock()
        mock_toolset2.get_tools = AsyncMock(return_value=[])
        mock_toolset2.close = AsyncMock()

        with patch(
            "src.adapters.outbound.adk.dynamic_toolset.MCPToolset",
            side_effect=[mock_toolset1, mock_toolset2],
        ):
            endpoint1 = Endpoint(url="http://localhost:9000/mcp", type=EndpointType.MCP)
            endpoint2 = Endpoint(url="http://localhost:9001/mcp", type=EndpointType.MCP)
            await dynamic_toolset.add_mcp_server(endpoint1)
            await dynamic_toolset.add_mcp_server(endpoint2)

            # When: close 호출
            await dynamic_toolset.close()

            # Then: 모든 toolset close 호출
            mock_toolset1.close.assert_called_once()
            mock_toolset2.close.assert_called_once()
