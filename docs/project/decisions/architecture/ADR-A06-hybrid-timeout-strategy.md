# ADR-A06: Hybrid Timeout Strategy

## Status

Accepted

## Context

Plan 07에서 MCP Sampling 콜백 구현 시 **HITL(Human-in-the-Loop) 타임아웃 전략**을 결정해야 했습니다.

### 문제점

MCP Sampling 콜백은 **blocking await**로 동작합니다:

```python
async def sampling_callback(messages, ...):
    # MCP 서버가 여기서 대기
    user_response = await sampling_service.wait_for_response(request_id, timeout=???)
    return user_response
```

**트레이드오프:**
1. **짧은 timeout (예: 5초)**: 빠른 실패, 하지만 사용자가 응답할 시간 부족
2. **긴 timeout (예: 300초)**: 사용자가 충분히 응답할 수 있지만, MCP 서버가 오래 blocking됨
3. **무한 대기**: MCP 서버가 영원히 대기 → 시스템 안정성 문제

### UX 요구사항

- 사용자가 **즉시 승인** 가능해야 함 (빠른 경로)
- 사용자가 **나중에 승인** 가능해야 함 (비동기 경로)
- MCP 서버가 **무한정 blocking**되면 안 됨

## Decision

**Hybrid Timeout (30s + 270s) 전략을 채택합니다.**

### 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│              MCP Sampling Callback (Blocking)                │
│                                                               │
│  1. wait_for_response(timeout=30s)  ← Short timeout         │
│     │                                                         │
│     ├─ 승인됨 (< 30s) → 즉시 반환 ✅                          │
│     │                                                         │
│     └─ Timeout (≥ 30s)                                       │
│        ├─ SSE 알림 → Extension에 통지                         │
│        ├─ wait_for_response(timeout=270s)  ← Long timeout   │
│        │  │                                                   │
│        │  ├─ 승인됨 (30s ~ 300s) → 반환 ✅                     │
│        │  │                                                   │
│        │  └─ Timeout (≥ 300s) → TIMED_OUT 반환 ❌             │
└─────────────────────────────────────────────────────────────┘
```

### 타임라인 예시

**케이스 1: 빠른 승인 (< 30초)**
```
T=0s   : MCP 콜백 시작, wait_for_response(30s)
T=5s   : 사용자 승인 버튼 클릭
T=5s   : MCP 콜백 즉시 반환 (LLM 결과)
```

**케이스 2: 느린 승인 (30초 ~ 300초)**
```
T=0s   : MCP 콜백 시작, wait_for_response(30s)
T=30s  : Short timeout 발생
T=30s  : SSE 알림 → Extension에 "Sampling Request: req-123"
T=30s  : wait_for_response(270s) 재시도
T=60s  : 사용자가 Extension에서 승인
T=60s  : MCP 콜백 반환 (총 60초 소요)
```

**케이스 3: 타임아웃 (≥ 300초)**
```
T=0s   : MCP 콜백 시작, wait_for_response(30s)
T=30s  : Short timeout, SSE 알림
T=30s  : wait_for_response(270s)
T=300s : Long timeout 발생
T=300s : MCP 콜백 TIMED_OUT 반환
```

### 구현

```python
# src/domain/services/sampling_service.py
async def wait_for_response(
    self,
    request_id: str,
    short_timeout: float = 30.0,
    long_timeout: float = 270.0,
) -> dict[str, Any]:
    """Hybrid Timeout 전략으로 응답 대기"""
    # Phase 1: Short timeout (빠른 승인)
    try:
        await asyncio.wait_for(
            self._events[request_id].wait(),
            timeout=short_timeout
        )
        return self._requests[request_id].llm_result
    except asyncio.TimeoutError:
        # SSE 알림 전송
        await self._hitl_notification.notify_sampling_request(
            self._requests[request_id]
        )

    # Phase 2: Long timeout (비동기 승인)
    try:
        await asyncio.wait_for(
            self._events[request_id].wait(),
            timeout=long_timeout
        )
        return self._requests[request_id].llm_result
    except asyncio.TimeoutError:
        # 완전 타임아웃
        self._requests[request_id].status = SamplingStatus.TIMED_OUT
        raise TimeoutError(f"Request {request_id} timed out")
```

## Consequences

### Positive

- **빠른 승인 지원**: 30초 이내 승인 시 즉시 반환 (UX 우수)
- **비동기 승인 지원**: 30초 이후에도 270초까지 승인 가능 (유연성)
- **시스템 안정성**: 최대 300초 후 강제 종료 (무한 blocking 방지)
- **SSE 알림**: Extension이 30초 후 자동으로 알림 수신

### Negative

- **복잡도 증가**: 이중 timeout 로직으로 코드 복잡도 상승
- **부분적 blocking**: 최대 300초 동안 MCP 서버 blocking (하지만 허용 가능)

### Neutral

- **타임아웃 조정 가능**: `short_timeout`과 `long_timeout`을 설정으로 제공 가능

## Alternatives Considered

### 1. Single Timeout (30초만)

단일 30초 timeout만 사용

**장점:**
- 구현 간단
- MCP 서버가 빨리 해제됨

**단점:**
- 사용자가 30초 내에 응답하지 못하면 실패
- 비동기 승인 불가

**채택 안 한 이유:** UX 불만족 (30초는 너무 짧음)

---

### 2. Long Timeout Only (300초)

단일 300초 timeout만 사용

**장점:**
- 구현 간단
- 사용자가 충분히 응답할 시간

**단점:**
- **SSE 알림 없음**: 사용자가 300초 기다려야 Extension에서 알림 확인
- 빠른 승인 시에도 Extension이 즉시 알림받지 못함

**채택 안 한 이유:** 빠른 승인 시 즉시 피드백 불가

---

### 3. Hybrid Timeout (30s + 270s) ✅

**채택됨** (위 Decision 섹션 참조)

---

### 4. Infinite Timeout + Background Job

무한 timeout + 백그라운드 작업으로 정리

**장점:**
- 사용자가 언제든 승인 가능

**단점:**
- **시스템 안정성 문제**: MCP 서버가 영원히 blocking
- **리소스 누수**: 오래된 요청이 메모리에 계속 남음

**채택 안 한 이유:** 프로덕션 환경에서 위험

## References

- [Plan 07 Phase 3: Domain Services](../../planning/active/07_hybrid_dual/03_domain_services.md) - SamplingService 구현
- [Plan 07 Phase 4: Adapter Implementation](../../planning/active/07_hybrid_dual/04_adapter_implementation.md) - HitlNotificationAdapter
- [ADR-A05: Method C](./ADR-A05-method-c-callback-centric.md) - LLM 호출 위치
- [CLAUDE.md](../../../../CLAUDE.md#quick-reference) - HITL Timeout 전략

---

*Created: 2026-02-06*
