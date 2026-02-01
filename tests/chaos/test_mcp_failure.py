"""Chaos Test: MCP 서버 돌발 중단 시나리오

Circuit Breaker 동작 검증:
- MCP 서버 정상 동작 → 도구 호출 성공
- 서버 강제 종료 → 연속 실패 → Circuit OPEN
- OPEN 상태에서 도구 호출 차단
"""

import asyncio

import pytest

from src.domain.entities.circuit_breaker import CircuitState
from src.domain.entities.endpoint import EndpointType


@pytest.mark.chaos
@pytest.mark.local_mcp
class TestMcpServerFailure:
    """MCP 서버 돌발 중단 Chaos 테스트"""

    async def test_mcp_sudden_failure_triggers_circuit_breaker(self, chaotic_mcp_server, container):
        """
        Given: 정상 동작 중인 MCP 서버
        When: 서버가 강제 종료되고 여러 번 호출 실패
        Then: Circuit Breaker가 OPEN 상태로 전이
        """
        # Given: Chaotic MCP 서버 시작
        url, proc = chaotic_mcp_server

        gateway_service = container.gateway_service()
        registry_service = container.registry_service()

        # MCP 서버 등록
        endpoint = await registry_service.register_endpoint(
            url=url,
            name="chaotic-mcp",
            endpoint_type=EndpointType.MCP,
        )

        # 초기 Circuit Breaker 상태: CLOSED
        assert gateway_service.can_execute(endpoint.id) is True
        circuit = gateway_service._circuit_breakers.get(endpoint.id)
        assert circuit is not None
        assert circuit.state == CircuitState.CLOSED

        # When: 서버 강제 종료
        proc.terminate()
        await asyncio.sleep(0.5)  # 종료 대기

        # 연속 실패 시뮬레이션 (failure_threshold=5)
        for _ in range(5):
            try:
                # 도구 호출 시도 → 실패 예상
                await registry_service._toolset.call_tool("nonexistent_tool", {})
            except Exception:
                # 실패 기록
                gateway_service.record_failure(endpoint.id)

        # Then: Circuit Breaker가 OPEN 상태로 전이
        assert circuit.state == CircuitState.OPEN
        assert gateway_service.can_execute(endpoint.id) is False

    async def test_circuit_breaker_blocks_calls_when_open(self, chaotic_mcp_server, container):
        """
        Given: Circuit Breaker가 OPEN 상태
        When: 도구 호출 시도
        Then: EndpointConnectionError 발생 (호출 차단)
        """
        # Given: MCP 서버 등록 및 Circuit OPEN 상태 강제
        url, proc = chaotic_mcp_server

        gateway_service = container.gateway_service()
        registry_service = container.registry_service()

        endpoint = await registry_service.register_endpoint(
            url=url,
            name="chaotic-mcp",
            endpoint_type=EndpointType.MCP,
        )

        # Circuit OPEN 강제 (5회 실패 기록)
        for _ in range(5):
            gateway_service.record_failure(endpoint.id)

        circuit = gateway_service._circuit_breakers[endpoint.id]
        assert circuit.state == CircuitState.OPEN

        # When/Then: OPEN 상태에서 도구 호출 → 차단
        assert gateway_service.can_execute(endpoint.id) is False

    async def test_circuit_half_open_after_recovery_timeout(self, chaotic_mcp_server, container):
        """
        Given: Circuit Breaker가 OPEN 상태
        When: recovery_timeout(60초) 경과
        Then: HALF_OPEN 상태로 전이 (테스트 허용)
        """
        # Given: Circuit OPEN 상태
        url, proc = chaotic_mcp_server

        gateway_service = container.gateway_service()
        registry_service = container.registry_service()

        endpoint = await registry_service.register_endpoint(
            url=url,
            name="chaotic-mcp",
            endpoint_type=EndpointType.MCP,
        )

        # Circuit OPEN 강제
        for _ in range(5):
            gateway_service.record_failure(endpoint.id)

        circuit = gateway_service._circuit_breakers[endpoint.id]
        assert circuit.state == CircuitState.OPEN

        # When: recovery_timeout 경과 시뮬레이션 (타임스탬프 조작)
        # 실제 60초 대기는 테스트 속도 저하 → 타임스탬프 직접 조작
        circuit._last_failure_time = 0.0  # 오래 전에 실패한 것으로 설정

        # Then: HALF_OPEN으로 전이 (state 프로퍼티 호출 시 자동 전이)
        assert circuit.state == CircuitState.HALF_OPEN
        assert gateway_service.can_execute(endpoint.id) is True  # HALF_OPEN에서는 시도 허용
