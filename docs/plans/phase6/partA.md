# Phase 6 Part A: MCP Gateway + Cost Tracking + Chaos Tests (Steps 1-4)

> **상태:** 📋 Planned
> **선행 조건:** Phase 5 Complete
> **목표:** Circuit Breaker + Rate Limiting + Fallback, 비용 추적/예산 관리, Chaos Engineering
> **예상 테스트:** ~21 신규
> **실행 순서:** Step 1 → Step 2 → Step 3 → Step 4

---

## Prerequisites

**선행 조건:**
- [x] Phase 5 Complete (2026-02-01)
- [x] Backend Coverage >= 91% (현재 91%)
- [x] Extension Tests 232 passing
- [ ] STEP 1 시작전 커밋
- [ ] 브랜치: `feature/phase-6` (신규 생성)

**Step별 검증 게이트:**

| Step | 구현 전 웹 검색 | 검증 시점 |
|:----:|----------------|----------|
| **1** | Circuit Breaker 패턴 best practices | Entity 설계 전 |
| **2** | Token Bucket 알고리즘 구현, DI Container Gateway 통합 | Service 구현 전 |
| **3** | LiteLLM cost tracking API, Budget 정책 패턴 | API 설계 전 |
| **4** | Chaos Engineering pytest fixture 패턴 | Fixture 구현 전 |

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

**TDD(SKILLS 호출) 순서(기재되지 않아도 구현 전 테스트 작성 필수):**
1. RED: `test_initial_state_is_closed`
2. RED: `test_transitions_to_open_after_threshold`
3. RED: `test_transitions_to_half_open_after_timeout`
4. RED: `test_half_open_success_closes_circuit`
5. GREEN: CircuitBreaker 구현
6. REFACTOR

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
| `src/config/settings.py` | MODIFY | GatewaySettings (rate_limit_rps, burst_size, fallback_enabled) |
| `src/config/container.py` | MODIFY | GatewayService, GatewayToolset DI 주입 (⚠️ DynamicToolset 교체) |
| `configs/default.yaml` | MODIFY | gateway 기본 설정 |
| `tests/unit/domain/services/test_gateway_service.py` | NEW | Gateway 서비스 테스트 |

**⚠️ DynamicToolset → GatewayToolset 통합 계획:**

Container.py 수정 영향:
```python
# Before (Phase 5):
dynamic_toolset = providers.Singleton(DynamicToolset, ...)
orchestrator_adapter = providers.Singleton(
    AdkOrchestratorAdapter,
    dynamic_toolset=dynamic_toolset,
    ...
)

# After (Phase 6 Part A):
dynamic_toolset = providers.Singleton(DynamicToolset, ...)  # 내부 사용
gateway_service = providers.Singleton(
    GatewayService,
    circuit_breaker_settings=...,
)
gateway_toolset = providers.Singleton(
    GatewayToolset,
    dynamic_toolset=dynamic_toolset,
    gateway_service=gateway_service,
)
orchestrator_adapter = providers.Singleton(
    AdkOrchestratorAdapter,
    dynamic_toolset=gateway_toolset,  # ⚠️ 교체
    ...
)
```

**영향 분석:**
- ✅ OrchestratorAdapter는 BaseToolset 인터페이스만 사용 → 호환성 유지
- ✅ GatewayToolset.get_tools()는 DynamicToolset 위임 → 기존 동작 유지
- ⚠️ 직접 call_tool() 호출 시 gateway_toolset.call_tool_with_gateway() 사용 필요
- ⚠️ Regression 테스트 필수 (기존 MCP 도구 호출 정상 동작 확인)

**핵심 설계:**

**1. Rate Limiting (Token Bucket 알고리즘):**
```python
# src/domain/services/gateway_service.py
@dataclass
class TokenBucket:
    capacity: int  # burst_size (예: 10)
    rate: float    # tokens/second (예: 5.0)
    _tokens: float = field(init=False)
    _last_refill: float = field(default_factory=time.time, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    async def consume(self, tokens: int = 1) -> bool:
        async with self._lock:  # 동시성 안전
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def _refill(self):
        now = time.time()
        elapsed = now - self._last_refill
        refill = elapsed * self.rate
        self._tokens = min(self.capacity, self._tokens + refill)
        self._last_refill = now
```

**2. Gateway Toolset:**
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
        # Circuit Breaker 확인
        if not self._gateway.can_execute(endpoint_id):
            raise EndpointConnectionError(f"Circuit breaker OPEN for {endpoint_id}")

        # Rate Limiting 확인
        if not await self._gateway.check_rate_limit(endpoint_id):
            raise RateLimitExceededError(f"Rate limit exceeded for {endpoint_id}")

        try:
            result = await self._toolset.call_tool(tool_name, args)
            self._gateway.record_success(endpoint_id)
            return result
        except Exception as e:
            self._gateway.record_failure(endpoint_id)
            # Fallback 서버 시도 (설정된 경우)
            if self._gateway.has_fallback(endpoint_id):
                return await self._try_fallback(endpoint_id, tool_name, args)
            raise

    async def _try_fallback(self, endpoint_id: str, tool_name: str, args: dict):
        """Fallback 서버로 도구 호출 시도"""
        fallback_url = self._gateway.get_fallback_url(endpoint_id)
        # Fallback 엔드포인트로 도구 호출 재시도
        ...
```

**3. GatewaySettings:**
```yaml
# configs/default.yaml
gateway:
  rate_limit_rps: 5.0        # requests per second
  burst_size: 10             # Token Bucket capacity
  fallback_enabled: true     # Fallback 서버 전환 활성화
```

**TDD(SKILLS 호출) 순서(기재되지 않아도 구현 전 테스트 작성 필수):**
1. RED: `test_gateway_allows_when_circuit_closed`
2. RED: `test_gateway_blocks_when_circuit_open`
3. RED: `test_gateway_rate_limit_exceeded`
4. RED: `test_gateway_fallback_server`
5. GREEN: GatewayService, GatewayToolset 구현
6. REFACTOR

**Fallback 서버 전환 메커니즘:**

Endpoint 엔티티 확장:
```python
# src/domain/entities/endpoint.py
@dataclass
class Endpoint:
    id: str
    name: str
    url: str
    type: EndpointType
    enabled: bool
    registered_at: datetime
    fallback_url: str | None = None  # 🆕 Fallback 서버 URL (선택적)
```

**전환 조건:**
1. Circuit Breaker OPEN 상태
2. `fallback_url`이 설정된 경우
3. Fallback 서버의 Circuit Breaker가 CLOSED 상태

**전환 로직:**
```python
# GatewayService
def get_active_url(self, endpoint_id: str) -> str:
    """현재 활성화된 URL 반환 (Primary or Fallback)"""
    endpoint = self._endpoints[endpoint_id]
    if self._circuit_breakers[endpoint_id].state == CircuitState.OPEN:
        if endpoint.fallback_url and self._is_fallback_healthy(endpoint_id):
            return endpoint.fallback_url  # Fallback 전환
    return endpoint.url  # Primary 유지
```

**DoD:**
- [ ] Circuit Breaker 통합 동작 (CLOSED → OPEN → HALF_OPEN 전이)
- [ ] Rate Limiting 동작 (Token Bucket 5 rps, burst 10)
- [ ] Fallback 서버 전환 동작 (Primary OPEN → Fallback 자동 전환 → Primary 복구)
- [ ] Endpoint 엔티티 `fallback_url` 필드 추가 (Regression 테스트 필수)

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
# src/domain/entities/usage.py
@dataclass
class BudgetStatus:
    """예산 상태"""
    monthly_budget: float       # 월 예산 (USD)
    current_spending: float     # 현재 지출 (USD)
    usage_percentage: float     # 사용률 (%)
    alert_level: str            # "safe" | "warning" | "critical" | "blocked"
    can_proceed: bool           # API 호출 허용 여부

    def get_alert_message(self) -> str:
        if self.alert_level == "warning":
            return f"Budget at {self.usage_percentage:.1f}% (${self.current_spending:.2f}/${self.monthly_budget:.2f})"
        elif self.alert_level == "critical":
            return f"Budget exceeded: {self.usage_percentage:.1f}% (${self.current_spending:.2f}/${self.monthly_budget:.2f})"
        elif self.alert_level == "blocked":
            return f"Budget hard limit reached. API calls blocked."
        return "Budget within safe limits"

# src/domain/services/cost_service.py
class CostService:
    """비용 추적 및 예산 관리 (순수 Python)"""

    # Budget 정책 임계값
    WARNING_THRESHOLD = 0.9    # 90%: 경고
    CRITICAL_THRESHOLD = 1.0   # 100%: 심각
    HARD_LIMIT_THRESHOLD = 1.1 # 110%: 차단

    def __init__(self, usage_port: UsageStoragePort, monthly_budget_usd: float = 100.0):
        self._storage = usage_port
        self._monthly_budget = monthly_budget_usd

    async def record_usage(self, usage: Usage) -> None:
        """LLM 호출 비용 기록"""
        await self._storage.save_usage(usage)

    async def get_monthly_summary(self) -> dict:
        """월별 사용량 요약"""
        ...

    async def check_budget(self) -> BudgetStatus:
        """예산 상태 확인 (경고/차단 여부)"""
        current_spending = await self._storage.get_monthly_total()
        usage_pct = current_spending / self._monthly_budget

        if usage_pct >= self.HARD_LIMIT_THRESHOLD:
            alert_level = "blocked"
            can_proceed = False  # 🚫 API 호출 차단
        elif usage_pct >= self.CRITICAL_THRESHOLD:
            alert_level = "critical"
            can_proceed = True   # ⚠️ 허용하되 Extension 경고 표시
        elif usage_pct >= self.WARNING_THRESHOLD:
            alert_level = "warning"
            can_proceed = True   # ⚠️ 허용하되 Extension 경고 표시
        else:
            alert_level = "safe"
            can_proceed = True

        return BudgetStatus(
            monthly_budget=self._monthly_budget,
            current_spending=current_spending,
            usage_percentage=usage_pct * 100,
            alert_level=alert_level,
            can_proceed=can_proceed,
        )
```

**Budget Alert 정책:**

| 사용률 | 상태 | 행동 | Extension UI |
|:------:|------|------|-------------|
| 0-89% | `safe` | 정상 처리 | 표시 없음 |
| 90-99% | `warning` | 정상 처리 | 🟡 노란색 경고 배지 |
| 100-109% | `critical` | 정상 처리 | 🟠 주황색 경고 배너 |
| 110%+ | `blocked` | API 호출 차단 (403 반환) | 🔴 빨간색 차단 메시지 |

**Extension 연동:**
- SSE 스트리밍 전: `check_budget()` 호출
- `can_proceed=False` 시 `BudgetExceededError` 발생 (403)
- Extension은 `/api/usage/budget` 주기적 폴링 (30초마다)
- 경고 상태일 때 Sidepanel 상단에 배너 표시

**테스트:** 10개 (엔티티 3 + 서비스 3 + API 2 + 콜백 2)

**DoD:**
- [ ] LLM 호출 시 비용 자동 기록
- [ ] 모델별/기간별 사용량 조회
- [ ] 예산 초과 시 경고/차단 (90% warning, 100% critical, 110% blocked)
- [ ] 모든 `/api/usage/*` 엔드포인트에 ExtensionAuthMiddleware 적용 (X-Extension-Token 검증)
- [ ] Budget 차단 시 403 반환 + `BudgetExceededError` 메시지

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

**1. MCP 서버 돌발 중단 (Circuit Breaker 검증):**
```python
# tests/chaos/conftest.py
@pytest.fixture
async def chaotic_mcp_server():
    """랜덤 타이밍에 종료되는 MCP 서버"""
    proc = subprocess.Popen(["python", "-m", "synapse", "--port", "9999"])
    await asyncio.sleep(2)  # 시작 대기

    yield "http://127.0.0.1:9999/mcp"

    # 중단 시뮬레이션
    proc.terminate()
    proc.wait(timeout=5)

# tests/chaos/test_mcp_failure.py
@pytest.mark.chaos
async def test_mcp_sudden_failure_triggers_circuit_breaker(chaotic_mcp_server):
    # MCP 서버 등록 → 도구 호출 → 서버 중단 → Circuit Breaker OPEN 확인
    ...
```

**2. LLM Rate Limit 429 (재시도 로직 검증):**
```python
@pytest.mark.chaos
async def test_llm_rate_limit_retry():
    with patch("litellm.completion") as mock_llm:
        # 처음 2번은 RateLimitError, 3번째는 성공
        mock_llm.side_effect = [
            RateLimitError("Rate limit exceeded"),
            RateLimitError("Rate limit exceeded"),
            {"choices": [{"message": {"content": "success"}}]},
        ]
        # 재시도 로직 검증
        ...
```

**3. 동시 도구 호출 (캐시 정합성):**
```python
@pytest.mark.chaos
async def test_concurrent_tool_calls_cache_consistency():
    # 100개 동시 요청 → 캐시 경쟁 조건 검증
    tasks = [call_tool("tool1", {}) for _ in range(100)]
    results = await asyncio.gather(*tasks)
    # 모든 결과가 동일한지 검증 (캐시 일관성)
    ...
```

**DoD:**
- [ ] 3개 Chaos 시나리오 통과
- [ ] `@pytest.mark.chaos` 마커 적용
- [ ] CI에서 선택적 실행 가능 (`pytest -m chaos`)
- [ ] Chaos fixture 재현성 보장 (conftest.py에 표준화)

---

## Skill/Agent 활용 전략

| 시점 | 호출 | 목적 |
|------|------|------|
| **Step 1 설계 전** | WebSearch | Circuit Breaker 패턴 best practices 검색 |
| **Step 2 설계 전** | WebSearch | Token Bucket 알고리즘, DI Container Gateway 통합 패턴 |
| **Step 3 설계 전** | WebSearch | LiteLLM cost tracking API, Budget 정책 패턴 |
| **Step 4 설계 전** | WebSearch | Chaos Engineering pytest fixture 패턴 |
| **각 Step 구현 전** | `/tdd` skill | Red-Green-Refactor 사이클 강제 |
| **Part A 완료 후** | `code-reviewer` agent | 헥사고날 아키텍처 준수 검증 |
| **API 추가 후 (Step 3)** | `security-reviewer` agent | `/api/usage/*` 보안 검증 |
| **Part A 완료 후** | ADR 작성 고려 | Circuit Breaker 패턴 채택 결정 (ADR-012, 선택적) |

---

## 커밋 정책

**브랜치:** `feature/phase-6`

**커밋 메시지 형식:**
```
feat(phase6): Step N - <간결한 설명>

- 구체적 변경 사항 1
- 구체적 변경 사항 2

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**예시:**
```bash
# Step 1 완료
git commit -m "feat(phase6): Step 1 - Circuit Breaker entity

- CircuitBreaker 상태 머신 (CLOSED/OPEN/HALF_OPEN)
- Usage 엔티티 (순수 Python)
- 상태 전이 테스트 5개

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Step 2 완료
git commit -m "feat(phase6): Step 2 - Gateway Service + MCP Integration

- GatewayService (Token Bucket Rate Limiting)
- GatewayToolset (DynamicToolset 래핑)
- Container.py DI 주입 (DynamicToolset → GatewayToolset)
- Gateway 통합 테스트 6개

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 리스크 및 대응

| # | 위험 요소 | 심각도 | 대응 방안 |
|---|----------|:------:|----------|
| 1 | **GatewayToolset 통합 영향** | 🔴 높음 | Regression 테스트 필수, OrchestratorAdapter 통합 검증 |
| 2 | **Circuit Breaker 오작동** | 🟡 중간 | Unit 테스트로 전체 상태 전이 검증, Chaos 테스트로 실패 시나리오 확인 |
| 3 | **Rate Limiting 동시성 안전성** | 🟡 중간 | TokenBucket에 asyncio.Lock 사용, 경쟁 조건 테스트 |
| 4 | **Budget 차단 오류** (false positive) | 🔴 높음 | 110% Hard Limit로 버퍼 확보, 관리자 예산 증액 API 제공 |
| 5 | **Chaos Tests 재현성** | 🟡 중간 | conftest.py fixture로 시뮬레이션 방법 표준화 |
| 6 | **API 보안 누락** | 🟡 중간 | Step 3 DoD에 ExtensionAuthMiddleware 적용 체크 추가 |
| 7 | **Cost 계산 정확도** | 🟢 낮음 | LiteLLM 공식 API 사용, 수동 검증 (OpenAI/Claude 대시보드) |

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
*최종 수정일: 2026-02-02 (plan-validator 검증 후 필수 수정 사항 반영)*
