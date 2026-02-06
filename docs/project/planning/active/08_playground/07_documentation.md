# Phase 7: Documentation

## Overview

**목표:** Playground 사용 가이드 문서 작성 및 프로젝트 문서 구조에 통합

**TDD 원칙:** 문서화는 TDD 예외 (구현 완료 후 작성)

**전제 조건:** Phase 1-6 완료 (모든 기능 및 테스트)

---

## Implementation Steps

### Step 7.1: playground/README.md 작성

**목표:** Playground 개요 및 빠른 시작 가이드

**파일:** `docs/developers/guides/playground/README.md`

```markdown
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

- **Chat**: SSE 스트리밍 채팅
- **MCP**: 서버 등록/도구 조회
- **A2A**: 에이전트 관리
- **Conversations**: 대화 CRUD + Tool Calls
- **Usage**: 사용량 조회 + Budget 설정
- **Workflow**: Workflow 생성/실행

---

## Guides

- [quickstart.md](quickstart.md) - 설치 및 실행
- [backend-api.md](backend-api.md) - API 테스트 가이드
- [sse-streaming.md](sse-streaming.md) - SSE 디버깅

---

*Last Updated: 2026-02-05*
```

---

### Step 7.2: playground/quickstart.md 작성

**목표:** 설치 및 실행 단계별 가이드

**파일:** `docs/developers/guides/playground/quickstart.md`

```markdown
# Quickstart

Playground를 로컬 환경에서 실행하는 방법입니다.

---

## Prerequisites

- Python 3.10+
- AgentHub 백엔드 설정 완료
- Chrome/Firefox 브라우저

---

## Step 1: 환경변수 설정

`.env` 파일에 DEV_MODE 추가:

```bash
DEV_MODE=true
```

**⚠️ 경고:** DEV_MODE는 로컬 개발 전용입니다. **절대** 프로덕션 환경에 배포하지 마세요.

---

## Step 2: 백엔드 시작

```bash
cd c:\Users\sungb\Documents\GitHub\AgentHub
DEV_MODE=true uvicorn src.main:app --reload
```

**확인:**
```bash
curl http://localhost:8000/health
# {"status":"healthy"}
```

---

## Step 3: Static 서버 시작

```bash
python -m http.server 3000 --directory tests/manual/playground
```

**확인:**
- 브라우저: `http://localhost:3000`
- Health 상태: "Healthy" 표시

---

## Step 4: 기능 테스트

### Chat 테스트
1. Chat 탭 클릭
2. 메시지 입력: "Hello, AgentHub!"
3. Send 버튼 클릭
4. 우측 SSE 로그에서 이벤트 확인

### MCP 서버 등록
1. MCP 탭 클릭
2. Server Name: `test-server`
3. Server URL: `http://localhost:9000`
4. Register 버튼 클릭
5. 서버 카드 표시 확인

---

## Troubleshooting

### Health 상태가 "Backend unreachable"
- 백엔드가 실행 중인지 확인: `curl http://localhost:8000/health`
- DEV_MODE=true 설정 확인

### CORS 에러 발생
- `.env`에 `DEV_MODE=true` 설정 확인
- 브라우저 Console에서 Origin 확인: `http://localhost:3000`

### SSE 연결 실패
- Network 탭에서 EventStream 확인
- 백엔드 로그 확인: `uvicorn` 출력

---

*Last Updated: 2026-02-05*
```

---

### Step 7.3: playground/backend-api.md 작성

**목표:** 각 API 엔드포인트 테스트 방법

**파일:** `docs/developers/guides/playground/backend-api.md`

```markdown
# Backend API Testing

Playground를 사용한 백엔드 API 테스트 가이드입니다.

---

## Health Check

**Endpoint:** `GET /health`

**Playground:**
- 페이지 로드 시 자동 호출
- Health Indicator: "Healthy" 또는 "Backend unreachable"

**cURL:**
```bash
curl http://localhost:8000/health
```

---

## Chat SSE Streaming

**Endpoint:** `POST /api/chat/stream` (SSE)

**Playground:**
1. Chat 탭 → 메시지 입력 → Send
2. 우측 SSE 로그에서 이벤트 확인:
   - `{"type":"text","content":"..."}`
   - `{"type":"tool_call",...}`
   - `{"type":"done"}`

**cURL:**
```bash
curl -N -H "Accept: text/event-stream" \
     -X POST http://localhost:8000/api/chat/stream \
     -d '{"message":"Hello"}'
```

---

## MCP Server Management

### 서버 등록
**Endpoint:** `POST /api/mcp/servers`

**Playground:**
1. MCP 탭 → Server Name/URL 입력 → Register
2. 서버 카드 표시 확인

**cURL:**
```bash
curl -X POST http://localhost:8000/api/mcp/servers \
     -H "Content-Type: application/json" \
     -d '{"name":"test","url":"http://localhost:9000"}'
```

### 서버 목록 조회
**Endpoint:** `GET /api/mcp/servers`

**Playground:**
- MCP 탭에서 자동 로드

**cURL:**
```bash
curl http://localhost:8000/api/mcp/servers
```

### 도구 목록 조회
**Endpoint:** `GET /api/mcp/servers/{server_id}/tools`

**Playground:**
- 서버 카드 → "Tools" 버튼 클릭

---

## A2A Agent Management

### 에이전트 등록
**Endpoint:** `POST /api/a2a/agents`

**Playground:**
1. A2A 탭 → Agent Name/URL 입력 → Register
2. Agent Card 표시 확인

---

## Conversations CRUD

### 대화 생성
**Endpoint:** `POST /api/conversations`

**Playground:**
- Conversations 탭 → "Create Conversation" 버튼

### Tool Calls 조회
**Endpoint:** `GET /api/conversations/{conversation_id}/tool-calls`

**Playground:**
- 대화 선택 → "Tool Calls" 탭

---

## Usage & Budget

### Usage 조회
**Endpoint:** `GET /api/usage/summary`

**Playground:**
- Usage 탭 → 자동 로드

### Budget 설정
**Endpoint:** `PUT /api/usage/budget`

**Playground:**
- Usage 탭 → Budget 입력 → "Set Budget"

---

## Workflow

### Workflow 실행
**Endpoint:** `POST /api/workflows/execute` (SSE)

**Playground:**
1. Workflow 탭 → Name/Steps 입력 → Execute
2. SSE 로그에서 실행 과정 확인

---

*Last Updated: 2026-02-05*
```

---

### Step 7.4: playground/sse-streaming.md 작성

**목표:** SSE 디버깅 및 문제 해결 가이드

**파일:** `docs/developers/guides/playground/sse-streaming.md`

```markdown
# SSE Streaming Debugging

SSE (Server-Sent Events) 스트리밍 디버깅 가이드입니다.

---

## SSE 이벤트 구조

### Chat 스트리밍
```json
{"type":"text","content":"Hello"}
{"type":"tool_call","tool":"get_weather","args":{...}}
{"type":"tool_result","result":{...}}
{"type":"done"}
```

### Workflow 스트리밍
```json
{"type":"workflow_started","workflow_id":"wf-1"}
{"type":"step_started","step":1}
{"type":"step_completed","step":1,"result":{...}}
{"type":"workflow_completed","status":"success"}
```

---

## 브라우저 DevTools 활용

### 1. Network 탭
- Filter: "EventStream"
- SSE 연결 상태 확인
- 이벤트 데이터 확인

### 2. Console 탭
```javascript
// EventSource 상태 확인
const es = new EventSource("http://localhost:8000/api/chat/stream");
console.log(es.readyState);  // 0: CONNECTING, 1: OPEN, 2: CLOSED

es.onmessage = (event) => console.log(event.data);
es.onerror = (error) => console.error(error);
```

---

## 문제 해결

### 연결이 즉시 종료됨
- **원인:** 백엔드에서 `done` 이벤트를 즉시 전송
- **확인:** SSE 로그에서 마지막 이벤트 확인
- **해결:** 백엔드 로그에서 에러 확인

### 이벤트가 수신되지 않음
- **원인:** CORS 설정 또는 Auth 실패
- **확인:** Network 탭에서 Response Headers 확인
- **해결:** DEV_MODE=true 설정 확인

### JSON 파싱 에러
- **원인:** 백엔드에서 잘못된 JSON 전송
- **확인:** SSE 로그에서 raw 데이터 확인
- **해결:** 백엔드 로그에서 직렬화 에러 확인

---

## Playground SSE 로그 활용

### 실시간 이벤트 확인
- 우측 패널: SSE Events
- 각 이벤트 자동 JSON 포맷팅
- 스크롤 자동 이동

### 연결 상태 확인
- 하단 표시: `connected` / `disconnected`
- `done` 이벤트 수신 시 자동 종료

---

*Last Updated: 2026-02-05*
```

---

### Step 7.5: 프로젝트 문서 구조 업데이트

**목표:** Playground 문서를 전체 문서 구조에 통합

#### 7.5.1: docs/MAP.md 업데이트

**파일:** `docs/MAP.md`

```markdown
# Documentation Map

...

## Directory Structure

```
docs/
├── developers/
│   ├── guides/
│   │   ├── playground/              # NEW: Playground 가이드
│   │   │   ├── README.md
│   │   │   ├── quickstart.md
│   │   │   ├── backend-api.md
│   │   │   └── sse-streaming.md
│   │   ├── extension/
│   │   ├── implementation/
│   │   └── standards/
...
```
```

#### 7.5.2: docs/developers/README.md 업데이트

**파일:** `docs/developers/README.md`

```markdown
# Developers Guide

...

## Quick Access

| 목적 | 경로 |
|------|------|
| Playground 사용법 | [guides/playground/README.md](guides/playground/README.md) |  # NEW
| 아키텍처 이해 | [architecture/](architecture/) |
...
```

#### 7.5.3: docs/developers/guides/README.md 업데이트

**파일:** `docs/developers/guides/README.md`

```markdown
# Implementation Guides

...

| 가이드 | 설명 |
|--------|------|
| **[playground/](playground/)** | Playground 사용 및 API 테스트 가이드 |  # NEW
| **[extension/](extension/)** | Extension 개발 가이드 |
...
```

---

## Verification

### 문서 링크 확인
```bash
# Markdown 링크 검증
python -m markdown_link_check docs/developers/guides/playground/README.md
```

### 문서 접근성 테스트
1. `docs/MAP.md` → `developers/README.md` → `guides/playground/README.md`
2. 각 가이드 상호 링크 확인

---

## Critical Files

| 파일 | 내용 |
|------|------|
| `docs/developers/guides/playground/README.md` | Playground 개요 |
| `docs/developers/guides/playground/quickstart.md` | 설치 및 실행 |
| `docs/developers/guides/playground/backend-api.md` | API 테스트 가이드 |
| `docs/developers/guides/playground/sse-streaming.md` | SSE 디버깅 |
| `docs/MAP.md` | 전체 문서 구조 (업데이트) |
| `docs/developers/README.md` | 개발자 가이드 (업데이트) |
| `docs/developers/guides/README.md` | 구현 가이드 (업데이트) |

---

## Next Steps

**Plan 08 완료**: 모든 Phase 완료 후 `planned/` → `completed/` 이동

**Active Planning 업데이트**: `docs/project/planning/active/README.md` 수정

---

## Documentation Best Practices

### 1. Progressive Disclosure
- README.md: 개요 및 Quick Start
- 상세 가이드: 각 기능별 별도 파일

### 2. Link Guidelines
- 강한 결합: 순차적으로 읽어야 하는 문서 (직접 링크)
- 약한 결합: 다른 도메인 참고 문서 (MAP 참조)

### 3. Update Triggers
- Plan 완료 시: `planning/completed/` 업데이트
- 문서 구조 변경 시: `docs/MAP.md` 업데이트

---

*Last Updated: 2026-02-05*
*No TDD (문서화)*
*Structure: Fractal (MAP → Sub-Map → Details)*
