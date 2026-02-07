# Method C: Signal Pattern (asyncio.Event-based HITL Queue)

> Method C 패턴은 LLM 호출과 HITL(Human-in-the-Loop) 큐를 분리하여 헥사고날 아키텍처를 준수하면서도 유연한 승인 흐름을 제공합니다.

---

## Overview

**핵심 원리:**
- LLM 호출: Route에서 OrchestratorPort를 통해 수행
- HITL 큐: SamplingService/ElicitationService가 asyncio.Event 기반 Signal 패턴으로 관리
- 콜백 대기: RegistryService 콜백에서 wait_for_response()로 시그널 대기
- 결과 전달: Route가 approve()/respond()로 시그널 전송

**장점:**
- 헥사고날 아키텍처 준수 (Route는 OrchestratorPort 사용)
- Domain Layer 순수성 유지 (외부 SDK 의존성 없음)
- 미래 대비 (ADK native sampling 지원 시 콜백만 변경)
- 유연성 (Hybrid Timeout 전략 지원)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Route Layer                              │
│                                                                   │
│  POST /api/sampling/requests/{id}/approve                        │
│  1. orchestrator.generate_response(messages)  ← OrchestratorPort │
│  2. sampling_service.approve(request_id, llm_result)  ← Signal   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓ Signal (asyncio.Event.set())
┌─────────────────────────────────────────────────────────────────┐
│                    Domain Service Layer                          │
│                                                                   │
│  SamplingService                                                  │
│  ├─ create_request(request) → Event 생성                         │
│  ├─ wait_for_response(timeout) → Event.wait() ⏳                │
│  ├─ approve(request_id, llm_result) → Event.set() 🔔           │
│  └─ reject(request_id, reason) → Event.set() 🔔                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↑ wait_for_response()
┌─────────────────────────────────────────────────────────────────┐
│                    Callback (RegistryService)                    │
│                                                                   │
│  async def sampling_callback(...):                                │
│      request = SamplingRequest(...)                               │
│      await sampling_service.create_request(request)               │
│                                                                   │
│      # Short timeout (30s)                                        │
│      result = await sampling_service.wait_for_response(30.0)      │
│      if result is None:                                           │
│          # SSE 알림 → Extension                                   │
│          await hitl_notification.notify_sampling_request(request) │
│          # Long timeout (270s)                                    │
│          result = await sampling_service.wait_for_response(270.0) │
│                                                                   │
│      if result is None or result.status == REJECTED:              │
│          raise HitlTimeoutError(...)                              │
│                                                                   │
│      return result.llm_result  # MCP 서버에 반환                 │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Flow Diagram

```
MCP Server                   Callback                    Service                     Route
    │                          │                          │                          │
    │  invoke tool             │                          │                          │
    ├─────────────────────────>│                          │                          │
    │                          │  create_request()        │                          │
    │                          ├─────────────────────────>│                          │
    │                          │                          │  (Event 생성)            │
    │                          │                          │                          │
    │                          │  wait_for_response(30s)  │                          │
    │                          ├─────────────────────────>│                          │
    │                          │                          │  Event.wait() ⏳         │
    │                          │                          │                          │
    │                          │                          │ SSE Notification         │
    │                          │                          ├─────────────────────────>│
    │                          │                          │                          │
    │                          │                          │                          │ User clicks "Approve"
    │                          │                          │                          │ POST /api/sampling/.../approve
    │                          │                          │  approve(id, llm_result) │
    │                          │                          │<─────────────────────────┤
    │                          │                          │  Event.set() 🔔          │
    │                          │  return result           │                          │
    │                          │<─────────────────────────┤                          │
    │  sampling result         │                          │                          │
    │<─────────────────────────┤                          │                          │
    │                          │                          │                          │
```

---

## Components

### 1. Domain Service (Signal Manager)

**SamplingService:**
```python
class SamplingService:
    def __init__(self, ttl_seconds: int = 600):
        self._requests: dict[str, SamplingRequest] = {}
        self._events: dict[str, asyncio.Event] = {}
        self._ttl_seconds = ttl_seconds

    async def create_request(self, request: SamplingRequest) -> None:
        """요청 생성 및 Event 준비"""
        self._requests[request.id] = request
        self._events[request.id] = asyncio.Event()

    async def wait_for_response(
        self, request_id: str, timeout: float = 30.0
    ) -> SamplingRequest | None:
        """Event.wait() 대기 (timeout 시 None)"""
        if request_id not in self._events:
            return None
        try:
            await asyncio.wait_for(
                self._events[request_id].wait(),
                timeout=timeout
            )
            return self._requests.get(request_id)
        except asyncio.TimeoutError:
            return None

    async def approve(self, request_id: str, llm_result: dict) -> bool:
        """Signal 전송 (Event.set())"""
        if request_id not in self._requests:
            return False
        request = self._requests[request_id]
        request.status = SamplingStatus.APPROVED
        request.llm_result = llm_result
        if request_id in self._events:
            self._events[request_id].set()  # 🔔 Wake up callback
        return True
```

### 2. Route (LLM Caller)

**Sampling Approval Route:**
```python
@router.post("/api/sampling/requests/{request_id}/approve")
async def approve_sampling_request(
    request_id: str,
    orchestrator: Provide[OrchestratorPort],
    sampling_service: Provide[SamplingService],
):
    # 1. Get request
    request = sampling_service.get_request(request_id)
    if not request:
        raise HTTPException(404, "Request not found")

    # 2. Call LLM (via OrchestratorPort)
    llm_result = await orchestrator.generate_response(
        endpoint_id=request.endpoint_id,
        messages=request.messages,
        model_preferences=request.model_preferences,
    )

    # 3. Signal to waiting callback
    await sampling_service.approve(request_id, llm_result)

    return {"status": "approved"}
```

### 3. Callback (RegistryService)

**Callback Creation:**
```python
def _create_sampling_callback(self) -> SamplingCallback:
    async def callback(
        messages: list[dict[str, str]],
        model_preferences: dict | None,
        **kwargs,
    ) -> dict:
        request = SamplingRequest(
            id=generate_id(),
            endpoint_id=endpoint_id,
            messages=messages,
            model_preferences=model_preferences,
        )
        await self._sampling_service.create_request(request)

        # Hybrid Timeout Strategy (30s + 270s)
        result = await self._sampling_service.wait_for_response(
            request.id, timeout=30.0
        )
        if result is None:
            # SSE notification to Extension
            await self._hitl_notification.notify_sampling_request(request)
            # Additional wait
            result = await self._sampling_service.wait_for_response(
                request.id, timeout=270.0
            )

        if result is None or result.status == SamplingStatus.REJECTED:
            raise HitlTimeoutError("Sampling request timed out or rejected")

        return result.llm_result

    return callback
```

---

## Key Design Decisions

### 1. LLM 호출 위치: Route

**근거:**
- 헥사고날 아키텍처 준수: Route는 OrchestratorPort 인터페이스 사용
- Domain Layer 순수성 유지: SamplingService는 순수 HITL 큐 역할만
- 테스트 용이성: Route 테스트 시 FakeOrchestrator로 LLM 호출 제어

**대안 거부:**
- Method A (콜백 내 LLM 호출): 헥사고날 위반 (Domain에서 Adapter 의존)
- Method B (Service 내 LLM 호출): 동일한 헥사고날 위반

**참조:** [ADR-A05: Method C — Callback-Centric LLM Placement](../../../../project/decisions/architecture/ADR-A05-method-c-callback-centric.md)

### 2. Signal 메커니즘: asyncio.Event

**장점:**
- 표준 라이브러리 (외부 의존성 없음)
- 단순성 (set/wait만으로 충분)
- 효율성 (polling 불필요)

**대안 거부:**
- asyncio.Queue: 불필요한 복잡도 (1:1 매칭만 필요)
- Condition Variable: 과도한 동기화 (단일 Event로 충분)

### 3. Hybrid Timeout Strategy

**구조:**
- Short timeout (30s): 빠른 응답 대기
- SSE 알림: Extension에 통지
- Long timeout (270s): 비동기 승인 대기

**참조:** [ADR-A06: Hybrid Timeout Strategy](../../../../project/decisions/architecture/ADR-A06-hybrid-timeout-strategy.md)

---

## Testing Strategy

### Unit Test Pattern

**asyncio.Event 기반 테스트:**
```python
async def test_wait_for_response_returns_after_signal(self):
    """wait_for_response() - 시그널 후 즉시 반환"""
    service = SamplingService()
    request = SamplingRequest(id="req-1", endpoint_id="ep-1", messages=[])
    await service.create_request(request)

    # Background task: 1초 후 approve
    async def delayed_approve():
        await asyncio.sleep(1.0)
        await service.approve("req-1", {"content": "test"})

    asyncio.create_task(delayed_approve())

    # 30초 타임아웃이지만 1초 내 반환됨
    result = await service.wait_for_response("req-1", timeout=30.0)

    assert result is not None
    assert result.status == SamplingStatus.APPROVED
```

**Timeout 테스트:**
```python
async def test_wait_for_response_timeout(self):
    """wait_for_response() - timeout → None"""
    service = SamplingService()
    request = SamplingRequest(id="req-1", endpoint_id="ep-1", messages=[])
    await service.create_request(request)

    # approve 없이 0.1초 timeout
    result = await service.wait_for_response("req-1", timeout=0.1)

    assert result is None  # Timeout
```

**참조:** [tests/docs/WritingGuide.md](../../../../../tests/docs/WritingGuide.md) - asyncio.Event 테스트 레시피

---

## Integration with RegistryService

**콜백 등록:**
```python
async def connect_sdk_session(self, endpoint: Endpoint) -> None:
    """SDK Track 세션 연결 (콜백 등록)"""
    sampling_callback = self._create_sampling_callback()
    elicitation_callback = self._create_elicitation_callback()

    await self._mcp_client.connect(
        endpoint_id=endpoint.id,
        url=endpoint.url,
        sampling_callback=sampling_callback,
        elicitation_callback=elicitation_callback,
    )
```

---

## ElicitationService (동일 패턴)

ElicitationService도 동일한 Signal 패턴 사용:
- `create_request()` → Event 생성
- `wait_for_response()` → Event.wait()
- `respond(action, content)` → Event.set()

**차이점:**
- Sampling: approve/reject (LLM 결과 전달)
- Elicitation: respond(ACCEPT/DECLINE/CANCEL, content) (사용자 입력 전달)

---

## Related Documents

- [ADR-A05: Method C — Callback-Centric LLM Placement](../../../../project/decisions/architecture/ADR-A05-method-c-callback-centric.md)
- [ADR-A06: Hybrid Timeout Strategy](../../../../project/decisions/architecture/ADR-A06-hybrid-timeout-strategy.md)
- [Core Layer: Services](../core/README.md)
- [Test Writing Guide: asyncio.Event Patterns](../../../../../tests/docs/WritingGuide.md)

---

*Last Updated: 2026-02-07*
*Phase: Plan 07 Phase 3 (Domain Services)*
