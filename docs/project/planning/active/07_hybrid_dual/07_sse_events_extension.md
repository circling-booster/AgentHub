# Phase 7: SSE Events & Extension

## 개요

SSE 이벤트 확장과 Chrome Extension 업데이트를 구현합니다.

**Note:** Extension 코드는 TDD 대신 E2E 테스트로 검증합니다.

---

## Step 7.1: StreamChunk 확장

**파일:** `src/domain/entities/stream_chunk.py`

새 이벤트 타입:
- `sampling_request` - Sampling 요청 알림
- `elicitation_request` - Elicitation 요청 알림

```python
# src/domain/entities/stream_chunk.py에 추가

@staticmethod
def sampling_request(
    request_id: str,
    endpoint_id: str,
    messages: list[dict[str, Any]],
) -> "StreamChunk":
    """Sampling 요청 알림 청크 생성"""
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
    """Elicitation 요청 알림 청크 생성"""
    return StreamChunk(
        type="elicitation_request",
        content=request_id,
        result=message,
        tool_arguments={"schema": requested_schema},
    )
```

### SSE 전송 위치

**파일:** `src/domain/services/sampling_service.py`

```python
async def create_request(self, request: SamplingRequest) -> None:
    """요청 생성 및 SSE 알림"""
    self._requests[request.id] = request
    self._events[request.id] = asyncio.Event()

    # SSE 브로드캐스트 (30초 후 timeout 시에만)
    # → Phase 5의 콜백에서 wait_for_response가 timeout되면 호출
```

---

## Step 7.2: Extension Types

**파일:** `extension/lib/types.ts`

```typescript
// 기존 StreamEvent 타입에 추가

export interface StreamEventSamplingRequest {
  type: 'sampling_request';
  request_id: string;
  endpoint_id: string;
  messages: Array<{role: string; content: unknown}>;
}

export interface StreamEventElicitationRequest {
  type: 'elicitation_request';
  request_id: string;
  message: string;
  requested_schema: Record<string, unknown>;
}

// Union 타입 확장
export type StreamEvent =
  | StreamEventText
  | StreamEventToolCall
  | StreamEventToolResult
  | StreamEventAgentTransfer
  | StreamEventDone
  | StreamEventError
  | StreamEventSamplingRequest      // 추가
  | StreamEventElicitationRequest;  // 추가
```

---

## Step 7.3: Extension API

**파일:** `extension/lib/api.ts`

### Sampling API

```typescript
export async function listSamplingRequests(): Promise<SamplingRequest[]> {
  const response = await fetch(`${API_BASE}/api/sampling/requests`);
  const data = await response.json();
  return data.requests;
}

export async function approveSamplingRequest(requestId: string): Promise<void> {
  await fetch(`${API_BASE}/api/sampling/requests/${requestId}/approve`, {
    method: 'POST',
  });
}

export async function rejectSamplingRequest(
  requestId: string,
  reason?: string
): Promise<void> {
  await fetch(`${API_BASE}/api/sampling/requests/${requestId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason }),
  });
}
```

### Elicitation API

```typescript
export async function listElicitationRequests(): Promise<ElicitationRequest[]> {
  const response = await fetch(`${API_BASE}/api/elicitation/requests`);
  const data = await response.json();
  return data.requests;
}

export async function respondElicitation(
  requestId: string,
  action: 'accept' | 'decline' | 'cancel',
  content?: Record<string, unknown>
): Promise<void> {
  await fetch(`${API_BASE}/api/elicitation/requests/${requestId}/respond`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, content }),
  });
}
```

### Resources/Prompts API

```typescript
export async function listResources(endpointId: string): Promise<Resource[]> {
  const response = await fetch(
    `${API_BASE}/api/mcp/servers/${endpointId}/resources`
  );
  const data = await response.json();
  return data.resources;
}

export async function readResource(
  endpointId: string,
  uri: string
): Promise<ResourceContent> {
  const encodedUri = encodeURIComponent(uri);
  const response = await fetch(
    `${API_BASE}/api/mcp/servers/${endpointId}/resources/${encodedUri}`
  );
  return response.json();
}

export async function listPrompts(endpointId: string): Promise<PromptTemplate[]> {
  const response = await fetch(
    `${API_BASE}/api/mcp/servers/${endpointId}/prompts`
  );
  const data = await response.json();
  return data.prompts;
}

export async function getPrompt(
  endpointId: string,
  name: string,
  args?: Record<string, unknown>
): Promise<string> {
  const response = await fetch(
    `${API_BASE}/api/mcp/servers/${endpointId}/prompts/${name}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ arguments: args }),
    }
  );
  const data = await response.json();
  return data.content;
}
```

---

## Step 7.4: HITL Modal Component

**파일:** `extension/entrypoints/sidepanel/components/HitlModal.tsx`

```tsx
interface HitlModalProps {
  type: 'sampling' | 'elicitation';
  request: SamplingRequest | ElicitationRequest;
  onClose: () => void;
}

export function HitlModal({ type, request, onClose }: HitlModalProps) {
  if (type === 'sampling') {
    return (
      <SamplingApprovalDialog
        request={request as SamplingRequest}
        onApprove={() => {
          approveSamplingRequest(request.id);
          onClose();
        }}
        onReject={(reason) => {
          rejectSamplingRequest(request.id, reason);
          onClose();
        }}
      />
    );
  }

  return (
    <ElicitationFormDialog
      request={request as ElicitationRequest}
      onRespond={(action, content) => {
        respondElicitation(request.id, action, content);
        onClose();
      }}
    />
  );
}
```

---

## Step 7.5: SSE 이벤트 핸들러

**파일:** `extension/entrypoints/sidepanel/hooks/useStreamEvents.ts`

```typescript
function handleStreamEvent(event: StreamEvent) {
  switch (event.type) {
    case 'sampling_request':
      // 모달 표시
      showHitlModal({
        type: 'sampling',
        request: {
          id: event.request_id,
          endpoint_id: event.endpoint_id,
          messages: event.messages,
        },
      });
      break;

    case 'elicitation_request':
      showHitlModal({
        type: 'elicitation',
        request: {
          id: event.request_id,
          message: event.message,
          requested_schema: event.requested_schema,
        },
      });
      break;

    // ... 기존 이벤트 핸들러
  }
}
```

---

## E2E 테스트 시나리오

**파일:** `tests/e2e/test_hitl_flow.py` (Playwright 마커)

```python
@pytest.mark.e2e_playwright
class TestHitlFlow:
    async def test_sampling_approval_flow(self, browser, mcp_server):
        """Sampling 승인 E2E 플로우"""
        # 1. Extension에서 MCP 서버 등록
        # 2. MCP 서버가 Sampling 요청 전송 (테스트 도구 호출)
        # 3. Extension UI에서 모달 표시 확인
        # 4. 승인 버튼 클릭
        # 5. LLM 응답 확인

    async def test_elicitation_form_flow(self, browser, mcp_server):
        """Elicitation 폼 입력 E2E 플로우"""
        # 1. Elicitation 요청 트리거
        # 2. 폼 모달 표시 확인
        # 3. 스키마 기반 폼 필드 확인
        # 4. 값 입력 후 Accept
        # 5. 응답 확인

    async def test_sampling_rejection_flow(self, browser, mcp_server):
        """Sampling 거부 E2E 플로우"""
        # 거부 버튼 클릭 → 에러 응답 확인

    async def test_hitl_timeout_notification(self, browser, mcp_server):
        """30초 타임아웃 후 SSE 알림 E2E 플로우"""
        # 30초 대기 → SSE 이벤트 → 모달 재표시
```

---

## 테스트 실행

```bash
# E2E 테스트 (Playwright 필요)
pytest tests/e2e/ -m e2e_playwright --headed
```

---

## Checklist

- [ ] StreamChunk에 새 이벤트 타입 추가
- [ ] Extension types.ts 업데이트
- [ ] Extension api.ts에 API 함수 추가
- [ ] HitlModal 컴포넌트 구현
- [ ] SSE 이벤트 핸들러 연결
- [ ] E2E 테스트 작성
