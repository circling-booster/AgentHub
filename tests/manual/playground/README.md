# AgentHub Playground

**Playground-First Testing** 환경으로, HTTP API와 SSE 이벤트를 브라우저에서 즉시 테스트합니다.

Plan 07 Phase 6+에서 도입된 테스트 전략입니다 ([ADR-T07](../../../docs/project/decisions/technical/ADR-T07-playground-first-testing.md)).

---

## 📋 Quick Reference

| 항목 | 값 |
|------|-----|
| **Purpose** | Backend API + Playground UI + E2E tests 동시 구현 |
| **URL** | http://localhost:9001 |
| **Target APIs** | Resources, Prompts, Sampling, Elicitation, HITL SSE |
| **E2E Framework** | Playwright (pytest-playwright) |
| **Test Marker** | `@pytest.mark.e2e_playwright` |

---

## 🎯 Playground-First Testing 원칙

**핵심 아이디어**: Chrome Extension 빌드 없이 백엔드 API를 즉시 검증

### 적용 범위

| Feature | Playground | Extension UI |
|---------|-----------|--------------|
| **HTTP Routes (Phase 6+)** | ✅ Immediate testing | ⏸️ Production phase |
| **SSE Events (Phase 7+)** | ✅ Real-time validation | ⏸️ Production phase |
| **Domain/Services** | ❌ Unit/Integration tests | N/A |

### 구현 순서

```
1. Backend 구현 (TDD)
   ↓
2. Playground UI 추가 (HTML/JS)
   ↓
3. Playwright E2E 테스트 작성
   ↓
4. 회귀 테스트 즉시 실행 (<10초)
```

**장점:**
- 즉각적인 피드백 (Extension 빌드 불필요)
- 빠른 회귀 테스트 (Playwright E2E < 10초)
- API 계약 조기 검증

---

## 🚀 Quick Start

### 1. Start Backend Server

```bash
uvicorn src.main:app --host localhost --port 8000
```

### 2. Open Playground

```bash
cd tests/manual/playground
npx http-server -p 9001
```

브라우저에서 http://localhost:9001 열기

### 3. Login

- Username: `admin`
- Password: `secret`

### 4. Explore Tabs

- **Resources**: MCP Server 리소스 목록/읽기
- **Prompts**: 프롬프트 템플릿 관리
- **Sampling**: LLM Sampling HITL 승인/거부
- **Elicitation**: 사용자 입력 요청/응답
- **HITL SSE**: 실시간 이벤트 모니터링

---

## 📁 Directory Structure

```
tests/manual/playground/
├── index.html              # Main UI (Tabs + Token Auth)
├── package.json            # Jest + Playwright dependencies
├── css/
│   └── styles.css          # Tailwind-inspired styles
├── js/
│   ├── main.js             # Tab switching + initialization
│   ├── api-client.js       # HTTP API client (fetch wrapper)
│   ├── sse-handler.js      # SSE EventSource handler
│   └── ui-components.js    # UI update helpers
├── tests/
│   └── *.test.js           # Jest unit tests (optional)
└── coverage/               # Jest coverage reports
```

---

## 🧪 Testing Strategy

### 1. Manual Testing (개발 중)

Playground UI를 직접 조작하여 기능 확인:
1. Backend API 구현 후 Playground에서 수동 테스트
2. 기능 정상 확인 후 E2E 테스트 작성

### 2. E2E Testing (회귀 방지)

Playwright로 자동화된 회귀 테스트:

**Run E2E Tests:**
```bash
pytest tests/e2e/test_playground.py -v -m e2e_playwright
```

**Test Classes:**
- `TestPlaygroundResources` - Resources 탭 (2 tests)
- `TestPlaygroundPrompts` - Prompts 탭 (2 tests)
- `TestPlaygroundSampling` - Sampling 탭 (2 tests)
- `TestPlaygroundElicitation` - Elicitation 탭 (2 tests)

**Coverage:**
- UI 요소 렌더링 확인
- API 요청/응답 검증
- 이벤트 핸들러 동작 확인
- 브라우저 콘솔 에러 모니터링

### 3. Unit Testing (JavaScript)

Jest로 JavaScript 모듈 단위 테스트:

```bash
cd tests/manual/playground
npm test
```

**Coverage Report:**
```bash
npm run test:coverage
```

---

## 🔌 API Integration

### Authentication

모든 API 요청은 Token 인증이 필요합니다.

**Token Acquisition:**
```javascript
const response = await fetch('http://localhost:8000/api/auth/token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'secret' })
});
const { access_token } = await response.json();
```

**API Request with Token:**
```javascript
const response = await fetch('http://localhost:8000/api/mcp/servers', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
```

### SDK Track APIs

- [Resources API](../../../docs/developers/architecture/api/sdk-track.md#1-resources-api)
- [Prompts API](../../../docs/developers/architecture/api/sdk-track.md#2-prompts-api)
- [Sampling API](../../../docs/developers/architecture/api/sdk-track.md#3-sampling-api-hitl)
- [Elicitation API](../../../docs/developers/architecture/api/sdk-track.md#4-elicitation-api-hitl)

### HITL SSE Events

- [HITL SSE API](../../../docs/developers/architecture/api/hitl-sse.md)

**EventSource Connection:**
```javascript
const eventSource = new EventSource('http://localhost:8000/api/hitl/events', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});

eventSource.addEventListener('sampling_request', (event) => {
  const data = JSON.parse(event.data);
  console.log('Sampling Request:', data);
});
```

---

## 📡 SSE Event Handlers

Playground는 **HITL SSE Events**를 실시간으로 수신하여 UI를 업데이트합니다.

**Phase 7**에서 StreamChunk 기반 이벤트 구조로 확장되었습니다.

### Event Types (Phase 7 - StreamChunk)

| Event Type | Trigger | UI Update |
|------------|---------|-----------|
| **sampling_request** | MCP Sampling 요청 30초 timeout | Sampling 탭 자동 새로고침 + SSE 로그 |
| **elicitation_request** | MCP Elicitation 요청 30초 timeout | Elicitation 탭 자동 새로고침 + SSE 로그 |

### StreamChunk Structure

Phase 7부터 모든 SSE 이벤트는 **StreamChunk** 구조를 따릅니다:

```javascript
// sampling_request event
{
  "type": "sampling_request",
  "content": "req-abc123",        // request_id
  "agent_name": "test-endpoint",  // endpoint_id
  "tool_arguments": {
    "messages": [...]              // MCP Sampling messages
  },
  "result": "",
  "tool_name": "",
  "error_code": "",
  "workflow_id": "",
  "workflow_type": "",
  "workflow_status": "",
  "step_number": 0,
  "total_steps": 0
}

// elicitation_request event
{
  "type": "elicitation_request",
  "content": "elicit-xyz789",     // request_id
  "result": "Enter API key",      // message
  "tool_arguments": {
    "schema": {...}                // JSON Schema
  },
  "agent_name": "",
  "tool_name": "",
  ...
}
```

### Implementation (js/main.js)

```javascript
// SSE Connection Initialization
function initHitlSseConnection() {
    const eventSource = new EventSource(`${API_BASE}/api/hitl/events`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });

    // Sampling Request Handler
    eventSource.addEventListener('sampling_request', (event) => {
        const data = JSON.parse(event.data);

        // Log to SSE panel
        appendSseLog('SAMPLING REQUEST', {
            request_id: data.content,
            endpoint_id: data.agent_name,
            messages: data.tool_arguments?.messages
        });

        // Auto-refresh Sampling tab if active
        if (currentTab === 'sampling') {
            refreshSamplingList();
        }
    });

    // Elicitation Request Handler
    eventSource.addEventListener('elicitation_request', (event) => {
        const data = JSON.parse(event.data);

        // Log to SSE panel
        appendSseLog('ELICITATION REQUEST', {
            request_id: data.content,
            message: data.result,
            schema: data.tool_arguments?.schema
        });

        // Auto-refresh Elicitation tab if active
        if (currentTab === 'elicitation') {
            refreshElicitationList();
        }
    });
}
```

### Auto-Refresh Behavior

**Sampling Tab:**
1. SSE `sampling_request` 이벤트 수신
2. Sampling 탭이 활성화되어 있으면 `refreshSamplingList()` 호출
3. 요청 목록 재로드 → 신규 요청 표시

**Elicitation Tab:**
1. SSE `elicitation_request` 이벤트 수신
2. Elicitation 탭이 활성화되어 있으면 `refreshElicitationList()` 호출
3. 요청 목록 재로드 → 신규 요청 표시

### SSE Log Panel

모든 SSE 이벤트는 **SSE Log Panel**에 실시간으로 기록됩니다.

**UI Component:**
```html
<div class="sse-log-panel">
    <h3>SSE Events Log</h3>
    <pre data-testid="sse-log" style="height: 200px; overflow-y: auto;"></pre>
</div>
```

**Log Format:**
```
[2026-02-08T10:30:45.123Z] SAMPLING REQUEST: {
  "request_id": "req-abc123",
  "endpoint_id": "test-endpoint",
  "messages": [...]
}

[2026-02-08T10:31:12.456Z] ELICITATION REQUEST: {
  "request_id": "elicit-xyz789",
  "message": "Enter API key",
  "schema": {...}
}
```

### Error Handling

**Connection Errors:**
```javascript
eventSource.onerror = (error) => {
    console.error('SSE Connection Error:', error);

    // Exponential backoff reconnection
    setTimeout(() => {
        initHitlSseConnection();  // Retry
    }, reconnectDelay);
};
```

**Timeout Handling:**
- SSE 연결 실패 시 자동 재연결 (EventSource 기본 동작)
- Backend timeout (30초) 후에만 이벤트 전송 (조기 사용자 응답 시 이벤트 없음)

### Related Documentation

- [SSE Event Flow](../../../docs/developers/guides/implementation/sse-event-flow.md) - HITL SSE 플로우 다이어그램
- [HITL SSE API](../../../docs/developers/architecture/api/hitl-sse.md) - API 명세 및 이벤트 스키마
- [StreamChunk Entity](../../../docs/developers/architecture/domain/entities.md#streamchunk) - Domain 엔티티 설계

---

## 📝 Playground UI Components

### Tab Structure

| Tab | Description | HITL | E2E Status |
|-----|-------------|------|-----------|
| **Resources** | MCP Server 리소스 목록/읽기 | No | ✅ 2/2 PASSING |
| **Prompts** | 프롬프트 템플릿 관리 | No | ⚠️ 1/2 PASSING |
| **Sampling** | LLM Sampling 요청 승인/거부 | Yes | ⚠️ Connection pool issues |
| **Elicitation** | 사용자 입력 요청/응답 | Yes | ⚠️ Connection pool issues |
| **HITL SSE** | 실시간 이벤트 모니터링 | - | ✅ 5/5 PASSING |

### MCP Apps Raw Response (iframe sandbox)

MCP Server의 원시 응답(HTML, JSON 등)은 **iframe sandbox**로 처리됩니다.

**Sandbox Attributes:**
```html
<iframe sandbox="allow-scripts allow-same-origin" srcdoc="..."></iframe>
```

**Security:**
- XSS 방지를 위해 sandbox 속성 사용
- allow-scripts: JavaScript 실행 허용
- allow-same-origin: 동일 출처 정책 유지

**Example (Resources Tab):**
```javascript
const iframe = document.getElementById('resource-content-frame');
iframe.srcdoc = resourceContent; // MCP Server raw response
```

---

## 🐛 Known Issues

### Connection Pool Exhaustion

**Symptom:**
- Elicitation Tab: 1/5 E2E tests PASSED (나머지 connection pool 고갈)
- Playwright `page.goto()` 시 `ConnectionAbortedError: [WinError 10053]`

**Root Cause:**
- Playground HTTP server fixture의 연결 처리 이슈
- Python `http.server` 모듈의 동시 연결 제한

**Mitigation:**
- 기능 자체는 정상 (manual 테스트로 확인)
- E2E 테스트 안정성 이슈 (non-blocking)
- Production 환경에서는 Nginx/gunicorn 사용 권장

**Status:** ⏸️ Tracked, non-blocking for Phase 6 completion

---

## 🔧 Development Workflow

### Adding New API Endpoint

1. **Backend Implementation** (TDD Red-Green-Refactor)
   ```bash
   pytest tests/unit/... -v
   pytest tests/integration/... -v
   ```

2. **Playground UI Update**
   - `index.html`: Add new tab
   - `js/main.js`: Add tab event listener
   - `js/api-client.js`: Add API call function
   - `css/styles.css`: Add tab-specific styles (if needed)

3. **E2E Test Creation**
   ```python
   # tests/e2e/test_playground.py
   class TestPlaygroundNewFeature:
       async def test_new_feature_renders(self, page):
           await page.goto("http://localhost:9001")
           await page.click("#tab-new-feature")
           # ...
   ```

4. **Regression Testing**
   ```bash
   pytest tests/e2e/test_playground.py::TestPlaygroundNewFeature -v -m e2e_playwright
   ```

### Debugging Tips

1. **Browser DevTools**
   - Console 탭: JavaScript 에러 확인
   - Network 탭: API 요청/응답 확인

2. **Playwright Trace**
   ```bash
   pytest tests/e2e/test_playground.py --tracing=on
   playwright show-trace trace.zip
   ```

3. **Backend Logs**
   ```bash
   uvicorn src.main:app --log-level debug
   ```

---

## 📚 Related Documentation

- [ADR-T07: Playground-First Testing](../../../docs/project/decisions/technical/ADR-T07-playground-first-testing.md) - Phase 6+ 원칙
- [SDK Track API](../../../docs/developers/architecture/api/sdk-track.md) - API 엔드포인트 문서
- [HITL SSE API](../../../docs/developers/architecture/api/hitl-sse.md) - SSE 이벤트 스트림
- [E2E Testing Guide](../../docs/EXECUTION.md#playground-e2e-tests) - Playwright 테스트 실행
- [Test Structure](../../docs/STRUCTURE.md#manual-testing) - tests/manual/ 구조

---

*Last Updated: 2026-02-07*
*Phase: Plan 07 Phase 6*
*Testing Strategy: Playground-First (ADR-T07)*
