# AgentHub Chrome Extension

> WXT + React + TypeScript 기반 Chrome Extension

AgentHub API 서버(`localhost:8000`)와 연동하여 브라우저 사이드패널에서 AI 에이전트와 대화하고 MCP 서버를 관리합니다.

---

## Architecture

```
Extension
├── Background Service Worker    # 토큰 핸드셰이크, Health Check, 메시지 라우팅
├── Offscreen Document           # SSE 스트리밍 (Service Worker 30s 타임아웃 우회)
├── Sidepanel UI (React)         # 채팅 인터페이스 + MCP 서버 관리
└── Shared Libraries             # API 클라이언트, SSE 파서, 메시지 타입
     ↓ HTTP + SSE
AgentHub API Server (localhost:8000)
```

### Offscreen Document

Service Worker는 30초 유휴 시 종료됩니다. LLM 응답은 30초 이상 걸릴 수 있어 Offscreen Document에서 SSE 스트리밍을 처리합니다.

**메시지 흐름:**
```
Sidepanel → START_STREAM_CHAT → Background → STREAM_CHAT → Offscreen
                                                              ↓ SSE
Sidepanel ← STREAM_CHAT_EVENT ← Background ← STREAM_CHAT_EVENT
```

---

## Structure

```
extension/
├── entrypoints/
│   ├── background.ts              # Service Worker
│   ├── offscreen/
│   │   ├── index.html             # Offscreen Document
│   │   └── main.ts                # SSE 메시지 핸들러
│   └── sidepanel/
│       ├── index.html             # Sidepanel HTML
│       ├── main.tsx               # React 진입점
│       ├── App.tsx                # 메인 앱 (탭 전환)
│       └── App.css                # 스타일
├── components/
│   ├── ChatInterface.tsx          # 채팅 UI (메시지 목록 + 입력)
│   ├── ChatInput.tsx              # 메시지 입력
│   ├── MessageBubble.tsx          # 메시지 버블
│   ├── McpServerManager.tsx       # MCP 서버 관리
│   └── ServerStatus.tsx           # 서버 연결 상태
├── hooks/
│   ├── useChat.ts                 # 채팅 상태 관리
│   ├── useMcpServers.ts           # MCP 서버 CRUD
│   └── useServerHealth.ts         # Health 상태 구독
├── lib/
│   ├── api.ts                     # 인증된 REST API 클라이언트
│   ├── sse.ts                     # POST SSE 스트리밍
│   ├── messaging.ts               # Extension 내부 메시지 타입
│   ├── types.ts                   # 서버 API 타입
│   ├── constants.ts               # 상수 (API_BASE, Storage keys)
│   ├── background-handlers.ts     # Background 핸들러 (테스트 분리)
│   └── offscreen-handlers.ts      # Offscreen 핸들러 (테스트 분리)
└── tests/                         # Vitest 테스트 (129 tests)
    ├── setup.ts                   # chrome.* API mock
    ├── lib/                       # 라이브러리 테스트
    ├── hooks/                     # Hook 테스트
    ├── components/                # 컴포넌트 테스트
    └── entrypoints/               # 엔트리포인트 테스트
```

---

## Security

### Token Handshake (Drive-by RCE 방지)

1. 서버 시작 시 `secrets.token_urlsafe(32)`로 토큰 생성
2. Extension Background가 `POST /auth/token`으로 토큰 교환
3. 토큰은 `chrome.storage.session`에 저장 (브라우저 종료 시 삭제)
4. 모든 `/api/*` 요청에 `X-Extension-Token` 헤더 자동 주입

### CORS

`allow_origin_regex: ^chrome-extension://[a-zA-Z0-9_-]+$`

---

## Development

```bash
# 의존성 설치
npm install

# 개발 모드 (HMR)
npm run dev

# Chrome 로드: chrome://extensions/ → Developer Mode → Load unpacked → .output/chrome-mv3
```

## Testing

```bash
# 전체 테스트 (129 tests)
npx vitest run

# 특정 파일
npx vitest run tests/hooks/useChat.test.ts

# Watch 모드
npx vitest
```

## Build

```bash
npm run build
# Output: .output/chrome-mv3/
```

---

## References

- [WXT Framework](https://wxt.dev/)
- [Chrome Offscreen API](https://developer.chrome.com/docs/extensions/reference/api/offscreen)
- [docs/extension-guide.md](../docs/extension-guide.md)
- [docs/implementation-guide.md#9-보안-패턴](../docs/implementation-guide.md#9-보안-패턴)
