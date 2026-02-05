# Troubleshooting Guide

AgentHub 개발 중 자주 발생하는 문제와 해결 방법입니다.

---

## Import Errors

### Problem: ModuleNotFoundError

```
ModuleNotFoundError: No module named 'domain'
```

### Cause

`src.` 접두사 없이 import를 시도했습니다.

### Solution

모든 프로젝트 내부 import는 `src.` 접두사를 사용해야 합니다.

```python
# Wrong
from domain.entities.agent import Agent
from adapters.outbound.sqlite_storage import SqliteStorage

# Correct
from src.domain.entities.agent import Agent
from src.adapters.outbound.sqlite_storage import SqliteStorage
```

### Verification

```bash
pytest tests/integration/test_app_startup.py::TestImportValidation
```

---

### Problem: Domain Layer Import Violation

```
AssertionError: Domain layer imports external library: google.adk
```

### Cause

Domain 레이어(`src/domain/`)에서 외부 라이브러리를 import했습니다.

### Solution

Domain 레이어는 순수 Python만 사용해야 합니다.

```python
# Wrong (in src/domain/services/)
from google.adk import Agent
from fastapi import HTTPException
import aiosqlite

# Correct (in src/domain/services/)
from src.domain.entities.agent import Agent
from src.domain.ports.outbound.orchestrator_port import OrchestratorPort
```

외부 라이브러리는 Adapter 레이어에서만 사용합니다.

---

## Test Failures

### Problem: asyncio Event Loop Error

```
RuntimeError: This event loop is already running
```

### Cause

pytest-asyncio 설정이 누락되었거나, 중첩된 이벤트 루프를 사용했습니다.

### Solution

1. `pyproject.toml`에서 asyncio_mode 확인:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

2. 테스트 함수에서 `@pytest.mark.asyncio` 제거 (auto 모드에서는 불필요):

```python
# With asyncio_mode = "auto", no decorator needed
async def test_async_function():
    result = await some_async_call()
    assert result is not None
```

---

### Problem: Fixture Not Found

```
fixture 'mcp_client' not found
```

### Cause

마커가 필요한 fixture를 사용했지만 마커를 적용하지 않았습니다.

### Solution

적절한 마커를 테스트에 추가합니다.

```python
# mcp_client fixture는 local_mcp 마커가 필요
@pytest.mark.local_mcp
async def test_mcp_tool_execution(mcp_client):
    result = await mcp_client.call_tool("echo", {"message": "test"})
    assert result is not None
```

### Available Markers

| Marker | Required Fixture |
|--------|------------------|
| `local_mcp` | mcp_client, mcp_server |
| `local_a2a` | a2a_client, a2a_echo_agent |
| `llm` | (LLM API 호출 테스트) |
| `e2e_playwright` | browser, page |
| `chaos` | (Chaos Engineering 테스트) |

---

### Problem: Test Isolation Failure

```
AssertionError: Expected 1 conversation, got 3
```

### Cause

이전 테스트의 데이터가 남아있어 테스트 격리가 실패했습니다.

### Solution

Fake Adapter에 `clear()` 메서드를 추가하고 fixture에서 호출합니다.

```python
# tests/unit/fakes/fake_storage.py
class FakeStorageAdapter:
    def clear(self) -> None:
        self._conversations.clear()
        self._endpoints.clear()

# tests/conftest.py
@pytest.fixture
def fake_storage():
    storage = FakeStorageAdapter()
    yield storage
    storage.clear()  # 테스트 후 정리
```

---

## Extension Connection Issues

### Problem: Extension Cannot Connect to Server

```
Error: Failed to fetch: net::ERR_CONNECTION_REFUSED
```

### Cause

1. 서버가 실행되지 않음
2. 서버가 다른 포트에서 실행 중
3. CORS 설정 문제

### Solution

1. 서버 실행 확인:

```bash
# 서버 시작
uvicorn src.main:app --host localhost --port 8000

# 서버 상태 확인
curl http://localhost:8000/api/health
```

2. CORS 설정 확인 (`src/main.py`):

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Problem: Token Handshake Failed

```
Error: Token handshake failed: 401 Unauthorized
```

### Cause

Extension과 서버 간 토큰 교환이 실패했습니다.

### Solution

1. 서버 재시작 (토큰 초기화):

```bash
# 서버 중지 후 재시작
uvicorn src.main:app --host localhost --port 8000 --reload
```

2. Extension 재로드:
   - `chrome://extensions/` 접속
   - AgentHub Extension에서 새로고침 버튼 클릭

3. Storage 초기화:
   - Extension DevTools Console에서:
   ```javascript
   chrome.storage.local.clear()
   ```

---

### Problem: SSE Connection Drops

```
EventSource connection closed unexpectedly
```

### Cause

1. Service Worker 비활성화 (5분 타임아웃)
2. 네트워크 불안정
3. 서버 타임아웃

### Solution

1. Offscreen Document 사용 (Service Worker 대신):

```typescript
// entrypoints/offscreen/main.ts
// Offscreen Document는 Service Worker와 달리 지속 연결 유지
```

2. SSE 재연결 로직 추가:

```typescript
function connectWithRetry(url: string, maxRetries = 3) {
  let retries = 0;

  function connect() {
    const eventSource = new EventSource(url);

    eventSource.onerror = () => {
      eventSource.close();
      if (retries < maxRetries) {
        retries++;
        setTimeout(connect, 1000 * retries);
      }
    };

    return eventSource;
  }

  return connect();
}
```

---

## MCP Server Connection

### Problem: MCP Server Connection Failed

```
Error: Failed to connect to MCP server: Connection refused
```

### Cause

1. MCP 서버가 실행되지 않음
2. 잘못된 URL
3. 방화벽 차단

### Solution

1. MCP 서버 시작:

```bash
# synapse MCP 서버
python -m synapse --port 9000
```

2. URL 형식 확인:

```
# Correct
http://127.0.0.1:9000/mcp

# Wrong
http://localhost:9000  (missing /mcp path)
127.0.0.1:9000/mcp     (missing http://)
```

3. 연결 테스트:

```bash
curl -X POST http://127.0.0.1:9000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

---

### Problem: MCP Tool Execution Timeout

```
Error: Tool execution timed out after 30000ms
```

### Cause

MCP 서버의 도구 실행이 너무 오래 걸립니다.

### Solution

1. 타임아웃 증가:

```python
async with asyncio.timeout(60):  # 60초로 증가
    result = await session.call_tool(tool_name, arguments)
```

2. 재시도 로직 추가:

```python
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
async def execute_tool_with_retry(session, tool_name, arguments):
    return await session.call_tool(tool_name, arguments)
```

---

## A2A Agent Communication

### Problem: Agent Card Not Found

```
Error: Failed to fetch agent card: 404 Not Found
```

### Cause

A2A 에이전트의 `/.well-known/agent.json` 엔드포인트가 없습니다.

### Solution

1. A2A 에이전트 URL 확인:

```bash
curl http://127.0.0.1:9003/.well-known/agent.json
```

2. 에이전트 서버에 Agent Card 엔드포인트 추가:

```python
@app.get("/.well-known/agent.json")
async def agent_card():
    return {
        "name": "My Agent",
        "description": "Agent description",
        "url": "http://127.0.0.1:9003",
        "version": "1.0.0",
    }
```

---

### Problem: A2A Task Execution Failed

```
Error: Task execution failed: Invalid message format
```

### Cause

요청 메시지 형식이 A2A 프로토콜과 맞지 않습니다.

### Solution

올바른 메시지 형식 사용:

```python
# Correct message format
message = {
    "role": "user",
    "content": "Hello, agent!",
}

# Send task
response = await client.post("/tasks", json={
    "message": message,
})
```

---

## SQLite Concurrency

### Problem: Database is Locked

```
sqlite3.OperationalError: database is locked
```

### Cause

여러 연결이 동시에 쓰기를 시도했습니다.

### Solution

1. WAL 모드 활성화:

```python
async def init_db(db_path: str):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA busy_timeout=5000")
```

2. 연결 풀 사용:

```python
class ConnectionPool:
    def __init__(self, db_path: str, max_connections: int = 5):
        self._pool = asyncio.Queue(maxsize=max_connections)
        for _ in range(max_connections):
            self._pool.put_nowait(aiosqlite.connect(db_path))

    async def acquire(self):
        return await self._pool.get()

    async def release(self, conn):
        await self._pool.put(conn)
```

---

### Problem: Deadlock in Async Context

```
RuntimeError: cannot schedule new futures after interpreter shutdown
```

### Cause

비동기 컨텍스트에서 동기 SQLite 호출을 사용했습니다.

### Solution

`aiosqlite` 사용:

```python
# Wrong
import sqlite3
conn = sqlite3.connect(db_path)  # Blocking call

# Correct
import aiosqlite
async with aiosqlite.connect(db_path) as db:
    cursor = await db.execute("SELECT * FROM table")
    rows = await cursor.fetchall()
```

---

## Common pytest Commands

### Debug Failing Test

```bash
# 상세 출력
pytest tests/unit/test_example.py -v --tb=long

# 첫 번째 실패에서 중단
pytest tests/unit/ -x

# 특정 테스트만 실행
pytest tests/unit/test_example.py::test_specific_function

# pdb 디버거 진입
pytest tests/unit/test_example.py --pdb
```

### Check Test Discovery

```bash
# 수집된 테스트 목록 확인
pytest --collect-only

# 특정 마커의 테스트만 수집
pytest --collect-only -m "not llm"
```

---

*Last Updated: 2026-02-05*
