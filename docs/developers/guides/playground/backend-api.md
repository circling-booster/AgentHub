# Backend API Testing

Playground를 사용한 백엔드 API 테스트 가이드입니다.

---

## Health Check

### Endpoint

```
GET /health
```

### Playground

페이지 로드 시 자동 호출:
- Health Indicator: "● Healthy" (녹색) 또는 "● Backend unreachable" (빨강)

### cURL

```bash
curl http://localhost:8000/health

# Response:
# {"status":"healthy"}
```

---

## Chat SSE Streaming

### Endpoints

```
GET /api/chat/stream?message=<text>&conversation_id=<id>
POST /api/chat/stream
```

**GET 메서드**: EventSource 지원 (브라우저 네이티브)
**POST 메서드**: JSON body 지원 (프로그래밍 API)

### Playground

1. **Chat** 탭 클릭
2. 메시지 입력 → **Send** 클릭
3. 좌측 패널: 사용자/에이전트 메시지 표시
4. 우측 SSE Events 패널에서 이벤트 확인:
   - `{"type":"text","content":"Hello"}`
   - `{"type":"tool_call","tool":"get_weather","args":{...}}`
   - `{"type":"tool_result","result":{...}}`
   - `{"type":"done"}`

### cURL (GET)

```bash
curl -N "http://localhost:8000/api/chat/stream?message=Hello&conversation_id="

# Response (SSE format):
# data: {"type":"text","content":"Hello! How can I help you?"}
#
# data: {"type":"done"}
```

### cURL (POST)

```bash
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","conversation_id":null}'

# Response: (동일한 SSE 스트림)
```

---

## MCP Server Management

### 서버 등록

**Endpoint:**
```
POST /api/mcp/servers
Body: {"name":"<name>","url":"<url>"}
```

**Playground:**
1. **MCP** 탭 클릭
2. Server Name/URL 입력
3. **Register** 버튼 클릭
4. 서버 카드 표시 확인

**cURL:**
```bash
curl -X POST http://localhost:8000/api/mcp/servers \
  -H "Content-Type: application/json" \
  -d '{"name":"test-server","url":"http://localhost:9000"}'

# Response:
# {"id":"test-server","name":"test-server","url":"http://localhost:9000","status":"active"}
```

### 서버 목록 조회

**Endpoint:**
```
GET /api/mcp/servers
```

**Playground:**
- MCP 탭에서 자동 로드

**cURL:**
```bash
curl http://localhost:8000/api/mcp/servers

# Response:
# [{"id":"test-server","name":"test-server","url":"http://localhost:9000","status":"active"}]
```

### 도구 목록 조회

**Endpoint:**
```
GET /api/mcp/servers/{server_id}/tools
```

**Playground:**
- 서버 카드 → **Tools** 버튼 클릭

**cURL:**
```bash
curl http://localhost:8000/api/mcp/servers/test-server/tools

# Response:
# [{"name":"get_weather","description":"Get weather data","parameters":{...}}]
```

### 서버 삭제

**Endpoint:**
```
DELETE /api/mcp/servers/{server_id}
```

**Playground:**
- 서버 카드 → **Unregister** 버튼 클릭 → 카드 제거

**cURL:**
```bash
curl -X DELETE http://localhost:8000/api/mcp/servers/test-server

# Response: 204 No Content
```

---

## A2A Agent Management

### 에이전트 등록

**Endpoint:**
```
POST /api/a2a/agents
Body: {"name":"<name>","url":"<url>"}
```

**Playground:**
1. **A2A** 탭 클릭
2. Agent Name/URL 입력
3. **Register** 버튼 클릭
4. Agent Card 표시 확인

**cURL:**
```bash
curl -X POST http://localhost:8000/api/a2a/agents \
  -H "Content-Type: application/json" \
  -d '{"name":"echo-agent","url":"http://localhost:7000"}'

# Response:
# {"id":"echo-agent","name":"echo-agent","url":"http://localhost:7000","status":"active"}
```

### 에이전트 목록 조회

**Endpoint:**
```
GET /api/a2a/agents
```

**Playground:**
- A2A 탭에서 자동 로드

**cURL:**
```bash
curl http://localhost:8000/api/a2a/agents

# Response:
# [{"id":"echo-agent","name":"echo-agent","url":"http://localhost:7000"}]
```

### 에이전트 삭제

**Endpoint:**
```
DELETE /api/a2a/agents/{agent_id}
```

**Playground:**
- Agent Card → **Unregister** 버튼 클릭

**cURL:**
```bash
curl -X DELETE http://localhost:8000/api/a2a/agents/echo-agent

# Response: 204 No Content
```

---

## Conversations CRUD

### 대화 생성

**Endpoint:**
```
POST /api/conversations
Body: {"title":"<title>"}
```

**Playground:**
1. **Conversations** 탭 클릭
2. **Create Conversation** 버튼 클릭
3. 새 대화 항목 표시

**cURL:**
```bash
curl -X POST http://localhost:8000/api/conversations \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Conversation"}'

# Response:
# {"id":"conv-123","title":"Test Conversation","created_at":"2026-02-06T..."}
```

### 대화 목록 조회

**Endpoint:**
```
GET /api/conversations
```

**Playground:**
- Conversations 탭에서 자동 로드

**cURL:**
```bash
curl http://localhost:8000/api/conversations

# Response:
# [{"id":"conv-123","title":"Test Conversation","created_at":"..."}]
```

### Tool Calls 조회

**Endpoint:**
```
GET /api/conversations/{conversation_id}/tool-calls
```

**Playground:**
1. 대화 항목 선택
2. **Tool Calls** 탭 클릭
3. Tool Calls 목록 표시 (빈 경우 "No tool calls")

**cURL:**
```bash
curl http://localhost:8000/api/conversations/conv-123/tool-calls

# Response:
# [
#   {
#     "id":"tc-1",
#     "tool_name":"get_weather",
#     "arguments":{"city":"Seoul"},
#     "result":{"temperature":15}
#   }
# ]
```

### 대화 삭제

**Endpoint:**
```
DELETE /api/conversations/{conversation_id}
```

**Playground:**
- 대화 항목 → **Delete** 버튼 클릭 → 항목 제거

**cURL:**
```bash
curl -X DELETE http://localhost:8000/api/conversations/conv-123

# Response: 204 No Content
```

---

## Usage & Budget

### Usage 조회

**Endpoint:**
```
GET /api/usage/summary
```

**Playground:**
1. **Usage** 탭 클릭
2. 자동 로드: Total Tokens, Total Cost 표시

**cURL:**
```bash
curl http://localhost:8000/api/usage/summary

# Response:
# {
#   "total_tokens": 1234,
#   "total_cost": 0.05,
#   "by_model": {
#     "gpt-4o-mini": {"tokens": 1234, "cost": 0.05}
#   }
# }
```

### Budget 설정

**Endpoint:**
```
PUT /api/usage/budget
Body: {"limit":<amount>}
```

**Playground:**
1. **Usage** 탭
2. Budget 입력: `100.00`
3. **Set Budget** 버튼 클릭
4. Budget Display: `$100.00` 표시

**cURL:**
```bash
curl -X PUT http://localhost:8000/api/usage/budget \
  -H "Content-Type: application/json" \
  -d '{"limit":100.00}'

# Response:
# {"limit":100.00,"currency":"USD"}
```

### Budget 조회

**Endpoint:**
```
GET /api/usage/budget
```

**cURL:**
```bash
curl http://localhost:8000/api/usage/budget

# Response:
# {"limit":100.00,"currency":"USD"}
```

---

## Workflow

### Workflow 생성

**Endpoint:**
```
POST /api/workflows
Body: {"name":"<name>","steps":[...]}
```

**cURL:**
```bash
curl -X POST http://localhost:8000/api/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Test Workflow",
    "steps":[
      {"name":"step1","type":"task","config":{...}}
    ]
  }'

# Response:
# {"id":"wf-123","name":"Test Workflow","steps":[...]}
```

### Workflow 실행 (SSE)

**Endpoint:**
```
GET /api/workflows/execute?name=<name>&steps=<json>
```

**Playground:**
1. **Workflow** 탭 클릭
2. Workflow Name: `Test Workflow`
3. Steps: `[{"name":"step1","type":"task"}]`
4. **Execute** 버튼 클릭
5. 우측 SSE Events 패널에서 실행 과정 확인:
   - `{"type":"workflow_start","workflow_id":"wf-123"}`
   - `{"type":"step_start","step_number":1}`
   - `{"type":"step_complete","step_number":1}`
   - `{"type":"workflow_complete","status":"success"}`
6. Workflow Result: `Status: completed`

**cURL:**
```bash
# Steps를 JSON 인코딩하여 query parameter로 전달
STEPS='[{"name":"step1","type":"task"}]'

curl -N "http://localhost:8000/api/workflows/execute?name=Test&steps=$(echo $STEPS | jq -sRr @uri)"

# Response (SSE format):
# data: {"type":"workflow_start","workflow_id":"wf-123"}
#
# data: {"type":"step_start","step_number":1}
#
# data: {"type":"step_complete","step_number":1}
#
# data: {"type":"workflow_complete","status":"success"}
```

---

## Common Patterns

### Testing SSE Endpoints

**Browser EventSource:**
```javascript
const eventSource = new EventSource(
  "http://localhost:8000/api/chat/stream?message=Hello"
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};

eventSource.onerror = (error) => {
  console.error("SSE error", error);
  eventSource.close();
};
```

**Python (httpx):**
```python
import httpx

with httpx.stream("GET", "http://localhost:8000/api/chat/stream", params={"message": "Hello"}) as response:
    for line in response.iter_lines():
        if line.startswith("data: "):
            data = json.loads(line[6:])
            print(data)
```

### Handling CORS in Tests

**DEV_MODE 필수:**
```bash
# .env
DEV_MODE=true
```

**Allowed Origins:**
- `http://localhost:3000` (Static Server)
- `http://localhost:*` (다른 포트도 허용)

**NOT Allowed:**
- `http://127.0.0.1:3000` (IP 주소 안됨)
- `https://localhost:3000` (HTTPS 안됨)

### Error Handling

**4xx Errors (Client Error):**
- `400 Bad Request`: 잘못된 요청 형식
- `422 Unprocessable Entity`: 유효성 검증 실패
- `404 Not Found`: 리소스 없음

**5xx Errors (Server Error):**
- `500 Internal Server Error`: 백엔드 에러
- `503 Service Unavailable`: MCP/A2A 서버 연결 실패

**Example (cURL):**
```bash
# 빈 메시지 전송 (422 에러)
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":""}'

# Response:
# {
#   "detail": [
#     {
#       "type": "string_too_short",
#       "loc": ["body", "message"],
#       "msg": "String should have at least 1 character"
#     }
#   ]
# }
```

---

## Advanced Testing

### Performance Testing

**Load Test (Apache Bench):**
```bash
# 100 requests, 10 concurrent
ab -n 100 -c 10 http://localhost:8000/health
```

**SSE Streaming Load:**
```bash
# Multiple EventSource connections
for i in {1..10}; do
  curl -N "http://localhost:8000/api/chat/stream?message=Test$i" &
done
wait
```

### Integration with pytest

```python
import httpx

def test_chat_stream_integration():
    url = "http://localhost:8000/api/chat/stream"
    params = {"message": "Hello"}

    with httpx.stream("GET", url, params=params, timeout=30) as response:
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        events = []
        for line in response.iter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))

        assert len(events) >= 1
        assert events[-1]["type"] == "done"
```

---

## Related Documentation

- [SSE Streaming Debugging](sse-streaming.md) - SSE 디버깅 가이드
- [Quickstart](quickstart.md) - 설치 및 실행
- [API Reference](../../architecture/api/README.md) - 전체 API 명세

---

*Last Updated: 2026-02-06*
*Version: 1.0*
*Plan: 08_playground*
