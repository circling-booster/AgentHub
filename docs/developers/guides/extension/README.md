# Extension Development Guide

Chrome Extension 개발 가이드입니다. WXT 프레임워크 기반 Manifest V3 Extension 개발 방법을 다룹니다.

---

## Development Environment Setup

### Prerequisites

- Node.js 18+
- npm 또는 pnpm

### Installation

```bash
cd extension
npm install
```

### Development Mode

```bash
# 개발 서버 시작 (Hot Reload)
npm run dev

# Chrome에 로드:
# 1. chrome://extensions/ 접속
# 2. "개발자 모드" 활성화
# 3. "압축해제된 확장 프로그램을 로드합니다." 클릭
# 4. extension/.output/chrome-mv3-dev 폴더 선택
```

---

## Adding New Components

### Entrypoint 추가

WXT에서 새로운 entrypoint를 추가하려면 `entrypoints/` 폴더에 파일을 생성합니다.

```typescript
// entrypoints/new-page.html (HTML entrypoint)
// entrypoints/new-page/index.tsx (React entrypoint)
// entrypoints/new-script.content.ts (Content Script)
```

### Popup 페이지 예시

```typescript
// entrypoints/popup/App.tsx
export default function App() {
  return (
    <div className="popup-container">
      <h1>AgentHub</h1>
      <button onClick={() => chrome.runtime.sendMessage({ type: 'OPEN_SIDEPANEL' })}>
        Open Sidepanel
      </button>
    </div>
  );
}
```

### Content Script 예시

```typescript
// entrypoints/injected.content.ts
export default defineContentScript({
  matches: ['<all_urls>'],
  main() {
    console.log('Content script loaded');
    // DOM 조작 로직
  },
});
```

---

## API Integration

### API Client 사용

`lib/api.ts`에서 API 클라이언트를 import하여 사용합니다.

```typescript
import { apiClient } from '@/lib/api';

// Endpoint 목록 조회
const endpoints = await apiClient.getEndpoints();

// Endpoint 등록
await apiClient.registerEndpoint({
  type: 'mcp',
  url: 'http://127.0.0.1:9000/mcp',
  name: 'Local MCP Server',
});

// 대화 시작
const response = await apiClient.chat({
  conversationId: 'conv-123',
  message: 'Hello, world!',
});
```

### 새 API 메서드 추가

```typescript
// lib/api.ts
export const apiClient = {
  // 기존 메서드들...

  // 새 메서드 추가
  async newMethod(params: NewMethodParams): Promise<NewMethodResponse> {
    const response = await fetch(`${this.baseUrl}/api/new-endpoint`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(params),
    });
    return response.json();
  },
};
```

---

## SSE Event Handling

### SSE 연결 설정

Offscreen Document에서 SSE 연결을 관리합니다.

```typescript
// entrypoints/offscreen/sse-handler.ts
export function connectSSE(conversationId: string) {
  const eventSource = new EventSource(
    `http://localhost:8000/api/chat/${conversationId}/stream`
  );

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleStreamChunk(data);
  };

  eventSource.onerror = (error) => {
    console.error('SSE Error:', error);
    eventSource.close();
  };

  return eventSource;
}
```

### StreamChunk 이벤트 타입 처리

```typescript
function handleStreamChunk(chunk: StreamChunk) {
  switch (chunk.type) {
    case 'text':
      appendText(chunk.content);
      break;
    case 'tool_call':
      showToolCallIndicator(chunk.tool_name, chunk.arguments);
      break;
    case 'tool_result':
      showToolResult(chunk.tool_name, chunk.result);
      break;
    case 'agent_transfer':
      showAgentTransfer(chunk.from_agent, chunk.to_agent);
      break;
    case 'error':
      showError(chunk.error_code, chunk.message);
      break;
    case 'done':
      finishStream();
      break;
  }
}
```

---

## Inter-Component Communication

### Background ↔ Sidepanel 메시지

```typescript
// Background에서 메시지 수신
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'GET_AUTH_TOKEN') {
    sendResponse({ token: authToken });
  }
  return true; // 비동기 응답 허용
});

// Sidepanel에서 메시지 전송
const response = await chrome.runtime.sendMessage({ type: 'GET_AUTH_TOKEN' });
console.log('Token:', response.token);
```

### Storage 동기화

```typescript
// 데이터 저장
await chrome.storage.local.set({ key: 'value' });

// 데이터 조회
const { key } = await chrome.storage.local.get('key');

// 변경 감지
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && changes.key) {
    console.log('Key changed:', changes.key.newValue);
  }
});
```

---

## Debugging

### Background Service Worker

1. `chrome://extensions/` 접속
2. AgentHub Extension 찾기
3. "서비스 워커" 링크 클릭
4. DevTools Console에서 로그 확인

### Sidepanel / Popup

1. Extension 아이콘 우클릭
2. "검사" 선택
3. DevTools에서 디버깅

### Content Script

1. 페이지에서 F12 (DevTools)
2. Console 탭에서 content script 로그 확인
3. Sources 탭에서 breakpoint 설정

### Network 요청 추적

```typescript
// lib/api.ts에 디버그 로깅 추가
const DEBUG = true;

async function fetchWithLog(url: string, options: RequestInit) {
  if (DEBUG) {
    console.log('[API Request]', url, options);
  }
  const response = await fetch(url, options);
  if (DEBUG) {
    console.log('[API Response]', response.status, await response.clone().text());
  }
  return response;
}
```

---

## Build and Deploy

### Production Build

```bash
# Chrome용 빌드
npm run build

# 빌드 결과물 위치
# extension/.output/chrome-mv3/
```

### Package for Distribution

```bash
# ZIP 파일 생성
npm run zip

# 결과물: extension/.output/agenthub-chrome.zip
```

### Chrome Web Store 배포

1. [Chrome Developer Dashboard](https://chrome.google.com/webstore/devconsole) 접속
2. "새 항목 추가" 클릭
3. ZIP 파일 업로드
4. 스토어 등록 정보 입력
5. 검토 제출

---

## Common Patterns

### Token Handshake

Extension 설치 시 서버와 토큰 교환을 수행합니다.

```typescript
// Background Service Worker
async function performTokenHandshake() {
  const response = await fetch('http://localhost:8000/api/auth/handshake', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ extensionId: chrome.runtime.id }),
  });

  const { token } = await response.json();
  await chrome.storage.local.set({ authToken: token });
}
```

### Connection Status Indicator

```typescript
// Popup에서 연결 상태 표시
async function checkConnectionStatus() {
  try {
    const response = await fetch('http://localhost:8000/api/health');
    if (response.ok) {
      setStatus('connected');
    } else {
      setStatus('error');
    }
  } catch {
    setStatus('disconnected');
  }
}
```

---

*Last Updated: 2026-02-05*
