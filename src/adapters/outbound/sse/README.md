# SSE Adapters

Server-Sent Events (SSE) 기반 이벤트 브로드캐스팅 Outbound Adapters입니다.

---

## Overview

| 항목 | 값 |
|------|-----|
| **Protocol** | SSE (Server-Sent Events) |
| **Pattern** | Pub/Sub (Publisher-Subscriber) |
| **Backend** | asyncio.Queue |
| **Components** | SseBroker, HitlNotificationAdapter |

**핵심 기능:**
- SSE 이벤트 브로드캐스팅 (1:N 전송)
- HITL (Human-In-The-Loop) 알림 전송
- Sampling/Elicitation 요청 알림

---

## Components

### SseBroker

**파일:** [broker.py](broker.py)

**역할:** SSE 이벤트를 모든 구독자에게 브로드캐스트하는 Pub/Sub 브로커

**Port:** [EventBroadcastPort](../../../domain/ports/outbound/event_broadcast_port.py)

**주요 메서드:**
- `broadcast(event_type, data)` - 모든 구독자에게 이벤트 전송
- `subscribe()` - 이벤트 스트림 구독 (AsyncIterator)

**아키텍처:**
```
           broadcast()
                │
                ▼
          ┌─────────┐
          │ SseBroker│
          │  (Pub)   │
          └─────────┘
           │   │   │
      ┌────┘   │   └────┐
      ▼        ▼        ▼
   Queue1   Queue2   Queue3
      │        │        │
      ▼        ▼        ▼
   Client1  Client2  Client3
```

**Quick Start:**
```python
from src.adapters.outbound.sse.broker import SseBroker

broker = SseBroker()

# Subscriber (FastAPI SSE endpoint)
async def sse_stream():
    async for event in broker.subscribe():
        yield f"event: {event['type']}\n"
        yield f"data: {json.dumps(event['data'])}\n\n"

# Publisher (anywhere in the app)
await broker.broadcast(
    event_type="sampling_request",
    data={"request_id": "req-1", "endpoint_id": "ep-1"}
)
```

---

### HitlNotificationAdapter

**파일:** [hitl_notification_adapter.py](hitl_notification_adapter.py)

**역할:** HITL (Human-In-The-Loop) 요청을 SSE 이벤트로 브로드캐스트

**Port:** [HitlNotificationPort](../../../domain/ports/outbound/hitl_notification_port.py)

**주요 메서드:**
- `notify_sampling_request(request: SamplingRequest)` - Sampling 요청 알림
- `notify_elicitation_request(request: ElicitationRequest)` - Elicitation 요청 알림

**Event Format:**

**Sampling Request:**
```json
{
  "type": "sampling_request",
  "data": {
    "request_id": "req-123",
    "endpoint_id": "ep-1",
    "messages": [{"role": "user", "content": "..."}],
    "model_preferences": {...},
    "system_prompt": "...",
    "max_tokens": 1024,
    "timestamp": "2026-02-07T10:30:00Z"
  }
}
```

**Elicitation Request:**
```json
{
  "type": "elicitation_request",
  "data": {
    "request_id": "req-456",
    "endpoint_id": "ep-1",
    "message": "Please provide your input:",
    "requested_schema": {...},
    "timestamp": "2026-02-07T10:31:00Z"
  }
}
```

**Quick Start:**
```python
from src.adapters.outbound.sse.hitl_notification_adapter import HitlNotificationAdapter
from src.domain.entities.sampling_request import SamplingRequest

# Adapter 생성 (SseBroker 주입)
adapter = HitlNotificationAdapter(sse_broker)

# Sampling 요청 알림
request = SamplingRequest(
    id="req-1",
    endpoint_id="ep-1",
    messages=[{"role": "user", "content": "Hello"}],
    model_preferences={"temperature": 0.7},
    max_tokens=1024
)
await adapter.notify_sampling_request(request)

# → SseBroker를 통해 모든 SSE 구독자에게 전송됨
```

---

## Integration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    HITL Notification Flow                        │
└─────────────────────────────────────────────────────────────────┘

MCP Server (Synapse)
      │ Sampling Request
      ▼
McpClientAdapter (sampling_callback)
      │ Domain SamplingRequest
      ▼
HitlNotificationAdapter.notify_sampling_request()
      │ SSE Event
      ▼
SseBroker.broadcast("sampling_request", {...})
      │
      ▼
   ┌──────┬──────┬──────┐
   ▼      ▼      ▼      ▼
Client1 Client2 Client3 ...
(Extension, Playground, Admin)
```

**사용 시나리오:**
1. MCP 서버가 Sampling 요청 (Human approval 필요)
2. McpClientAdapter의 콜백이 Domain 형식으로 변환
3. HitlNotificationAdapter가 SSE 이벤트로 브로드캐스트
4. 모든 SSE 클라이언트(Extension, Playground 등)가 알림 수신
5. 사용자가 승인/거부 결정 → 원래 콜백으로 응답 반환

---

## Testing

### Integration Tests

**SseBroker:**
- **파일:** [tests/integration/test_sse_broker.py](../../../../tests/integration/test_sse_broker.py)
- **커버리지:** broadcast, subscribe, 다중 구독자, 구독 취소
- **실행:** `pytest tests/integration/test_sse_broker.py -v`

**HitlNotificationAdapter:**
- **파일:** [tests/integration/test_hitl_notification_adapter.py](../../../../tests/integration/test_hitl_notification_adapter.py)
- **커버리지:** Sampling 알림, Elicitation 알림, 이벤트 형식 검증
- **실행:** `pytest tests/integration/test_hitl_notification_adapter.py -v`

---

## Configuration

SSE Adapters는 설정 없이 즉시 사용 가능합니다. DI Container에서 자동 주입됩니다:

```python
# config/container.py
from src.adapters.outbound.sse.broker import SseBroker
from src.adapters.outbound.sse.hitl_notification_adapter import HitlNotificationAdapter

def get_sse_broker() -> SseBroker:
    return SseBroker()

def get_hitl_notification_adapter(
    sse_broker: SseBroker = Depends(get_sse_broker)
) -> HitlNotificationAdapter:
    return HitlNotificationAdapter(sse_broker)
```

---

## Performance Considerations

### Queue Size Limit

각 구독자의 Queue는 최대 100개 이벤트를 버퍼링합니다:

```python
queue: asyncio.Queue = asyncio.Queue(maxsize=100)
```

**초과 시 동작:**
- `queue.put()` 호출이 block되지 않고 즉시 반환 (`contextlib.suppress(Exception)`)
- 느린 클라이언트가 전체 시스템을 block하지 않음

**권장 사항:**
- 클라이언트는 이벤트를 빠르게 소비해야 함
- 100개 이상의 이벤트가 쌓이면 일부 이벤트 누락 가능

### Concurrency Safety

- `asyncio.Lock`으로 구독자 리스트 보호
- `broadcast()` 중 구독자 추가/제거 안전

---

## Related Documentation

- **Domain Entities:**
  - [SamplingRequest](../../../domain/entities/sampling_request.py)
  - [ElicitationRequest](../../../domain/entities/elicitation_request.py)

- **Ports:**
  - [EventBroadcastPort](../../../domain/ports/outbound/event_broadcast_port.py)
  - [HitlNotificationPort](../../../domain/ports/outbound/hitl_notification_port.py)

- **Architecture:**
  - [Method C Signal Pattern](../../../../docs/developers/architecture/layer/patterns/method-c-signal.md)

---

*Last Updated: 2026-02-07*
*Phase: 07 - Hybrid-Dual Architecture*
