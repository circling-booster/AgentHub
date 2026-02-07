"""GatewayService 테스트 (TDD Red-Green-Refactor)"""

import asyncio
import time

import pytest

from src.domain.entities.endpoint import Endpoint
from src.domain.entities.enums import EndpointType
from src.domain.services.gateway_service import GatewayService, TokenBucket


class TestTokenBucket:
    """Token Bucket Rate Limiting 테스트"""

    async def test_consume_success_when_tokens_available(self):
        """
        Given: Token Bucket with capacity 10, rate 5 tokens/sec
        When: consume(1) 호출
        Then: True 반환, tokens 감소
        """
        # Given
        bucket = TokenBucket(capacity=10, rate=5.0)

        # When
        result = await bucket.consume(1)

        # Then
        assert result is True

    async def test_consume_fail_when_no_tokens(self):
        """
        Given: Token Bucket with capacity 2
        When: consume(5) 호출 (용량 초과)
        Then: False 반환
        """
        # Given
        bucket = TokenBucket(capacity=2, rate=1.0)

        # When
        result = await bucket.consume(5)

        # Then
        assert result is False

    async def test_refill_over_time(self):
        """
        Given: Token Bucket with rate 10 tokens/sec
        When: 0.5초 대기 후 consume(5)
        Then: True 반환 (5 tokens 충전됨)
        """
        # Given
        bucket = TokenBucket(capacity=10, rate=10.0)
        await bucket.consume(10)  # 모든 토큰 소진

        # When
        await asyncio.sleep(0.5)  # 0.5초 대기 → 5 tokens 충전
        result = await bucket.consume(5)

        # Then
        assert result is True

    async def test_refill_does_not_exceed_capacity(self):
        """
        Given: Token Bucket with capacity 10, rate 10 tokens/sec
        When: 2초 대기 후 consume(15)
        Then: False (최대 10 tokens까지만 충전)
        """
        # Given
        bucket = TokenBucket(capacity=10, rate=10.0)

        # When
        await asyncio.sleep(2.0)  # 20 tokens 충전 시도
        result = await bucket.consume(15)

        # Then
        assert result is False  # 용량 초과


class TestGatewayService:
    """GatewayService 도메인 서비스 테스트"""

    def test_gateway_allows_when_circuit_closed(self):
        """
        Given: Circuit Breaker가 CLOSED 상태
        When: can_execute() 호출
        Then: True 반환
        """
        # Given
        endpoint = Endpoint(url="https://example.com/mcp", type=EndpointType.MCP)
        gateway = GatewayService(rate_limit_rps=5.0, burst_size=10)
        gateway.register_endpoint(endpoint)

        # When
        result = gateway.can_execute(endpoint.id)

        # Then
        assert result is True

    def test_gateway_blocks_when_circuit_open(self):
        """
        Given: Circuit Breaker가 OPEN 상태 (실패 임계값 초과)
        When: can_execute() 호출
        Then: False 반환
        """
        # Given
        endpoint = Endpoint(url="https://example.com/mcp", type=EndpointType.MCP)
        gateway = GatewayService(
            rate_limit_rps=5.0,
            burst_size=10,
            circuit_failure_threshold=3,
        )
        gateway.register_endpoint(endpoint)

        # 3번 실패 기록 → OPEN 전이
        for _ in range(3):
            gateway.record_failure(endpoint.id)

        # When
        result = gateway.can_execute(endpoint.id)

        # Then
        assert result is False

    async def test_gateway_rate_limit_exceeded(self):
        """
        Given: Rate Limit 5 rps (burst 10)
        When: 10개 동시 요청 후 추가 요청
        Then: 11번째 요청은 False
        """
        # Given
        endpoint = Endpoint(url="https://example.com/mcp", type=EndpointType.MCP)
        gateway = GatewayService(rate_limit_rps=5.0, burst_size=10)
        gateway.register_endpoint(endpoint)

        # When: 10개 요청 성공
        for _ in range(10):
            result = await gateway.check_rate_limit(endpoint.id)
            assert result is True

        # 11번째 요청은 실패 (burst 초과)
        result = await gateway.check_rate_limit(endpoint.id)

        # Then
        assert result is False

    def test_gateway_fallback_server(self):
        """
        Given: Primary 서버 OPEN, Fallback URL 설정
        When: get_active_url() 호출
        Then: Fallback URL 반환
        """
        # Given
        endpoint = Endpoint(
            url="https://primary.example.com/mcp",
            type=EndpointType.MCP,
            fallback_url="https://backup.example.com/mcp",
        )
        gateway = GatewayService(
            rate_limit_rps=5.0,
            burst_size=10,
            circuit_failure_threshold=3,
        )
        gateway.register_endpoint(endpoint)

        # Primary 서버 3번 실패 → OPEN
        for _ in range(3):
            gateway.record_failure(endpoint.id)

        # When
        active_url = gateway.get_active_url(endpoint.id)

        # Then
        assert active_url == "https://backup.example.com/mcp"

    def test_gateway_primary_url_when_no_fallback(self):
        """
        Given: Fallback URL 미설정
        When: get_active_url() 호출
        Then: Primary URL 반환 (Circuit OPEN이어도)
        """
        # Given
        endpoint = Endpoint(
            url="https://primary.example.com/mcp",
            type=EndpointType.MCP,
        )
        gateway = GatewayService(
            rate_limit_rps=5.0,
            burst_size=10,
            circuit_failure_threshold=3,
        )
        gateway.register_endpoint(endpoint)

        # Primary 서버 3번 실패 → OPEN
        for _ in range(3):
            gateway.record_failure(endpoint.id)

        # When
        active_url = gateway.get_active_url(endpoint.id)

        # Then
        assert active_url == "https://primary.example.com/mcp"

    def test_gateway_record_success_resets_failure_count(self):
        """
        Given: 2번 실패 후
        When: record_success() 호출
        Then: failure_count 리셋, Circuit 유지
        """
        # Given
        endpoint = Endpoint(url="https://example.com/mcp", type=EndpointType.MCP)
        gateway = GatewayService(
            rate_limit_rps=5.0,
            burst_size=10,
            circuit_failure_threshold=5,
        )
        gateway.register_endpoint(endpoint)

        gateway.record_failure(endpoint.id)
        gateway.record_failure(endpoint.id)

        # When
        gateway.record_success(endpoint.id)

        # 추가 2번 실패 (총 4번이었으면 OPEN이었을 것)
        gateway.record_failure(endpoint.id)
        gateway.record_failure(endpoint.id)

        # Then
        assert gateway.can_execute(endpoint.id) is True  # 여전히 CLOSED

    def test_gateway_half_open_recovery(self):
        """
        Given: Circuit OPEN → 60초 경과 → HALF_OPEN
        When: record_success() 호출
        Then: CLOSED로 복구
        """
        # Given
        endpoint = Endpoint(url="https://example.com/mcp", type=EndpointType.MCP)
        gateway = GatewayService(
            rate_limit_rps=5.0,
            burst_size=10,
            circuit_failure_threshold=3,
            circuit_recovery_timeout=0.1,  # 0.1초로 테스트 단축
        )
        gateway.register_endpoint(endpoint)

        # OPEN 전이
        for _ in range(3):
            gateway.record_failure(endpoint.id)

        assert gateway.can_execute(endpoint.id) is False  # OPEN

        # When: 0.1초 대기 → HALF_OPEN
        time.sleep(0.15)
        assert gateway.can_execute(endpoint.id) is True  # HALF_OPEN

        gateway.record_success(endpoint.id)

        # Then
        assert gateway.can_execute(endpoint.id) is True  # CLOSED
