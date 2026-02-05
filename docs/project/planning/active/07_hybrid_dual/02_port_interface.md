# Phase 2: Port Interface + Fake

## 개요

Port Interface와 테스트용 Fake를 함께 작성합니다.
Phase 3에서 Domain Services 테스트 시 FakeMcpClient가 필요하므로 여기서 함께 구현합니다.

---

## Step 2.1: McpClientPort 생성

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
    async def list_resources(self, endpoint_id: str) -> list[Resource]: ...

    @abstractmethod
    async def read_resource(self, endpoint_id: str, uri: str) -> ResourceContent: ...

    @abstractmethod
    async def list_prompts(self, endpoint_id: str) -> list[PromptTemplate]: ...

    @abstractmethod
    async def get_prompt(self, endpoint_id: str, name: str, arguments: dict | None) -> str: ...
```

---

## Step 2.2: FakeMcpClient 구현 (TDD)

**테스트 먼저:** `tests/unit/fakes/test_fake_mcp_client.py`
**구현:** `tests/unit/fakes/fake_mcp_client.py`

### 테스트 시나리오

```python
# tests/unit/fakes/test_fake_mcp_client.py

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

    async def test_get_prompt_renders_template(self):
        """set_prompt_result로 설정한 결과 반환"""
        fake = FakeMcpClient()
        fake.set_prompt_result("ep-1", "greeting", "Hello, Alice!")

        await fake.connect("ep-1", "http://localhost:8080/mcp")
        result = await fake.get_prompt("ep-1", "greeting", {"name": "Alice"})

        assert result == "Hello, Alice!"
```

### Fake 구현

```python
# tests/unit/fakes/fake_mcp_client.py

from src.domain.ports.outbound.mcp_client_port import (
    McpClientPort,
    SamplingCallback,
    ElicitationCallback,
)
from src.domain.entities.resource import Resource, ResourceContent
from src.domain.entities.prompt_template import PromptTemplate
from src.domain.exceptions import EndpointNotFoundError, ResourceNotFoundError

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

## 테스트 실행

```bash
# Phase 2 테스트
pytest tests/unit/fakes/test_fake_mcp_client.py -v
```

---

## Checklist

- [ ] `src/domain/ports/outbound/mcp_client_port.py` 생성
- [ ] `tests/unit/fakes/test_fake_mcp_client.py` 작성 (Red)
- [ ] `tests/unit/fakes/fake_mcp_client.py` 구현 (Green)
- [ ] 테스트 통과 확인
