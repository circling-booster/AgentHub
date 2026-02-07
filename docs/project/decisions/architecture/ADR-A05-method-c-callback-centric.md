# ADR-A05: Method C — Callback-Centric LLM Placement

## Status

Accepted

## Context

Plan 07에서 MCP Sampling 콜백을 구현하면서 **LLM 호출 위치**를 결정해야 했습니다.

MCP Sampling 콜백은 blocking await로 동작하며, MCP 서버는 LLM 응답을 기다립니다:

```python
async def sampling_callback(messages, model_preferences, ...):
    # 여기서 LLM 호출 - MCP 서버가 대기
    llm_result = await ???  # 어디서 호출할 것인가?
    return llm_result
```

### 문제점

1. **헥사고날 위반 우려**: Domain Service가 직접 LLM을 호출하면 Adapter 의존성 발생
2. **콜백 내 제어 흐름**: 콜백 안에서 LLM을 호출하면 Domain 로직이 Adapter 레이어로 유출
3. **테스트 복잡도**: 콜백의 blocking 특성으로 인한 테스트 작성 어려움

세 가지 대안을 검토했습니다.

## Decision

**Method C — Callback-Centric (Route에서 LLM 호출, Service는 Signal만 담당)** 을 채택합니다.

### 아키텍처

```
┌──────────────────────────────────────────────────────────────┐
│                     HTTP Route (Adapter)                      │
│                                                                │
│  1. POST /sampling/requests/{id}/approve                      │
│  2. orchestrator.generate_response() ← Port 사용              │
│  3. sampling_service.approve(id, llm_result) ← Signal         │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │   SamplingService     │
                  │   (Domain)            │
                  │                       │
                  │  wait_for_response()  │
                  │     ↓                 │
                  │  asyncio.Event.wait() │
                  │     ↓                 │
                  │  approve() → set()    │
                  └───────────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │  Callback awakens     │
                  │  (RegistryService)    │
                  │  Return llm_result    │
                  └───────────────────────┘
```

### 핵심 원리

1. **LLM 호출 위치**: HTTP Route에서 `orchestrator_port.generate_response()` 호출
2. **Signal 패턴**: `sampling_service.approve(request_id, llm_result)`로 결과 전달
3. **콜백 깨우기**: `asyncio.Event.wait()`가 시그널받고 MCP 서버에 반환

### 코드 예시

```python
# src/adapters/inbound/http/routes/sampling.py
@router.post("/requests/{request_id}/approve")
async def approve_sampling_request(
    request_id: str,
    sampling_service: SamplingService = Depends(...),
    orchestrator: OrchestratorPort = Depends(...),  # Port 사용
):
    # 1. 요청 조회
    request = sampling_service.get_request(request_id)

    # 2. LLM 호출 (Route에서 - Port 통해)
    llm_result = await orchestrator.generate_response(
        messages=request.messages,
        model=request.model_preferences.get("model"),
        system_prompt=request.system_prompt,
        max_tokens=request.max_tokens,
    )

    # 3. Signal (콜백이 깨어남)
    await sampling_service.approve(request_id, llm_result)

    return {"status": "approved", "result": llm_result}
```

## Consequences

### Positive

- **헥사고날 준수**: Route는 Adapter 레이어이므로 Port를 통한 LLM 호출 합법
- **Domain 순수성 유지**: SamplingService는 순수 Python으로 유지 (asyncio만 사용)
- **ADK Native 대응**: 추후 ADK가 native sampling을 지원하면 콜백 부분만 변경
- **테스트 용이**: Fake Port로 LLM 응답을 제어 가능

### Negative

- **Route 복잡도 증가**: Route가 LLM 호출과 Signal 전달을 모두 담당
- **Route-Service 강결합**: approve 엔드포인트가 SamplingService 내부 구조에 의존

### Neutral

- 사용자 승인 UX는 30초 Short timeout + 270초 Long timeout으로 별도 해결 (ADR-A06 참조)

## Alternatives Considered

### 1. Method A — Service Owns LLM

SamplingService가 직접 orchestrator_port를 의존성으로 받아 LLM 호출

```python
# src/domain/services/sampling_service.py
class SamplingService:
    def __init__(self, orchestrator: OrchestratorPort):  # ❌ Domain → Port 의존
        self._orchestrator = orchestrator
```

**장점:**
- Route가 간단함 (approve 엔드포인트가 단순히 service.approve() 호출)

**단점:**
- **헥사고날 위반**: Domain Service가 Outbound Port에 의존
- Domain 레이어가 Adapter 레이어를 알게 됨

**채택 안 한 이유:** 헥사고날 아키텍처의 핵심 원칙 위반

---

### 2. Method B — Callback 내 직접 호출

RegistryService의 콜백 내부에서 직접 orchestrator.generate_response() 호출

```python
# src/domain/services/registry_service.py
async def _create_sampling_callback(self, endpoint_id: str):
    async def mcp_callback(request_id, messages, ...):
        # ❌ 콜백 내부에서 LLM 직접 호출
        llm_result = await self._orchestrator.generate_response(messages, ...)
        return llm_result
```

**장점:**
- Route가 LLM 호출을 몰라도 됨
- 콜백이 자체 완결적

**단점:**
- **Domain 침범**: RegistryService가 Domain 레이어인데 Adapter Port 의존
- **사용자 승인 불가**: 콜백이 즉시 LLM 호출하므로 HITL 흐름 구현 불가

**채택 안 한 이유:** HITL 요구사항(사용자 승인)을 만족하지 못함

---

### 3. Method C — Callback-Centric (Route → Service Signal) ✅

**채택됨** (위 Decision 섹션 참조)

## References

- [Plan 07 Phase 3: Domain Services](../../planning/active/07_hybrid_dual/03_domain_services.md) - SamplingService 구현
- [Plan 07 Phase 6: HTTP Routes](../../planning/active/07_hybrid_dual/06_http_routes.md) - Method C 적용
- [ADR-A06: Hybrid Timeout Strategy](./ADR-A06-hybrid-timeout-strategy.md) - HITL UX 전략
- [CLAUDE.md](../../../../CLAUDE.md#hexagonal-architecture) - Hexagonal Architecture 원칙

---

*Created: 2026-02-06*
