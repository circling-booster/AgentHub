# Phase 4: Adapter Implementation (TDD)

## 개요

MCP SDK를 사용하는 실제 Adapter를 구현합니다.
FakeMcpClient는 이미 Phase 2에서 작성되었으므로, 여기서는 실제 구현에 집중합니다.

---

## Step 4.1: 의존성 추가

**파일:** `pyproject.toml`

```toml
"mcp>=1.25,<2",  # MCP Python SDK (v2 breaking changes 방지)
```

---

## Step 4.2: McpClientAdapter 구현

**파일:** `src/adapters/outbound/mcp/mcp_client_adapter.py`
**테스트:** `tests/integration/test_mcp_client_adapter.py` *(Integration - 외부 SDK 사용)*

### 콜백 변환 로직 (핵심!)

Domain 콜백을 MCP SDK 콜백으로 변환합니다:

```python
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp import types
from contextlib import AsyncExitStack

from src.domain.ports.outbound.mcp_client_port import (
    McpClientPort,
    SamplingCallback,
    ElicitationCallback,
)
from src.domain.entities.resource import Resource, ResourceContent
from src.domain.entities.prompt_template import PromptTemplate

class McpClientAdapter(McpClientPort):
    """MCP SDK 기반 클라이언트 어댑터

    MCP Python SDK를 사용하여 MCP 서버와 통신합니다.
    Resources, Prompts, Sampling, Elicitation을 지원합니다.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, ClientSession] = {}
        self._exit_stacks: dict[str, AsyncExitStack] = {}

    async def connect(
        self,
        endpoint_id: str,
        url: str,
        sampling_callback: SamplingCallback | None = None,
        elicitation_callback: ElicitationCallback | None = None,
    ) -> None:
        # Domain 콜백 → MCP SDK 콜백 변환
        mcp_sampling_cb = None
        if sampling_callback:
            mcp_sampling_cb = self._wrap_sampling_callback(endpoint_id, sampling_callback)

        mcp_elicitation_cb = None
        if elicitation_callback:
            mcp_elicitation_cb = self._wrap_elicitation_callback(endpoint_id, elicitation_callback)

        # MCP SDK 연결
        exit_stack = AsyncExitStack()
        read, write, _ = await exit_stack.enter_async_context(
            streamable_http_client(url)
        )
        session = await exit_stack.enter_async_context(
            ClientSession(
                read, write,
                sampling_callback=mcp_sampling_cb,
                elicitation_callback=mcp_elicitation_cb,
            )
        )
        await session.initialize()

        self._sessions[endpoint_id] = session
        self._exit_stacks[endpoint_id] = exit_stack

    async def disconnect(self, endpoint_id: str) -> None:
        """세션 정리 (AsyncExitStack 해제)"""
        if endpoint_id in self._exit_stacks:
            await self._exit_stacks[endpoint_id].aclose()
            del self._exit_stacks[endpoint_id]
            del self._sessions[endpoint_id]

    async def disconnect_all(self) -> None:
        """모든 세션 정리 (서버 종료 시)"""
        for endpoint_id in list(self._sessions.keys()):
            await self.disconnect(endpoint_id)

    async def list_resources(self, endpoint_id: str) -> list[Resource]:
        session = self._get_session(endpoint_id)
        result = await session.list_resources()
        return [
            Resource(
                uri=r.uri,
                name=r.name,
                description=r.description or "",
                mime_type=r.mimeType or "",
            )
            for r in result.resources
        ]

    async def read_resource(self, endpoint_id: str, uri: str) -> ResourceContent:
        session = self._get_session(endpoint_id)
        result = await session.read_resource(uri)
        # result.contents[0]이 TextResourceContents 또는 BlobResourceContents
        content = result.contents[0]
        if hasattr(content, 'text'):
            return ResourceContent(uri=uri, text=content.text, mime_type=content.mimeType or "")
        else:
            return ResourceContent(uri=uri, blob=content.blob, mime_type=content.mimeType or "")

    async def list_prompts(self, endpoint_id: str) -> list[PromptTemplate]:
        session = self._get_session(endpoint_id)
        result = await session.list_prompts()
        return [
            PromptTemplate(
                name=p.name,
                description=p.description or "",
                arguments=[
                    {"name": a.name, "required": a.required, "description": a.description or ""}
                    for a in (p.arguments or [])
                ],
            )
            for p in result.prompts
        ]

    async def get_prompt(
        self, endpoint_id: str, name: str, arguments: dict | None
    ) -> str:
        session = self._get_session(endpoint_id)
        result = await session.get_prompt(name, arguments or {})
        # 메시지들을 결합하여 반환
        return "\n".join(
            m.content.text if hasattr(m.content, 'text') else str(m.content)
            for m in result.messages
        )

    def _get_session(self, endpoint_id: str) -> ClientSession:
        """세션 조회 (없으면 예외)"""
        if endpoint_id not in self._sessions:
            from src.domain.exceptions import EndpointNotFoundError
            raise EndpointNotFoundError(f"Not connected: {endpoint_id}")
        return self._sessions[endpoint_id]

    def _wrap_sampling_callback(
        self,
        endpoint_id: str,
        domain_callback: SamplingCallback
    ):
        """Domain 콜백을 MCP SDK SamplingFnT로 래핑"""
        async def mcp_callback(
            context,  # RequestContext[ClientSession]
            params: types.CreateMessageRequestParams
        ) -> types.CreateMessageResult | types.ErrorData:
            import uuid
            request_id = str(uuid.uuid4())

            # MCP params → Domain 형식 변환
            messages = [
                {"role": m.role, "content": m.content.text if hasattr(m.content, 'text') else str(m.content)}
                for m in params.messages
            ]

            try:
                result = await domain_callback(
                    request_id=request_id,
                    endpoint_id=endpoint_id,
                    messages=messages,
                    model_preferences=params.modelPreferences,
                    system_prompt=params.systemPrompt,
                    max_tokens=params.maxTokens,
                )

                # Domain 결과 → MCP 형식 변환
                return types.CreateMessageResult(
                    role=result.get("role", "assistant"),
                    content=types.TextContent(type="text", text=result.get("content", "")),
                    model=result.get("model", ""),
                )
            except Exception as e:
                return types.ErrorData(code="SAMPLING_ERROR", message=str(e))

        return mcp_callback

    def _wrap_elicitation_callback(
        self,
        endpoint_id: str,
        domain_callback: ElicitationCallback
    ):
        """Domain 콜백을 MCP SDK ElicitationFnT로 래핑"""
        async def mcp_callback(
            context,
            params: types.ElicitRequestParams
        ) -> types.ElicitResult | types.ErrorData:
            import uuid
            request_id = str(uuid.uuid4())

            try:
                result = await domain_callback(
                    request_id=request_id,
                    endpoint_id=endpoint_id,
                    message=params.message,
                    requested_schema=params.requestedSchema or {},
                )

                return types.ElicitResult(
                    action=result.get("action", "accept"),
                    content=result.get("content"),
                )
            except Exception as e:
                return types.ErrorData(code="ELICITATION_ERROR", message=str(e))

        return mcp_callback
```

### 세션 생명주기 관리

```
connect() → AsyncExitStack 생성 → _exit_stacks에 저장
disconnect() → AsyncExitStack.aclose() → 리소스 정리
disconnect_all() → 서버 종료 시 모든 세션 정리
```

---

## Step 4.3: Integration 테스트

**파일:** `tests/integration/test_mcp_client_adapter.py`

```python
import pytest
from src.adapters.outbound.mcp.mcp_client_adapter import McpClientAdapter

@pytest.mark.local_mcp  # 로컬 MCP 서버 필요
class TestMcpClientAdapter:
    """McpClientAdapter Integration 테스트

    Note: 실제 MCP 서버가 필요합니다.
    테스트 실행: pytest -m local_mcp
    """

    @pytest.fixture
    async def adapter(self):
        adapter = McpClientAdapter()
        yield adapter
        await adapter.disconnect_all()

    async def test_connect_and_list_resources(self, adapter, mcp_server_url):
        """연결 후 리소스 목록 조회"""
        await adapter.connect("test-ep", mcp_server_url)
        resources = await adapter.list_resources("test-ep")
        assert isinstance(resources, list)

    async def test_disconnect_cleans_up_session(self, adapter, mcp_server_url):
        """disconnect 후 세션 정리"""
        await adapter.connect("test-ep", mcp_server_url)
        await adapter.disconnect("test-ep")

        with pytest.raises(EndpointNotFoundError):
            await adapter.list_resources("test-ep")

    async def test_sampling_callback_invoked(self, adapter, mcp_server_url):
        """MCP 서버가 sampling 요청 시 콜백 호출"""
        callback_invoked = False

        async def test_callback(**kwargs):
            nonlocal callback_invoked
            callback_invoked = True
            return {"role": "assistant", "content": "Test response", "model": "test"}

        await adapter.connect("test-ep", mcp_server_url, sampling_callback=test_callback)
        # MCP 서버에서 sampling 요청 트리거 필요
        # assert callback_invoked
```

---

## 테스트 실행

```bash
# Unit 테스트 (Fake 사용 - Phase 2, 3에서 작성)
pytest tests/unit/ -q --tb=line

# Integration 테스트 (실제 MCP 서버 필요)
pytest tests/integration/test_mcp_client_adapter.py -m local_mcp -v
```

---

## Checklist

- [ ] `pyproject.toml`에 mcp 의존성 추가
- [ ] `src/adapters/outbound/mcp/__init__.py` 생성
- [ ] `src/adapters/outbound/mcp/mcp_client_adapter.py` 구현
- [ ] `tests/integration/test_mcp_client_adapter.py` 작성
- [ ] 로컬 MCP 서버로 테스트
