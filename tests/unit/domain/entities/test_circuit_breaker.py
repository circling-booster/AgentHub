"""Circuit Breaker 엔티티 테스트 (TDD Red Phase)"""

import time

from src.domain.entities.circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreakerInitialization:
    """Circuit Breaker 초기화 테스트"""

    def test_initial_state_is_closed(self):
        """초기 상태는 CLOSED여야 함"""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED

    def test_default_thresholds(self):
        """기본 임계값 확인"""
        cb = CircuitBreaker()
        assert cb.failure_threshold == 5
        assert cb.recovery_timeout == 60.0

    def test_custom_thresholds(self):
        """사용자 정의 임계값"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 30.0


class TestCircuitBreakerStateTransitions:
    """Circuit Breaker 상태 전이 테스트"""

    def test_transitions_to_open_after_threshold(self):
        """실패 임계값 초과 시 OPEN으로 전이"""
        cb = CircuitBreaker(failure_threshold=3)

        # 임계값 이하: CLOSED 유지
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

        # 임계값 도달: OPEN으로 전이
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_transitions_to_half_open_after_timeout(self):
        """복구 타임아웃 후 HALF_OPEN으로 전이"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)  # 100ms 타임아웃

        # OPEN 상태로 전이
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # 타임아웃 전: OPEN 유지
        time.sleep(0.05)
        assert cb.state == CircuitState.OPEN

        # 타임아웃 후: HALF_OPEN으로 자동 전이
        time.sleep(0.1)
        assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_success_closes_circuit(self):
        """HALF_OPEN 상태에서 성공 시 CLOSED로 전이"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        # OPEN 상태로 전이
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # 타임아웃 후 HALF_OPEN
        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN

        # 성공 기록 → CLOSED 복구
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_half_open_failure_reopens_circuit(self):
        """HALF_OPEN 상태에서 실패 시 다시 OPEN으로"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        # OPEN 상태로 전이
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN

        # 실패 기록 → OPEN으로 재전이
        cb.record_failure()
        assert cb.state == CircuitState.OPEN


class TestCircuitBreakerExecutionControl:
    """Circuit Breaker 실행 제어 테스트"""

    def test_can_execute_when_closed(self):
        """CLOSED 상태에서는 실행 허용"""
        cb = CircuitBreaker()
        assert cb.can_execute() is True

    def test_cannot_execute_when_open(self):
        """OPEN 상태에서는 실행 차단"""
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.can_execute() is False

    def test_can_execute_when_half_open(self):
        """HALF_OPEN 상태에서는 테스트 실행 허용"""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        cb.record_failure()
        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.can_execute() is True


class TestCircuitBreakerSuccessReset:
    """Circuit Breaker 성공 카운터 리셋 테스트"""

    def test_success_resets_failure_count(self):
        """CLOSED 상태에서 성공 시 실패 카운터 리셋"""
        cb = CircuitBreaker(failure_threshold=3)

        # 실패 2회 누적
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

        # 성공 → 실패 카운터 리셋
        cb.record_success()

        # 다시 3회 실패해야 OPEN
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED  # 아직 CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN  # 이제 OPEN
