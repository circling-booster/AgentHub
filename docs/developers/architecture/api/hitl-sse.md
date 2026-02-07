# HITL SSE Events API

HITL (Human-In-The-Loop) 요청을 SSE (Server-Sent Events) 스트림으로 실시간 수신합니다.

**Plan 07 Phase 6**에서 구현되었습니다.

---

## Overview

HITL SSE는 **Sampling** 및 **Elicitation** 요청을 실시간으로 Extension/Playground에 알림하기 위한 이벤트 스트림입니다.

**Use Cases:**
- Sampling 요청 발생 시 즉시 알림 (사용자 승인/거부 필요)
- Elicitation 요청 발생 시 즉시 알림 (사용자 입력 필요)

**Architecture Pattern:**
- **Pub/Sub**: SseBroker가 이벤트를 브로드캐스트
- **asyncio.Queue**: 구독자별로 독립적인 큐 관리
- **Keep-Alive**: 연결 즉시 `: ping\n\n` 전송 (테스트 용이성)

---

## Endpoint

```http
GET /api/hitl/events
```

**Authentication:** Token 인증 필요
```http
Authorization: Bearer <token>
```

**Response:** `200 OK` (Streaming)
```http
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

**Response Body (SSE Stream):**
```
: ping

event: sampling_request
data: {"request_id": "req-abc123", "endpoint_id": "test-endpoint", ...}

event: elicitation_request
data: {"request_id": "elicit-xyz789", "endpoint_id": "test-endpoint", ...}
```

---

## Event Types

### 1. `sampling_request`

LLM Sampling 요청이 발생했을 때 전송됩니다.

**Event Name:** `sampling_request`

**Data Schema:**
```json
{
  "request_id": "req-abc123",
  "endpoint_id": "test-endpoint",
  "messages": [
    {
      "role": "user",
      "content": {
        "type": "text",
        "text": "Hello"
      }
    }
  ],
  "model_preferences": {
    "hints": [
      { "name": "claude-3-5-sonnet-20241022" }
    ]
  },
  "system_prompt": "You are a helpful assistant",
  "max_tokens": 100
}
```

**Fields:**
- `request_id` (string): Sampling request unique ID
- `endpoint_id` (string): MCP Server endpoint ID
- `messages` (array): MCP Sampling 메시지 배열
- `model_preferences` (object): 모델 선호도 (hints)
- `system_prompt` (string, optional): 시스템 프롬프트
- `max_tokens` (number): 최대 토큰 수

**Action Required:**
사용자는 `/api/sampling/requests/{request_id}/approve` 또는 `/api/sampling/requests/{request_id}/reject` 엔드포인트로 응답해야 합니다.

---

### 2. `elicitation_request`

사용자 입력 요청이 발생했을 때 전송됩니다.

**Event Name:** `elicitation_request`

**Data Schema:**
```json
{
  "request_id": "elicit-xyz789",
  "endpoint_id": "test-endpoint",
  "message": "Please provide code review parameters",
  "requested_schema": {
    "type": "object",
    "properties": {
      "language": { "type": "string" },
      "style_guide": { "type": "string" }
    },
    "required": ["language"]
  }
}
```

**Fields:**
- `request_id` (string): Elicitation request unique ID
- `endpoint_id` (string): MCP Server endpoint ID
- `message` (string): 사용자에게 표시할 메시지
- `requested_schema` (object, optional): JSON Schema 형식의 입력 스키마

**Action Required:**
사용자는 `/api/elicitation/requests/{request_id}/respond` 엔드포인트로 응답해야 합니다.

---

## Client Implementation

### JavaScript (EventSource)

```javascript
const eventSource = new EventSource('http://localhost:8000/api/hitl/events', {
  headers: {
    'Authorization': 'Bearer <token>'
  }
});

// Sampling 요청 처리
eventSource.addEventListener('sampling_request', (event) => {
  const data = JSON.parse(event.data);
  console.log('Sampling Request:', data);

  // UI 업데이트 (승인/거부 버튼 표시)
  displaySamplingRequest(data);
});

// Elicitation 요청 처리
eventSource.addEventListener('elicitation_request', (event) => {
  const data = JSON.parse(event.data);
  console.log('Elicitation Request:', data);

  // UI 업데이트 (입력 폼 표시)
  displayElicitationRequest(data);
});

// 에러 처리
eventSource.onerror = (error) => {
  console.error('SSE Error:', error);
  eventSource.close();
};
```

### Python (httpx)

```python
import httpx

async with httpx.AsyncClient() as client:
    headers = {"Authorization": f"Bearer {token}"}
    async with client.stream("GET", "http://localhost:8000/api/hitl/events", headers=headers) as response:
        async for line in response.aiter_lines():
            if line.startswith("event:"):
                event_type = line.split(": ", 1)[1]
            elif line.startswith("data:"):
                data = json.loads(line.split(": ", 1)[1])
                print(f"{event_type}: {data}")
```

---

## SSE Stream Format

### Keep-Alive Ping

연결 즉시 전송되는 keep-alive 메시지:
```
: ping

```

**Purpose:**
- 연결 즉시 응답하여 연결 성공 확인
- E2E 테스트 용이성 (timeout 없이 즉시 응답 확인)

### Event Format

SSE 표준 형식:
```
event: {event_type}
data: {json_data}

```

**Example:**
```
event: sampling_request
data: {"request_id": "req-123", "endpoint_id": "ep-1", "messages": [...]}

```

---

## Error Handling

### Connection Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid token | 토큰 재발급 후 재연결 |
| `Connection timeout` | Network issue | 재연결 시도 (exponential backoff) |
| `Connection closed` | Server restart | 자동 재연결 |

### Reconnection Strategy

```javascript
let reconnectDelay = 1000; // 1초
const maxDelay = 60000; // 최대 60초

function connectSSE() {
  const eventSource = new EventSource('/api/hitl/events');

  eventSource.onerror = () => {
    eventSource.close();

    // Exponential backoff
    setTimeout(() => {
      reconnectDelay = Math.min(reconnectDelay * 2, maxDelay);
      connectSSE();
    }, reconnectDelay);
  };

  eventSource.onopen = () => {
    reconnectDelay = 1000; // 연결 성공 시 리셋
  };
}
```

---

## Architecture

### Component Diagram

```
┌──────────────────┐
│  MCP Server      │
│  (Sampling/      │
│   Elicitation)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ SamplingService  │
│ ElicitationSvc   │
└────────┬─────────┘
         │ notify_sampling_request()
         ▼
┌──────────────────┐
│ HitlNotification │
│    Adapter       │
└────────┬─────────┘
         │ broadcast()
         ▼
┌──────────────────┐
│   SseBroker      │
│   (Pub/Sub)      │
└────────┬─────────┘
         │ subscribe()
         ▼
┌──────────────────┐
│  /api/hitl/      │
│    events        │
│  (SSE Stream)    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Extension/       │
│ Playground       │
│ (EventSource)    │
└──────────────────┘
```

### Broker Pattern

**SseBroker** (Singleton):
- asyncio.Queue 기반 pub/sub
- 구독자별 독립 큐 (maxsize=100)
- Thread-safe (asyncio.Lock)

**Event Flow:**
1. Domain Service → `notify_sampling_request()`
2. HitlNotificationAdapter → `broadcast("sampling_request", {...})`
3. SseBroker → 모든 구독자 큐에 이벤트 전송
4. HTTP Route → `subscribe()` → SSE 스트림 생성
5. Client → EventSource → 이벤트 수신

---

## Testing

### Unit Test (Fake Adapter)

```python
# tests/unit/fakes/fake_event_broadcaster.py
class FakeEventBroadcaster(EventBroadcastPort):
    def __init__(self):
        self.events = []

    async def broadcast(self, event_type: str, data: dict):
        self.events.append({"type": event_type, "data": data})
```

### Integration Test

```python
# tests/integration/adapters/test_hitl_events_sse.py
async def test_sse_stream_emits_sampling_request(authenticated_client):
    # SSE 스트림 구독
    with authenticated_client.stream("GET", "/api/hitl/events") as response:
        # Sampling 요청 트리거
        trigger_sampling_request()

        # 이벤트 수신 확인
        for line in response.iter_lines():
            if line.startswith("event: sampling_request"):
                assert True
                break
```

### E2E Test (Playwright)

```python
# tests/e2e/test_playground.py
async def test_sse_events_display(page):
    await page.goto("http://localhost:9001")

    # SSE 연결 확인
    await page.wait_for_function("window.eventSource !== undefined")

    # Sampling 요청 트리거
    await trigger_sampling_request()

    # UI 업데이트 확인
    await page.wait_for_selector("#sampling-request-req-123")
```

---

## Related Documentation

- [SDK Track API](sdk-track.md) - Sampling/Elicitation API 엔드포인트
- [Method C Pattern](../../../project/decisions/architecture/ADR-A05-method-c-callback-centric.md) - Callback-centric LLM 배치
- [SSE Broker Implementation](../../../../src/adapters/outbound/sse/README.md) - SseBroker 아키텍처
- [Playground README](../../../../tests/manual/playground/README.md) - Playground UI 사용 가이드

---

## Security Considerations

### Token-Based Authentication

SSE 엔드포인트는 Token 인증을 요구합니다:
- EventSource는 기본적으로 Custom Header를 지원하지 않음
- **Workaround**: Query Parameter로 Token 전달 (개발 환경 전용)
- **Production**: Nginx/Proxy에서 Cookie 기반 인증 사용 권장

### Connection Limits

- 브라우저당 최대 6개 SSE 연결 (HTTP/1.1)
- HTTP/2 사용 시 제한 완화 가능

### Memory Management

- SseBroker: 구독자별 Queue maxsize=100
- 구독 종료 시 자동으로 큐 제거
- asyncio.Lock으로 race condition 방지

---

*Last Updated: 2026-02-07*
*Phase: Plan 07 Phase 6*
