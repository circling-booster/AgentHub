# SSE Streaming Debugging

SSE (Server-Sent Events) 스트리밍 디버깅 및 문제 해결 가이드입니다.

---

## SSE 이벤트 구조

### Chat 스트리밍

**Event Types:**
```json
{"type":"text","content":"Hello! How can I help you?"}
{"type":"tool_call","tool":"get_weather","args":{"city":"Seoul"}}
{"type":"tool_result","result":{"temperature":15,"condition":"sunny"}}
{"type":"done"}
```

**Field Descriptions:**
- `type`: 이벤트 유형 (`text`, `tool_call`, `tool_result`, `done`)
- `content`: 텍스트 응답 내용 (type=text)
- `tool`: 호출된 도구 이름 (type=tool_call)
- `args`: 도구 인자 (type=tool_call)
- `result`: 도구 실행 결과 (type=tool_result)

### Workflow 스트리밍

**Event Types:**
```json
{"type":"workflow_start","workflow_id":"wf-123"}
{"type":"step_start","step_number":1,"total_steps":3}
{"type":"step_complete","step_number":1,"result":{...}}
{"type":"workflow_complete","status":"success"}
```

**Field Descriptions:**
- `workflow_id`: Workflow 고유 ID
- `step_number`: 현재 단계 번호 (1-indexed)
- `total_steps`: 전체 단계 수
- `result`: 단계 실행 결과
- `status`: Workflow 최종 상태 (`success`, `failed`)

---

## 브라우저 DevTools 활용

### 1. Network 탭

**SSE 연결 확인:**
1. DevTools 열기 (F12)
2. Network 탭 선택
3. Filter: "EventStream" 또는 "stream" 입력
4. Chat 메시지 전송 또는 Workflow 실행
5. `/api/chat/stream` 또는 `/api/workflows/execute` 요청 확인

**확인 사항:**
- **Status**: 200 OK (정상 연결)
- **Type**: eventsource
- **Size**: (pending) 또는 실시간 증가
- **Time**: 연결 유지 시간

**Headers 확인:**
```
Response Headers:
Content-Type: text/event-stream; charset=utf-8
Cache-Control: no-cache
Connection: keep-alive
```

**EventStream 탭:**
- 수신된 SSE 이벤트 실시간 표시
- 각 이벤트의 data 필드 확인

### 2. Console 탭

**EventSource 상태 확인:**
```javascript
// Playground의 SSE Handler 확인
const es = new EventSource("http://localhost:8000/api/chat/stream?message=Hello");

console.log(es.readyState);
// 0: CONNECTING - 연결 중
// 1: OPEN - 연결됨
// 2: CLOSED - 닫힘

es.onmessage = (event) => {
  console.log("Event:", event.data);
};

es.onerror = (error) => {
  console.error("SSE Error:", error);
  console.log("ReadyState:", es.readyState);
};
```

**수동 테스트:**
```javascript
// Playground console에서 실행
const testSSE = (message) => {
  const es = new EventSource(
    `http://localhost:8000/api/chat/stream?message=${encodeURIComponent(message)}`
  );

  es.onmessage = (e) => console.log(JSON.parse(e.data));
  es.onerror = (e) => { console.error(e); es.close(); };

  return es; // 나중에 es.close() 호출 가능
};

// 사용:
const stream = testSSE("Hello, AgentHub!");
// 테스트 종료 시:
// stream.close();
```

### 3. Sources 탭

**JavaScript Breakpoints:**
1. Sources 탭 → `js/sse-handler.js` 파일 열기
2. `onmessage` 핸들러에 breakpoint 설정
3. Chat 메시지 전송
4. 각 이벤트마다 breakpoint 실행 → 이벤트 데이터 검사

**Conditional Breakpoints:**
```javascript
// type이 "tool_call"일 때만 멈춤
data.type === "tool_call"
```

---

## 문제 해결

### 연결이 즉시 종료됨

**증상:**
- SSE Events 패널에 이벤트 없음
- Network 탭에서 요청이 즉시 완료됨 (pending 없음)

**원인:**
1. 백엔드에서 `done` 이벤트를 즉시 전송
2. 백엔드 에러 발생 (SSE 스트림 시작 전 실패)
3. CORS 에러로 연결 차단

**확인:**
1. SSE Events 패널 확인: 마지막 이벤트가 `{"type":"done"}`인지
2. Console 확인: CORS 에러 메시지
3. 백엔드 로그 확인 (uvicorn 출력):
   ```
   ERROR: Exception in ASGI application
   ```

**해결:**
- **빠른 종료 (정상)**: 응답이 짧아서 즉시 종료 (문제 아님)
- **CORS 에러**: `.env`에 `DEV_MODE=true` 설정 → 백엔드 재시작
- **백엔드 에러**: 로그에서 스택 트레이스 확인 → 버그 수정

### 이벤트가 수신되지 않음

**증상:**
- Network 탭에서 pending 상태 유지
- SSE Events 패널 비어있음
- Playground SSE 로그 패널에 "connected" 표시만

**원인:**
1. CORS preflight 실패 (OPTIONS 요청 차단)
2. 백엔드에서 SSE 이벤트 전송 안함
3. EventSource readyState가 CONNECTING에서 멈춤

**확인:**
1. Network 탭 → OPTIONS 요청 확인:
   ```
   OPTIONS /api/chat/stream
   Status: 200 OK
   Access-Control-Allow-Origin: http://localhost:3000
   Access-Control-Allow-Methods: GET, POST, OPTIONS
   ```
2. Console → EventSource readyState:
   ```javascript
   console.log(es.readyState); // 1이어야 정상 (OPEN)
   ```
3. 백엔드 로그 → SSE 이벤트 생성 확인

**해결:**
- **CORS preflight 실패**: DEV_MODE 확인 → 백엔드 재시작
- **이벤트 미전송**: 백엔드 로직 버그 → `yield f"data: {json.dumps(...)}\n\n"` 확인
- **CONNECTING 멈춤**: 네트워크 문제 → 방화벽/프록시 확인

### JSON 파싱 에러

**증상:**
- Console에 `SyntaxError: Unexpected token...` 에러
- SSE Events 패널에 잘못된 형식 표시

**원인:**
1. 백엔드에서 잘못된 JSON 전송 (따옴표 이스케이프 실패)
2. SSE 형식 오류 (`data: ` 접두사 누락)
3. 중복 이벤트 전송

**확인:**
1. Network 탭 → EventStream 탭 → raw 데이터 확인:
   ```
   data: {"type":"text","content":"Hello"}

   data: {"type":"done"}
   ```
2. Console → 에러 메시지:
   ```
   SyntaxError: Unexpected token < in JSON at position 0
   ```
3. 백엔드 로그 → 직렬화 에러:
   ```
   TypeError: Object of type ... is not JSON serializable
   ```

**해결:**
- **잘못된 JSON**: 백엔드에서 `json.dumps()` 사용 확인
- **SSE 형식 오류**: `data: ` 접두사 및 `\n\n` 구분자 확인
- **직렬화 에러**: Pydantic 스키마 사용 → `.model_dump()` 또는 `.dict()`

### 연결이 중간에 끊김

**증상:**
- 이벤트를 일부 수신하다가 갑자기 종료
- Console에 `EventSource error` 출력
- Network 탭에서 연결 상태: (failed)

**원인:**
1. 백엔드 타임아웃 (서버 설정)
2. 네트워크 연결 끊김
3. 백엔드 예외 발생 (try-except 누락)

**확인:**
1. Network 탭 → Timing 탭:
   ```
   Waiting (TTFB): 100ms
   Content Download: 5.2s
   (cancelled)
   ```
2. 백엔드 로그 → 예외 스택 트레이스
3. 타임아웃 설정:
   ```bash
   # uvicorn timeout (기본 60초)
   uvicorn src.main:app --timeout-keep-alive 300
   ```

**해결:**
- **타임아웃**: uvicorn `--timeout-keep-alive` 증가
- **예외 발생**: 백엔드에서 try-except 추가 → 에러 이벤트 전송:
  ```python
  try:
      # SSE 이벤트 생성
      pass
  except Exception as e:
      yield f"data: {json.dumps({'type':'error','message':str(e)})}\n\n"
  ```
- **네트워크 끊김**: 클라이언트 재연결 로직 추가

---

## Playground SSE 로그 활용

### 실시간 이벤트 확인

**SSE Events 패널 (우측):**
- 각 이벤트 자동 JSON 포맷팅
- 타임스탬프 표시
- 스크롤 자동 이동 (최신 이벤트)

**연결 상태 표시:**
- `connected` (녹색): EventSource OPEN 상태
- `disconnected` (빨강): EventSource CLOSED 또는 ERROR
- `done` 이벤트 수신 시 자동 종료

### 이벤트 필터링

**Console에서 특정 타입만 표시:**
```javascript
// main.js에서 appendSseLog() 호출 전 필터 추가
if (data.type === "text") {
  appendSseLog(data);
}
```

**디버깅용 상세 로그:**
```javascript
// sse-handler.js onmessage 수정
this.onMessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("SSE Event:", {
    type: data.type,
    timestamp: new Date().toISOString(),
    data: data
  });
  onData(data);
};
```

---

## Advanced Debugging

### Backend SSE 로깅

**`src/adapters/inbound/http/routes/chat.py`:**
```python
async def _generate_chat_stream(...):
    logger.info(f"SSE stream started: conversation_id={conversation_id}")

    try:
        for chunk in orchestrator.chat_stream(...):
            event_data = {...}
            logger.debug(f"SSE event: {event_data}")
            yield f"data: {json.dumps(event_data)}\n\n"

        logger.info("SSE stream completed")
        yield f"data: {json.dumps({'type':'done'})}\n\n"

    except Exception as e:
        logger.error(f"SSE stream error: {e}", exc_info=True)
        yield f"data: {json.dumps({'type':'error','message':str(e)})}\n\n"
```

### EventSource Reconnection

**자동 재연결:**
```javascript
// sse-handler.js 개선
class SseHandler {
  constructor(url, onData, onError, onComplete, maxRetries = 3) {
    this.maxRetries = maxRetries;
    this.retryCount = 0;
  }

  connect() {
    this.eventSource = new EventSource(this.url);

    this.eventSource.onerror = (error) => {
      console.error("SSE error", error);

      if (this.retryCount < this.maxRetries) {
        this.retryCount++;
        console.log(`Reconnecting (${this.retryCount}/${this.maxRetries})...`);
        setTimeout(() => this.connect(), 2000); // 2초 후 재연결
      } else {
        this.onError(error);
      }
    };
  }
}
```

### Network Simulation

**Chrome DevTools → Network Conditions:**
1. Network 탭 → Network throttling: "Slow 3G"
2. Chat 메시지 전송
3. SSE 이벤트 수신 지연 확인

**Latency 시뮬레이션:**
```python
# 백엔드에서 인위적 지연
import asyncio

async def _generate_chat_stream(...):
    for chunk in orchestrator.chat_stream(...):
        await asyncio.sleep(0.5)  # 500ms 지연
        yield f"data: {json.dumps(...)}\n\n"
```

---

## Monitoring

### SSE 연결 수 추적

**Backend (FastAPI middleware):**
```python
from contextvars import ContextVar

active_sse_connections = ContextVar("active_sse_connections", default=0)

async def sse_middleware(request: Request, call_next):
    if "/stream" in request.url.path:
        count = active_sse_connections.get() + 1
        active_sse_connections.set(count)
        logger.info(f"Active SSE connections: {count}")

    response = await call_next(request)

    if "/stream" in request.url.path:
        count = active_sse_connections.get() - 1
        active_sse_connections.set(count)
        logger.info(f"Active SSE connections: {count}")

    return response
```

### Performance Metrics

**측정 항목:**
- TTFB (Time To First Byte): 첫 이벤트까지 시간
- Event Rate: 초당 이벤트 수
- Connection Duration: SSE 연결 유지 시간

**Browser Performance API:**
```javascript
const perfObserver = new PerformanceObserver((list) => {
  list.getEntries().forEach((entry) => {
    if (entry.name.includes("/stream")) {
      console.log("TTFB:", entry.responseStart - entry.requestStart, "ms");
      console.log("Duration:", entry.duration, "ms");
    }
  });
});
perfObserver.observe({ entryTypes: ["resource"] });
```

---

## Common Patterns

### Heartbeat (Keep-Alive)

**백엔드에서 주기적 이벤트 전송:**
```python
import asyncio

async def _generate_chat_stream(...):
    last_event_time = time.time()

    for chunk in orchestrator.chat_stream(...):
        yield f"data: {json.dumps(...)}\n\n"
        last_event_time = time.time()

        # 5초마다 heartbeat
        if time.time() - last_event_time > 5:
            yield f"data: {json.dumps({'type':'heartbeat'})}\n\n"
            last_event_time = time.time()
```

### Graceful Shutdown

**브라우저 페이지 닫을 때 SSE 종료:**
```javascript
window.addEventListener("beforeunload", () => {
  if (sseHandler && sseHandler.eventSource) {
    sseHandler.eventSource.close();
  }
});
```

---

## Related Documentation

- [Backend API Testing](backend-api.md) - API 엔드포인트 가이드
- [Quickstart](quickstart.md) - Playground 설치 및 실행
- [Architecture Overview](../../architecture/README.md) - SSE 아키텍처 설계

---

*Last Updated: 2026-02-06*
*Version: 1.0*
*Plan: 08_playground*
