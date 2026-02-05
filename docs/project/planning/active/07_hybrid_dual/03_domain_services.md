# Phase 3: Domain Services (TDD)

## 서비스 의존 관계

```
RegistryService (기존)
    └── McpClientPort (신규 주입)
            │
            ├── ResourceService ─┐
            ├── PromptService   ─┼── McpClientPort 위임
            │                    │
            ├── SamplingService ─┘   (HITL 큐 + 콜백 생성)
            └── ElicitationService   (HITL 큐 + 콜백 생성)
```

**핵심 원칙:**
- `ResourceService`, `PromptService`는 `McpClientPort`를 직접 주입받음
- `SamplingService`, `ElicitationService`는 Port 없이 인메모리 큐만 관리
- 콜백 생성은 `RegistryService`에서 담당 (Phase 5에서 연결)

---

## Step 3.1: ResourceService

**파일:** `src/domain/services/resource_service.py`
**테스트:** `tests/unit/domain/services/test_resource_service.py`

```python
class ResourceService:
    """MCP Resource 조회 서비스"""

    def __init__(self, mcp_client: McpClientPort) -> None:
        self._mcp_client = mcp_client

    async def list_resources(self, endpoint_id: str) -> list[Resource]:
        """엔드포인트의 리소스 목록 조회"""
        return await self._mcp_client.list_resources(endpoint_id)

    async def read_resource(self, endpoint_id: str, uri: str) -> ResourceContent:
        """리소스 콘텐츠 읽기"""
        return await self._mcp_client.read_resource(endpoint_id, uri)
```

**테스트 시나리오:**
1. `list_resources` - FakeMcpClient로 목록 반환 검증
2. `read_resource` - 텍스트/blob 콘텐츠 반환 검증
3. 존재하지 않는 endpoint_id → `EndpointNotFoundError`

---

## Step 3.2: PromptService

**파일:** `src/domain/services/prompt_service.py`
**테스트:** `tests/unit/domain/services/test_prompt_service.py`

```python
class PromptService:
    """MCP Prompt 템플릿 서비스"""

    def __init__(self, mcp_client: McpClientPort) -> None:
        self._mcp_client = mcp_client

    async def list_prompts(self, endpoint_id: str) -> list[PromptTemplate]:
        """엔드포인트의 프롬프트 목록 조회"""
        return await self._mcp_client.list_prompts(endpoint_id)

    async def get_prompt(
        self, endpoint_id: str, name: str, arguments: dict | None = None
    ) -> str:
        """프롬프트 렌더링"""
        return await self._mcp_client.get_prompt(endpoint_id, name, arguments)
```

**테스트 시나리오:**
1. `list_prompts` - 템플릿 목록 반환
2. `get_prompt` - arguments 적용된 렌더링 결과
3. 존재하지 않는 prompt → `PromptNotFoundError`

---

## Step 3.3: SamplingService (HITL 큐 관리)

**파일:** `src/domain/services/sampling_service.py`
**테스트:** `tests/unit/domain/services/test_sampling_service.py`

```python
class SamplingService:
    """Sampling HITL 요청 큐 관리

    Note: McpClientPort를 직접 사용하지 않음.
    RegistryService가 콜백을 생성하여 MCP SDK에 전달함.
    """

    def __init__(self, ttl_seconds: int = 600) -> None:
        self._requests: dict[str, SamplingRequest] = {}
        self._ttl_seconds = ttl_seconds
        self._events: dict[str, asyncio.Event] = {}

    async def create_request(self, request: SamplingRequest) -> None:
        """요청 생성 및 대기 이벤트 설정"""

    async def wait_for_response(
        self, request_id: str, timeout: float = 30.0
    ) -> SamplingRequest | None:
        """Long-polling 대기 (Hybrid 방식)"""

    async def approve(self, request_id: str, llm_result: dict) -> bool:
        """요청 승인 및 LLM 결과 설정"""

    async def reject(self, request_id: str, reason: str = "") -> bool:
        """요청 거부"""

    def list_pending(self) -> list[SamplingRequest]:
        """대기 중인 요청 목록"""

    async def cleanup_expired(self) -> int:
        """만료된 요청 정리 (TTL 기반)"""
```

**테스트 시나리오:**
1. `create_request` → `list_pending`에 포함
2. `wait_for_response` - 30초 내 approve 시 즉시 반환
3. `wait_for_response` - timeout 후 None 반환
4. `approve` → 상태 COMPLETED, 이벤트 signal
5. `reject` → 상태 REJECTED
6. `cleanup_expired` - TTL 초과 요청 제거

---

## Step 3.4: ElicitationService

**파일:** `src/domain/services/elicitation_service.py`
**테스트:** `tests/unit/domain/services/test_elicitation_service.py`

```python
class ElicitationService:
    """Elicitation HITL 요청 큐 관리

    Note: SamplingService와 동일한 패턴
    """

    async def create_request(self, request: ElicitationRequest) -> None: ...
    async def wait_for_response(self, request_id: str, timeout: float = 30.0) -> ElicitationRequest | None: ...
    async def respond(self, request_id: str, action: ElicitationAction, content: dict | None = None) -> bool: ...
    def list_pending(self) -> list[ElicitationRequest]: ...
    async def cleanup_expired(self) -> int: ...
```

**테스트 시나리오:**
1. `create_request` → `list_pending`에 포함
2. `respond(ACCEPT)` → 상태 전이, content 저장
3. `respond(DECLINE)` / `respond(CANCEL)` → 적절한 상태 전이
4. timeout 처리
