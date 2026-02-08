# MCP Streamable HTTP Transport

MCP Python SDK v1.25+의 Streamable HTTP Transport 사용 가이드입니다.

---

## Overview

**Streamable HTTP**는 MCP v1.25+에서 도입된 HTTP 기반 전송 계층입니다.

**특징:**
- HTTP/1.1 기반 (Long-polling 또는 Chunked Transfer)
- stdio, SSE 대체 (단일 전송 방식으로 통합)
- AsyncExitStack 기반 세션 관리

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│         AgentHub (Client)                       │
│  ┌───────────────────────────────────────────┐  │
│  │  McpClientAdapter                         │  │
│  │  - AsyncExitStack (생명주기 관리)         │  │
│  │  - streamable_http_client(url)            │  │
│  │  - ClientSession(read, write, callbacks)  │  │
│  └───────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────┘
                     │ HTTP/1.1
                     v
┌─────────────────────────────────────────────────┐
│         MCP Server (Synapse)                    │
│  - Streamable HTTP Endpoint: /mcp              │
│  - Resources, Prompts, Sampling, Elicitation   │
└─────────────────────────────────────────────────┘
```

---

## Connection Flow

```python
from mcp.client.streamable_http import streamable_http_client
from mcp.client.session import ClientSession
from contextlib import AsyncExitStack

# 1. AsyncExitStack 생성
exit_stack = AsyncExitStack()

# 2. Streamable HTTP Client 연결
read, write, _ = await exit_stack.enter_async_context(
    streamable_http_client(url)  # url: http://localhost:9000/mcp
)

# 3. ClientSession 초기화
session = await exit_stack.enter_async_context(
    ClientSession(
        read, write,
        sampling_callback=...,
        elicitation_callback=...
    )
)
await session.initialize()

# 4. MCP 메서드 호출
resources = await session.list_resources()
content = await session.read_resource(uri)

# 5. 세션 정리
await exit_stack.aclose()  # 모든 리소스 자동 정리
```

---

## Synapse Server Setup

### Installation

```bash
# Synapse MCP 서버 설치 (예시)
npm install -g @anthropics/synapse

# 또는 로컬 실행
git clone https://github.com/anthropics/synapse
cd synapse
npm install
npm start -- --port 9000
```

### Configuration

```json
{
  "transport": "streamable-http",
  "port": 9000,
  "path": "/mcp",
  "features": [
    "resources",
    "prompts",
    "sampling",
    "elicitation"
  ]
}
```

### Verification

```bash
# Health Check
curl http://localhost:9000/health

# MCP Endpoint
curl http://localhost:9000/mcp
```

---

## Testing with Synapse

### Integration Test Setup

```python
# tests/integration/test_mcp_client_adapter.py

import pytest
from src.adapters.outbound.mcp.mcp_client_adapter import McpClientAdapter

@pytest.mark.local_mcp  # 로컬 MCP 서버 필요
class TestMcpClientAdapter:
    @pytest.fixture
    async def adapter(self):
        adapter = McpClientAdapter()
        yield adapter
        await adapter.disconnect_all()

    @pytest.fixture
    def synapse_url(self):
        return "http://localhost:9000/mcp"  # Synapse Streamable HTTP

    async def test_list_resources(self, adapter, synapse_url):
        await adapter.connect("synapse", synapse_url)
        resources = await adapter.list_resources("synapse")
        assert len(resources) > 0
```

### Running Tests

```bash
# 1. Synapse 서버 실행
npm start -- --port 9000

# 2. 통합 테스트 실행
pytest -m local_mcp -v

# 3. 특정 테스트만 실행
pytest tests/integration/test_mcp_client_adapter.py -m local_mcp -v
```

---

## Callback Implementation

### Sampling Callback

**Domain 콜백 프로토콜:**
```python
from src.domain.ports.outbound.mcp_client_port import SamplingCallback

async def my_sampling_callback(
    request_id: str,
    endpoint_id: str,
    messages: list[dict[str, Any]],
    model_preferences: dict[str, Any] | None,
    system_prompt: str | None,
    max_tokens: int,
) -> dict[str, Any]:
    # LLM 호출
    response = await llm.complete(messages, system_prompt, max_tokens)
    return {
        "role": "assistant",
        "content": response.text,
        "model": response.model
    }
```

**Adapter에서 MCP SDK로 변환:**
```python
# McpClientAdapter._wrap_sampling_callback()
async def mcp_callback(context, params: types.CreateMessageRequestParams):
    # MCP params → Domain 형식
    messages = [
        {"role": m.role, "content": m.content.text}
        for m in params.messages
    ]

    # Domain 콜백 호출
    result = await domain_callback(
        request_id=str(uuid.uuid4()),
        endpoint_id=endpoint_id,
        messages=messages,
        model_preferences=params.modelPreferences,
        system_prompt=params.systemPrompt,
        max_tokens=params.maxTokens,
    )

    # Domain 결과 → MCP 형식
    return types.CreateMessageResult(
        role=result["role"],
        content=types.TextContent(type="text", text=result["content"]),
        model=result["model"],
    )
```

---

## Known Issues & Troubleshooting

### 1. AsyncExitStack Teardown Error

**문제:**
```
RuntimeError: Attempted to exit cancel scope in a different task than it was entered in
```

**원인:**
- pytest-asyncio의 각 테스트가 별도 event loop/task에서 실행
- anyio의 task group은 동일한 task 내에서 enter/exit되어야 함

**영향:**
- 테스트 teardown 시 에러 로그 출력
- 테스트 자체는 PASSED
- 실제 서버 운영에는 영향 없음 (FastAPI lifespan에서는 정상 동작)

**임시 해결:**
- Phase 4에서는 문제 인지만 하고 문서화
- Phase 5에서 AsyncExitStack 대체 방법 검토

### 2. Connection Timeout

**증상:**
```bash
httpx.ConnectTimeout: [Errno 110] Connection timed out
```

**해결:**
1. Synapse 서버가 실행 중인지 확인
2. 포트 충돌 확인 (`lsof -i :9000`)
3. 방화벽 설정 확인

### 3. Missing Required Argument

**증상:**
```
mcp.shared.exceptions.McpError: Missing required argument: code
```

**원인:**
- 프롬프트에 필수 인자(argument)가 있는데 제공하지 않음

**해결:**
```python
# 프롬프트 인자 확인
prompts = await adapter.list_prompts("synapse")
prompt = prompts[0]
print(prompt.arguments)  # [PromptArgument(name="code", required=True)]

# 필수 인자 제공
result = await adapter.get_prompt("synapse", prompt.name, {"code": "example"})
```

---

## References

- [MCP Python SDK GitHub](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Specification](https://modelcontextprotocol.org/)
- [Synapse MCP Server](https://github.com/anthropics/synapse)
- [Phase 4 Plan](../../../../project/planning/active/07_hybrid_dual/04_adapter_implementation.md)

---

*Last Updated: 2026-02-07*
