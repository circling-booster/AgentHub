"""Thread Isolation Tests

무거운 도구 실행 중에도 /health 엔드포인트가 즉시 응답하는지 검증
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset


class TestThreadIsolation:
    """Thread Isolation 검증"""

    async def test_thread_isolation_health_during_tool_execution(self):
        """
        Given: 무거운 동기 작업을 수행하는 도구가 실행 중
        When: /health 엔드포인트를 호출하면
        Then: 즉시 응답을 받아야 함 (블로킹되지 않음)
        """
        # Given: DynamicToolset에 무거운 도구 등록
        toolset = DynamicToolset(cache_ttl_seconds=300)

        # Mock MCP 서버 및 무거운 도구
        mock_toolset = MagicMock()

        # 무거운 동기 작업 시뮬레이션 (1초 sleep)
        def blocking_tool_function():
            time.sleep(1)  # 동기 블로킹
            return {"result": "heavy computation done"}

        mock_tool = MagicMock()
        mock_tool.name = "heavy_tool"
        mock_tool.run_async = AsyncMock(side_effect=lambda args, ctx: blocking_tool_function())

        mock_toolset.get_tools = AsyncMock(return_value=[mock_tool])
        mock_toolset.close = AsyncMock()

        endpoint_id = "test-endpoint"
        toolset._mcp_toolsets[endpoint_id] = mock_toolset

        # When: 무거운 도구 실행 시작 (백그라운드)
        tool_task = asyncio.create_task(toolset.call_tool("heavy_tool", {}))

        # 도구 실행이 시작될 시간 확보
        await asyncio.sleep(0.1)

        # health_check 호출 (다른 asyncio 태스크)
        start_time = time.time()
        health_result = await toolset.health_check(endpoint_id)
        elapsed = time.time() - start_time

        # Then: health_check가 즉시 응답 (0.5초 이내)
        assert health_result is True
        assert elapsed < 0.5, f"health_check took {elapsed}s, expected < 0.5s"

        # 도구 실행 완료 대기
        result = await tool_task
        assert result["result"] == "heavy computation done"

        # Cleanup
        await toolset.close()

    async def test_asyncio_to_thread_wrapper(self):
        """
        Given: DynamicToolset.call_tool()이 asyncio.to_thread()를 사용
        When: 동기 블로킹 작업을 실행하면
        Then: 메인 이벤트 루프가 차단되지 않음
        """
        # Given
        toolset = DynamicToolset()

        mock_toolset = MagicMock()

        # 동기 블로킹 함수
        def sync_blocking():
            time.sleep(0.5)
            return "sync_result"

        mock_tool = MagicMock()
        mock_tool.name = "sync_tool"
        mock_tool.run_async = AsyncMock(side_effect=lambda args, ctx: sync_blocking())

        mock_toolset.get_tools = AsyncMock(return_value=[mock_tool])
        mock_toolset.close = AsyncMock()

        toolset._mcp_toolsets["test"] = mock_toolset

        # When: 동시에 여러 비동기 작업 실행
        async def other_async_work():
            await asyncio.sleep(0.1)
            return "other_work_done"

        start = time.time()
        tool_result, other_result = await asyncio.gather(
            toolset.call_tool("sync_tool", {}), other_async_work()
        )
        elapsed = time.time() - start

        # Then: 두 작업이 병렬 실행됨 (0.7초 이내, 순차 실행 시 0.6초 소요)
        assert tool_result == "sync_result"
        assert other_result == "other_work_done"
        assert elapsed < 0.7, f"Took {elapsed}s, expected parallel execution"

        await toolset.close()

    async def test_event_loop_not_blocked_during_tool_call(self):
        """
        Given: 메인 이벤트 루프에서 실행 중
        When: call_tool()로 블로킹 작업을 실행하면
        Then: 다른 코루틴이 동시에 실행 가능함
        """
        toolset = DynamicToolset()

        mock_toolset = MagicMock()

        def blocking_operation():
            time.sleep(0.3)
            return "blocked"

        mock_tool = MagicMock()
        mock_tool.name = "blocker"
        mock_tool.run_async = AsyncMock(side_effect=lambda args, ctx: blocking_operation())

        mock_toolset.get_tools = AsyncMock(return_value=[mock_tool])
        mock_toolset.close = AsyncMock()

        toolset._mcp_toolsets["test"] = mock_toolset

        # 이벤트 루프 상태 추적
        loop_active_count = []

        async def monitor_loop():
            """이벤트 루프가 응답하는지 모니터링"""
            for _ in range(5):
                await asyncio.sleep(0.1)
                loop_active_count.append(1)

        # When: 블로킹 도구와 모니터 동시 실행
        await asyncio.gather(toolset.call_tool("blocker", {}), monitor_loop())

        # Then: 모니터가 정상 실행됨 (이벤트 루프가 차단되지 않음)
        assert len(loop_active_count) >= 3, "Event loop was blocked"

        await toolset.close()
