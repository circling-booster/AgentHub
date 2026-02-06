# Playground

백엔드 API를 Extension 없이 빠르게 테스트할 수 있는 수동 테스트 도구입니다.

---

## Quick Start

### 1. 백엔드 시작 (DEV_MODE)

```bash
DEV_MODE=true uvicorn src.main:app --reload
```

### 2. Static 서버 시작

```bash
python -m http.server 3000 --directory tests/manual/playground
```

### 3. 브라우저 접속

```
http://localhost:3000
```

---

## Features

### Core Features

- **Health Check**: 백엔드 연결 상태 확인
- **Chat**: SSE 스트리밍 채팅 (GET/POST 지원)
- **MCP**: 서버 등록/해제/도구 조회
- **A2A**: 에이전트 등록/해제
- **Conversations**: 대화 CRUD + Tool Calls 조회
- **Usage**: 사용량 조회 + Budget 설정
- **Workflow**: Workflow 생성/실행 (SSE 스트리밍)

### Technical Highlights

- **SSE Streaming**: EventSource 기반 실시간 이벤트 수신
- **DEV_MODE**: 로컬 개발 환경 전용 인증 우회
- **Vanilla JavaScript**: 빌드 도구 없이 즉시 실행 가능
- **Real-time Logging**: SSE 이벤트 실시간 로그 패널

---

## Architecture

```
┌─────────────────────────────────────┐
│   Browser (localhost:3000)          │
│   - index.html                      │
│   - api-client.js (fetch wrapper)   │
│   - sse-handler.js (EventSource)    │
│   - ui-components.js (DOM render)   │
│   - main.js (event handlers)        │
└──────────┬──────────────────────────┘
           │ HTTP/SSE
           ▼
┌─────────────────────────────────────┐
│   AgentHub Backend (localhost:8000) │
│   ┌─────────────────────────────┐   │
│   │ CORS Middleware (DEV_MODE)  │   │
│   │ - Allow localhost:3000      │   │
│   └─────────────────────────────┘   │
│   ┌─────────────────────────────┐   │
│   │ Security Layer (DEV_MODE)   │   │
│   │ - Skip token verification   │   │
│   └─────────────────────────────┘   │
│   ┌─────────────────────────────┐   │
│   │ HTTP Routes                 │   │
│   │ - /health                   │   │
│   │ - /api/chat/stream (GET/POST)│  │
│   │ - /api/mcp/servers          │   │
│   │ - /api/a2a/agents           │   │
│   │ - /api/conversations        │   │
│   │ - /api/usage                │   │
│   │ - /api/workflows            │   │
│   └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

---

## Guides

| 가이드 | 설명 |
|--------|------|
| [quickstart.md](quickstart.md) | 설치 및 실행 단계별 가이드 |
| [backend-api.md](backend-api.md) | API 엔드포인트 테스트 방법 |
| [sse-streaming.md](sse-streaming.md) | SSE 스트리밍 디버깅 가이드 |

---

## Security Note

⚠️ **WARNING**: DEV_MODE는 로컬 개발 환경 전용입니다.

- **절대** 프로덕션 환경에 배포하지 마세요
- DEV_MODE는 인증을 우회하고 localhost CORS를 허용합니다
- 공개 네트워크에 노출되어서는 안 됩니다

---

## Test Strategy

### JavaScript Unit Tests

위치: `tests/manual/playground/tests/`

```bash
cd tests/manual/playground
npm test
```

**Coverage:**
- api-client.js: API 호출 함수
- sse-handler.js: EventSource 래퍼
- ui-components.js: DOM 렌더링 함수

### E2E Tests (Playwright)

위치: `tests/e2e/test_playground.py`

```bash
pytest tests/e2e/test_playground.py -v
```

**Test Classes:**
- TestPlaygroundHealthCheck (2 tests)
- TestPlaygroundChatStreaming (3 tests)
- TestPlaygroundMcpManagement (3 tests)
- TestPlaygroundA2aManagement (2 tests)
- TestPlaygroundConversations (3 tests)
- TestPlaygroundUsage (2 tests)
- TestPlaygroundWorkflow (3 tests)

---

## Development

### File Structure

```
tests/manual/playground/
├── index.html              # Main UI (Tab Navigation)
├── css/
│   └── styles.css          # Tailwind-like styles
├── js/
│   ├── api-client.js       # API wrapper (fetch/EventSource)
│   ├── sse-handler.js      # SSE handler class
│   ├── ui-components.js    # DOM rendering functions
│   └── main.js             # Event handlers
├── tests/
│   ├── api-client.test.js
│   ├── sse-handler.test.js
│   ├── ui-components.test.js
│   └── main.test.js
├── package.json            # Jest configuration
└── coverage/               # Test coverage reports
```

### Key Implementation Details

**SSE Streaming:**
- Chat: `GET /api/chat/stream?message=...&conversation_id=...`
- Workflow: `GET /api/workflows/execute?name=...&steps=...`
- EventSource는 GET만 지원하므로 query parameters 사용

**CORS Configuration:**
- DEV_MODE: `allow_origins` = `["http://localhost:3000"]`
- Methods: `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`
- Headers: `Content-Type`, `Accept`

**Tool Calls:**
- Endpoint: `GET /api/conversations/{id}/tool-calls`
- 각 대화의 Tool Calls 탭에서 조회 가능
- 빈 경우 "No tool calls" 메시지 표시

---

## Troubleshooting

### Health Check 실패

**증상**: Health Indicator가 "Backend unreachable"

**해결:**
1. 백엔드 실행 확인: `curl http://localhost:8000/health`
2. DEV_MODE 확인: `.env`에 `DEV_MODE=true` 설정
3. 포트 충돌 확인: `netstat -ano | findstr :8000`

### CORS 에러

**증상**: Console에 CORS policy 에러

**해결:**
1. DEV_MODE 확인: `.env`에 `DEV_MODE=true` 필수
2. Origin 확인: 반드시 `http://localhost:3000` (포트 정확히 매칭)
3. 백엔드 재시작: 설정 변경 후 uvicorn 재시작

### SSE 연결 실패

**증상**: SSE Events 패널에 "disconnected" 상태

**해결:**
1. Network 탭에서 EventStream 확인
2. Response Headers 확인: `Content-Type: text/event-stream`
3. 백엔드 로그 확인: uvicorn 출력에서 에러 메시지 확인

### Tool Calls 표시 안됨

**증상**: Tool Calls 탭 클릭 시 빈 화면

**해결:**
1. 대화에 실제 Tool Calls가 있는지 확인: API 직접 호출
   ```bash
   curl http://localhost:8000/api/conversations/{id}/tool-calls
   ```
2. Console 에러 확인: 네트워크 요청 실패 여부
3. 빈 경우 정상: "No tool calls" 메시지 표시됨

---

## Related Documentation

- [Architecture Overview](../../architecture/README.md) - 전체 시스템 아키텍처
- [Testing Guide](../../testing/README.md) - 테스트 전략
- [API Reference](../../architecture/api/README.md) - REST API 명세

---

*Last Updated: 2026-02-06*
*Version: 1.0*
*Plan: 08_playground*
