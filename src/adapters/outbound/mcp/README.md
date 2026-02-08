# MCP Client Adapter

MCP Python SDK를 사용하여 MCP 서버와 통신하는 Outbound Adapter입니다.

---

## Overview

| 항목 | 값 |
|------|-----|
| **Protocol** | MCP (Model Context Protocol) |
| **Transport** | Streamable HTTP |
| **SDK Version** | mcp >= 1.25 |
| **Port Implementation** | [McpClientPort](../../../domain/ports/outbound/mcp_client_port.py) |
| **Lifecycle Management** | AsyncExitStack |

**핵심 기능:**
- MCP 서버 연결/해제 (Streamable HTTP Transport)
- Resources 조회 및 읽기
- Prompts 조회 및 렌더링
- Sampling/Elicitation 콜백 변환 (Domain ↔ MCP SDK)

---

## Quick Start

### 연결 및 리소스 조회

```python
from src.adapters.outbound.mcp.mcp_client_adapter import McpClientAdapter

# Adapter 생성
adapter = McpClientAdapter()

# MCP 서버 연결 (Streamable HTTP)
await adapter.connect("synapse", "http://localhost:9000/mcp")

# 리소스 목록 조회
resources = await adapter.list_resources("synapse")
for resource in resources:
    print(f"- {resource.name}: {resource.uri}")

# 리소스 읽기
content = await adapter.read_resource("synapse", resources[0].uri)
print(content.text or content.blob)

# 연결 해제
await adapter.disconnect("synapse")
```

### 프롬프트 조회 및 렌더링

```python
# 프롬프트 목록 조회
prompts = await adapter.list_prompts("synapse")

# 프롬프트 렌더링
result = await adapter.get_prompt(
    "synapse",
    "summarize",
    {"text": "Long document..."}
)
print(result)  # 렌더링된 프롬프트 메시지
```

### 콜백과 함께 연결 (Sampling/Elicitation)

```python
async def my_sampling_callback(request_id, endpoint_id, messages, **kwargs):
    """Domain Sampling 콜백"""
    # LLM 호출 로직
    return {
        "role": "assistant",
        "content": "Response from LLM",
        "model": "gpt-4"
    }

async def my_elicitation_callback(request_id, endpoint_id, message, requested_schema):
    """Domain Elicitation 콜백"""
    # 사용자 입력 처리 로직
    return {
        "action": "accept",
        "content": "User input..."
    }

# 콜백과 함께 연결
await adapter.connect(
    "synapse",
    "http://localhost:9000/mcp",
    sampling_callback=my_sampling_callback,
    elicitation_callback=my_elicitation_callback
)
```

---

## Architecture

### Callback Conversion

McpClientAdapter는 Domain 콜백을 MCP SDK 콜백으로 변환합니다:

```
Domain Protocol (Simple dict)  →  MCP SDK Types (types.CreateMessageResult)
         ↓                                    ↓
 SamplingCallback              →    SamplingFnT (MCP SDK)
 ElicitationCallback           →    ElicitationFnT (MCP SDK)
```

**변환 로직:**

1. **Sampling Callback:**
   - Input: `types.CreateMessageRequestParams` (MCP SDK)
   - Convert: messages → Domain format (list[dict])
   - Call: Domain callback
   - Convert: Domain result → `types.CreateMessageResult` (MCP SDK)

2. **Elicitation Callback:**
   - Input: `types.ElicitRequestParams` (MCP SDK)
   - Call: Domain callback
   - Convert: Domain result → `types.ElicitResult` (MCP SDK)

**코드 위치:** [mcp_client_adapter.py](mcp_client_adapter.py) (lines 156-229)

### Lifecycle Management (AsyncExitStack)

MCP SDK의 ClientSession과 Transport는 async context manager입니다. AsyncExitStack을 사용하여 생명주기를 관리합니다:

```python
async def connect(self, endpoint_id, url, ...):
    exit_stack = AsyncExitStack()

    # Transport 진입
    read, write, _ = await exit_stack.enter_async_context(
        streamable_http_client(url)
    )

    # Session 진입
    session = await exit_stack.enter_async_context(
        ClientSession(read, write, ...)
    )

    # ExitStack 저장 (disconnect 시 자동 정리)
    self._exit_stacks[endpoint_id] = exit_stack
```

**장점:**
- 자동 리소스 정리 (Transport + Session)
- 예외 발생 시에도 안전하게 정리
- 여러 context manager를 하나로 관리

---

## Testing

### Integration Tests

**파일:** [tests/integration/test_mcp_client_adapter.py](../../../../tests/integration/test_mcp_client_adapter.py)

**마커:** `@pytest.mark.local_mcp` (기본 제외)

**요구사항:**
- Synapse MCP 서버가 `localhost:9000/mcp`에서 실행 중이어야 함
- Synapse 설치: `pip install mcp-server-synapse`
- 서버 실행: `synapse start` (별도 터미널)

**실행:**
```bash
# 1. Synapse 서버 시작 (별도 터미널)
synapse start

# 2. 통합 테스트 실행
pytest -m local_mcp -v
```

**테스트 커버리지:**
- ✅ 연결 및 리소스 목록 조회
- ✅ 리소스 읽기
- ✅ 프롬프트 목록 조회 및 렌더링
- ✅ 단일 세션 disconnect
- ✅ 모든 세션 disconnect_all

---

## Known Issues

### ~~AsyncExitStack Teardown Error~~ (Resolved in Phase 4.5)

**해결:** anyio pytest plugin 도입으로 fixture가 단일 task에서 실행되어 이 문제 해소

**상세:** [ADR-T08: AnyIO Pytest Plugin Migration](../../../../docs/project/decisions/technical/ADR-T08-anyio-pytest-plugin-migration.md)

---

## Related Documentation

- **Port Interface:** [McpClientPort](../../../domain/ports/outbound/mcp_client_port.py)
- **MCP Streamable HTTP Guide:** [docs/developers/guides/standards/mcp/streamable-http.md](../../../../docs/developers/guides/standards/mcp/streamable-http.md)
- **MCP Standards:** [docs/developers/guides/standards/README.md](../../../../docs/developers/guides/standards/README.md)
- **Test Resources:** [tests/docs/RESOURCES.md](../../../../tests/docs/RESOURCES.md#mcp-servers)

---

*Last Updated: 2026-02-07*
*Phase: 07 - Hybrid-Dual Architecture*
