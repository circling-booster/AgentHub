# Phase 2: Port Interface + Fake

## 개요

Port Interface와 테스트용 Fake를 함께 작성합니다. Phase 3에서 Domain Services 테스트 시 필요하므로 여기서 함께 구현합니다.

**TDD Required:** ✅ Fake 구현 전 테스트 먼저 작성

---

## Step 2.1: McpClientPort

**파일:** `src/domain/ports/outbound/mcp_client_port.py`

### 콜백 타입 정의 (Domain Layer - 순수 Python)

MCP SDK의 콜백 프로토콜을 Domain에서 추상화합니다:

```python
from typing import Protocol, Any

class SamplingCallback(Protocol):
    """Sampling 콜백 프로토콜 (Domain 추상화)

    MCP SDK의 SamplingFnT를 Domain에서 사용 가능하게 추상화합니다.
    Adapter에서 MCP SDK 타입으로 변환합니다.
    """
    async def __call__(
        self,
        request_id: str,
        endpoint_id: str,
        messages: list[dict[str, Any]],
        model_preferences: dict[str, Any] | None,
        system_prompt: str | None,
        max_tokens: int,
    ) -> dict[str, Any]: ...

class ElicitationCallback(Protocol):
    """Elicitation 콜백 프로토콜 (Domain 추상화)"""
    async def __call__(
        self,
        request_id: str,
        endpoint_id: str,
        message: str,
        requested_schema: dict[str, Any],
    ) -> dict[str, Any]: ...
```

### Port Interface

```python
from abc import ABC, abstractmethod
from src.domain.entities.resource import Resource, ResourceContent
from src.domain.entities.prompt_template import PromptTemplate

class McpClientPort(ABC):
    """MCP SDK 기반 클라이언트 포트 - Resources/Prompts/HITL용

    Note: 콜백은 Domain 타입을 사용합니다. Adapter에서 MCP SDK 타입으로 변환합니다.
    """

    @abstractmethod
    async def connect(
        self,
        endpoint_id: str,
        url: str,
        sampling_callback: SamplingCallback | None = None,
        elicitation_callback: ElicitationCallback | None = None,
    ) -> None: ...

    @abstractmethod
    async def disconnect(self, endpoint_id: str) -> None: ...

    @abstractmethod
    async def disconnect_all(self) -> None: ...

    @abstractmethod
    async def list_resources(self, endpoint_id: str) -> list[Resource]: ...

    @abstractmethod
    async def read_resource(self, endpoint_id: str, uri: str) -> ResourceContent: ...

    @abstractmethod
    async def list_prompts(self, endpoint_id: str) -> list[PromptTemplate]: ...

    @abstractmethod
    async def get_prompt(self, endpoint_id: str, name: str, arguments: dict | None) -> str: ...
```

---

## Step 2.2: HitlNotificationPort (신규)

**파일:** `src/domain/ports/outbound/hitl_notification_port.py`

**목적:** HITL timeout 시 SSE/Extension에 알림 전송. Domain은 알림 방법을 알 필요 없음.

```python
from abc import ABC, abstractmethod
from src.domain.entities.sampling_request import SamplingRequest
from src.domain.entities.elicitation_request import ElicitationRequest

class HitlNotificationPort(ABC):
    """HITL 요청 알림 포트

    HITL timeout 시 Extension으로 알림을 전송합니다.
    Domain은 알림 메커니즘(SSE, WebSocket 등)을 알 필요 없습니다.
    """

    @abstractmethod
    async def notify_sampling_request(self, request: SamplingRequest) -> None:
        """Sampling 요청 알림"""
        pass

    @abstractmethod
    async def notify_elicitation_request(self, request: ElicitationRequest) -> None:
        """Elicitation 요청 알림"""
        pass
```

---

## Step 2.3: OrchestratorPort.generate_response() 추가

**파일:** `src/domain/ports/outbound/orchestrator_port.py` (기존 파일 확장)

### 추가할 메서드

```python
@abstractmethod
async def generate_response(
    self,
    messages: list[dict[str, Any]],
    model: str | None = None,
    system_prompt: str | None = None,
    max_tokens: int = 1024,
) -> dict[str, Any]:
    """단일 LLM 응답 생성 (Sampling 콜백용)

    기존 process_message()와 별도:
    - process_message: ADK Runner 기반 스트리밍 (Tool Call Loop 자동)
    - generate_response: 단일 LLM 호출 (Sampling HITL 승인 시 사용)

    Args:
        messages: LLM 메시지 목록 [{"role": "user", "content": "..."}]
        model: 모델 이름 (None이면 기본 모델)
        system_prompt: 시스템 프롬프트 (선택)
        max_tokens: 최대 토큰 수

    Returns:
        {"role": "assistant", "content": "...", "model": "..."}
    """
    pass
```

---

## Step 2.4: FakeMcpClient

**테스트 먼저:** `tests/unit/fakes/test_fake_mcp_client.py`
**구현:** `tests/unit/fakes/fake_mcp_client.py`

### 테스트 시나리오

```python
# tests/unit/fakes/test_fake_mcp_client.py

import pytest
from src.domain.entities.resource import Resource, ResourceContent
from src.domain.entities.prompt_template import PromptTemplate
from src.domain.exceptions import EndpointNotFoundError, ResourceNotFoundError
from tests.unit.fakes.fake_mcp_client import FakeMcpClient

class TestFakeMcpClient:
    """FakeMcpClient 자체 테스트"""

    async def test_connect_stores_connection(self):
        """connect 후 is_connected True"""
        fake = FakeMcpClient()
        await fake.connect("ep-1", "http://localhost:8080/mcp")
        assert fake.is_connected("ep-1")

    async def test_disconnect_removes_connection(self):
        """disconnect 후 is_connected False"""
        fake = FakeMcpClient()
        await fake.connect("ep-1", "http://localhost:8080/mcp")
        await fake.disconnect("ep-1")
        assert not fake.is_connected("ep-1")

    async def test_disconnect_all_removes_all_connections(self):
        """disconnect_all 후 모든 연결 해제"""
        fake = FakeMcpClient()
        await fake.connect("ep-1", "http://localhost:8080/mcp")
        await fake.connect("ep-2", "http://localhost:9000/mcp")
        await fake.disconnect_all()
        assert not fake.is_connected("ep-1")
        assert not fake.is_connected("ep-2")

    async def test_list_resources_returns_preset(self):
        """set_resources로 설정한 리소스 반환"""
        fake = FakeMcpClient()
        resources = [Resource(uri="file:///test.txt", name="test")]
        fake.set_resources("ep-1", resources)

        await fake.connect("ep-1", "http://localhost:8080/mcp")
        result = await fake.list_resources("ep-1")

        assert result == resources

    async def test_list_resources_raises_when_not_connected(self):
        """연결 안 된 상태에서 list_resources → 예외"""
        fake = FakeMcpClient()
        with pytest.raises(EndpointNotFoundError):
            await fake.list_resources("ep-1")

    async def test_read_resource_returns_content(self):
        """set_resource_content로 설정한 콘텐츠 반환"""
        fake = FakeMcpClient()
        content = ResourceContent(uri="file:///test.txt", text="Hello")
        fake.set_resource_content("ep-1", "file:///test.txt", content)

        await fake.connect("ep-1", "http://localhost:8080/mcp")
        result = await fake.read_resource("ep-1", "file:///test.txt")

        assert result.text == "Hello"

    async def test_list_prompts_returns_preset(self):
        """set_prompts로 설정한 프롬프트 반환"""
        fake = FakeMcpClient()
        prompts = [PromptTemplate(name="greeting", description="Say hello")]
        fake.set_prompts("ep-1", prompts)

        await fake.connect("ep-1", "http://localhost:8080/mcp")
        result = await fake.list_prompts("ep-1")

        assert len(result) == 1
        assert result[0].name == "greeting"

    async def test_get_prompt_renders_template(self):
        """set_prompt_result로 설정한 결과 반환"""
        fake = FakeMcpClient()
        fake.set_prompt_result("ep-1", "greeting", "Hello, Alice!")

        await fake.connect("ep-1", "http://localhost:8080/mcp")
        result = await fake.get_prompt("ep-1", "greeting", {"name": "Alice"})

        assert result == "Hello, Alice!"

    async def test_callback_stored_on_connect(self):
        """콜백이 connect 시 저장됨"""
        fake = FakeMcpClient()

        async def sample_callback(**kwargs):
            return {"role": "assistant", "content": "test"}

        await fake.connect("ep-1", "http://localhost:8080/mcp", sampling_callback=sample_callback)
        stored = fake.get_sampling_callback("ep-1")

        assert stored is sample_callback
```

### Fake 구현

```python
# tests/unit/fakes/fake_mcp_client.py

"""FakeMcpClient - 테스트용 MCP Client Fake

시나리오 기반 응답을 설정할 수 있습니다.
"""

from src.domain.ports.outbound.mcp_client_port import (
    McpClientPort,
    SamplingCallback,
    ElicitationCallback,
)
from src.domain.entities.resource import Resource, ResourceContent
from src.domain.entities.prompt_template import PromptTemplate
from src.domain.exceptions import (
    EndpointNotFoundError,
    ResourceNotFoundError,
    PromptNotFoundError,
)


class FakeMcpClient(McpClientPort):
    """테스트용 MCP Client Fake

    시나리오 기반 응답을 설정할 수 있습니다.
    """

    def __init__(self) -> None:
        self._connections: dict[str, bool] = {}
        self._resources: dict[str, list[Resource]] = {}
        self._resource_contents: dict[str, dict[str, ResourceContent]] = {}
        self._prompts: dict[str, list[PromptTemplate]] = {}
        self._prompt_results: dict[str, dict[str, str]] = {}
        self._sampling_callbacks: dict[str, SamplingCallback] = {}
        self._elicitation_callbacks: dict[str, ElicitationCallback] = {}

    # ============================================================
    # 테스트 설정 메서드
    # ============================================================

    def set_resources(self, endpoint_id: str, resources: list[Resource]) -> None:
        """엔드포인트의 리소스 목록 설정"""
        self._resources[endpoint_id] = resources

    def set_resource_content(
        self, endpoint_id: str, uri: str, content: ResourceContent
    ) -> None:
        """특정 리소스의 콘텐츠 설정"""
        if endpoint_id not in self._resource_contents:
            self._resource_contents[endpoint_id] = {}
        self._resource_contents[endpoint_id][uri] = content

    def set_prompts(self, endpoint_id: str, prompts: list[PromptTemplate]) -> None:
        """엔드포인트의 프롬프트 목록 설정"""
        self._prompts[endpoint_id] = prompts

    def set_prompt_result(self, endpoint_id: str, name: str, result: str) -> None:
        """특정 프롬프트의 렌더링 결과 설정"""
        if endpoint_id not in self._prompt_results:
            self._prompt_results[endpoint_id] = {}
        self._prompt_results[endpoint_id][name] = result

    def is_connected(self, endpoint_id: str) -> bool:
        """연결 상태 확인 (테스트 검증용)"""
        return self._connections.get(endpoint_id, False)

    def get_sampling_callback(self, endpoint_id: str) -> SamplingCallback | None:
        """저장된 sampling 콜백 반환 (테스트 검증용)"""
        return self._sampling_callbacks.get(endpoint_id)

    def get_elicitation_callback(self, endpoint_id: str) -> ElicitationCallback | None:
        """저장된 elicitation 콜백 반환 (테스트 검증용)"""
        return self._elicitation_callbacks.get(endpoint_id)

    def reset(self) -> None:
        """모든 상태 초기화 (테스트 간 격리)"""
        self._connections.clear()
        self._resources.clear()
        self._resource_contents.clear()
        self._prompts.clear()
        self._prompt_results.clear()
        self._sampling_callbacks.clear()
        self._elicitation_callbacks.clear()

    # ============================================================
    # Port 구현
    # ============================================================

    async def connect(
        self,
        endpoint_id: str,
        url: str,
        sampling_callback: SamplingCallback | None = None,
        elicitation_callback: ElicitationCallback | None = None,
    ) -> None:
        self._connections[endpoint_id] = True
        if sampling_callback:
            self._sampling_callbacks[endpoint_id] = sampling_callback
        if elicitation_callback:
            self._elicitation_callbacks[endpoint_id] = elicitation_callback

    async def disconnect(self, endpoint_id: str) -> None:
        self._connections.pop(endpoint_id, None)
        self._sampling_callbacks.pop(endpoint_id, None)
        self._elicitation_callbacks.pop(endpoint_id, None)

    async def disconnect_all(self) -> None:
        """모든 세션 정리 (서버 종료 시)"""
        self._connections.clear()
        self._sampling_callbacks.clear()
        self._elicitation_callbacks.clear()

    async def list_resources(self, endpoint_id: str) -> list[Resource]:
        if not self._connections.get(endpoint_id):
            raise EndpointNotFoundError(f"Not connected: {endpoint_id}")
        return self._resources.get(endpoint_id, [])

    async def read_resource(self, endpoint_id: str, uri: str) -> ResourceContent:
        if not self._connections.get(endpoint_id):
            raise EndpointNotFoundError(f"Not connected: {endpoint_id}")
        contents = self._resource_contents.get(endpoint_id, {})
        if uri not in contents:
            raise ResourceNotFoundError(f"Resource not found: {uri}")
        return contents[uri]

    async def list_prompts(self, endpoint_id: str) -> list[PromptTemplate]:
        if not self._connections.get(endpoint_id):
            raise EndpointNotFoundError(f"Not connected: {endpoint_id}")
        return self._prompts.get(endpoint_id, [])

    async def get_prompt(
        self, endpoint_id: str, name: str, arguments: dict | None
    ) -> str:
        if not self._connections.get(endpoint_id):
            raise EndpointNotFoundError(f"Not connected: {endpoint_id}")
        results = self._prompt_results.get(endpoint_id, {})
        if name not in results:
            raise PromptNotFoundError(f"Prompt not found: {name}")
        return results[name]
```

---

## Step 2.5: FakeHitlNotification

**테스트 먼저:** `tests/unit/fakes/test_fake_hitl_notification.py`
**구현:** `tests/unit/fakes/fake_hitl_notification.py`

### 테스트 시나리오

```python
# tests/unit/fakes/test_fake_hitl_notification.py

from src.domain.entities.sampling_request import SamplingRequest, SamplingStatus
from src.domain.entities.elicitation_request import ElicitationRequest, ElicitationStatus
from tests.unit.fakes.fake_hitl_notification import FakeHitlNotification

class TestFakeHitlNotification:
    async def test_notify_sampling_request_records_call(self):
        """Sampling 알림 호출 기록"""
        fake = FakeHitlNotification()
        request = SamplingRequest(
            id="req-123",
            endpoint_id="ep-1",
            messages=[],
        )

        await fake.notify_sampling_request(request)

        assert len(fake.sampling_notifications) == 1
        assert fake.sampling_notifications[0].id == "req-123"

    async def test_notify_elicitation_request_records_call(self):
        """Elicitation 알림 호출 기록"""
        fake = FakeHitlNotification()
        request = ElicitationRequest(
            id="req-456",
            endpoint_id="ep-1",
            message="Enter API key",
            requested_schema={},
        )

        await fake.notify_elicitation_request(request)

        assert len(fake.elicitation_notifications) == 1
        assert fake.elicitation_notifications[0].id == "req-456"
```

### Fake 구현

```python
# tests/unit/fakes/fake_hitl_notification.py

"""FakeHitlNotification - 테스트용 HITL 알림 Fake"""

from src.domain.ports.outbound.hitl_notification_port import HitlNotificationPort
from src.domain.entities.sampling_request import SamplingRequest
from src.domain.entities.elicitation_request import ElicitationRequest


class FakeHitlNotification(HitlNotificationPort):
    """테스트용 HITL Notification Fake

    알림 호출을 기록하여 검증할 수 있습니다.
    """

    def __init__(self) -> None:
        self.sampling_notifications: list[SamplingRequest] = []
        self.elicitation_notifications: list[ElicitationRequest] = []

    async def notify_sampling_request(self, request: SamplingRequest) -> None:
        """Sampling 요청 알림 기록"""
        self.sampling_notifications.append(request)

    async def notify_elicitation_request(self, request: ElicitationRequest) -> None:
        """Elicitation 요청 알림 기록"""
        self.elicitation_notifications.append(request)

    def reset(self) -> None:
        """모든 기록 초기화 (테스트 간 격리)"""
        self.sampling_notifications.clear()
        self.elicitation_notifications.clear()
```

---

## Step 2.6: FakeOrchestrator 확장

**파일:** `tests/unit/fakes/fake_orchestrator.py` (기존 파일 확장)

### 추가할 메서드

```python
# tests/unit/fakes/fake_orchestrator.py에 추가

class FakeOrchestrator(OrchestratorPort):
    def __init__(self):
        # ... 기존 코드 ...
        self._generate_result: dict[str, Any] = {
            "role": "assistant",
            "content": "Fake LLM response",
            "model": "fake-model",
        }

    def set_generate_result(self, result: dict[str, Any]) -> None:
        """generate_response 결과 설정 (테스트용)"""
        self._generate_result = result

    async def generate_response(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        system_prompt: str | None = None,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        """단일 LLM 응답 생성 (Fake)"""
        return self._generate_result
```

### 테스트 시나리오

```python
# tests/unit/fakes/test_fake_orchestrator.py에 추가

async def test_generate_response_returns_preset(fake_orchestrator):
    """generate_response가 설정된 결과 반환"""
    fake_orchestrator.set_generate_result({
        "role": "assistant",
        "content": "Custom response",
        "model": "gpt-4",
    })

    result = await fake_orchestrator.generate_response(
        messages=[{"role": "user", "content": "test"}]
    )

    assert result["content"] == "Custom response"
    assert result["model"] == "gpt-4"
```

---

## Step 2.7: EventBroadcastPort (SSE Broker 추상화)

**파일:** `src/domain/ports/outbound/event_broadcast_port.py`

### Port Interface

```python
# src/domain/ports/outbound/event_broadcast_port.py
"""Event Broadcasting Port (SSE 추상화)

HITL 알림을 Extension에 전달하기 위한 SSE Broker 추상화입니다.
"""

from typing import Protocol, AsyncIterator, Any


class EventBroadcastPort(Protocol):
    """Event Broadcasting Port (Domain 추상화)

    SSE를 통해 클라이언트에게 이벤트를 브로드캐스트합니다.
    Adapter 레이어에서 asyncio.Queue 기반 pub/sub으로 구현됩니다.
    """

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """이벤트를 모든 구독자에게 브로드캐스트

        Args:
            event_type: 이벤트 타입 (예: "sampling_request", "elicitation_request")
            data: 이벤트 데이터
        """
        ...

    async def subscribe(self) -> AsyncIterator[dict[str, Any]]:
        """이벤트 스트림 구독

        Yields:
            이벤트 딕셔너리 {"type": str, "data": dict}
        """
        ...
```

---

## Step 2.8: FakeSseBroker (테스트용)

**파일:** `tests/unit/fakes/fake_sse_broker.py`

**테스트 먼저 작성:** `tests/unit/fakes/test_fake_sse_broker.py`

### 테스트 시나리오

```python
# tests/unit/fakes/test_fake_sse_broker.py

import pytest
from tests.unit.fakes.fake_sse_broker import FakeSseBroker


class TestFakeSseBroker:
    @pytest.fixture
    def broker(self):
        return FakeSseBroker()

    async def test_broadcast_appends_to_history(self, broker):
        """broadcast가 이벤트를 히스토리에 추가"""
        await broker.broadcast("test_event", {"key": "value"})

        assert len(broker.broadcasted_events) == 1
        assert broker.broadcasted_events[0]["type"] == "test_event"
        assert broker.broadcasted_events[0]["data"] == {"key": "value"}

    async def test_get_events_by_type_filters(self, broker):
        """get_events_by_type이 타입별로 필터링"""
        await broker.broadcast("event_a", {"msg": "A"})
        await broker.broadcast("event_b", {"msg": "B"})
        await broker.broadcast("event_a", {"msg": "A2"})

        events_a = broker.get_events_by_type("event_a")
        assert len(events_a) == 2
        assert all(e["type"] == "event_a" for e in events_a)

    async def test_clear_events_empties_history(self, broker):
        """clear_events가 히스토리 초기화"""
        await broker.broadcast("test", {"data": 1})
        broker.clear_events()

        assert len(broker.broadcasted_events) == 0
```

### Fake 구현

```python
# tests/unit/fakes/fake_sse_broker.py

from typing import AsyncIterator, Any


class FakeSseBroker:
    """SSE Broker Fake (테스트용)

    실제 asyncio.Queue 대신 메모리에 이벤트를 저장합니다.
    subscribe()는 구현하지 않습니다 (테스트 불필요).
    """

    def __init__(self):
        self.broadcasted_events: list[dict[str, Any]] = []

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """이벤트를 히스토리에 추가"""
        self.broadcasted_events.append({"type": event_type, "data": data})

    def get_events_by_type(self, event_type: str) -> list[dict[str, Any]]:
        """특정 타입의 이벤트만 필터링 (테스트용)"""
        return [e for e in self.broadcasted_events if e["type"] == event_type]

    def clear_events(self) -> None:
        """이벤트 히스토리 초기화 (테스트 간 격리)"""
        self.broadcasted_events.clear()

    async def subscribe(self) -> AsyncIterator[dict[str, Any]]:
        """구독 (Fake에서는 미사용)"""
        # Fake에서는 subscribe 불필요 (테스트 시 broadcast만 검증)
        raise NotImplementedError("FakeSseBroker does not implement subscribe")
```

---

## Verification

```bash
# Phase 2 테스트
pytest tests/unit/fakes/ -v
```

---

## Step 2.9: Documentation Update

**목표:** Phase 2에서 추가된 Port 및 Fake Adapter 문서화

**문서화 항목:**

| 작업 | 대상 파일 | 유형 | 내용 |
|------|----------|------|------|
| Modify | docs/developers/architecture/layer/ports/README.md | Architecture | McpClientPort 섹션 추가 (SDK Track 전용 포트) |
| Modify | docs/developers/architecture/layer/ports/README.md | Architecture | HitlNotificationPort 섹션 추가 (SSE 알림 추상화) |
| Modify | docs/developers/architecture/layer/ports/README.md | Architecture | EventBroadcastPort 섹션 추가 (pub/sub 패턴) |
| Modify | tests/docs/STRATEGY.md | Test Documentation | Fake Adapter 작성 패턴 섹션에 FakeMcpClient 예시 추가 |
| Modify | tests/docs/WritingGuide.md | Test Documentation | 콜백 테스트 레시피 추가 (SamplingCallback, ElicitationCallback) |

**주의사항:**
- Domain 콜백 타입 vs MCP SDK 콜백 타입 변환 로직은 Phase 4 Adapter 문서에서 설명
- Protocol 타입 사용 이유 명시 (Duck Typing for Domain Purity)

---

## Checklist

- [ ] **Baseline 회귀 테스트**: `pytest -q --tb=line` (Phase 시작 전 Green 상태 확인)
- [ ] **Phase 시작**: Status 변경 (⏸️ → 🔄)
- [ ] Step 2.1: McpClientPort 생성
- [ ] Step 2.2: HitlNotificationPort 생성
- [ ] Step 2.3: OrchestratorPort.generate_response() 추가
- [ ] Step 2.4: FakeMcpClient (TDD)
- [ ] Step 2.5: FakeHitlNotification (TDD)
- [ ] Step 2.6: FakeOrchestrator 확장 (TDD)
- [ ] Step 2.7: EventBroadcastPort 생성
- [ ] Step 2.8: FakeSseBroker (TDD)
- [ ] Step 2.9: Documentation Update (Ports + Test Docs)
- [ ] **회귀 테스트**: `pytest --cov=src --cov-fail-under=80 -q` (Phase 완료 후 검증)
- [ ] **Phase 완료**: Status 변경 (🔄 → ✅)
- [ ] Git 커밋: `docs: complete phase N - {phase_name}`
---

*Last Updated: 2026-02-07*
*Principle: TDD (Red → Green → Refactor), Fake Adapters (no mocking)*
