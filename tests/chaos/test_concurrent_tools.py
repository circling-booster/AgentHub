"""Chaos Test: 동시 도구 호출 경합 시나리오

캐시 정합성 검증:
- 100개 동시 도구 호출
- DynamicToolset 캐시 경쟁 조건
- Rate Limiting Token Bucket 동시성 안전성
"""

import asyncio

import pytest


@pytest.mark.chaos
@pytest.mark.local_mcp
class TestConcurrentToolCalls:
    """동시 도구 호출 Chaos 테스트"""

    async def test_concurrent_tool_calls_cache_consistency(self, container):
        """
        Given: 등록된 MCP 서버의 도구
        When: 100개 동시 요청으로 동일 도구 호출
        Then: 모든 결과가 일관성 유지 (캐시 정합성)
        """
        # Given: MCP 서버 등록 (테스트용 로컬 서버 필요)
        from src.domain.entities.endpoint import EndpointType

        registry_service = container.registry_service()

        # 로컬 MCP 서버 등록
        await registry_service.register_endpoint(
            url="http://127.0.0.1:9000/mcp",
            name="test-mcp",
            endpoint_type=EndpointType.MCP,
        )

        # 도구 목록 조회 (캐시 초기화)
        toolset = container.dynamic_toolset()
        tools = await toolset.get_tools()
        assert len(tools) > 0

        # When: 100개 동시 도구 조회 (캐시 경쟁 조건 유발)
        tasks = [toolset.get_tools() for _ in range(100)]
        results = await asyncio.gather(*tasks)

        # Then: 모든 결과가 동일 (캐시 일관성)
        first_result = results[0]
        for result in results:
            assert len(result) == len(first_result)
            # 도구 이름 리스트 비교
            assert [t.name for t in result] == [t.name for t in first_result]

    async def test_rate_limiter_concurrent_consume(self):
        """
        Given: Rate Limiter (Token Bucket)
        When: 100개 동시 요청으로 토큰 소비
        Then: Token Bucket 동시성 안전 (총 소비량 = capacity 이하)
        """
        # Given: GatewayService의 Token Bucket (container 불필요, 직접 생성)
        from src.domain.services.gateway_service import TokenBucket

        bucket = TokenBucket(capacity=10, rate=5.0)

        # 초기 토큰: 10개 (full capacity)
        assert bucket._tokens == 10.0

        # When: 100개 동시 토큰 소비 시도
        tasks = [bucket.consume(1) for _ in range(100)]
        results = await asyncio.gather(*tasks)

        # Then: 성공한 요청은 최대 10개 (초기 capacity)
        successful = sum(1 for r in results if r is True)
        assert successful <= 10

        # 실패한 요청은 90개 이상
        failed = sum(1 for r in results if r is False)
        assert failed >= 90

        # 남은 토큰은 0 (모두 소비됨)
        assert bucket._tokens < 1.0

    async def test_concurrent_endpoint_registration(self, container):
        """
        Given: RegistryService
        When: 동시에 10개 엔드포인트 등록
        Then: 모든 엔드포인트가 정상 등록 (경쟁 조건 없음)
        """
        from unittest.mock import AsyncMock, patch

        from src.domain.entities.endpoint import EndpointType

        # Given: RegistryService + Mock MCPToolset (실제 서버 연결 회피)
        registry_service = container.registry_service()

        # Mock MCPToolset to avoid actual MCP server connections
        with patch.object(
            registry_service._toolset, "add_mcp_server", new_callable=AsyncMock, return_value=[]
        ):
            # When: 10개 엔드포인트 동시 등록
            async def register_endpoint(i: int):
                return await registry_service.register_endpoint(
                    url=f"http://127.0.0.1:{9000 + i}/mcp",
                    name=f"concurrent-mcp-{i}",
                    endpoint_type=EndpointType.MCP,
                )

            tasks = [register_endpoint(i) for i in range(10)]
            results = await asyncio.gather(*tasks)

            # Then: 모든 등록 성공
            assert len(results) == 10

            # 등록된 엔드포인트 조회
            endpoints = await registry_service.list_endpoints()
            assert len(endpoints) >= 10

            # 이름 중복 없음
            names = [e.name for e in endpoints]
            assert len(names) == len(set(names))
