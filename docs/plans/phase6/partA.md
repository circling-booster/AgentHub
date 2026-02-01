# Phase 6 Part A: MCP Gateway + Cost Tracking + Chaos Tests (Steps 1-4)

> **상태:** 📋 Planned
> **선행 조건:** Phase 5 Complete
> **목표:** Circuit Breaker + Rate Limiting + Fallback, 비용 추적/예산 관리, Chaos Engineering
> **예상 테스트:** ~21 신규
> **실행 순서:** Step 1 → Step 2 → Step 3 → Step 4

---

## 🎯 Progress Checklist

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **1** | Circuit Breaker Entity | ⬜ |
| **2** | Gateway Service + MCP Integration | ⬜ |
| **3** | Cost Tracking & Budget Alert | ⬜ |
| **4** | Chaos Engineering Tests | ⬜ |

---

## Step 1: Circuit Breaker Entity

**목표:** 순수 Python 도메인 엔티티로 Circuit Breaker 상태 머신 구현

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/entities/circuit_breaker.py` | NEW | CircuitBreaker 상태 머신 (순수 Python) |
| `src/domain/entities/usage.py` | NEW | Usage 엔티티 (순수 Python) |
| `tests/unit/domain/entities/test_circuit_breaker.py` | NEW | 상태 전이 테스트 |
| `tests/unit/domain/entities/test_usage.py` | NEW | Usage 엔티티 테스트 |

**핵심 설계:**
```python
# src/domain/entities/circuit_breaker.py
from enum import Enum
from dataclasses import dataclass, field
import time

class CircuitState(Enum):
    CLOSED = "closed"      # 정상
    OPEN = "open"          # 차단 (failure_threshold 초과)
    HALF_OPEN = "half_open"  # 테스트 (recovery_timeout 후)

@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0.0, init=False)
    _success_count: int = field(default=0, init=False)

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def record_success(self) -> None: ...
    def record_failure(self) -> None: ...
    def can_execute(self) -> bool: ...
```

**TDD 순서:**
1. RED: `test_initial_state_is_closed`
2. RED: `test_transitions_to_open_after_threshold`
3. RED: `test_transitions_to_half_open_after_timeout`
4. RED: `test_half_open_success_closes_circuit`
5. GREEN: CircuitBreaker 구현

**DoD:**
- [ ] CLOSED → OPEN → HALF_OPEN → CLOSED 전체 전이 검증
- [ ] Usage 엔티티 생성/검증

---

## Step 2: Gateway Service + MCP Integration

**목표:** DynamicToolset을 래핑하는 Gateway 레이어 (CB + Rate Limit + Fallback)

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/services/gateway_service.py` | NEW | GatewayService (순수 Python 로직) |
| `src/adapters/outbound/adk/gateway_toolset.py` | NEW | DynamicToolset 래핑 Gateway |
| `src/config/settings.py` | MODIFY | GatewaySettings 추가 |
| `configs/default.yaml` | MODIFY | gateway 기본 설정 |
| `tests/unit/domain/services/test_gateway_service.py` | NEW | Gateway 서비스 테스트 |

**핵심 설계:**
```python
# gateway_toolset.py
class GatewayToolset(BaseToolset):
    """DynamicToolset을 Circuit Breaker + Rate Limiting으로 래핑"""

    def __init__(self, dynamic_toolset: DynamicToolset, gateway_service: GatewayService):
        self._toolset = dynamic_toolset
        self._gateway = gateway_service

    async def get_tools(self, readonly_context=None) -> list[BaseTool]:
        return await self._toolset.get_tools(readonly_context)

    async def call_tool_with_gateway(self, endpoint_id: str, tool_name: str, args: dict):
        if not self._gateway.can_execute(endpoint_id):
            raise EndpointConnectionError(f"Circuit breaker OPEN for {endpoint_id}")
        try:
            result = await self._toolset.call_tool(tool_name, args)
            self._gateway.record_success(endpoint_id)
            return result
        except Exception as e:
            self._gateway.record_failure(endpoint_id)
            raise
```

**TDD 순서:**
1. RED: `test_gateway_allows_when_circuit_closed`
2. RED: `test_gateway_blocks_when_circuit_open`
3. RED: `test_gateway_rate_limit_exceeded`
4. RED: `test_gateway_fallback_server`
5. GREEN: GatewayService, GatewayToolset 구현

**DoD:**
- [ ] Circuit Breaker 통합 동작
- [ ] Rate Limiting 동작
- [ ] Fallback 서버 전환 동작

---

## Step 3: Cost Tracking & Budget Alert

**목표:** LLM 호출 비용 추적, SQLite 저장, 예산 알림

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/services/cost_service.py` | NEW | CostService (비용 계산, 예산 검증) |
| `src/domain/ports/outbound/usage_port.py` | NEW | UsageStoragePort 인터페이스 |
| `src/adapters/outbound/storage/sqlite_usage.py` | NEW | SQLite usage 테이블 |
| `src/adapters/outbound/adk/litellm_callbacks.py` | MODIFY | cost 데이터 수집 확장 |
| `src/adapters/inbound/http/routes/usage.py` | NEW | Usage API 엔드포인트 |
| `src/config/settings.py` | MODIFY | CostSettings 추가 |
| `configs/default.yaml` | MODIFY | cost 기본 설정 |
| `tests/unit/domain/services/test_cost_service.py` | NEW | 비용 서비스 테스트 |
| `tests/integration/adapters/test_cost_tracking.py` | NEW | 비용 추적 통합 테스트 |

**API 엔드포인트:**
- `GET /api/usage/summary` - 기간별 사용량 요약
- `GET /api/usage/by-model` - 모델별 비용
- `GET /api/usage/budget` - 예산 상태
- `PUT /api/usage/budget` - 예산 설정

**핵심 설계:**
```python
# src/domain/services/cost_service.py
class CostService:
    def __init__(self, usage_port: UsageStoragePort, budget_usd: float = 100.0):
        self._storage = usage_port
        self._monthly_budget = budget_usd

    async def record_usage(self, usage: Usage) -> None: ...
    async def get_monthly_summary(self) -> dict: ...
    async def check_budget(self) -> BudgetStatus: ...
```

**테스트:** 10개 (엔티티 3 + 서비스 3 + API 2 + 콜백 2)

**DoD:**
- [ ] LLM 호출 시 비용 자동 기록
- [ ] 모델별/기간별 사용량 조회
- [ ] 예산 초과 시 경고

---

## Step 4: Chaos Engineering Tests

**의존성:** Step 2 (Circuit Breaker) 완료 필요

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `tests/chaos/test_mcp_failure.py` | NEW | MCP 서버 돌발 중단 시나리오 |
| `tests/chaos/test_llm_rate_limit.py` | NEW | LLM Rate Limit 시나리오 |
| `tests/chaos/test_concurrent_tools.py` | NEW | 동시 도구 호출 경합 시나리오 |
| `tests/chaos/conftest.py` | NEW | Chaos 테스트 fixture |
| `pyproject.toml` | MODIFY | `pytest.mark.chaos` 마커 등록 |

**3개 시나리오:**
1. MCP 서버 돌발 중단 → Circuit Breaker 활성화 → Degraded 모드 → 복구
2. LLM Rate Limit 429 → 재시도 → 복구
3. 동시 도구 호출 → 캐시 정합성 유지

**DoD:**
- [ ] 3개 Chaos 시나리오 통과
- [ ] `@pytest.mark.chaos` 마커 적용
- [ ] CI에서 선택적 실행 가능 (`pytest -m chaos`)

---

## Part A Definition of Done

### 기능
- [ ] Circuit Breaker: CLOSED → OPEN → HALF_OPEN → CLOSED 전이
- [ ] Rate Limiting: Token Bucket 동작
- [ ] Cost Tracking: LLM 비용 자동 기록 + API 조회
- [ ] Budget Alert: 예산 초과 경고
- [ ] Chaos Tests: 3개 시나리오 통과

### 품질
- [ ] Backend 21+ 테스트 추가
- [ ] Coverage >= 90% 유지
- [ ] TDD Red-Green-Refactor 사이클 준수

---

*Part A 계획 작성일: 2026-01-31*
