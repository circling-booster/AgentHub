"""Circuit Breaker 엔티티 (순수 Python, 외부 의존성 없음)"""

import time
from dataclasses import dataclass, field
from enum import Enum


class CircuitState(Enum):
    """Circuit Breaker 상태"""

    CLOSED = "closed"  # 정상 (요청 허용)
    OPEN = "open"  # 차단 (요청 거부, 실패 임계값 초과)
    HALF_OPEN = "half_open"  # 테스트 (복구 시도, 타임아웃 후)


@dataclass
class CircuitBreaker:
    """
    Circuit Breaker 패턴 구현 (순수 Python)

    상태 전이:
    - CLOSED → OPEN: failure_count >= failure_threshold
    - OPEN → HALF_OPEN: 자동 (recovery_timeout 경과 후)
    - HALF_OPEN → CLOSED: 성공 기록 시
    - HALF_OPEN → OPEN: 실패 기록 시

    참고:
    - https://pypi.org/project/circuitbreaker/
    - https://github.com/danielfm/pybreaker
    """

    failure_threshold: int = 5  # 연속 실패 임계값
    recovery_timeout: float = 60.0  # 복구 대기 시간 (초)

    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0.0, init=False)

    @property
    def state(self) -> CircuitState:
        """
        현재 상태 반환 (자동 전이 포함)

        OPEN 상태에서 recovery_timeout 경과 시 자동으로 HALF_OPEN 전이
        """
        if self._state == CircuitState.OPEN:
            elapsed = time.time() - self._last_failure_time
            if elapsed >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def record_success(self) -> None:
        """
        성공 기록

        - CLOSED: 실패 카운터 리셋
        - HALF_OPEN: CLOSED로 복구
        """
        if self._state == CircuitState.HALF_OPEN:
            # HALF_OPEN → CLOSED 복구
            self._state = CircuitState.CLOSED

        # 실패 카운터 리셋
        self._failure_count = 0

    def record_failure(self) -> None:
        """
        실패 기록

        - CLOSED: 실패 카운터 증가, 임계값 도달 시 OPEN
        - HALF_OPEN: 즉시 OPEN으로 재전이
        """
        if self._state == CircuitState.HALF_OPEN:
            # HALF_OPEN → OPEN 재전이
            self._state = CircuitState.OPEN
            self._last_failure_time = time.time()
            return

        # CLOSED 상태에서 실패 카운터 증가
        self._failure_count += 1
        self._last_failure_time = time.time()

        # 임계값 도달 시 OPEN 전이
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN

    def can_execute(self) -> bool:
        """
        실행 가능 여부 반환

        - CLOSED: True (정상)
        - OPEN: False (차단)
        - HALF_OPEN: True (테스트 허용)
        """
        current_state = self.state  # 자동 전이 트리거
        return current_state != CircuitState.OPEN
