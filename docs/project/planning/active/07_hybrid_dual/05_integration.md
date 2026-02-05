# Phase 5: Integration

## 개요

RegistryService를 수정하여 ADK Track과 SDK Track을 통합합니다.

```
MCP 서버 등록 시:
┌─────────────────────────────────────────────────────────┐
│                  RegistryService                        │
├─────────────────────────────────────────────────────────┤
│  1. ADK Track: _toolset.add_mcp_server()               │ ← 기존 (Tools)
│  2. SDK Track: _mcp_client.connect()                   │ ← 신규 (Resources/Prompts/HITL)
│       └── 콜백 연결: SamplingService, ElicitationService │
└─────────────────────────────────────────────────────────┘
```

---

## Step 5.1: RegistryService 수정

**파일:** `src/domain/services/registry_service.py`
**테스트:** `tests/unit/domain/services/test_registry_service.py` (기존 파일 확장)

### 변경사항

1. 생성자에 새 의존성 추가:
   - `mcp_client: McpClientPort | None`
   - `sampling_service: SamplingService | None`
   - `elicitation_service: ElicitationService | None`

2. MCP 등록 시 이중 연결

3. 콜백 생성 및 전달

```python
def __init__(
    self,
    storage: EndpointStoragePort,
    toolset: ToolsetPort,
    a2a_client: A2aPort | None = None,
    orchestrator: OrchestratorPort | None = None,
    gateway_service: GatewayService | None = None,
    # 신규 의존성
    mcp_client: McpClientPort | None = None,
    sampling_service: SamplingService | None = None,
    elicitation_service: ElicitationService | None = None,
) -> None:
    # ... 기존 코드 ...
    self._mcp_client = mcp_client
    self._sampling_service = sampling_service
    self._elicitation_service = elicitation_service

async def register_endpoint(self, url, ...):
    if endpoint_type == EndpointType.MCP:
        # ADK Track (기존)
        tools = await self._toolset.add_mcp_server(endpoint)
        # ... 기존 코드 ...

        # SDK Track (신규 - 이중 연결)
        if self._mcp_client:
            sampling_cb = self._create_sampling_callback(endpoint.id)
            elicitation_cb = self._create_elicitation_callback(endpoint.id)
            await self._mcp_client.connect(
                endpoint.id, url, sampling_cb, elicitation_cb
            )

def _create_sampling_callback(self, endpoint_id: str) -> SamplingCallback:
    """SamplingService와 연결된 콜백 생성"""
    async def callback(
        request_id: str,
        endpoint_id: str,
        messages: list[dict],
        model_preferences: dict | None,
        system_prompt: str | None,
        max_tokens: int,
    ) -> dict:
        # SamplingRequest 생성
        request = SamplingRequest(
            id=request_id,
            endpoint_id=endpoint_id,
            messages=messages,
            model_preferences=model_preferences,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
        )

        # 큐에 추가 및 대기
        await self._sampling_service.create_request(request)
        result = await self._sampling_service.wait_for_response(request_id, timeout=30.0)

        if result is None or result.status == SamplingStatus.REJECTED:
            raise HitlTimeoutError(f"Sampling request {request_id} rejected or timed out")

        return result.llm_result

    return callback

async def unregister_endpoint(self, endpoint_id: str) -> bool:
    # ... 기존 코드 ...

    # SDK Track 연결 해제 (신규)
    if endpoint.type == EndpointType.MCP and self._mcp_client:
        await self._mcp_client.disconnect(endpoint_id)

    return await self._storage.delete_endpoint(endpoint_id)
```

### 테스트 시나리오 (추가)

**파일:** `tests/unit/domain/services/test_registry_service.py`

```python
# 기존 테스트에 추가

class TestRegistryServiceWithMcpClient:
    """SDK Track 통합 테스트"""

    async def test_register_mcp_connects_sdk_track(
        self, fake_storage, fake_toolset, fake_mcp_client
    ):
        """MCP 등록 시 SDK Track도 연결됨"""
        service = RegistryService(
            storage=fake_storage,
            toolset=fake_toolset,
            mcp_client=fake_mcp_client,
        )
        endpoint = await service.register_endpoint("http://localhost:8080/mcp")

        assert fake_mcp_client.is_connected(endpoint.id)

    async def test_unregister_disconnects_sdk_track(
        self, fake_storage, fake_toolset, fake_mcp_client
    ):
        """MCP 해제 시 SDK Track도 연결 해제됨"""
        # ... setup ...
        await service.unregister_endpoint(endpoint.id)

        assert not fake_mcp_client.is_connected(endpoint.id)

    async def test_sampling_callback_creates_request(
        self, fake_storage, fake_toolset, fake_mcp_client, fake_sampling_service
    ):
        """콜백 호출 시 SamplingService에 요청 생성됨"""
        service = RegistryService(
            storage=fake_storage,
            toolset=fake_toolset,
            mcp_client=fake_mcp_client,
            sampling_service=fake_sampling_service,
        )
        # ... 콜백 트리거 및 검증 ...
```

---

## Step 5.2: DI Container 수정

**파일:** `src/config/container.py`

### 추가할 Provider

```python
# MCP SDK Track
mcp_client_adapter = providers.Singleton(McpClientAdapter)

# HITL Services (Singleton - 전역 큐)
sampling_service = providers.Singleton(SamplingService)
elicitation_service = providers.Singleton(ElicitationService)

# Resource/Prompt Services
resource_service = providers.Factory(
    ResourceService,
    mcp_client=mcp_client_adapter,
)
prompt_service = providers.Factory(
    PromptService,
    mcp_client=mcp_client_adapter,
)

# RegistryService 수정
registry_service = providers.Factory(
    RegistryService,
    storage=endpoint_storage,
    toolset=gateway_toolset,
    a2a_client=a2a_client_adapter,
    orchestrator=orchestrator_adapter,
    gateway_service=gateway_service,
    # 신규
    mcp_client=mcp_client_adapter,
    sampling_service=sampling_service,
    elicitation_service=elicitation_service,
)
```

---

## Step 5.3: 서버 종료 시 세션 정리

**파일:** `src/main.py` 또는 `src/adapters/inbound/http/app.py`

```python
@app.on_event("shutdown")
async def shutdown_event():
    # 기존 정리 코드 ...

    # MCP SDK Track 세션 정리
    mcp_client = container.mcp_client_adapter()
    await mcp_client.disconnect_all()  # 모든 세션 해제
```

McpClientAdapter에 `disconnect_all()` 메서드 추가:

```python
async def disconnect_all(self) -> None:
    """모든 세션 정리 (서버 종료 시)"""
    for endpoint_id in list(self._sessions.keys()):
        await self.disconnect(endpoint_id)
```

### 테스트

**파일:** `tests/integration/test_app_lifecycle.py`

```python
async def test_shutdown_disconnects_all_mcp_sessions():
    """서버 종료 시 모든 MCP 세션 정리됨"""
    # AsyncClient로 서버 시작/종료 테스트
```

---

## 이중 연결 리소스 모니터링

**로깅 추가:**
```python
logger.info(f"MCP endpoint {endpoint.id} connected: ADK Track + SDK Track")
```

**메트릭 (추후):**
- 활성 SDK 세션 수
- 세션당 메모리 사용량 (프로파일링 필요 시)
