# Phase 4: Adapter Implementation (TDD)

## 개요

MCP SDK 기반 Adapter와 Synapse 통합 테스트를 구현합니다.

**핵심:**
- McpClientAdapter: Domain 콜백 → MCP SDK 콜백 변환
- HitlNotificationAdapter: SSE 브로드캐스트 어댑터 (신규)
- AdkOrchestratorAdapter.generate_response(): 단일 LLM 호출 (Method C용)
- Synapse 통합 테스트: Resources/Prompts/Sampling 검증

---

## Step 4.1: 의존성 추가

**파일:** `pyproject.toml`

```toml
[tool.poetry.dependencies]
# ... 기존 의존성 ...
"mcp>=1.25,<2"  # MCP Python SDK
```

**변경 이유:** MCP Streamable HTTP 지원 (v1.25+)

---

## Step 4.2: McpClientAdapter 구현

**파일:** `src/adapters/outbound/mcp/mcp_client_adapter.py`
**테스트:** `tests/integration/test_mcp_client_adapter.py` (Integration - 외부 SDK 사용)

### 세션 생명주기 관리

```
connect() → AsyncExitStack 생성 → streamable_http_client → ClientSession
disconnect() → AsyncExitStack.aclose() → 리소스 정리
disconnect_all() → 서버 종료 시 모든 세션 정리
```

### 콜백 변환 로직 (핵심)

```python
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp import types
from contextlib import AsyncExitStack
from typing import Any

from src.domain.ports.outbound.mcp_client_port import (
    McpClientPort,
    SamplingCallback,
    ElicitationCallback,
)
from src.domain.entities.resource import Resource, ResourceContent
from src.domain.entities.prompt_template import PromptTemplate, PromptArgument
from src.domain.exceptions import EndpointNotFoundError, ResourceNotFoundError, PromptNotFoundError

class McpClientAdapter(McpClientPort):
    """MCP SDK 기반 클라이언트 어댑터

    MCP Python SDK를 사용하여 MCP 서버와 통신합니다.
    Streamable HTTP Transport를 사용합니다.
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
        """MCP 서버에 연결

        Args:
            endpoint_id: 엔드포인트 ID
            url: MCP 서버 URL (Streamable HTTP)
            sampling_callback: Domain 샘플링 콜백 (optional)
            elicitation_callback: Domain Elicitation 콜백 (optional)
        """
        # Domain 콜백 → MCP SDK 콜백 변환
        mcp_sampling_cb = None
        if sampling_callback:
            mcp_sampling_cb = self._wrap_sampling_callback(endpoint_id, sampling_callback)

        mcp_elicitation_cb = None
        if elicitation_callback:
            mcp_elicitation_cb = self._wrap_elicitation_callback(endpoint_id, elicitation_callback)

        # MCP SDK 연결 (AsyncExitStack으로 생명주기 관리)
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
        """세션 정리 (AsyncExitStack 해제)

        Args:
            endpoint_id: 엔드포인트 ID
        """
        if endpoint_id in self._exit_stacks:
            await self._exit_stacks[endpoint_id].aclose()
            del self._exit_stacks[endpoint_id]
            del self._sessions[endpoint_id]

    async def disconnect_all(self) -> None:
        """모든 세션 정리 (서버 종료 시)"""
        for endpoint_id in list(self._sessions.keys()):
            await self.disconnect(endpoint_id)

    async def list_resources(self, endpoint_id: str) -> list[Resource]:
        """리소스 목록 조회"""
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
        """리소스 콘텐츠 읽기"""
        session = self._get_session(endpoint_id)
        result = await session.read_resource(uri)
        # result.contents[0]이 TextResourceContents 또는 BlobResourceContents
        content = result.contents[0]
        if hasattr(content, 'text'):
            return ResourceContent(uri=uri, text=content.text, mime_type=content.mimeType or "")
        else:
            return ResourceContent(uri=uri, blob=content.blob, mime_type=content.mimeType or "")

    async def list_prompts(self, endpoint_id: str) -> list[PromptTemplate]:
        """프롬프트 목록 조회"""
        session = self._get_session(endpoint_id)
        result = await session.list_prompts()
        return [
            PromptTemplate(
                name=p.name,
                description=p.description or "",
                arguments=[
                    PromptArgument(
                        name=a.name,
                        required=a.required,
                        description=a.description or ""
                    )
                    for a in (p.arguments or [])
                ],
            )
            for p in result.prompts
        ]

    async def get_prompt(
        self, endpoint_id: str, name: str, arguments: dict | None
    ) -> str:
        """프롬프트 렌더링"""
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
            raise EndpointNotFoundError(f"Not connected: {endpoint_id}")
        return self._sessions[endpoint_id]

    def _wrap_sampling_callback(
        self,
        endpoint_id: str,
        domain_callback: SamplingCallback
    ):
        """Domain 콜백을 MCP SDK SamplingFnT로 래핑

        MCP SDK callback signature:
        async def(context: RequestContext[ClientSession],
                  params: CreateMessageRequestParams)
            -> CreateMessageResult | ErrorData
        """
        async def mcp_callback(
            context,  # RequestContext[ClientSession]
            params: types.CreateMessageRequestParams
        ) -> types.CreateMessageResult | types.ErrorData:
            import uuid
            request_id = str(uuid.uuid4())

            # MCP params → Domain 형식 변환
            messages = [
                {
                    "role": m.role,
                    "content": m.content.text if hasattr(m.content, 'text') else str(m.content)
                }
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
        """Domain 콜백을 MCP SDK ElicitationFnT로 래핑

        MCP SDK callback signature:
        async def(context: RequestContext[ClientSession],
                  params: ElicitRequestParams)
            -> ElicitResult | ErrorData
        """
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

---

## Step 4.2a: SseBroker 구현 (신규)

**파일:** `src/adapters/outbound/sse/broker.py`
**테스트:** `tests/integration/test_sse_broker.py`

### 구현

```python
# src/adapters/outbound/sse/broker.py
"""SSE Broker for Event Broadcasting

asyncio.Queue 기반 pub/sub 패턴으로 SSE 이벤트를 브로드캐스트합니다.
"""

import asyncio
from typing import AsyncIterator, Any


class SseBroker:
    """SSE 이벤트 브로드캐스터 (Singleton)

    여러 클라이언트가 subscribe()로 이벤트 스트림을 구독하고,
    broadcast()로 모든 구독자에게 이벤트를 전송합니다.
    """

    def __init__(self):
        self._subscribers: list[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """이벤트를 모든 구독자에게 브로드캐스트

        Args:
            event_type: 이벤트 타입
            data: 이벤트 데이터
        """
        event = {"type": event_type, "data": data}
        async with self._lock:
            # 모든 구독자의 Queue에 이벤트 전송
            for queue in self._subscribers:
                try:
                    await queue.put(event)
                except Exception:
                    # Queue가 꽉 찼거나 취소된 경우 무시
                    pass

    async def subscribe(self) -> AsyncIterator[dict[str, Any]]:
        """이벤트 스트림 구독

        Yields:
            이벤트 딕셔너리 {"type": str, "data": dict}
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)

        async with self._lock:
            self._subscribers.append(queue)

        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            # 구독 종료 시 큐 제거
            async with self._lock:
                if queue in self._subscribers:
                    self._subscribers.remove(queue)
```

### Integration 테스트

```python
# tests/integration/test_sse_broker.py

import pytest
import asyncio
from src.adapters.outbound.sse.broker import SseBroker


class TestSseBroker:
    @pytest.fixture
    def broker(self):
        return SseBroker()

    async def test_broadcast_to_subscribers(self, broker):
        """broadcast가 모든 구독자에게 전달"""
        received_events = []

        async def subscriber():
            async for event in broker.subscribe():
                received_events.append(event)
                if len(received_events) >= 2:
                    break

        # 구독 시작
        task = asyncio.create_task(subscriber())
        await asyncio.sleep(0.1)  # 구독 대기

        # 이벤트 브로드캐스트
        await broker.broadcast("test_event", {"key": "value"})
        await broker.broadcast("test_event_2", {"key": "value2"})

        await task

        assert len(received_events) == 2
        assert received_events[0]["type"] == "test_event"
        assert received_events[1]["type"] == "test_event_2"

    async def test_multiple_subscribers(self, broker):
        """여러 구독자가 동일한 이벤트 수신"""
        received_1 = []
        received_2 = []

        async def subscriber_1():
            async for event in broker.subscribe():
                received_1.append(event)
                break

        async def subscriber_2():
            async for event in broker.subscribe():
                received_2.append(event)
                break

        # 두 구독자 시작
        task1 = asyncio.create_task(subscriber_1())
        task2 = asyncio.create_task(subscriber_2())
        await asyncio.sleep(0.1)

        # 이벤트 브로드캐스트
        await broker.broadcast("shared", {"msg": "hello"})

        await asyncio.gather(task1, task2)

        assert len(received_1) == 1
        assert len(received_2) == 1
        assert received_1[0]["type"] == "shared"
        assert received_2[0]["type"] == "shared"
```

---

## Step 4.3: HitlNotificationAdapter 구현 (신규)

**파일:** `src/adapters/outbound/sse/hitl_notification_adapter.py`
**테스트:** `tests/integration/test_hitl_notification_adapter.py`

### 구현

```python
from src.domain.ports.outbound.hitl_notification_port import HitlNotificationPort
from src.domain.ports.outbound.event_broadcast_port import EventBroadcastPort
from src.domain.entities.sampling_request import SamplingRequest
from src.domain.entities.elicitation_request import ElicitationRequest


class HitlNotificationAdapter(HitlNotificationPort):
    """HITL 요청 알림 어댑터 (SSE 브로드캐스트)

    timeout 시 SSE를 통해 Extension/Playground에 알림 전송
    """

    def __init__(self, sse_broker: EventBroadcastPort) -> None:
        """
        Args:
            sse_broker: EventBroadcastPort 구현체 (DI로 주입)
        """
        self._broker = sse_broker

    async def notify_sampling_request(self, request: SamplingRequest) -> None:
        """Sampling 요청 알림 (SSE 브로드캐스트)

        Args:
            request: SamplingRequest 엔티티
        """
        await self._broker.broadcast(
            event_type="sampling_request",
            data={
                "request_id": request.id,
                "endpoint_id": request.endpoint_id,
                "messages": request.messages,
                "model_preferences": request.model_preferences,
                "system_prompt": request.system_prompt,
                "max_tokens": request.max_tokens,
            }
        )

    async def notify_elicitation_request(self, request: ElicitationRequest) -> None:
        """Elicitation 요청 알림 (SSE 브로드캐스트)

        Args:
            request: ElicitationRequest 엔티티
        """
        await self._broker.broadcast(
            event_type="elicitation_request",
            data={
                "request_id": request.id,
                "endpoint_id": request.endpoint_id,
                "message": request.message,
                "requested_schema": request.requested_schema,
            }
        )
```

### 테스트 (Integration)

```python
# tests/integration/test_hitl_notification_adapter.py

import pytest
from src.adapters.outbound.sse.hitl_notification_adapter import HitlNotificationAdapter
from src.domain.entities.sampling_request import SamplingRequest

class TestHitlNotificationAdapter:
    async def test_notify_sampling_request_broadcasts(self, fake_sse_broker):
        """notify_sampling_request() - SSE 브로드캐스트"""
        adapter = HitlNotificationAdapter(sse_broker=fake_sse_broker)
        request = SamplingRequest(
            id="req-1",
            endpoint_id="ep-1",
            messages=[{"role": "user", "content": "test"}]
        )

        await adapter.notify_sampling_request(request)

        # FakeSseBroker의 브로드캐스트 호출 확인
        assert len(fake_sse_broker.broadcasted_events) == 1
        event = fake_sse_broker.broadcasted_events[0]
        assert event["type"] == "sampling_request"
        assert event["data"]["request_id"] == "req-1"
```

---

## Step 4.4: AdkOrchestratorAdapter.generate_response() 구현

**파일:** `src/adapters/outbound/adk/orchestrator_adapter.py` (기존 파일 확장)
**테스트:** `tests/integration/test_orchestrator_generate.py`

### 추가 메서드

```python
# src/adapters/outbound/adk/orchestrator_adapter.py에 추가

import litellm

class AdkOrchestratorAdapter(OrchestratorPort):
    # ... 기존 process_message() 등 ...

    async def generate_response(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        system_prompt: str | None = None,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        """단일 LLM 응답 생성 (Sampling 콜백용)

        ADK Runner를 우회하고 litellm.acompletion()을 직접 호출합니다.
        이는 Sampling HITL에서 단일 LLM 호출이 필요하기 때문입니다.

        Args:
            messages: 메시지 목록 [{"role": "user", "content": "..."}]
            model: 모델 이름 (optional, 기본값: self._model_name)
            system_prompt: 시스템 프롬프트 (optional)
            max_tokens: 최대 토큰 수

        Returns:
            {"role": "assistant", "content": "...", "model": "..."}
        """
        litellm_messages = []
        if system_prompt:
            litellm_messages.append({"role": "system", "content": system_prompt})
        litellm_messages.extend(messages)

        response = await litellm.acompletion(
            model=model or self._model_name,
            messages=litellm_messages,
            max_tokens=max_tokens,
        )

        return {
            "role": "assistant",
            "content": response.choices[0].message.content,
            "model": response.model,
        }
```

### 테스트 (Integration - LLM 호출)

```python
# tests/integration/test_orchestrator_generate.py

import pytest
from src.adapters.outbound.adk.orchestrator_adapter import AdkOrchestratorAdapter

@pytest.mark.llm  # 실제 LLM 호출
class TestOrchestratorGenerate:
    async def test_generate_response_returns_llm_result(self, orchestrator_adapter):
        """generate_response() - 단일 LLM 응답"""
        messages = [{"role": "user", "content": "Say hello"}]

        result = await orchestrator_adapter.generate_response(
            messages=messages,
            max_tokens=50
        )

        assert result["role"] == "assistant"
        assert len(result["content"]) > 0
        assert "model" in result

    async def test_generate_response_with_system_prompt(self, orchestrator_adapter):
        """generate_response() - system_prompt 적용"""
        messages = [{"role": "user", "content": "What is 2+2?"}]

        result = await orchestrator_adapter.generate_response(
            messages=messages,
            system_prompt="You are a math tutor. Answer concisely.",
            max_tokens=50
        )

        assert "4" in result["content"]
```

---

## Step 4.5: Synapse 통합 테스트 (신규 - 핵심)

**파일:** `tests/integration/test_mcp_client_adapter.py`
**마커:** `@pytest.mark.local_mcp`

### Synapse 실행 전제

```bash
# Synapse localhost:9000에서 실행 중이어야 함
# tests/README.md 참고
```

### 테스트 시나리오

```python
import pytest
from src.adapters.outbound.mcp.mcp_client_adapter import McpClientAdapter
from src.domain.exceptions import EndpointNotFoundError

@pytest.mark.local_mcp  # 로컬 MCP 서버 필요
class TestMcpClientAdapter:
    """McpClientAdapter Integration 테스트

    Note: 실제 MCP 서버(Synapse)가 필요합니다.
    테스트 실행: pytest -m local_mcp
    """

    @pytest.fixture
    async def adapter(self):
        adapter = McpClientAdapter()
        yield adapter
        await adapter.disconnect_all()

    @pytest.fixture
    def synapse_url(self):
        return "http://localhost:9000/mcp"  # Synapse Streamable HTTP

    async def test_connect_and_list_resources(self, adapter, synapse_url):
        """연결 후 리소스 목록 조회"""
        await adapter.connect("synapse", synapse_url)

        resources = await adapter.list_resources("synapse")

        assert isinstance(resources, list)
        # Synapse는 최소 1개 이상의 리소스 제공
        assert len(resources) > 0
        assert all(hasattr(r, 'uri') for r in resources)

    async def test_read_resource_returns_content(self, adapter, synapse_url):
        """리소스 읽기 성공"""
        await adapter.connect("synapse", synapse_url)
        resources = await adapter.list_resources("synapse")
        test_uri = resources[0].uri  # 첫 번째 리소스

        content = await adapter.read_resource("synapse", test_uri)

        assert content.uri == test_uri
        assert (content.text is not None) or (content.blob is not None)

    async def test_list_prompts_returns_templates(self, adapter, synapse_url):
        """프롬프트 목록 조회"""
        await adapter.connect("synapse", synapse_url)

        prompts = await adapter.list_prompts("synapse")

        assert isinstance(prompts, list)
        # Synapse는 summarize 등 프롬프트 제공
        assert len(prompts) > 0
        assert all(hasattr(p, 'name') for p in prompts)

    async def test_get_prompt_renders(self, adapter, synapse_url):
        """프롬프트 렌더링"""
        await adapter.connect("synapse", synapse_url)
        prompts = await adapter.list_prompts("synapse")
        test_prompt_name = prompts[0].name

        result = await adapter.get_prompt("synapse", test_prompt_name, {})

        assert isinstance(result, str)
        assert len(result) > 0

    async def test_disconnect_cleans_up_session(self, adapter, synapse_url):
        """disconnect 후 세션 정리"""
        await adapter.connect("synapse", synapse_url)
        await adapter.disconnect("synapse")

        with pytest.raises(EndpointNotFoundError):
            await adapter.list_resources("synapse")

    async def test_disconnect_all_cleans_everything(self, adapter, synapse_url):
        """disconnect_all 후 모든 세션 정리"""
        await adapter.connect("synapse-1", synapse_url)
        await adapter.connect("synapse-2", synapse_url)

        await adapter.disconnect_all()

        with pytest.raises(EndpointNotFoundError):
            await adapter.list_resources("synapse-1")
        with pytest.raises(EndpointNotFoundError):
            await adapter.list_resources("synapse-2")

    # Sampling 콜백 테스트는 Phase 5에서 수행 (callback 설정 필요)
```

**주의사항:**
- Synapse Streamable HTTP에서 sampling 콜백 테스트는 Phase 5에서 수행 (RegistryService가 콜백을 생성하므로)
- Synapse가 sampling 요청 시 hang되는지 확인 필요 (이전 검증에서 발견된 위험)

---

## Verification

```bash
# Phase 1-3 Unit Tests (복습)
pytest tests/unit/ -q --tb=line -x

# Phase 4 Integration Tests (Synapse 필요)
pytest tests/integration/test_mcp_client_adapter.py -m local_mcp -v

# Phase 4 Integration Tests (LLM API 키 필요)
pytest tests/integration/test_orchestrator_generate.py -m llm -v

# Phase 4 모든 통합 테스트 (Synapse + LLM)
pytest tests/integration/ -m "local_mcp or llm" -v
```

---

## Step 4.6: Documentation Update

**목표:** Phase 4에서 구현된 Adapter 및 SDK Track 통합 문서화

**문서화 항목:**

| 작업 | 대상 파일 | 유형 | 내용 |
|------|----------|------|------|
| Create | src/adapters/outbound/mcp/README.md | Component README | McpClientAdapter 개요 (MCP SDK v1.25+, Streamable HTTP, AsyncExitStack 생명주기) |
| Create | src/adapters/outbound/sse/README.md | Component README | SseBroker + HitlNotificationAdapter 개요 (pub/sub 패턴, HITL 알림) |
| Modify | docs/developers/architecture/layer/adapters/README.md | Architecture | SDK Track Adapter 섹션 추가 (McpClientAdapter, 콜백 변환 로직) |
| Modify | docs/developers/architecture/layer/adapters/README.md | Architecture | SSE Adapter 섹션 추가 (SseBroker, HitlNotificationAdapter) |
| Create | docs/developers/guides/standards/mcp/streamable-http.md | Integration Guide | MCP Streamable HTTP 연결 가이드 (AsyncExitStack, Synapse 테스트) |
| Modify | tests/docs/RESOURCES.md | Test Resources | Synapse MCP 서버 정보 추가 (localhost:9000/mcp, 테스트 마커 local_mcp) |
| Modify | docs/MAP.md | Directory Structure | src/adapters/outbound/mcp/, src/adapters/outbound/sse/ 폴더 추가 반영 |

**ADR 참조:**
- [ADR-A07 (Dual-Track Architecture)](../../decisions/architecture/ADR-A07-dual-track-architecture.md)

**주의사항:**
- README.md는 ToC + 빠른 시작 (각 파일 400줄 이하 권장)
- 콜백 변환 로직 상세 설명 (Domain Protocol → MCP SDK 타입)
- Synapse hang 위험 명시 (timeout 필수)

---

## Checklist

- [ ] **Baseline 회귀 테스트**: `pytest -q --tb=line` (Phase 시작 전 Green 상태 확인)
- [ ] **Phase 시작**: Status 변경 (⏸️ → 🔄)
- [ ] Step 4.1: pyproject.toml에 mcp 의존성 추가
- [ ] Step 4.2: McpClientAdapter 구현 (콜백 변환, AsyncExitStack)
- [ ] Step 4.3: HitlNotificationAdapter 구현 (SSE 브로드캐스트)
- [ ] Step 4.4: AdkOrchestratorAdapter.generate_response() 추가
- [ ] Step 4.5: Synapse 통합 테스트 작성 및 통과
- [ ] Step 4.6: Documentation Update (Component READMEs + Architecture + Integration Guides)
- [ ] `src/adapters/outbound/mcp/__init__.py` 생성
- [ ] `src/adapters/outbound/sse/__init__.py` 생성
- [ ] **Phase 완료**: Status 변경 (🔄 → ✅)
- [ ] Git 커밋: `docs: complete phase N - {phase_name}`

---

*Last Updated: 2026-02-07*
*Synapse Streamable HTTP: localhost:9000/mcp*
