# API Architecture

AgentHub REST API 설계 문서입니다.

---

## Endpoint Structure

AgentHub API는 기능별로 그룹화된 RESTful 엔드포인트를 제공합니다.

| 그룹 | 경로 | 설명 | 상세 스펙 |
|------|------|------|----------|
| **Auth** | `/auth/*` | Extension 인증 (Token Handshake) | - |
| **Health** | `/health` | 서버 상태 확인 | - |
| **Chat** | `/api/chat/*` | LLM 대화 (SSE 스트리밍) | - |
| **Conversations** | `/api/conversations/*` | 대화 이력 관리 | - |
| **MCP** | `/api/mcp/*` | MCP 서버 등록/해제 | - |
| **A2A** | `/api/a2a/*` | A2A 에이전트 관리 | - |
| **OAuth** | `/api/oauth/*` | OAuth 2.0 인증 흐름 | - |
| **Usage** | `/api/usage/*` | 사용량/비용 추적 | [endpoints/usage.md](./endpoints/usage.md) |
| **Workflow** | `/api/workflow/*` | 워크플로우 관리 | - |

**상세 스펙:** [endpoints/](./endpoints/) 디렉토리 참조

---

## URL Naming Convention

### 규칙

1. **리소스 복수형**: `/api/conversations`, `/api/endpoints`
2. **소문자 + 하이픈**: `/api/mcp/servers`, `/api/tool-calls`
3. **계층 구조**: `/api/conversations/{id}/messages`
4. **동사 지양**: `POST /api/chat/stream` (예외: 액션 API)

### 예시

```
GET    /api/conversations              # 목록 조회
GET    /api/conversations/{id}         # 단건 조회
POST   /api/conversations              # 생성
DELETE /api/conversations/{id}         # 삭제

POST   /api/mcp/register               # MCP 서버 등록 (액션)
DELETE /api/mcp/unregister/{endpoint}  # MCP 서버 해제 (액션)
```

---

## Request/Response Schema

### 설계 원칙

| 원칙 | 설명 |
|------|------|
| **Pydantic 스키마** | 모든 요청/응답은 Pydantic BaseModel 정의 |
| **일관된 에러 형식** | `{"detail": "에러 메시지", "code": "ERROR_CODE"}` |
| **타입 안전성** | Backend ↔ Extension 간 에러 코드 상수 공유 |

### 에러 응답 구조

```json
{
  "detail": "Conversation not found",
  "code": "CONVERSATION_NOT_FOUND"
}
```

### HTTP 상태 코드

| 코드 | 용도 |
|------|------|
| `200` | 성공 |
| `201` | 리소스 생성 |
| `400` | 잘못된 요청 |
| `401` | 인증 필요 |
| `403` | 권한 없음 (토큰 불일치) |
| `404` | 리소스 없음 |
| `422` | 유효성 검증 실패 |
| `500` | 서버 오류 |

---

## SSE Streaming

`/api/chat/stream` 엔드포인트는 Server-Sent Events를 사용합니다.

### Event Types

| 이벤트 | 설명 |
|--------|------|
| `text` | LLM 텍스트 응답 |
| `tool_call` | 도구 호출 시작 |
| `tool_result` | 도구 실행 결과 |
| `agent_transfer` | 에이전트 전환 |
| `error` | 오류 발생 |
| `done` | 스트림 완료 |

### SSE 형식

```
event: text
data: {"content": "Hello, "}

event: tool_call
data: {"tool_name": "get_weather", "tool_id": "call_123"}

event: done
data: {}
```

---

## Versioning Strategy

### 현재 상태

- **버전 없음**: 모든 엔드포인트는 `/api/*` 경로 사용
- **하위 호환성**: 기존 클라이언트 지원 우선

### 향후 계획

버전 관리가 필요한 경우:

```
/api/v1/chat/stream    # v1 API
/api/v2/chat/stream    # v2 API (breaking change)
```

도입 시점: Major breaking change 발생 시

---

## Authentication

### Extension Token

Chrome Extension과의 통신은 Token Handshake 방식을 사용합니다.

```
1. Extension → POST /auth/handshake (X-Extension-Origin)
2. Server → {"token": "uuid-token"}
3. Extension → 모든 요청에 X-Extension-Token 헤더 포함
```

### 보호 대상

| 경로 | 인증 |
|------|------|
| `/health`, `/auth/*` | 불필요 |
| `/api/*` | Extension Token 필수 |
| `/.well-known/agent.json` | 불필요 (A2A 표준) |

---

## CORS Policy

Chrome Extension 전용 CORS 설정:

```
allow_origin_regex: ^chrome-extension://[a-zA-Z0-9_-]+$
allow_methods: GET, POST, DELETE, OPTIONS
allow_headers: X-Extension-Token, Content-Type
```

---

*Last Updated: 2026-02-05*
