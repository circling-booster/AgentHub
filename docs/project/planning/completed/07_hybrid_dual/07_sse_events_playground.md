# Phase 7: SSE Events + Playground (Playground-First Testing)

## 개요

SSE 이벤트 확장과 Playground 검증을 구현합니다.

**Playground-First Principle:** Backend SSE 이벤트 → Playground로 즉시 검증 → Extension UI는 Production Phase로 연기

**핵심:**
- StreamChunk 확장: sampling_request, elicitation_request 이벤트
- Playground SSE Handler 업데이트
- Playground HITL 탭 개선 (Optional)
- Extension UI 제외 (Production Phase로 연기)

---

## Step 7.1: StreamChunk 확장 (Backend)

**파일:** `src/domain/entities/stream_chunk.py` (기존 파일 확장)
**테스트:** `tests/unit/domain/entities/test_stream_chunk.py` (기존 파일 확장)

### TDD Required - 테스트 먼저 작성

```python
# tests/unit/domain/entities/test_stream_chunk.py

def test_sampling_request_chunk_creation():
    """Sampling 요청 청크 생성"""
    chunk = StreamChunk.sampling_request(
        request_id="req-123",
        endpoint_id="mcp-server-1",
        messages=[{"role": "user", "content": "test"}],
    )

    assert chunk.type == "sampling_request"
    assert chunk.content == "req-123"
    assert chunk.agent_name == "mcp-server-1"
    assert "messages" in chunk.tool_arguments

def test_elicitation_request_chunk_creation():
    """Elicitation 요청 청크 생성"""
    chunk = StreamChunk.elicitation_request(
        request_id="req-456",
        message="Enter API key",
        requested_schema={"type": "object", "properties": {"api_key": {"type": "string"}}},
    )

    assert chunk.type == "elicitation_request"
    assert chunk.content == "req-456"
    assert chunk.result == "Enter API key"
    assert "schema" in chunk.tool_arguments
```

### 구현

```python
# src/domain/entities/stream_chunk.py에 추가

from typing import Any

@staticmethod
def sampling_request(
    request_id: str,
    endpoint_id: str,
    messages: list[dict[str, Any]],
) -> "StreamChunk":
    """Sampling 요청 알림 청크 생성

    Args:
        request_id: 요청 ID
        endpoint_id: MCP 서버 엔드포인트 ID
        messages: 메시지 목록

    Returns:
        StreamChunk (type="sampling_request")
    """
    return StreamChunk(
        type="sampling_request",
        content=request_id,
        agent_name=endpoint_id,
        tool_arguments={"messages": messages},
    )

@staticmethod
def elicitation_request(
    request_id: str,
    message: str,
    requested_schema: dict[str, Any],
) -> "StreamChunk":
    """Elicitation 요청 알림 청크 생성

    Args:
        request_id: 요청 ID
        message: Elicitation 메시지
        requested_schema: 요청 스키마

    Returns:
        StreamChunk (type="elicitation_request")
    """
    return StreamChunk(
        type="elicitation_request",
        content=request_id,
        result=message,
        tool_arguments={"schema": requested_schema},
    )
```

### SSE 전송 위치

HitlNotificationAdapter가 이 팩토리 메서드를 사용 (Phase 4에서 이미 구현):

```python
# src/adapters/outbound/sse/hitl_notification_adapter.py

async def notify_sampling_request(self, request: SamplingRequest) -> None:
    """Sampling 요청 알림 (SSE 브로드캐스트)"""
    chunk = StreamChunk.sampling_request(
        request_id=request.id,
        endpoint_id=request.endpoint_id,
        messages=request.messages,
    )
    await self._broker.broadcast(chunk)
```

RegistryService의 콜백에서 30초 timeout 후 호출 (Phase 5에서 이미 구현):

```python
# src/domain/services/registry_service.py의 _create_sampling_callback

# 3. Short timeout (30초) 대기
result = await self._sampling_service.wait_for_response(request_id, timeout=30.0)

# 4. Timeout 시 SSE 알림 전송
if result is None:
    if self._hitl_notification:
        await self._hitl_notification.notify_sampling_request(request)
```

---

## Step 7.2: Playground SSE Handler Update

**파일:** `tests/manual/playground/js/sse-handler.js` (기존 파일 확장)
**테스트:** `tests/e2e/test_playground.py` (E2E TDD)

### E2E 테스트 먼저 작성

```python
# tests/e2e/test_playground.py

import pytest
import asyncio
from playwright.async_api import async_playwright

@pytest.mark.e2e_playwright
@pytest.mark.local_mcp
class TestPlaygroundSSEEvents:
    async def test_sampling_request_sse_logged(self, page, sampling_service):
        """Sampling 요청 SSE 이벤트 로그 검증"""
        # 1. Chat 탭에서 SSE 연결
        await page.goto("http://localhost:3000")
        await page.click('[data-testid="tab-chat"]')

        # 2. Backend에서 Sampling 요청 생성 (30초 timeout 트리거)
        from src.domain.entities.sampling_request import SamplingRequest
        request = SamplingRequest(
            id="test-req-1",
            endpoint_id="test-ep",
            messages=[{"role": "user", "content": "test"}],
        )
        await sampling_service.create_request(request)

        # Wait for timeout (30초는 너무 길므로, mock 또는 단축 timeout 사용)
        # 실제 구현에서는 wait_for_response timeout을 조정하거나
        # timeout을 강제로 트리거하는 헬퍼 메서드 필요

        # 3. SSE 로그에 이벤트 확인
        await page.wait_for_selector('[data-testid="sse-log"]')
        log_content = await page.locator('[data-testid="sse-log"]').text_content()

        assert "SAMPLING REQUEST" in log_content
        assert "test-req-1" in log_content  # request_id 포함

    async def test_elicitation_request_sse_logged(self, page, elicitation_service):
        """Elicitation 요청 SSE 이벤트 로그 검증"""
        # 동일한 패턴
        await page.goto("http://localhost:3000")
        await page.click('[data-testid="tab-chat"]')

        from src.domain.entities.elicitation_request import ElicitationRequest
        request = ElicitationRequest(
            id="test-req-2",
            endpoint_id="test-ep",
            message="Enter API key",
            requested_schema={},
        )
        await elicitation_service.create_request(request)

        # Timeout 트리거 (30초 대기)
        # ...

        # SSE 로그 확인
        log_content = await page.locator('[data-testid="sse-log"]').text_content()
        assert "ELICITATION REQUEST" in log_content
        assert "test-req-2" in log_content
```

### JavaScript Implementation

```javascript
// tests/manual/playground/js/sse-handler.js

class SSEHandler {
    constructor(eventSource) {
        this.eventSource = eventSource;
        this.logPanel = document.querySelector('[data-testid="sse-log"]');
    }

    handleEvent(event) {
        const data = JSON.parse(event.data);

        switch (data.type) {
            case 'sampling_request':
                this.logEvent('SAMPLING REQUEST', {
                    request_id: data.content,
                    endpoint_id: data.agent_name,
                    messages: data.tool_arguments?.messages
                });
                // Optional: Auto-refresh Sampling tab
                this.refreshSamplingTab();
                break;

            case 'elicitation_request':
                this.logEvent('ELICITATION REQUEST', {
                    request_id: data.content,
                    message: data.result,
                    schema: data.tool_arguments?.schema
                });
                // Optional: Auto-refresh Elicitation tab
                this.refreshElicitationTab();
                break;

            case 'text':
            case 'tool_call':
            case 'tool_result':
                // 기존 이벤트 핸들러
                this.handleExistingEvents(data);
                break;

            default:
                console.warn('Unknown SSE event type:', data.type);
        }
    }

    logEvent(type, payload) {
        const timestamp = new Date().toISOString();
        const logEntry = `[${timestamp}] ${type}: ${JSON.stringify(payload, null, 2)}\n`;
        this.logPanel.textContent += logEntry;
        this.logPanel.scrollTop = this.logPanel.scrollHeight;  // Auto-scroll
    }

    refreshSamplingTab() {
        // Sampling 탭이 활성화되어 있으면 목록 새로고침
        const samplingTab = document.getElementById('sampling-tab');
        if (samplingTab && samplingTab.classList.contains('active')) {
            // listSamplingRequests() 호출 (Phase 6에서 구현)
            window.listSamplingRequests();
        }
    }

    refreshElicitationTab() {
        // Elicitation 탭이 활성화되어 있으면 목록 새로고침
        const elicitationTab = document.getElementById('elicitation-tab');
        if (elicitationTab && elicitationTab.classList.contains('active')) {
            window.listElicitationRequests();
        }
    }

    handleExistingEvents(data) {
        // 기존 Phase 1-6의 이벤트 핸들러
        // text, tool_call, tool_result, error 등
        // ...
    }
}

// Initialize
const eventSource = new EventSource(`${API_BASE}/api/chat/stream`);
const sseHandler = new SSEHandler(eventSource);

eventSource.onmessage = (event) => {
    sseHandler.handleEvent(event);
};
```

### Playground HTML 업데이트

```html
<!-- tests/manual/playground/index.html -->

<div id="chat-tab" class="tab-pane">
    <h2>Chat</h2>
    <!-- 기존 chat UI -->

    <!-- SSE Log Panel (신규) -->
    <div class="sse-log-panel">
        <h3>SSE Events Log</h3>
        <pre data-testid="sse-log" style="height: 200px; overflow-y: auto; background: #f5f5f5; padding: 10px;"></pre>
    </div>
</div>
```

---

## Step 7.3: Playground HITL Verification (Optional Enhancement)

**목표:** Sampling/Elicitation 탭에서 SSE 이벤트 수신 후 자동 새로고침

**Scope:**
- SSE 이벤트 수신 시 Sampling/Elicitation 탭 자동 새로고침 (Step 7.2의 refreshSamplingTab() 구현)
- 대기 중인 요청 목록 하이라이트 (신규 요청 강조)
- Modal Dialog 제외 (Extension UI와 중복, Production Phase로 연기)

**구현:**
```javascript
// tests/manual/playground/js/main.js에 추가

function highlightNewRequest(requestId) {
    // 새로 추가된 요청 하이라이트 (3초 후 자동 해제)
    const requestCard = document.querySelector(`[data-request-id="${requestId}"]`);
    if (requestCard) {
        requestCard.classList.add('new-request');
        setTimeout(() => {
            requestCard.classList.remove('new-request');
        }, 3000);
    }
}
```

**CSS:**
```css
/* tests/manual/playground/css/style.css */

.request-card.new-request {
    background-color: #fff3cd;  /* Yellow highlight */
    animation: pulse 1s ease-in-out 3;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}
```

---

## Excluded from This Phase

**Chrome Extension UI는 별도 Phase로 연기:**

1. `extension/lib/types.ts` - StreamEventSamplingRequest, StreamEventElicitationRequest 타입
2. `extension/lib/api.ts` - Sampling/Elicitation API 함수
3. `extension/entrypoints/sidepanel/components/HitlModal.tsx` - Modal 컴포넌트
4. `extension/entrypoints/sidepanel/hooks/useStreamEvents.ts` - SSE 이벤트 핸들러

**연기 이유:**
- Playground로 충분히 검증 가능 (SSE 이벤트 수신, API 호출)
- Extension UI는 Production 준비 단계에서 일괄 구현 (더 나은 UX 설계 가능)
- 중복 작업 방지 (Playground 기본 UI vs Extension Modal)

---

## Verification

```bash
# Phase 1-6 복습
pytest tests/unit/ -q --tb=line -x
pytest tests/integration/ -m "local_mcp or llm" -v
pytest tests/e2e/test_playground.py -v

# Phase 7 Unit Tests (StreamChunk)
pytest tests/unit/domain/entities/test_stream_chunk.py::test_sampling_request_chunk_creation -v
pytest tests/unit/domain/entities/test_stream_chunk.py::test_elicitation_request_chunk_creation -v

# Phase 7 E2E Tests (Playground SSE)
pytest tests/e2e/test_playground.py::TestPlaygroundSSEEvents -v

# JavaScript Unit Tests (Optional)
cd tests/manual/playground
npm test -- sse-handler.test.js

# Regression Tests
pytest tests/e2e/test_playground.py -v  # All playground tests (Phase 6 + 7)

# Coverage
pytest --cov=src --cov-fail-under=80 -q
```

---

## Step 7.4: Documentation Update

**목표:** Phase 7에서 확장된 SSE 이벤트 및 Playground 검증 문서화

**문서화 항목:**

| 작업 | 대상 파일 | 유형 | 내용 |
|------|----------|------|------|
| Modify | docs/developers/architecture/api/hitl-sse.md | API Documentation | sampling_request, elicitation_request 이벤트 타입 추가 |
| Modify | docs/developers/architecture/api/hitl-sse.md | API Documentation | StreamChunk 팩토리 메서드 사용 패턴 설명 |
| Create | docs/developers/guides/implementation/sse-event-flow.md | Implementation Guide | HITL SSE 이벤트 플로우 다이어그램 (timeout → SSE 알림 → Playground 표시) |
| Modify | tests/manual/playground/README.md | Component README | SSE 이벤트 핸들러 섹션 추가 (js/sse-handler.js 설명) |
| Modify | docs/project/planning/active/07_hybrid_dual/README.md | Planning Documentation | Extension UI Deferral 섹션 업데이트 (완료된 Phase 반영) |

**주의사항:**
- Extension UI 제외 사유 명확히 기술 (Playground 충분성, Production Phase 일괄 구현)
- SSE 이벤트 플로우는 시퀀스 다이어그램 포함 (mermaid 또는 ASCII art)
- Playground SSE 로그 패널 사용법 설명

---

## Checklist

- [ ] **Baseline 회귀 테스트**: `pytest -q --tb=line` (Phase 시작 전 Green 상태 확인)
- [ ] **Phase 시작**: Status 변경 (⏸️ → 🔄)
- [ ] Step 7.1: StreamChunk에 새 이벤트 타입 추가 (TDD)
- [ ] Step 7.2: Playground SSE 핸들러 업데이트 (E2E TDD)
- [ ] Step 7.3: Playground HITL 탭 개선 (Optional - 자동 새로고침)
- [ ] Step 7.4: Documentation Update (SSE Event Documentation + Event Flow Diagram)
- [ ] Verification: 모든 테스트 통과
- [ ] Extension UI 제외 확인 (Production Phase로 연기)
- [ ] **Phase 완료**: Status 변경 (🔄 → ✅)
- [ ] Git 커밋: `docs: complete phase N - {phase_name}`
---

## Integration Points

### Phase 4 연결점
- HitlNotificationAdapter: StreamChunk 팩토리 메서드 사용

### Phase 5 연결점
- RegistryService 콜백: 30초 timeout 후 HitlNotificationAdapter 호출

### Phase 6 연결점
- Playground Sampling/Elicitation 탭: SSE 이벤트 수신 시 자동 새로고침

---

## Testing Strategy

| 레이어 | 테스트 유형 | 파일 | 검증 항목 |
|--------|------------|------|----------|
| Domain | Unit | `test_stream_chunk.py` | 팩토리 메서드 동작 |
| Adapter | Integration | `test_hitl_notification_adapter.py` | SSE 브로드캐스트 |
| Playground | E2E | `test_playground.py` | SSE 이벤트 수신 및 로그 표시 |

---

*Last Updated: 2026-02-07*
*Principle: Playground-First Testing (Backend SSE → Playground Verification → Extension UI Deferred)*
