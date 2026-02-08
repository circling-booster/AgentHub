# SDK Track API

MCP SDK Track 표준 API 엔드포인트 문서입니다.

**Plan 07 Phase 6**에서 구현된 4개 API (Resources, Prompts, Sampling, Elicitation)를 다룹니다.

---

## Overview

| API | Purpose | HITL Required | Method C Pattern |
|-----|---------|---------------|------------------|
| **Resources** | MCP Server의 리소스 목록/읽기 | No | - |
| **Prompts** | MCP Server의 프롬프트 템플릿 관리 | No | - |
| **Sampling** | LLM Sampling 요청 승인/거부 | Yes | ✅ Approve endpoint |
| **Elicitation** | 사용자 입력 요청/응답 | Yes | ✅ Respond endpoint |

**HITL (Human-in-the-Loop)**: Sampling과 Elicitation은 사용자 승인/응답이 필요합니다.

**Method C Pattern**: Callback-centric LLM 배치 패턴으로, approve/respond 엔드포인트를 통해 MCP Server로 결과를 전달합니다. ([ADR-A05](../../../project/decisions/architecture/ADR-A05-method-c-callback-centric.md) 참조)

---

## Authentication

모든 엔드포인트는 Token 인증이 필요합니다.

**Header:**
```http
Authorization: Bearer <token>
```

**Token 획득:**
```http
POST /api/auth/token
Content-Type: application/json

{
  "username": "admin",
  "password": "secret"
}
```

---

## 1. Resources API

MCP Server의 리소스를 조회하고 읽습니다.

### 1.1 List Resources

**Endpoint:**
```http
GET /api/mcp/servers/{endpoint_id}/resources
```

**Path Parameters:**
- `endpoint_id` (string, required): MCP Server Endpoint ID

**Response:** `200 OK`
```json
{
  "resources": [
    {
      "uri": "file:///path/to/resource.txt",
      "name": "Resource Name",
      "description": "Resource description",
      "mimeType": "text/plain"
    }
  ]
}
```

**Error Responses:**
- `404 Not Found`: Endpoint not found
- `401 Unauthorized`: Invalid token

**Example:**
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/mcp/servers/test-endpoint/resources
```

### 1.2 Read Resource

**Endpoint:**
```http
GET /api/mcp/servers/{endpoint_id}/resources/{uri:path}
```

**Path Parameters:**
- `endpoint_id` (string, required): MCP Server Endpoint ID
- `uri` (string, required): Resource URI (e.g., `file:///path/to/file.txt`)

**Response:** `200 OK`
```json
{
  "uri": "file:///path/to/resource.txt",
  "mimeType": "text/plain",
  "text": "File content here"
}
```

또는 (binary content):
```json
{
  "uri": "file:///path/to/image.png",
  "mimeType": "image/png",
  "blob": "base64-encoded-data"
}
```

**Error Responses:**
- `404 Not Found`: Resource or endpoint not found
- `401 Unauthorized`: Invalid token

---

## 2. Prompts API

MCP Server의 프롬프트 템플릿을 관리합니다.

### 2.1 List Prompts

**Endpoint:**
```http
GET /api/mcp/servers/{endpoint_id}/prompts
```

**Path Parameters:**
- `endpoint_id` (string, required): MCP Server Endpoint ID

**Response:** `200 OK`
```json
{
  "prompts": [
    {
      "name": "code-review",
      "description": "Review code for best practices",
      "arguments": [
        {
          "name": "language",
          "required": true,
          "description": "Programming language"
        },
        {
          "name": "style_guide",
          "required": false,
          "description": "Style guide to follow"
        }
      ]
    }
  ]
}
```

**Error Responses:**
- `404 Not Found`: Endpoint not found
- `401 Unauthorized`: Invalid token

### 2.2 Get Prompt

**Endpoint:**
```http
POST /api/mcp/servers/{endpoint_id}/prompts/{name}
```

**Path Parameters:**
- `endpoint_id` (string, required): MCP Server Endpoint ID
- `name` (string, required): Prompt template name

**Request Body:**
```json
{
  "arguments": {
    "language": "Python",
    "style_guide": "PEP 8"
  }
}
```

**Response:** `200 OK`
```json
{
  "description": "Review code for best practices",
  "messages": [
    {
      "role": "user",
      "content": {
        "type": "text",
        "text": "Review this Python code following PEP 8..."
      }
    }
  ]
}
```

**Error Responses:**
- `404 Not Found`: Prompt or endpoint not found
- `400 Bad Request`: Missing required arguments
- `401 Unauthorized`: Invalid token

---

## 3. Sampling API (HITL)

LLM Sampling 요청을 승인하거나 거부합니다.

### 3.1 List Sampling Requests

**Endpoint:**
```http
GET /api/sampling/requests
```

**Query Parameters:**
- `status` (string, optional): Filter by status (`pending`, `approved`, `rejected`)

**Response:** `200 OK`
```json
{
  "requests": [
    {
      "id": "req-abc123",
      "endpoint_id": "test-endpoint",
      "method": "sampling/createMessage",
      "params": {
        "messages": [
          {
            "role": "user",
            "content": { "type": "text", "text": "Hello" }
          }
        ],
        "modelPreferences": {
          "hints": [{ "name": "claude-3-5-sonnet-20241022" }]
        },
        "maxTokens": 100
      },
      "status": "pending",
      "created_at": "2026-02-07T12:00:00Z"
    }
  ]
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid token

### 3.2 Approve Sampling Request (Method C)

**Endpoint:**
```http
POST /api/sampling/requests/{request_id}/approve
```

**Path Parameters:**
- `request_id` (string, required): Sampling request ID

**Request Body:** (optional, empty body allowed)
```json
{}
```

**Response:** `200 OK`
```json
{
  "request_id": "req-abc123",
  "status": "approved",
  "result": {
    "role": "assistant",
    "content": { "type": "text", "text": "Hi there!" },
    "model": "claude-3-5-sonnet-20241022",
    "stopReason": "end_turn"
  }
}
```

**Method C Pattern:**
이 엔드포인트는 MCP Server의 콜백으로 LLM 응답을 반환합니다. LLM 추론은 approve 시점에 수행되며, 결과는 즉시 MCP Server로 전달됩니다.

**Error Responses:**
- `404 Not Found`: Request not found
- `409 Conflict`: Request already processed
- `401 Unauthorized`: Invalid token

### 3.3 Reject Sampling Request

**Endpoint:**
```http
POST /api/sampling/requests/{request_id}/reject
```

**Path Parameters:**
- `request_id` (string, required): Sampling request ID

**Request Body:**
```json
{
  "reason": "Inappropriate request"
}
```

**Response:** `200 OK`
```json
{
  "request_id": "req-abc123",
  "status": "rejected"
}
```

**Error Responses:**
- `404 Not Found`: Request not found
- `409 Conflict`: Request already processed
- `401 Unauthorized`: Invalid token

---

## 4. Elicitation API (HITL)

사용자 입력을 요청하고 응답합니다.

### 4.1 List Elicitation Requests

**Endpoint:**
```http
GET /api/elicitation/requests
```

**Query Parameters:**
- `status` (string, optional): Filter by status (`pending`, `responded`, `cancelled`)

**Response:** `200 OK`
```json
{
  "requests": [
    {
      "id": "elicit-xyz789",
      "endpoint_id": "test-endpoint",
      "method": "prompts/get",
      "params": {
        "name": "code-review",
        "arguments": {
          "language": "Python"
        }
      },
      "status": "pending",
      "created_at": "2026-02-07T12:05:00Z"
    }
  ]
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid token

### 4.2 Respond to Elicitation Request (Method C)

**Endpoint:**
```http
POST /api/elicitation/requests/{request_id}/respond
```

**Path Parameters:**
- `request_id` (string, required): Elicitation request ID

**Request Body:**
```json
{
  "response": {
    "language": "Python",
    "style_guide": "PEP 8"
  }
}
```

**Response:** `200 OK`
```json
{
  "request_id": "elicit-xyz789",
  "status": "responded",
  "result": {
    "description": "Review code for best practices",
    "messages": [
      {
        "role": "user",
        "content": { "type": "text", "text": "Review this Python code..." }
      }
    ]
  }
}
```

**Method C Pattern:**
이 엔드포인트는 사용자 응답을 받아 MCP Server로 전달하고, prompts/get 결과를 반환합니다.

**Error Responses:**
- `404 Not Found`: Request not found
- `409 Conflict`: Request already processed
- `400 Bad Request`: Invalid response data
- `401 Unauthorized`: Invalid token

---

## HITL SSE Events

Sampling/Elicitation 요청이 발생하면 SSE 이벤트가 전송됩니다.

**Endpoint:** `/api/hitl/events` (상세 내용은 [hitl-sse.md](hitl-sse.md) 참조)

**Event Types:**
- `sampling_request`: 새 Sampling 요청
- `elicitation_request`: 새 Elicitation 요청

---

## MCP Apps Raw Response

MCP Server의 원시 응답(HTML, JSON 등)은 **iframe sandbox**로 처리됩니다.

**구현 위치:** Playground UI (`tests/manual/playground/index.html`)

**Sandbox 속성:**
```html
<iframe sandbox="allow-scripts allow-same-origin" srcdoc="..."></iframe>
```

**보안:** XSS 방지를 위해 sandbox 속성 사용

---

## Error Handling

### Common Error Responses

| Status Code | Description | Example |
|-------------|-------------|---------|
| `400 Bad Request` | Invalid request body or parameters | Missing required argument |
| `401 Unauthorized` | Invalid or missing token | Token expired |
| `404 Not Found` | Resource/endpoint not found | Unknown endpoint_id |
| `409 Conflict` | Request already processed | Duplicate approve |
| `500 Internal Server Error` | Server error | Database failure |

### Error Response Format

```json
{
  "detail": "Error description here"
}
```

---

## Related Documentation

- [HITL SSE Events](hitl-sse.md) - SSE 이벤트 스트림 API
- [ADR-A05 (Method C Pattern)](../../../project/decisions/architecture/ADR-A05-method-c-callback-centric.md) - Callback-centric LLM 배치
- [ADR-T07 (Playground-First Testing)](../../../project/decisions/technical/ADR-T07-playground-first-testing.md) - Phase 6+ 테스트 원칙
- [Playground README](../../../../tests/manual/playground/README.md) - Playground UI 사용 가이드

---

*Last Updated: 2026-02-07*
*Phase: Plan 07 Phase 6*
