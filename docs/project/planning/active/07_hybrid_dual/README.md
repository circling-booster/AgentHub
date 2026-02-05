# Architecture C "Hybrid-Dual" Implementation Plan

## Overview

**목표:** ADK Track(MCP Tools + A2A)과 SDK Track(Resources/Prompts/Sampling/Elicitation)을 병행하는 Hybrid-Dual 아키텍처 구현

**현재 상태:**
- ADK Track: 작동 중 (DynamicToolset, GatewayToolset, RemoteA2aAgent)
- SDK Track: 삭제됨 (McpClientAdapter, SamplingService 등 복원 필요)

**핵심 원칙:**
- TDD (테스트 먼저 작성)
- 헥사고날 아키텍처 (Domain 레이어는 순수 Python)
- MCP SDK v1.25+ 사용 (`mcp>=1.25,<2`)

---

## Phase 1: Domain Entities (TDD)

### Step 1.1: 새 엔티티 생성

| 파일 | 목적 |
|------|------|
| `src/domain/entities/resource.py` | MCP Resource 메타데이터 |
| `src/domain/entities/resource_content.py` | Resource 콘텐츠 (text/blob) |
| `src/domain/entities/prompt_template.py` | Prompt 템플릿 + PromptArgument |
| `src/domain/entities/sampling_request.py` | Sampling HITL 요청 (상태머신) |
| `src/domain/entities/elicitation_request.py` | Elicitation HITL 요청 |

**테스트 파일 (먼저 작성):**
- `tests/unit/domain/entities/test_resource.py`
- `tests/unit/domain/entities/test_prompt_template.py`
- `tests/unit/domain/entities/test_sampling_request.py`
- `tests/unit/domain/entities/test_elicitation_request.py`

### Step 1.2: Enums 추가

**파일:** `src/domain/entities/enums.py` (기존 파일 수정)

```python
class SamplingStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    COMPLETED = "completed"
    REJECTED = "rejected"

class ElicitationAction(str, Enum):
    PENDING = "pending"
    ACCEPT = "accept"
    DECLINE = "decline"
    CANCEL = "cancel"
```

### Step 1.3: Exceptions 추가

**파일:** `src/domain/exceptions.py` (기존 파일 수정)

- `ResourceNotFoundError`
- `PromptNotFoundError`
- `SamplingNotFoundError`
- `ElicitationNotFoundError`
- `HitlTimeoutError`

---

## Phase 2: Port Interface

### Step 2.1: McpClientPort 생성

**파일:** `src/domain/ports/outbound/mcp_client_port.py`

```python
class McpClientPort(ABC):
    """MCP SDK 기반 클라이언트 포트 - Resources/Prompts/HITL용"""

    @abstractmethod
    async def connect(
        self,
        endpoint_id: str,
        url: str,
        sampling_callback: Callable[[dict], Awaitable[dict]] | None = None,
        elicitation_callback: Callable[[dict], Awaitable[dict]] | None = None,
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

**테스트:** `tests/unit/domain/ports/test_mcp_client_port.py`

---

## Phase 3: Domain Services (TDD)

### Step 3.1: ResourceService

**파일:** `src/domain/services/resource_service.py`
**테스트:** `tests/unit/domain/services/test_resource_service.py`

### Step 3.2: PromptService

**파일:** `src/domain/services/prompt_service.py`
**테스트:** `tests/unit/domain/services/test_prompt_service.py`

### Step 3.3: SamplingService (HITL 큐 관리)

**파일:** `src/domain/services/sampling_service.py`
**테스트:** `tests/unit/domain/services/test_sampling_service.py`

핵심 기능:
- 인메모리 요청 큐
- TTL 기반 자동 만료 (기본 10분)
- 승인/거부 상태 전이

### Step 3.4: ElicitationService

**파일:** `src/domain/services/elicitation_service.py`
**테스트:** `tests/unit/domain/services/test_elicitation_service.py`

---

## Phase 4: Adapter Implementation (TDD)

### Step 4.1: 의존성 추가

**파일:** `pyproject.toml`

```toml
"mcp>=1.25,<2",  # MCP Python SDK (v2 breaking changes 방지)
```

### Step 4.2: McpClientAdapter

**파일:** `src/adapters/outbound/mcp/mcp_client_adapter.py`
**테스트:** `tests/unit/adapters/test_mcp_client_adapter.py`

핵심 구현:
```python
async def connect(self, endpoint_id, url, sampling_callback, elicitation_callback):
    exit_stack = AsyncExitStack()
    read, write, _ = await exit_stack.enter_async_context(
        streamable_http_client(url)
    )
    session = await exit_stack.enter_async_context(
        ClientSession(
            read, write,
            sampling_callback=sampling_callback,      # 콜백 와이어링!
            elicitation_callback=elicitation_callback,  # 콜백 와이어링!
        )
    )
    await session.initialize()
```

### Step 4.3: FakeMcpClient (테스트용)

**파일:** `tests/unit/fakes/fake_mcp_client.py`

---

## Phase 5: Integration

### Step 5.1: RegistryService 수정

**파일:** `src/domain/services/registry_service.py`

변경사항:
1. 생성자에 `mcp_client: McpClientPort | None` 추가
2. MCP 등록 시 `mcp_client.connect()` 호출 (이중 연결)
3. 콜백 생성 및 전달

```python
async def register_endpoint(self, url, ...):
    if endpoint_type == EndpointType.MCP:
        # ADK Track (기존)
        tools = await self._toolset.add_mcp_server(endpoint)

        # SDK Track (신규 - 이중 연결)
        if self._mcp_client:
            sampling_cb = self._create_sampling_callback(endpoint.id)
            elicitation_cb = self._create_elicitation_callback(endpoint.id)
            await self._mcp_client.connect(
                endpoint.id, url, sampling_cb, elicitation_cb
            )
```

### Step 5.2: DI Container 수정

**파일:** `src/config/container.py`

추가할 Provider:
- `mcp_client_adapter = providers.Singleton(McpClientAdapter)`
- `sampling_service = providers.Factory(SamplingService, ...)`
- `elicitation_service = providers.Factory(ElicitationService, ...)`
- `resource_service = providers.Factory(ResourceService, ...)`
- `prompt_service = providers.Factory(PromptService, ...)`

RegistryService 수정:
- `mcp_client=mcp_client_adapter` 추가

---

## Phase 6: HTTP Routes (TDD)

### Step 6.1: Resources API

**파일:** `src/adapters/inbound/http/routes/resources.py`
**테스트:** `tests/integration/http/test_resources_routes.py`

| Endpoint | 설명 |
|----------|------|
| `GET /api/mcp/servers/{id}/resources` | 리소스 목록 |
| `GET /api/mcp/servers/{id}/resources/{uri}` | 리소스 읽기 |

### Step 6.2: Prompts API

**파일:** `src/adapters/inbound/http/routes/prompts.py`
**테스트:** `tests/integration/http/test_prompts_routes.py`

| Endpoint | 설명 |
|----------|------|
| `GET /api/mcp/servers/{id}/prompts` | 프롬프트 목록 |
| `POST /api/mcp/servers/{id}/prompts/{name}` | 프롬프트 렌더링 |

### Step 6.3: Sampling HITL API

**파일:** `src/adapters/inbound/http/routes/sampling.py`
**테스트:** `tests/integration/http/test_sampling_routes.py`

| Endpoint | 설명 |
|----------|------|
| `GET /api/sampling/requests` | 대기 중인 요청 목록 |
| `POST /api/sampling/requests/{id}/approve` | 승인 + LLM 실행 |
| `POST /api/sampling/requests/{id}/reject` | 거부 |

### Step 6.4: Elicitation HITL API

**파일:** `src/adapters/inbound/http/routes/elicitation.py`
**테스트:** `tests/integration/http/test_elicitation_routes.py`

| Endpoint | 설명 |
|----------|------|
| `GET /api/elicitation/requests` | 대기 중인 요청 목록 |
| `POST /api/elicitation/requests/{id}/respond` | accept/decline/cancel |

---

## Phase 7: SSE Events & Extension

### Step 7.1: StreamChunk 확장

**파일:** `src/domain/entities/stream_chunk.py`

새 이벤트 타입:
- `sampling_request` - Sampling 요청 알림
- `elicitation_request` - Elicitation 요청 알림

### Step 7.2: Extension Types

**파일:** `extension/lib/types.ts`

```typescript
export interface StreamEventSamplingRequest {
  type: 'sampling_request';
  request_id: string;
  endpoint_id: string;
  messages: Array<{role: string; content: unknown}>;
}

export interface StreamEventElicitationRequest {
  type: 'elicitation_request';
  request_id: string;
  message: string;
  requested_schema: Record<string, unknown>;
}
```

### Step 7.3: Extension API

**파일:** `extension/lib/api.ts`

새 함수:
- `listSamplingRequests()`, `approveSamplingRequest()`, `rejectSamplingRequest()`
- `listElicitationRequests()`, `respondElicitation()`
- `listResources()`, `readResource()`
- `listPrompts()`, `getPrompt()`

---

## Verification

### Unit Tests
```bash
pytest tests/unit/ -q --tb=line
```

### Integration Tests
```bash
pytest tests/integration/ -q --tb=line
```

### Coverage
```bash
pytest --cov=src --cov-fail-under=80 -q
```

### Local MCP Server Test
```bash
# MCP 서버 시작 (별도 터미널)
cd C:\Users\sungb\Documents\GitHub\MCP_SERVER\MCP_Streamable_HTTP
python -m synapse

# 서버 시작 및 테스트
uvicorn src.main:app --port 8000
```

### E2E Test (Extension HITL Flow)
1. Extension에서 MCP 서버 등록
2. MCP 서버가 Sampling 요청 전송
3. Extension UI에서 승인 다이얼로그 확인
4. 승인 후 LLM 응답 확인

---

## Critical Files Summary

| 구분 | 파일 |
|------|------|
| **Domain Entities** | `src/domain/entities/resource.py`, `sampling_request.py`, `elicitation_request.py`, `prompt_template.py` |
| **Port Interface** | `src/domain/ports/outbound/mcp_client_port.py` |
| **Domain Services** | `src/domain/services/resource_service.py`, `prompt_service.py`, `sampling_service.py`, `elicitation_service.py` |
| **Adapter** | `src/adapters/outbound/mcp/mcp_client_adapter.py` |
| **Integration** | `src/domain/services/registry_service.py`, `src/config/container.py` |
| **HTTP Routes** | `src/adapters/inbound/http/routes/resources.py`, `prompts.py`, `sampling.py`, `elicitation.py` |
| **Extension** | `extension/lib/types.ts`, `extension/lib/api.ts` |

---

## Design Decisions

### HITL Flow: Hybrid 방식
- **Short timeout (30s)**: 요청 수신 후 30초간 Long-Polling 대기
- **Timeout 초과 시**: 요청 큐잉 + SSE로 Extension에 알림
- **장점**: 빠른 응답(30s 이내)과 비동기 처리(30s 초과) 모두 지원

### Extension UI: Modal Dialog
- **전체 화면 모달**로 즉각적인 주의 환기
- Sampling: 메시지 내용 + 승인/거부 버튼
- Elicitation: 동적 폼 (requested_schema 기반) + accept/decline/cancel

---

## Risk Mitigation

1. **MCP SDK v2 Breaking Changes**: `mcp>=1.25,<2`로 버전 고정
2. **이중 세션 오버헤드**: 모니터링 필요, 리소스 영향은 낮을 것으로 예상
3. **콜백 시그니처 변경**: MCP SDK 최신 스펙 검증 후 구현
4. **HITL 타임아웃**: Hybrid 방식 (30s Long-Polling + Queue + TTL 자동 정리)
