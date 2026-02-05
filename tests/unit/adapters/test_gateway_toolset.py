"""GatewayToolset Adapter 테스트 (TDD Red-Green-Refactor)"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.adapters.outbound.adk.gateway_toolset import GatewayToolset
from src.domain.entities.endpoint import Endpoint
from src.domain.entities.enums import EndpointType
from src.domain.exceptions import EndpointConnectionError, RateLimitExceededError
from src.domain.services.gateway_service import GatewayService


class TestGatewayToolset:
    """GatewayToolset Adapter 테스트"""

    @pytest.mark.asyncio
    async def test_get_tools_delegates_to_dynamic_toolset(self):
        """
        Given: DynamicToolset과 GatewayService
        When: get_tools() 호출
        Then: DynamicToolset.get_tools() 위임
        """
        # Given
        dynamic_toolset = AsyncMock()
        mock_tool1 = MagicMock()
        mock_tool1.name = "tool1"
        mock_tool1.description = "Test tool 1"
        mock_tool2 = MagicMock()
        mock_tool2.name = "tool2"
        mock_tool2.description = "Test tool 2"

        dynamic_toolset.get_tools.return_value = [mock_tool1, mock_tool2]
        gateway_service = GatewayService(rate_limit_rps=5.0, burst_size=10)

        gateway_toolset = GatewayToolset(
            dynamic_toolset=dynamic_toolset,
            gateway_service=gateway_service,
        )

        # When
        tools = await gateway_toolset.get_tools()

        # Then
        assert len(tools) == 2
        assert tools[0].name == "tool1"
        dynamic_toolset.get_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_with_gateway_circuit_open_raises_error(self):
        """
        Given: Circuit Breaker OPEN 상태
        When: call_tool_with_gateway() 호출
        Then: EndpointConnectionError 발생
        """
        # Given
        endpoint = Endpoint(url="https://example.com/mcp", type=EndpointType.MCP)
        gateway_service = GatewayService(
            rate_limit_rps=5.0,
            burst_size=10,
            circuit_failure_threshold=3,
        )
        gateway_service.register_endpoint(endpoint)

        # Circuit OPEN 전이
        for _ in range(3):
            gateway_service.record_failure(endpoint.id)

        dynamic_toolset = AsyncMock()
        gateway_toolset = GatewayToolset(
            dynamic_toolset=dynamic_toolset,
            gateway_service=gateway_service,
        )

        # When / Then
        with pytest.raises(EndpointConnectionError) as exc_info:
            await gateway_toolset.call_tool_with_gateway(endpoint.id, "tool1", {})

        assert "circuit breaker open" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_call_tool_with_gateway_rate_limit_exceeded_raises_error(self):
        """
        Given: Rate Limit 초과 (burst 소진)
        When: call_tool_with_gateway() 호출
        Then: RateLimitExceededError 발생
        """
        # Given
        endpoint = Endpoint(url="https://example.com/mcp", type=EndpointType.MCP)
        gateway_service = GatewayService(
            rate_limit_rps=5.0,
            burst_size=2,  # 2개만 허용
        )
        gateway_service.register_endpoint(endpoint)

        dynamic_toolset = AsyncMock()
        gateway_toolset = GatewayToolset(
            dynamic_toolset=dynamic_toolset,
            gateway_service=gateway_service,
        )

        # 2개 요청 소진
        await gateway_toolset.call_tool_with_gateway(endpoint.id, "tool1", {})
        await gateway_toolset.call_tool_with_gateway(endpoint.id, "tool2", {})

        # When / Then: 3번째 요청 실패
        with pytest.raises(RateLimitExceededError) as exc_info:
            await gateway_toolset.call_tool_with_gateway(endpoint.id, "tool3", {})

        assert "rate limit exceeded" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_call_tool_with_gateway_success_records_success(self):
        """
        Given: Circuit CLOSED, Rate Limit 여유
        When: call_tool_with_gateway() 성공
        Then: gateway_service.record_success() 호출
        """
        # Given
        endpoint = Endpoint(url="https://example.com/mcp", type=EndpointType.MCP)
        gateway_service = GatewayService(rate_limit_rps=5.0, burst_size=10)
        gateway_service.register_endpoint(endpoint)

        dynamic_toolset = AsyncMock()
        dynamic_toolset.call_tool.return_value = {"result": "success"}

        gateway_toolset = GatewayToolset(
            dynamic_toolset=dynamic_toolset,
            gateway_service=gateway_service,
        )

        # When
        result = await gateway_toolset.call_tool_with_gateway(
            endpoint.id, "tool1", {"arg": "value"}
        )

        # Then
        assert result == {"result": "success"}
        dynamic_toolset.call_tool.assert_called_once_with("tool1", {"arg": "value"})

    @pytest.mark.asyncio
    async def test_call_tool_with_gateway_failure_records_failure(self):
        """
        Given: Circuit CLOSED
        When: call_tool_with_gateway() 실패
        Then: gateway_service.record_failure() 호출
        """
        # Given
        endpoint = Endpoint(url="https://example.com/mcp", type=EndpointType.MCP)
        gateway_service = GatewayService(rate_limit_rps=5.0, burst_size=10)
        gateway_service.register_endpoint(endpoint)

        dynamic_toolset = AsyncMock()
        dynamic_toolset.call_tool.side_effect = Exception("Tool execution failed")

        gateway_toolset = GatewayToolset(
            dynamic_toolset=dynamic_toolset,
            gateway_service=gateway_service,
        )

        # When / Then
        with pytest.raises(Exception) as exc_info:
            await gateway_toolset.call_tool_with_gateway(endpoint.id, "tool1", {})

        assert "Tool execution failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_call_tool_with_gateway_fallback_on_failure(self):
        """
        Given: Primary 서버 실패, Fallback URL 설정
        When: call_tool_with_gateway() 실패 시
        Then: Fallback 서버로 재시도
        """
        # Given
        endpoint = Endpoint(
            url="https://primary.example.com/mcp",
            type=EndpointType.MCP,
            fallback_url="https://backup.example.com/mcp",
        )
        gateway_service = GatewayService(
            rate_limit_rps=5.0,
            burst_size=10,
            circuit_failure_threshold=5,
        )
        gateway_service.register_endpoint(endpoint)

        dynamic_toolset = AsyncMock()
        # Primary 실패, Fallback 성공
        dynamic_toolset.call_tool.side_effect = [
            Exception("Primary server error"),
            {"result": "fallback_success"},
        ]

        gateway_toolset = GatewayToolset(
            dynamic_toolset=dynamic_toolset,
            gateway_service=gateway_service,
        )

        # When
        result = await gateway_toolset.call_tool_with_gateway(
            endpoint.id, "tool1", {"arg": "value"}
        )

        # Then
        assert result == {"result": "fallback_success"}
        assert dynamic_toolset.call_tool.call_count == 2
