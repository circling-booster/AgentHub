# Chrome Extension 개발 가이드

> AgentHub Chrome Extension의 아키텍처, 핵심 패턴, 구현 가이드

**최종 수정일:** 2026-01-28

---

## 개요

AgentHub Chrome Extension은 웹 페이지에서 직접 AI 에이전트와 상호작용할 수 있게 해주는 Manifest V3 기반 확장 프로그램입니다.

### 핵심 특징

| 특징 | 설명 |
|------|------|
| **WXT 프레임워크** | Vite 기반, TypeScript 우선, 자동 manifest 생성 |
| **Manifest V3** | 최신 Chrome Extension 표준 준수 |
| **Offscreen Document** | 장시간 LLM 요청 처리를 위한 필수 패턴 |
| **SSE 스트리밍** | POST + fetch ReadableStream 방식 |

---

## 아키텍처

### 컴포넌트 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    Chrome Extension                          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   Popup UI   │  │  Side Panel  │  │  Content Script  │   │
│  │   (React)    │  │   (React)    │  │  (Page Context)  │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                 │                    │             │
│         └─────────────────┼────────────────────┘             │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Background Service Worker                  │ │
│  │  - 메시지 라우팅                                         │ │
│  │  - Health Check (chrome.alarms)                        │ │
│  │  - Offscreen Document 관리                              │ │
│  └────────────────────────┬───────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────▼───────────────────────────────┐ │
│  │              Offscreen Document (핵심)                   │ │
│  │  - SSE 스트리밍 처리                                     │ │
│  │  - 장시간 API 요청                                       │ │
│  │  - Service Worker 타임아웃 우회                          │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP (localhost:8000)
                               ↓
                    ┌──────────────────┐
                    │ AgentHub Server  │
                    └──────────────────┘
```

### 왜 Offscreen Document가 필수인가?

#### 문제: Service Worker 30초 타임아웃

Chrome은 Manifest V3에서 Background Script를 Service Worker로 대체했습니다. Service Worker는 다음 조건에서 **강제 종료**됩니다:

| 조건 | 설명 |
|------|------|
| **30초 유휴** | 이벤트나 API 호출 없이 30초 경과 |
| **5분 처리** | 단일 이벤트 처리가 5분 초과 |
| **30초 무응답** | fetch 응답이 30초 내 도착하지 않음 |

**LLM 응답은 30초 이상 걸릴 수 있어 Service Worker에서 직접 처리 불가능합니다.**

#### 해결: Offscreen Document

Offscreen Document는 Service Worker와 **독립적인 수명 주기**를 가집니다:
- DOM 접근 가능 (Service Worker는 불가)
- 장시간 작업 처리 가능
- Service Worker 종료와 무관하게 유지

---

## 디렉토리 구조

```
extension/
├── wxt.config.ts              # WXT 설정
├── package.json
├── tsconfig.json
│
├── entrypoints/               # WXT 엔트리포인트 (자동 감지)
│   ├── popup/                 # 팝업 UI
│   │   ├── index.html
│   │   ├── main.tsx
│   │   └── App.tsx
│   │
│   ├── sidepanel/             # 사이드패널 (MV3)
│   │   ├── index.html
│   │   └── main.tsx
│   │
│   ├── background.ts          # Service Worker
│   ├── content.ts             # 콘텐츠 스크립트
│   │
│   └── offscreen/             # Offscreen Document (핵심)
│       ├── index.html
│       └── main.ts
│
├── components/                # 공유 React 컴포넌트
├── lib/                       # 유틸리티
│   ├── api.ts                 # REST API 클라이언트
│   ├── sse.ts                 # SSE 스트리밍 클라이언트
│   └── messaging.ts           # 내부 메시지 타입
│
├── assets/                    # 아이콘, 이미지
└── public/                    # 정적 파일
```

---

## 핵심 구현

### 1. WXT 설정

```typescript
// wxt.config.ts
import { defineConfig } from 'wxt';

export default defineConfig({
  modules: ['@wxt-dev/module-react'],
  manifest: {
    name: 'AgentHub',
    description: 'MCP + A2A 통합 AI Agent 인터페이스',
    permissions: [
      'activeTab',
      'storage',
      'sidePanel',
      'offscreen',      // Offscreen Document 권한
      'alarms',         // Health Check용
    ],
    host_permissions: [
      'http://localhost:8000/*',
      'http://127.0.0.1:8000/*',
    ],
  },
});
```

### 2. Offscreen Document 구현 (핵심)

#### offscreen/index.html

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>AgentHub Offscreen</title>
</head>
<body>
  <script type="module" src="./main.ts"></script>
</body>
</html>
```

#### offscreen/main.ts

```typescript
// offscreen/main.ts
/**
 * Offscreen Document - SSE 스트리밍 처리
 *
 * Service Worker 타임아웃(30초)을 우회하여 장시간 LLM 요청 처리
 */

import { streamChat, StreamEvent } from '../lib/sse';

interface StreamChatRequest {
  type: 'STREAM_CHAT';
  payload: {
    conversationId: string;
    message: string;
    requestId: string;
  };
}

interface StreamChatResponse {
  type: 'STREAM_CHAT_EVENT' | 'STREAM_CHAT_DONE' | 'STREAM_CHAT_ERROR';
  requestId: string;
  event?: StreamEvent;
  error?: string;
}

// 메시지 핸들러
chrome.runtime.onMessage.addListener((
  message: StreamChatRequest,
  sender,
  sendResponse
) => {
  if (message.type === 'STREAM_CHAT') {
    handleStreamChat(message.payload);
    sendResponse({ received: true });
  }
  return true;
});

async function handleStreamChat(payload: {
  conversationId: string;
  message: string;
  requestId: string;
}) {
  const { conversationId, message, requestId } = payload;

  try {
    await streamChat(
      conversationId,
      message,
      // 각 이벤트를 Background로 전달
      (event: StreamEvent) => {
        chrome.runtime.sendMessage({
          type: 'STREAM_CHAT_EVENT',
          requestId,
          event,
        } as StreamChatResponse);
      }
    );

    // 완료 알림
    chrome.runtime.sendMessage({
      type: 'STREAM_CHAT_DONE',
      requestId,
    } as StreamChatResponse);

  } catch (error) {
    // 에러 알림
    chrome.runtime.sendMessage({
      type: 'STREAM_CHAT_ERROR',
      requestId,
      error: error instanceof Error ? error.message : 'Unknown error',
    } as StreamChatResponse);
  }
}

console.log('[Offscreen] Document loaded and ready');
```

### 3. Background Service Worker

```typescript
// background.ts
/**
 * Background Service Worker
 *
 * 역할:
 * - Offscreen Document 생명주기 관리
 * - UI ↔ Offscreen 메시지 라우팅
 * - Health Check (30초 주기)
 */

const OFFSCREEN_DOCUMENT_PATH = 'offscreen/index.html';

// 활성 스트리밍 요청 추적
const activeRequests = new Map<string, {
  resolve: (value: void) => void;
  onEvent: (event: any) => void;
}>();

// ==================== Offscreen Document 관리 ====================

async function ensureOffscreenDocument(): Promise<void> {
  // 이미 존재하는지 확인
  const existingContexts = await chrome.runtime.getContexts({
    contextTypes: [chrome.runtime.ContextType.OFFSCREEN_DOCUMENT],
    documentUrls: [chrome.runtime.getURL(OFFSCREEN_DOCUMENT_PATH)],
  });

  if (existingContexts.length > 0) {
    return; // 이미 존재
  }

  // 새로 생성
  await chrome.offscreen.createDocument({
    url: OFFSCREEN_DOCUMENT_PATH,
    reasons: [chrome.offscreen.Reason.WORKERS],
    justification: 'Handle long-running LLM API requests that exceed Service Worker timeout',
  });

  console.log('[Background] Offscreen document created');
}

// ==================== 메시지 라우팅 ====================

// UI → Background → Offscreen
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // UI에서 스트리밍 요청
  if (message.type === 'START_STREAM_CHAT') {
    handleStartStreamChat(message.payload, sender.tab?.id);
    sendResponse({ received: true });
    return true;
  }

  // Offscreen에서 이벤트 수신
  if (message.type === 'STREAM_CHAT_EVENT') {
    const request = activeRequests.get(message.requestId);
    if (request) {
      request.onEvent(message.event);
    }
    return false;
  }

  // Offscreen에서 완료/에러 수신
  if (message.type === 'STREAM_CHAT_DONE' || message.type === 'STREAM_CHAT_ERROR') {
    const request = activeRequests.get(message.requestId);
    if (request) {
      request.resolve();
      activeRequests.delete(message.requestId);
    }

    // UI에 전달
    broadcastToUI(message);
    return false;
  }

  return false;
});

async function handleStartStreamChat(
  payload: { conversationId: string; message: string },
  tabId?: number
) {
  const requestId = crypto.randomUUID();

  // Offscreen Document 확보
  await ensureOffscreenDocument();

  // 요청 추적 등록
  activeRequests.set(requestId, {
    resolve: () => {},
    onEvent: (event) => {
      // UI에 이벤트 전달
      if (tabId) {
        chrome.tabs.sendMessage(tabId, {
          type: 'STREAM_CHAT_EVENT',
          requestId,
          event,
        });
      }
    },
  });

  // Offscreen에 요청 전달
  chrome.runtime.sendMessage({
    type: 'STREAM_CHAT',
    payload: {
      ...payload,
      requestId,
    },
  });
}

function broadcastToUI(message: any) {
  // 모든 탭에 브로드캐스트 (또는 특정 탭만)
  chrome.runtime.sendMessage(message).catch(() => {
    // UI가 없으면 무시
  });
}

// ==================== Health Check ====================

// 30초마다 서버 상태 확인
chrome.alarms.create('healthCheck', { periodInMinutes: 0.5 });

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === 'healthCheck') {
    await checkServerHealth();
  }
});

async function checkServerHealth(): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch('http://localhost:8000/health', {
      method: 'GET',
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    const isHealthy = response.ok;

    // 상태 저장
    await chrome.storage.local.set({
      serverHealth: {
        status: isHealthy ? 'healthy' : 'unhealthy',
        lastChecked: Date.now(),
      },
    });

    return isHealthy;
  } catch (error) {
    await chrome.storage.local.set({
      serverHealth: {
        status: 'unhealthy',
        lastChecked: Date.now(),
      },
    });
    return false;
  }
}

// ==================== 보안: Token Handshake ====================

let extensionToken: string | null = null;

async function initializeAuth(): Promise<boolean> {
  /**
   * 서버와 토큰 교환 (Drive-by RCE 방지)
   *
   * 서버 시작 시 생성된 난수 토큰을 교환하여
   * 악성 웹사이트의 localhost API 접근을 차단
   */
  try {
    const response = await fetch('http://localhost:8000/auth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ extension_id: chrome.runtime.id }),
    });

    if (!response.ok) {
      console.error('[Background] Token exchange failed');
      return false;
    }

    const { token } = await response.json();
    extensionToken = token;

    // Session Storage에 저장 (브라우저 종료 시 삭제)
    await chrome.storage.session.set({ extensionToken: token });
    console.log('[Background] Token exchange successful');
    return true;
  } catch (error) {
    console.error('[Background] Token exchange error:', error);
    return false;
  }
}

// 토큰 getter (다른 모듈에서 사용)
export function getExtensionToken(): string | null {
  return extensionToken;
}

// ==================== 초기화 ====================

chrome.runtime.onInstalled.addListener(async () => {
  console.log('[Background] Extension installed');
  await checkServerHealth();
});

// 서버 Health Check 후 토큰 교환
chrome.runtime.onStartup.addListener(async () => {
  console.log('[Background] Extension startup');
  const isHealthy = await checkServerHealth();
  if (isHealthy) {
    await initializeAuth();
  }
});

console.log('[Background] Service Worker started');
```

### 4. SSE 클라이언트

```typescript
// lib/sse.ts
/**
 * POST 기반 SSE 스트리밍 클라이언트
 *
 * EventSource는 GET만 지원하므로 fetch + ReadableStream 사용
 */

const API_BASE = 'http://localhost:8000/api';

export interface StreamEvent {
  type: 'text' | 'tool_call' | 'tool_result' | 'done' | 'error';
  content?: string;
  name?: string;
  arguments?: Record<string, unknown>;
  result?: unknown;
  message?: string;
}

export async function streamChat(
  conversationId: string,
  message: string,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      message: message,
    }),
    signal,
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('Response body is not readable');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE 이벤트 파싱
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data) {
            try {
              const event: StreamEvent = JSON.parse(data);
              onEvent(event);

              if (event.type === 'done' || event.type === 'error') {
                return;
              }
            } catch (e) {
              console.error('Failed to parse SSE event:', e);
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
```

### 5. REST API 클라이언트

```typescript
// lib/api.ts
/**
 * REST API 클라이언트 (보안 토큰 포함)
 *
 * CRUD 작업용 (MCP 서버 등록, 설정 변경 등)
 * Drive-by RCE 방지를 위한 Token Handshake 패턴 적용
 */

const API_BASE = 'http://localhost:8000/api';

// ==================== 인증 ====================

let extensionToken: string | null = null;

/**
 * 인증된 API 요청 (모든 /api/* 요청에 사용)
 */
async function authenticatedFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  // 토큰이 없으면 Session Storage에서 로드
  if (!extensionToken) {
    const stored = await chrome.storage.session.get('extensionToken');
    extensionToken = stored.extensionToken || null;
  }

  if (!extensionToken) {
    throw new Error('Not authenticated. Server may not be running.');
  }

  return fetch(`http://localhost:8000${path}`, {
    ...options,
    headers: {
      ...options.headers,
      'X-Extension-Token': extensionToken,
      'Content-Type': 'application/json',
    },
  });
}

// ==================== MCP 서버 관리 ====================

export interface McpServer {
  id: string;
  name: string;
  url: string;
  enabled: boolean;
  registeredAt: string;
  tools?: Tool[];
}

export interface Tool {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
}

export async function registerMcpServer(url: string, name?: string): Promise<McpServer> {
  const response = await authenticatedFetch('/api/mcp/servers', {
    method: 'POST',
    body: JSON.stringify({ url, name }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to register MCP server');
  }

  return response.json();
}

export async function listMcpServers(): Promise<McpServer[]> {
  const response = await authenticatedFetch('/api/mcp/servers');

  if (!response.ok) {
    throw new Error('Failed to list MCP servers');
  }

  return response.json();
}

export async function removeMcpServer(serverId: string): Promise<void> {
  const response = await authenticatedFetch(`/api/mcp/servers/${serverId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to remove MCP server');
  }
}

// ==================== Health Check ====================

export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  version?: string;
}

export async function getServerHealth(): Promise<HealthStatus> {
  try {
    const response = await fetch(`${API_BASE.replace('/api', '')}/health`, {
      method: 'GET',
    });

    if (response.ok) {
      return response.json();
    }

    return { status: 'unhealthy' };
  } catch {
    return { status: 'unhealthy' };
  }
}
```

---

## localhost 통신 보안

### Mixed Content 문제 없음

Chrome Extension의 **Background Service Worker**는 웹 페이지 컨텍스트와 다르게 동작합니다:

| 컨텍스트 | Mixed Content 적용 |
|---------|-------------------|
| Content Script (웹 페이지) | ✅ 적용됨 |
| **Background Service Worker** | ❌ 미적용 |
| **Offscreen Document** | ❌ 미적용 |

`host_permissions`만 설정하면 HTTP localhost 접근이 가능합니다.

### 권장 사항

```typescript
// ❌ Content Script에서 직접 API 호출 금지
// content.ts
fetch('http://localhost:8000/api/...');  // 차단될 수 있음

// ✅ Background로 메시지 전달 후 처리
// content.ts
chrome.runtime.sendMessage({ type: 'API_REQUEST', ... });

// background.ts
chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'API_REQUEST') {
    fetch('http://localhost:8000/api/...');  // 정상 동작
  }
});
```

---

## 개발 명령어

```bash
cd extension

# 개발 모드 (HMR 활성화)
npm run dev

# Chrome용 빌드
npm run build

# Firefox용 빌드
npm run build:firefox

# 타입 체크
npm run typecheck

# 린트
npm run lint
```

---

## 참고 자료

- [Chrome Extension Service Worker Lifecycle](https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle)
- [Offscreen Documents in Manifest V3](https://developer.chrome.com/blog/Offscreen-Documents-in-Manifest-v3)
- [WXT Framework Documentation](https://wxt.dev/)
- [Chrome Extension Network Requests](https://developer.chrome.com/docs/extensions/develop/concepts/network-requests)

---

*문서 생성일: 2026-01-28*
