"""Gateway Service - Circuit Breaker + Rate Limiting (순수 Python)"""

import asyncio
import time
from dataclasses import dataclass, field

from src.domain.entities.circuit_breaker import CircuitBreaker, CircuitState
from src.domain.entities.endpoint import Endpoint


@dataclass
class TokenBucket:
    """
    Token Bucket Rate Limiting 알고리즘 (asyncio 동시성 안전)

    참고:
    - https://aiolimiter.readthedocs.io/
    - https://pypi.org/project/pyrate-limiter/
    - https://johal.in/ratelimit-python-slowapi-token-bucket-async-throttling-2025/

    Attributes:
        capacity: 최대 토큰 수 (burst size)
        rate: 초당 토큰 충전 속도 (tokens/second)
    """

    capacity: int  # burst_size (예: 10)
    rate: float  # tokens/second (예: 5.0)

    _tokens: float = field(init=False)
    _last_refill: float = field(default_factory=time.time, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def __post_init__(self) -> None:
        """초기화 시 토큰 full capacity로 시작"""
        self._tokens = float(self.capacity)

    async def consume(self, tokens: int = 1) -> bool:
        """
        토큰 소비 (동시성 안전)

        Args:
            tokens: 소비할 토큰 수

        Returns:
            토큰이 충분하면 True, 부족하면 False
        """
        async with self._lock:  # 동시성 안전
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def _refill(self) -> None:
        """경과 시간에 따라 토큰 충전 (capacity 초과 불가)"""
        now = time.time()
        elapsed = now - self._last_refill
        refill_amount = elapsed * self.rate
        self._tokens = min(self.capacity, self._tokens + refill_amount)
        self._last_refill = now


class GatewayService:
    """
    Gateway 서비스 - Circuit Breaker + Rate Limiting + Fallback (순수 Python)

    DynamicToolset을 래핑하여 안정성 및 확장성을 제공합니다.

    기능:
    - Circuit Breaker: 연속 실패 시 엔드포인트 차단
    - Rate Limiting: Token Bucket 알고리즘으로 요청 속도 제한
    - Fallback: Primary 서버 장애 시 Fallback 서버로 자동 전환

    참고:
    - https://python-dependency-injector.ets-labs.org/introduction/di_in_python.html
    - https://snir-orlanczyk.medium.com/python-di-dependency-injection-part-2-containers-c621f4311d55
    """

    def __init__(
        self,
        rate_limit_rps: float = 5.0,
        burst_size: int = 10,
        circuit_failure_threshold: int = 5,
        circuit_recovery_timeout: float = 60.0,
    ):
        """
        Args:
            rate_limit_rps: 초당 요청 제한 (requests per second)
            burst_size: Token Bucket capacity (burst 허용)
            circuit_failure_threshold: Circuit Breaker 실패 임계값
            circuit_recovery_timeout: Circuit Breaker 복구 대기 시간 (초)
        """
        self._rate_limit_rps = rate_limit_rps
        self._burst_size = burst_size
        self._circuit_failure_threshold = circuit_failure_threshold
        self._circuit_recovery_timeout = circuit_recovery_timeout

        # Endpoint별 Circuit Breaker 및 Rate Limiter
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._rate_limiters: dict[str, TokenBucket] = {}
        self._endpoints: dict[str, Endpoint] = {}

    def register_endpoint(self, endpoint: Endpoint) -> None:
        """
        엔드포인트 등록 (Circuit Breaker + Rate Limiter 초기화)

        Args:
            endpoint: 등록할 엔드포인트
        """
        self._endpoints[endpoint.id] = endpoint
        self._circuit_breakers[endpoint.id] = CircuitBreaker(
            failure_threshold=self._circuit_failure_threshold,
            recovery_timeout=self._circuit_recovery_timeout,
        )
        self._rate_limiters[endpoint.id] = TokenBucket(
            capacity=self._burst_size,
            rate=self._rate_limit_rps,
        )

    def can_execute(self, endpoint_id: str) -> bool:
        """
        실행 가능 여부 (Circuit Breaker 상태 확인)

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            Circuit이 CLOSED 또는 HALF_OPEN이면 True, OPEN이면 False
        """
        if endpoint_id not in self._circuit_breakers:
            return False
        return self._circuit_breakers[endpoint_id].can_execute()

    async def check_rate_limit(self, endpoint_id: str) -> bool:
        """
        Rate Limit 확인 (Token Bucket)

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            토큰이 충분하면 True, 부족하면 False
        """
        if endpoint_id not in self._rate_limiters:
            return False
        return await self._rate_limiters[endpoint_id].consume(1)

    def record_success(self, endpoint_id: str) -> None:
        """
        성공 기록 (Circuit Breaker)

        Args:
            endpoint_id: 엔드포인트 ID
        """
        if endpoint_id in self._circuit_breakers:
            self._circuit_breakers[endpoint_id].record_success()

    def record_failure(self, endpoint_id: str) -> None:
        """
        실패 기록 (Circuit Breaker)

        Args:
            endpoint_id: 엔드포인트 ID
        """
        if endpoint_id in self._circuit_breakers:
            self._circuit_breakers[endpoint_id].record_failure()

    def get_active_url(self, endpoint_id: str) -> str:
        """
        현재 활성화된 URL 반환 (Primary or Fallback)

        Circuit Breaker가 OPEN이고 Fallback URL이 설정되어 있으면 Fallback 반환

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            활성 URL (Primary or Fallback)
        """
        endpoint = self._endpoints.get(endpoint_id)
        if not endpoint:
            return ""

        circuit_breaker = self._circuit_breakers.get(endpoint_id)
        if circuit_breaker and circuit_breaker.state == CircuitState.OPEN and endpoint.fallback_url:
            return endpoint.fallback_url

        return endpoint.url

    def has_fallback(self, endpoint_id: str) -> bool:
        """
        Fallback URL 설정 여부

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            Fallback URL이 설정되어 있으면 True
        """
        endpoint = self._endpoints.get(endpoint_id)
        return bool(endpoint and endpoint.fallback_url)

    def get_fallback_url(self, endpoint_id: str) -> str | None:
        """
        Fallback URL 반환

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            Fallback URL 또는 None
        """
        endpoint = self._endpoints.get(endpoint_id)
        return endpoint.fallback_url if endpoint else None
