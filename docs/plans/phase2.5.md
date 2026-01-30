# Phase 2.5: Chrome Extension 구현 계획

> WXT + React + TypeScript 기반 Chrome Extension으로 AgentHub 서버 연동 (TDD 전체 적용)

**작성일:** 2026-01-30
**선행 Phase:** Phase 2.0 (MCP Integration) - 완료 (88% 커버리지)
**구현 시 저장:** `docs/plans/phase2.5.md`에 동일 내용 저장

---

## 개요

Phase 2(MCP Integration) 완료 상태에서, Chrome Extension을 구축하여 사용자가 브라우저 사이드패널에서 직접 AI 에이전트와 대화하고 MCP 서버를 관리할 수 있도록 합니다.

**산출물 요약:**
- 서버 API 보강 (GET /api/conversations 라우트 추가)
- WXT 프로젝트 (`extension/` 디렉토리)
- Background Service Worker (토큰 핸드셰이크, 메시지 라우팅, Health Check)
- Offscreen Document (SSE 스트리밍 처리)
- Sidepanel UI (채팅 인터페이스 + MCP 서버 관리 + 대화 이력)
- 공유 라이브러리 (API 클라이언트, SSE 클라이언트, 메시지 타입)
- **Vitest 기반 전체 TDD** (모든 TypeScript 코드에 테스트 먼저 작성)

**핵심 위임:** Extension 구현의 각 Step에서 `/agenthub-extension` skill을 호출하여 WXT 패턴, Offscreen Document, Token Handshake, SSE 스트리밍의 최신 구현 가이드를 활용합니다.

---

## Phase 시작 전 체크리스트

### 선행 조건

- [ ] Phase 2.0 DoD 전체 충족 확인 (88% 커버리지, MCP 통합 완료)
- [ ] 브랜치: `feature/phase-2.5-extension` 신규 생성
- [ ] Node.js 18+ 설치 확인
- [ ] 서버 정상 동작 확인: `uvicorn src.main:app --host localhost --port 8000`

### 필수 웹 검색 (Plan 단계 — 구현 전 1회)

- [ ] `wxt framework latest version 2026` — Breaking Changes 확인
- [ ] `chrome offscreen document api 2026` — API 변경사항 확인
- [ ] `chrome.runtime.getContexts availability 2026` — Chrome 최소 버전 확인
- [ ] `chrome side_panel api 2026` — Side Panel API 변경사항
- [ ] `chrome.storage.session api 2026` — Session Storage API 확인
- [ ] `vitest chrome extension testing 2026` — Extension 테스트 패턴 확인

### Step별 재검증 게이트

| Step | 검증 항목 | 방법 |
|:----:|----------|------|
| 0 시작 | 기존 서버 테스트 통과 확인 | `pytest tests/ -q` |
| 1 시작 | WXT 최신 버전, Vitest 설정 | `/agenthub-extension` skill + 웹 검색 |
| 3 시작 | chrome.storage.session API | 웹 검색 |
| 5 시작 | chrome.offscreen API, getContexts | `/agenthub-extension` skill + 웹 검색 |
| 6 시작 | SSE POST fetch ReadableStream 패턴 | `/agenthub-extension` skill |
| 8 완료 | Extension 보안 패턴 전체 검토 | `/security-checklist` skill |
| 9 완료 | 기존 백엔드 테스트 regression 확인 | `pytest tests/ --cov=src --cov-fail-under=80` |

---

## DoD (Definition of Done)

### 기능 검증

- [ ] Extension 설치 시 서버와 자동 토큰 교환 성공
- [ ] Sidepanel에서 "Hello" 입력 시 LLM 응답 스트리밍 표시
- [ ] MCP 도구 호출 결과가 UI에 표시
- [ ] MCP 서버 등록/해제 UI 동작
- [ ] 대화 목록 표시 및 이전 대화 이어가기
- [ ] 브라우저 종료 후 재시작 시 토큰 재발급 정상 동작
- [ ] 30초 이상 걸리는 LLM 응답도 정상 수신 (Offscreen Document)

### 품질 검증

- [ ] TypeScript strict mode 컴파일 에러 없음 (`npx tsc --noEmit`)
- [ ] ESLint 경고/에러 없음
- [ ] **Vitest 전체 통과** (`npx vitest run`)
- [ ] 백엔드 테스트 regression 없음 (기존 80%+ 커버리지 유지)

### 문서화

- [ ] `extension/README.md` 생성
- [ ] 루트 `README.md`에 Extension 사용법 추가

---

## TDD 전략 (Extension 전체 적용)

### 테스트 프레임워크

| 도구 | 용도 |
|------|------|
| **Vitest** | 단위 테스트 (Vite 네이티브, WXT와 호환) |
| **@testing-library/react** | React 컴포넌트 테스트 |
| **happy-dom** or **jsdom** | DOM 환경 시뮬레이션 |

### chrome.* API Mock 전략

모든 chrome.* API는 테스트 setup에서 글로벌 mock으로 제공:

```typescript
// extension/tests/setup.ts
globalThis.chrome = {
  runtime: {
    id: 'test-extension-id',
    sendMessage: vi.fn(),
    onMessage: { addListener: vi.fn(), removeListener: vi.fn() },
    getContexts: vi.fn().mockResolvedValue([]),
    getURL: vi.fn((path) => `chrome-extension://test-id/${path}`),
  },
  storage: {
    session: {
      get: vi.fn().mockResolvedValue({}),
      set: vi.fn().mockResolvedValue(undefined),
    },
    local: {
      get: vi.fn().mockResolvedValue({}),
      set: vi.fn().mockResolvedValue(undefined),
    },
  },
  offscreen: {
    createDocument: vi.fn().mockResolvedValue(undefined),
    Reason: { WORKERS: 'WORKERS' },
  },
  alarms: {
    create: vi.fn(),
    onAlarm: { addListener: vi.fn() },
  },
  sidePanel: {
    setOptions: vi.fn(),
  },
} as any;
```

### TDD 사이클 (모든 Step 적용)

```
Red   → 테스트 파일 작성 (실패 확인)
Green → 구현 파일 작성 (테스트 통과)
Refactor → 코드 정리
```

### 테스트 파일 위치

```
extension/
├── tests/
│   ├── setup.ts              # chrome.* mock + Vitest 설정
│   ├── lib/
│   │   ├── api.test.ts       # API 클라이언트 테스트
│   │   ├── sse.test.ts       # SSE 파싱 테스트
│   │   └── messaging.test.ts # 메시지 타입 테스트
│   ├── entrypoints/
│   │   ├── background.test.ts  # Background SW 테스트
│   │   └── offscreen.test.ts   # Offscreen 핸들러 테스트
│   ├── components/
│   │   ├── ChatInterface.test.tsx
│   │   ├── ChatInput.test.tsx
│   │   ├── MessageBubble.test.tsx
│   │   ├── McpServerManager.test.tsx
│   │   └── ServerStatus.test.tsx
│   └── hooks/
│       ├── useChat.test.ts
│       ├── useMcpServers.test.ts
│       └── useServerHealth.test.ts
```

---

## 구현 순서 (10 Steps)

### Step 0: 서버 API 보강 (GET /api/conversations)

**목표:** Extension Sidepanel에서 대화 이력을 조회할 수 있도록 서버 라우트 추가

**TDD 순서:**
1. `tests/integration/adapters/test_conversation_routes.py` — 테스트 먼저 작성 (Red)
2. `src/adapters/inbound/http/routes/conversations.py` — 라우트 추가 (Green)

**생성/수정 파일:**

| 파일 | 변경 | 역할 |
|------|------|------|
| `tests/integration/adapters/test_conversation_routes.py` | 수정 | GET /api/conversations 테스트 추가 |
| `src/adapters/inbound/http/routes/conversations.py` | 수정 | GET 라우트 추가 |
| `src/adapters/inbound/http/schemas/conversations.py` | 수정 (필요 시) | 목록 응답 스키마 |

**핵심 구현:**
- `GET /api/conversations` → `conversation_service.list_conversations(limit)` 호출
- 도메인 서비스 `list_conversations()`는 이미 구현 완료 (`orchestrator_service.py:63`)
- 라우트와 스키마만 추가하면 됨

**의존성:** 없음 (서버 측 작업)

---

### Step 1: WXT 프로젝트 스캐폴딩 + Vitest 설정

**목표:** WXT + React + TypeScript + Vitest 프로젝트 초기화

**Skill 위임:** `/agenthub-extension` — WXT 설정 패턴 및 Manifest 권한 참조

**생성 파일:**

| 파일 | 역할 |
|------|------|
| `extension/package.json` | 프로젝트 의존성 (wxt, react, vitest, typescript) |
| `extension/wxt.config.ts` | WXT 설정 (manifest, permissions, modules) |
| `extension/tsconfig.json` | TypeScript strict mode |
| `extension/vitest.config.ts` | Vitest 설정 (happy-dom, setup 파일) |
| `extension/tests/setup.ts` | chrome.* API 글로벌 mock |

**핵심 구현:**

Manifest permissions:
- `activeTab`, `storage`, `sidePanel`, `offscreen`, `alarms`
- `host_permissions`: `http://localhost:8000/*`, `http://127.0.0.1:8000/*`

Vitest 설정:
```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
export default defineConfig({
  test: {
    environment: 'happy-dom',
    setupFiles: ['./tests/setup.ts'],
    globals: true,
  },
});
```

npm 의존성:
- Runtime: `wxt`, `@wxt-dev/module-react`, `react`, `react-dom`
- Dev: `typescript`, `vitest`, `happy-dom`, `@testing-library/react`, `@testing-library/dom`, `@types/react`, `@types/react-dom`, `eslint`

**의존성:** Step 0 (서버 API 준비 완료)

---

### Step 2: 공유 타입 및 메시지 인터페이스 (TDD)

**목표:** Extension 내부 통신용 TypeScript 인터페이스 정의

**TDD 순서:**
1. `extension/tests/lib/messaging.test.ts` — 메시지 타입 검증 테스트 (Red)
2. `extension/lib/types.ts`, `extension/lib/messaging.ts`, `extension/lib/constants.ts` — 구현 (Green)

**생성 파일:**

| 파일 | 역할 |
|------|------|
| `extension/tests/lib/messaging.test.ts` | 메시지 타입 가드 함수 테스트 |
| `extension/lib/types.ts` | 서버 API 타입 (서버 스키마와 1:1 대응) |
| `extension/lib/messaging.ts` | Extension 내부 메시지 타입 + 타입 가드 함수 |
| `extension/lib/constants.ts` | 공통 상수 (API_BASE, Storage keys) |

**핵심 구현:**

`lib/types.ts` — 서버 스키마 기반 (`src/adapters/inbound/http/schemas/` 참조):
- `StreamEvent`: `type` = `conversation_created` | `text` | `done` | `error`
  - **주의:** 서버 `chat.py:56-58`에서 `conversation_created` 이벤트에 `conversation_id` 필드 포함
  - 서버 `chat.py:73`에서 `text` 이벤트에 `content` 필드 포함
- `McpServer`, `Tool`, `HealthStatus`, **`Conversation`** 등 서버 응답 타입
- `ChatStreamEvent` (서버 `schemas/chat.py`의 타입 필드와 일치)

`lib/messaging.ts` — Extension 내부 메시지 + 타입 가드:
- `START_STREAM_CHAT`: UI → Background (채팅 시작)
- `STREAM_CHAT`: Background → Offscreen (SSE 실행)
- `STREAM_CHAT_EVENT` / `STREAM_CHAT_DONE` / `STREAM_CHAT_ERROR`: 이벤트 흐름
- `CANCEL_STREAM`: 스트림 취소
- `isStreamChatEvent()`, `isStreamChatDone()` 등 타입 가드 함수 (테스트 대상)

**의존성:** Step 1

---

### Step 3: API 클라이언트 라이브러리 (TDD)

**목표:** 인증된 REST API 호출을 위한 공유 클라이언트

**Skill 위임:** `/agenthub-extension` — Token Handshake 클라이언트 패턴 참조

**TDD 순서:**
1. `extension/tests/lib/api.test.ts` — 테스트 먼저 작성 (Red)
2. `extension/lib/api.ts` — 구현 (Green)

**생성 파일:**

| 파일 | 역할 |
|------|------|
| `extension/tests/lib/api.test.ts` | fetch mock 기반 API 테스트 |
| `extension/lib/api.ts` | 인증된 REST API 클라이언트 |

**테스트 케이스:**
- `authenticatedFetch()`가 `X-Extension-Token` 헤더를 포함하는지 검증
- `chrome.storage.session`에서 토큰 로드 검증
- 토큰 없을 때 에러 throw 검증
- `initializeAuth()`: fetch mock으로 토큰 교환 흐름 검증
- 각 API 함수(`listMcpServers`, `registerMcpServer` 등)의 올바른 URL/method 호출 검증
- HTTP 에러 응답 시 에러 핸들링 검증

**서버 API 매핑 (Step 0 보강 포함):**

| 클라이언트 함수 | 서버 엔드포인트 | 인증 |
|----------------|---------------|:----:|
| `getServerHealth()` | `GET /health` | No |
| `initializeAuth()` | `POST /auth/token` | No (Origin 검증) |
| `registerMcpServer()` | `POST /api/mcp/servers` | Yes |
| `listMcpServers()` | `GET /api/mcp/servers` | Yes |
| `removeMcpServer()` | `DELETE /api/mcp/servers/{id}` | Yes |
| `getServerTools()` | `GET /api/mcp/servers/{id}/tools` | Yes |
| `createConversation()` | `POST /api/conversations` | Yes |
| **`listConversations()`** | **`GET /api/conversations`** | Yes |

**보안 핵심:**
- 토큰은 `chrome.storage.session`에 저장 (브라우저 종료 시 자동 삭제)
- `authenticatedFetch()`: 모든 `/api/*` 요청에 `X-Extension-Token` 헤더 자동 주입
- 서버의 `security.py` ExtensionAuthMiddleware가 이 헤더를 검증

**의존성:** Step 2

---

### Step 4: SSE 스트리밍 클라이언트 (TDD)

**목표:** POST 기반 SSE 스트리밍을 fetch ReadableStream으로 처리

**Skill 위임:** `/agenthub-extension` — SSE 스트리밍 패턴 참조

**TDD 순서:**
1. `extension/tests/lib/sse.test.ts` — 테스트 먼저 작성 (Red)
2. `extension/lib/sse.ts` — 구현 (Green)

**생성 파일:**

| 파일 | 역할 |
|------|------|
| `extension/tests/lib/sse.test.ts` | SSE 파싱 로직 테스트 |
| `extension/lib/sse.ts` | POST SSE 스트리밍 클라이언트 |

**테스트 케이스:**
- SSE 이벤트 파싱: `data: {"type":"text","content":"Hello"}\n\n` → `onEvent` 콜백 호출
- `conversation_created` 이벤트 파싱: `conversation_id` 필드 추출
- `done` 이벤트 수신 시 스트림 종료
- `error` 이벤트 수신 시 에러 처리
- **buffer 경계 처리**: 이벤트가 두 chunk에 걸쳐 올 때 정확한 파싱
- `AbortSignal`로 스트림 취소
- HTTP 에러 응답 시 에러 throw
- 인증 헤더 포함 검증

**서버 SSE 이벤트 형식 (`chat.py` 기반, 정확히 일치해야 함):**
```
data: {"type": "conversation_created", "conversation_id": "uuid"}\n\n
data: {"type": "text", "content": "Hello"}\n\n
data: {"type": "done"}\n\n
data: {"type": "error", "message": "..."}\n\n
```

- **EventSource 사용 금지** (CLAUDE.md 제약)
- `fetch` + `ReadableStream` + `TextDecoder`로 SSE 파싱
- 요청 body: `{ conversation_id: string | null, message: string }` (서버 `ChatRequest` 일치)

**의존성:** Step 3

---

### Step 5: Background Service Worker (TDD)

**목표:** 토큰 핸드셰이크, Offscreen 관리, 메시지 라우팅, Health Check

**Skill 위임:** `/agenthub-extension` — Offscreen 관리, Token Handshake, 메시지 라우팅

**TDD 순서:**
1. `extension/tests/entrypoints/background.test.ts` — 테스트 먼저 작성 (Red)
2. `extension/entrypoints/background.ts` — 구현 (Green)

**생성 파일:**

| 파일 | 역할 |
|------|------|
| `extension/tests/entrypoints/background.test.ts` | Background SW 테스트 |
| `extension/entrypoints/background.ts` | Background Service Worker |

**테스트 케이스:**
- `initializeAuth()`: fetch mock으로 토큰 교환 성공/실패 검증
- `initializeAuth()` 실패 시 재시도 로직 검증
- `ensureOffscreenDocument()`: `getContexts()` 반환값에 따른 분기 검증
- 메시지 라우팅: `START_STREAM_CHAT` → `STREAM_CHAT` 변환 + requestId 생성
- 메시지 라우팅: `STREAM_CHAT_EVENT` → UI 전달 검증
- Health Check: `chrome.alarms.create` 호출 확인, 상태 저장 검증

**4가지 핵심 역할:**

1. **Token Handshake**: `POST /auth/token`에 `extension_id: chrome.runtime.id` 전송
   - 서버 `auth.py`가 Origin 검증 (`chrome-extension://` 필수)
   - 응답 토큰을 `chrome.storage.session`에 저장
   - `onInstalled` + `onStartup` 이벤트에서 호출
   - **서버 미응답 시 재시도**: Health Check alarm에서 서버 복구 감지 후 재시도

2. **Offscreen Document 라이프사이클**:
   - `chrome.runtime.getContexts()`로 기존 문서 확인
   - 없으면 `chrome.offscreen.createDocument()` 호출
   - `Reason.WORKERS` + justification 필수
   - **Idle 정리**: 활성 스트림이 없으면 `chrome.offscreen.closeDocument()` (선택적 최적화)

3. **메시지 라우팅** (UI ↔ Background ↔ Offscreen):
   - `START_STREAM_CHAT`: UI에서 수신 → requestId 생성 → Offscreen으로 `STREAM_CHAT` 전달
   - `STREAM_CHAT_EVENT/DONE/ERROR`: Offscreen에서 수신 → UI(Sidepanel)로 전달
   - `CANCEL_STREAM`: UI에서 수신 → Offscreen으로 전달

4. **Health Check**: `chrome.alarms.create('healthCheck', { periodInMinutes: 0.5 })`
   - 30초마다 `GET /health` 호출
   - `chrome.storage.local`에 상태 저장
   - 서버 복구 시 자동 토큰 교환 재시도

**의존성:** Step 2 (메시지 타입), Step 3 (API 클라이언트)

---

### Step 6: Offscreen Document (TDD)

**목표:** Service Worker 30초 타임아웃을 우회하여 장시간 SSE 스트리밍 처리

**Skill 위임:** `/agenthub-extension` — Offscreen Document 구현 패턴 참조

**TDD 순서:**
1. `extension/tests/entrypoints/offscreen.test.ts` — 테스트 먼저 작성 (Red)
2. `extension/entrypoints/offscreen/index.html` + `main.ts` — 구현 (Green)

**생성 파일:**

| 파일 | 역할 |
|------|------|
| `extension/tests/entrypoints/offscreen.test.ts` | Offscreen 핸들러 테스트 |
| `extension/entrypoints/offscreen/index.html` | Offscreen HTML |
| `extension/entrypoints/offscreen/main.ts` | SSE 스트리밍 핸들러 |

**테스트 케이스:**
- `STREAM_CHAT` 메시지 수신 시 `streamChat()` 호출 검증
- 각 SSE 이벤트가 `STREAM_CHAT_EVENT`로 Background에 전달되는지 검증
- 스트림 완료 시 `STREAM_CHAT_DONE` 전달 검증
- 스트림 에러 시 `STREAM_CHAT_ERROR` 전달 검증
- `CANCEL_STREAM` 수신 시 AbortController.abort() 호출 검증
- 동시 다중 스트림 관리 (`activeStreams` Map) 검증

**핵심 구현:**
- `chrome.runtime.onMessage`에서 `STREAM_CHAT` 수신
- `streamChat()` (lib/sse.ts) 호출
- `AbortController` + `activeStreams` Map으로 동시 요청 관리

**의존성:** Step 4 (SSE 클라이언트), Step 5 (Background에서 Offscreen 생성)

---

### Step 7: React Hooks (TDD)

**목표:** 상태 관리 Hook 구현 (UI 로직과 분리)

**TDD 순서:**
1. `extension/tests/hooks/useChat.test.ts` 등 — 테스트 먼저 (Red)
2. `extension/hooks/useChat.ts` 등 — 구현 (Green)

**생성 파일:**

| 파일 | 역할 |
|------|------|
| `extension/tests/hooks/useChat.test.ts` | 채팅 Hook 테스트 |
| `extension/tests/hooks/useMcpServers.test.ts` | MCP 서버 Hook 테스트 |
| `extension/tests/hooks/useServerHealth.test.ts` | Health Hook 테스트 |
| `extension/hooks/useChat.ts` | 채팅 상태 관리 |
| `extension/hooks/useMcpServers.ts` | MCP 서버 상태 관리 |
| `extension/hooks/useServerHealth.ts` | 서버 Health 상태 |

**useChat 테스트 케이스:**
- `sendMessage()` 호출 시 `chrome.runtime.sendMessage`에 `START_STREAM_CHAT` 전달
- `STREAM_CHAT_EVENT(conversation_created)` 수신 시 `conversationId` 업데이트
- `STREAM_CHAT_EVENT(text)` 수신 시 마지막 assistant 메시지에 content 누적 (스트리밍)
- `STREAM_CHAT_DONE` 수신 시 `streaming` 상태 false
- `STREAM_CHAT_ERROR` 수신 시 에러 상태 설정

**useMcpServers 테스트 케이스:**
- `loadServers()` 호출 시 `listMcpServers()` API 호출
- `addServer()` 호출 시 `registerMcpServer()` API 호출 + 목록 갱신
- `removeServer()` 호출 시 `removeMcpServer()` API 호출 + 목록에서 제거

**useServerHealth 테스트 케이스:**
- `chrome.storage.local`에서 `serverHealth` 데이터 구독
- 상태 변경 시 UI 업데이트

**의존성:** Step 2 (타입), Step 3 (API 클라이언트), Step 5 (메시지 라우팅)

---

### Step 8: Sidepanel UI (TDD)

**목표:** React 기반 채팅 인터페이스 + MCP 서버 관리 + 대화 이력 UI

**Skill 위임:** `/frontend-design` — UI 디자인 (선택적)

**TDD 순서:**
1. `extension/tests/components/*.test.tsx` — 컴포넌트 테스트 먼저 (Red)
2. `extension/components/*.tsx` + `extension/entrypoints/sidepanel/*` — 구현 (Green)

**생성 파일:**

| 파일 | 역할 |
|------|------|
| `extension/tests/components/ChatInterface.test.tsx` | 채팅 UI 테스트 |
| `extension/tests/components/ChatInput.test.tsx` | 입력 컴포넌트 테스트 |
| `extension/tests/components/MessageBubble.test.tsx` | 메시지 버블 테스트 |
| `extension/tests/components/McpServerManager.test.tsx` | MCP 관리 테스트 |
| `extension/tests/components/ServerStatus.test.tsx` | 상태 표시 테스트 |
| `extension/entrypoints/sidepanel/index.html` | Sidepanel HTML |
| `extension/entrypoints/sidepanel/main.tsx` | React 진입점 |
| `extension/entrypoints/sidepanel/App.tsx` | 메인 앱 (탭 전환: Chat / MCP 관리) |
| `extension/entrypoints/sidepanel/App.css` | 전역 스타일 |
| `extension/components/ChatInterface.tsx` | 채팅 UI (메시지 목록 + 입력 + 대화 이력) |
| `extension/components/MessageBubble.tsx` | 메시지 버블 |
| `extension/components/ChatInput.tsx` | 채팅 입력 |
| `extension/components/McpServerManager.tsx` | MCP 서버 등록/삭제 |
| `extension/components/ServerStatus.tsx` | 서버 연결 상태 |

**컴포넌트 테스트 케이스:**
- `ChatInterface`: 메시지 목록 렌더링, 스트리밍 중 실시간 업데이트, 자동 스크롤
- `ChatInput`: 입력 → Enter → sendMessage 호출, 빈 입력 방지, 스트리밍 중 비활성화
- `MessageBubble`: user/assistant 역할별 스타일, 텍스트 렌더링
- `McpServerManager`: 서버 목록 렌더링, URL 입력 → 등록, 삭제 버튼
- `ServerStatus`: healthy/unhealthy 상태별 표시

**UI 기능:**
- **채팅**: 메시지 목록 + 자동 스크롤 + 스트리밍 표시 + 대화 이력 사이드바
- **MCP 관리**: URL 입력으로 서버 등록, 목록 조회, 삭제, 도구 목록 접기/펼치기
- **상태 표시**: Health Check 기반 연결 상태 (초록/빨강 아이콘)

**의존성:** Steps 2, 3, 7 (Hooks)

---

### Step 9: 서버 측 E2E 테스트

**목표:** Extension이 사용하는 전체 API 시퀀스를 서버 측에서 검증

**생성 파일:**

| 파일 | 역할 |
|------|------|
| `tests/e2e/test_extension_server.py` | Extension API 시퀀스 시뮬레이션 |

**테스트 시나리오:**
- `test_full_chat_flow`: Health Check → 토큰 교환 → 대화 생성 → SSE 채팅 → 대화 목록 조회
- `test_mcp_management_flow`: 서버 등록 → 목록 조회 → 도구 조회 → 삭제
- `test_token_required`: 토큰 없이 API 호출 시 403

**의존성:** Steps 0-8

---

### Step 10: 문서화

**목표:** Extension 개발 가이드 및 README 업데이트

**생성 파일:**

| 파일 | 역할 |
|------|------|
| `extension/README.md` | Extension 개발 가이드 |

**수정 파일:**

| 파일 | 변경 |
|------|------|
| `README.md` (루트) | Development Status + Extension 사용법 추가 |
| `docs/roadmap.md` | Phase 2.5 DoD 체크박스 완료 |

**extension/README.md 구성:**
1. Purpose — Chrome Extension의 역할
2. Structure — 엔트리포인트별 역할
3. Architecture — Offscreen Document 패턴
4. Security — Token Handshake, Session Storage
5. Development — `npm run dev`, Chrome 로드 방법
6. Testing — `npx vitest run`, 테스트 구조
7. Build — `npm run build`

**의존성:** Steps 0-9

---

## 병렬 작업 가능 구간

```
Step 0 (서버 API 보강)
  └── Step 1 (WXT + Vitest 스캐폴딩)
        └── Step 2 (타입/메시지)
              ├── Step 3 (API 클라이언트) ──┐
              │     └── Step 4 (SSE)       │
              │           └── Step 6 (Offscreen) ←── Step 5
              └── Step 5 (Background) ─────┘
                                                    ↓
                                Step 7 (React Hooks) ← Steps 2, 3, 5
                                        ↓
                                Step 8 (Sidepanel UI) ← Step 7
                                        ↓
                                Step 9 (E2E 테스트)
                                        ↓
                                Step 10 (문서화)
```

Step 3과 Step 5는 Step 2 완료 후 **병렬 진행 가능**.

---

## Skill/Agent 활용 계획

### 명시적 호출 시점

| 시점 | 호출 | 목적 |
|------|------|------|
| Step 0 시작 | `/tdd` skill | 서버 API 보강 TDD |
| Step 1 시작 | `/agenthub-extension` skill | WXT + Vitest 설정 |
| Step 3 시작 | `/agenthub-extension` skill | Token Handshake 클라이언트 |
| Step 4 시작 | `/agenthub-extension` skill | SSE ReadableStream 패턴 |
| Step 5 시작 | `/agenthub-extension` skill | Offscreen 관리, 메시지 라우팅 |
| Step 6 시작 | `/agenthub-extension` skill | Offscreen Document 구현 |
| Step 8 구현 | `/frontend-design` skill (선택) | UI 디자인 |
| Step 8 완료 | `/security-checklist` skill | Extension 보안 검토 |
| Step 9 완료 | `code-reviewer` Agent | 코드 품질 리뷰 |
| Phase 완료 | `phase-orchestrator` Agent | DoD 검증 |

### Standards Verification 필수 항목

| 항목 | Step | 확인 내용 |
|------|:----:|----------|
| WXT 최신 버전 | 1 | npm latest, Breaking Changes |
| Vitest + WXT 통합 | 1 | 호환 설정 방법 |
| `chrome.offscreen` | 5, 6 | `createDocument` 시그니처 |
| `chrome.runtime.getContexts` | 5 | Chrome 116+ 지원 |
| `chrome.storage.session` | 3, 5 | 사용법, 용량 제한 |
| `chrome.sidePanel` | 8 | Side Panel API 설정 |

---

## 검증 방법

### 자동화 검증

```bash
# Extension 빌드
cd extension && npm run build

# TypeScript 타입 체크
cd extension && npx tsc --noEmit

# Extension Vitest 전체 실행
cd extension && npx vitest run

# 서버 regression (기존 커버리지 유지)
pytest tests/ --cov=src --cov-fail-under=80

# 서버 E2E 테스트
pytest tests/e2e/ -v
```

### 수동 검증

```bash
# 1. 서버 시작
uvicorn src.main:app --host localhost --port 8000

# 2. (선택) MCP 테스트 서버
cd C:\Users\sungb\Documents\GitHub\MCP_SERVER\MCP_Streamable_HTTP
SYNAPSE_PORT=9000 python -m synapse

# 3. Extension 개발 모드
cd extension && npm run dev

# 4. Chrome 로드: chrome://extensions/ → Developer Mode → Load unpacked
# 5. Sidepanel → "Hello" 입력 → 30초+ 스트리밍 응답 확인
# 6. MCP 서버 등록 (http://127.0.0.1:9000/mcp) → 도구 목록 확인
# 7. 브라우저 재시작 → 토큰 재발급 → 채팅 재동작 확인
```

---

## 생성 파일 요약 (약 42개)

| 카테고리 | 파일 수 | 주요 파일 |
|---------|:------:|----------|
| 프로젝트 설정 | 4 | package.json, wxt.config.ts, tsconfig.json, vitest.config.ts |
| 테스트 setup | 1 | tests/setup.ts |
| 공유 라이브러리 | 5 | types.ts, messaging.ts, constants.ts, api.ts, sse.ts |
| 라이브러리 테스트 | 3 | api.test.ts, sse.test.ts, messaging.test.ts |
| 엔트리포인트 | 6 | background.ts, offscreen/*, sidepanel/* |
| 엔트리포인트 테스트 | 2 | background.test.ts, offscreen.test.ts |
| UI 컴포넌트 | 5 | ChatInterface, MessageBubble, ChatInput, McpServerManager, ServerStatus |
| 컴포넌트 테스트 | 5 | 각 컴포넌트별 .test.tsx |
| Custom Hooks | 3 | useChat, useMcpServers, useServerHealth |
| Hook 테스트 | 3 | 각 Hook별 .test.ts |
| 서버 E2E | 1 | tests/e2e/test_extension_server.py |
| 문서 | 1 | extension/README.md |
| 에셋 | 3 | icon-16/48/128.png |

**수정 파일:** conversations.py (서버), test_conversation_routes.py (서버 테스트), README.md (루트), roadmap.md

---

## 커밋 정책

각 Step 완료 시 커밋 (빌드 + 테스트 통과 상태):
- `feat(phase2.5): Step N - [설명]`
- 예: `feat(phase2.5): Step 0 - Add GET /api/conversations route`
- 예: `feat(phase2.5): Step 1 - WXT project scaffolding with Vitest`

---

## 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|:----:|------|
| WXT Breaking Changes (2026) | 높음 | Step 1 시작 전 웹 검색 |
| Vitest + WXT 통합 이슈 | 중간 | 웹 검색으로 호환 설정 확인 |
| chrome.* mock 복잡도 | 중간 | `tests/setup.ts`에 포괄적 mock 집중, Step별 점진 확장 |
| chrome.offscreen API 변경 | 중간 | Step 5 시작 전 Chrome API 문서 확인 |
| CORS 미스매치 | 높음 | 서버 `allow_origin_regex` 패턴과 Extension ID 일치 확인 |
| 서버 미실행 시 Extension UX | 중간 | Health Check 기반 상태 표시 + 토큰 교환 재시도 로직 |
| Offscreen Document 메모리 누수 | 중간 | 활성 스트림 없을 시 idle 정리 (선택적 최적화) |
| 토큰 교환 실패 | 높음 | Health Check에서 서버 복구 감지 시 자동 재시도 |

---

## 참조

- [docs/guides/extension-guide.md](../guides/extension-guide.md) — Extension 아키텍처 설계
- [docs/guides/implementation-guide.md#9](../guides/implementation-guide.md) — Token Handshake 서버 측
- `.claude/skills/agenthub-extension/` — WXT, Offscreen, SSE 구현 패턴
- [WXT Framework](https://wxt.dev/)
- [Chrome Offscreen API](https://developer.chrome.com/docs/extensions/reference/api/offscreen)
- [Vitest](https://vitest.dev/)

---

*작성일: 2026-01-30*
