# MCP Standards Guide

Model Context Protocol (MCP) 구현 가이드입니다. Streamable HTTP 프로토콜 기반 MCP 클라이언트 통합 방법을 다룹니다.

---

## MCP Protocol Overview

### Supported Transport

- **Streamable HTTP**: AgentHub의 기본 MCP 전송 방식
- 단일 HTTP 연결에서 양방향 스트리밍 지원
- Server-Sent Events (SSE) 기반 응답 스트리밍

### Protocol Flow

```
Extension → AgentHub API → MCP Client → MCP Server
                                ↓
                         Tool Discovery
                         Tool Execution
                         Result Streaming
```

---

## MCP Client Implementation

### Using mcp Library

```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def create_mcp_client(server_url: str) -> ClientSession:
    """MCP 클라이언트 세션 생성."""
    async with streamablehttp_client(server_url) as (read, write):
        async with ClientSession(read, write) as session:
            # 초기화 (capabilities 교환)
            await session.initialize()
            return session
```

### Tool Discovery

```python
async def discover_tools(session: ClientSession) -> list[Tool]:
    """MCP 서버에서 사용 가능한 도구 목록 조회."""
    result = await session.list_tools()

    tools = []
    for tool_info in result.tools:
        tools.append(Tool(
            name=tool_info.name,
            description=tool_info.description,
            input_schema=tool_info.inputSchema,
        ))
    return tools
```

### Tool Execution

```python
async def execute_tool(
    session: ClientSession,
    tool_name: str,
    arguments: dict,
) -> str:
    """MCP 도구 실행."""
    result = await session.call_tool(tool_name, arguments)

    # 결과 처리
    if result.isError:
        raise ToolExecutionError(result.content[0].text)

    return result.content[0].text
```

---

## DynamicToolset Integration

### ADK DynamicToolset

AgentHub는 ADK의 DynamicToolset을 사용하여 MCP 도구를 동적으로 로드합니다.

```python
from google.adk.toolsets import DynamicToolset
from google.adk.tools.mcp_tool import McpTool

class McpDynamicToolset(DynamicToolset):
    """MCP 서버 기반 동적 도구셋."""

    def __init__(self, mcp_endpoints: list[str]) -> None:
        self._endpoints = mcp_endpoints
        self._tools: dict[str, McpTool] = {}

    async def load_tools(self) -> None:
        """MCP 서버에서 도구 로드."""
        for endpoint in self._endpoints:
            async with create_mcp_client(endpoint) as session:
                tools = await discover_tools(session)
                for tool in tools:
                    self._tools[tool.name] = McpTool(
                        session=session,
                        tool_info=tool,
                    )

    def get_tools(self) -> list[McpTool]:
        """로드된 도구 목록 반환."""
        return list(self._tools.values())
```

---

## Endpoint Registration

### Register MCP Server

```python
async def register_mcp_endpoint(
    storage: StoragePort,
    url: str,
    name: str | None = None,
    auth_config: AuthConfig | None = None,
) -> Endpoint:
    """MCP 서버 등록."""
    # 연결 테스트
    async with create_mcp_client(url) as session:
        tools = await discover_tools(session)

    endpoint = Endpoint(
        id=generate_id(),
        type=EndpointType.MCP,
        url=url,
        name=name or f"MCP Server ({url})",
        tool_count=len(tools),
        auth_config=auth_config,
    )

    await storage.save_endpoint(endpoint)
    return endpoint
```

### Unregister MCP Server

```python
async def unregister_mcp_endpoint(
    storage: StoragePort,
    endpoint_id: str,
) -> None:
    """MCP 서버 등록 해제."""
    # 활성 연결 종료
    await close_mcp_connection(endpoint_id)

    # 저장소에서 삭제
    await storage.delete_endpoint(endpoint_id)
```

---

## Authentication

### API Key Authentication

```python
from mcp.client.streamable_http import streamablehttp_client

async def create_authenticated_client(
    url: str,
    api_key: str,
) -> ClientSession:
    """API Key 인증이 포함된 MCP 클라이언트."""
    headers = {"Authorization": f"Bearer {api_key}"}

    async with streamablehttp_client(url, headers=headers) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return session
```

### OAuth 2.0 Authentication

```python
async def create_oauth_client(
    url: str,
    oauth_config: OAuthConfig,
) -> ClientSession:
    """OAuth 2.0 인증이 포함된 MCP 클라이언트."""
    # Access Token 획득
    token = await get_oauth_token(
        token_url=oauth_config.token_url,
        client_id=oauth_config.client_id,
        client_secret=oauth_config.client_secret,
        scope=oauth_config.scope,
    )

    headers = {"Authorization": f"Bearer {token}"}

    async with streamablehttp_client(url, headers=headers) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return session
```

### Token Refresh

```python
class OAuthTokenManager:
    """OAuth 토큰 관리자."""

    def __init__(self, oauth_config: OAuthConfig) -> None:
        self._config = oauth_config
        self._access_token: str | None = None
        self._expires_at: datetime | None = None

    async def get_valid_token(self) -> str:
        """유효한 Access Token 반환 (필요시 갱신)."""
        if self._is_expired():
            await self._refresh_token()
        return self._access_token

    def _is_expired(self) -> bool:
        """토큰 만료 여부 확인."""
        if self._expires_at is None:
            return True
        # 10초 여유를 두고 갱신
        return datetime.now() >= self._expires_at - timedelta(seconds=10)
```

---

## Testing with Local Server

### Start Local MCP Server

```bash
# synapse MCP 서버 시작 (기본 포트 9000)
python -m synapse

# 커스텀 포트
python -m synapse --port 9001
```

### pytest Fixture

```python
# tests/conftest.py
import pytest

@pytest.fixture
async def mcp_server():
    """로컬 MCP 테스트 서버."""
    # synapse 서버가 이미 실행 중이라고 가정
    # 또는 subprocess로 시작
    yield "http://127.0.0.1:9000/mcp"

@pytest.fixture
async def mcp_client(mcp_server):
    """MCP 클라이언트 fixture."""
    async with create_mcp_client(mcp_server) as session:
        yield session
```

### Integration Test Example

```python
@pytest.mark.local_mcp
async def test_mcp_tool_discovery(mcp_client):
    """MCP 도구 목록 조회 테스트."""
    tools = await discover_tools(mcp_client)

    assert len(tools) > 0
    assert any(t.name == "echo" for t in tools)

@pytest.mark.local_mcp
async def test_mcp_tool_execution(mcp_client):
    """MCP 도구 실행 테스트."""
    result = await execute_tool(
        mcp_client,
        tool_name="echo",
        arguments={"message": "Hello"},
    )

    assert "Hello" in result
```

---

## Error Handling

### Connection Errors

```python
from mcp.exceptions import ConnectionError, TimeoutError

async def safe_mcp_connect(url: str) -> ClientSession | None:
    """안전한 MCP 연결."""
    try:
        return await create_mcp_client(url)
    except ConnectionError:
        logger.error(f"MCP 서버 연결 실패: {url}")
        return None
    except TimeoutError:
        logger.error(f"MCP 서버 응답 시간 초과: {url}")
        return None
```

### Tool Execution Retry

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
)
async def execute_tool_with_retry(
    session: ClientSession,
    tool_name: str,
    arguments: dict,
) -> str:
    """재시도 로직이 포함된 도구 실행."""
    return await execute_tool(session, tool_name, arguments)
```

---

*Last Updated: 2026-02-05*
