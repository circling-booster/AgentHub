# Dual-Track Architecture

단일 MCP 서버에 ADK Track과 SDK Track을 동시 연결하는 아키텍처입니다.

---

## Overview

**Dual-Track**은 동일한 MCP 서버에 두 개의 독립적인 연결을 유지합니다:

- **ADK Track**: Google ADK를 통한 Tool 호출 (기존)
- **SDK Track**: MCP SDK를 통한 Resources/Prompts/Sampling/Elicitation (신규)

이 구조는 Phase 7에서 구현되었으며, MCP의 모든 기능을 완전히 지원하면서도 기존 ADK 통합을 유지합니다.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      AgentHub Server                        │
│                                                             │
│  ┌─────────────────────┐      ┌──────────────────────────┐ │
│  │   ADK Track         │      │   SDK Track              │ │
│  │                     │      │                          │ │
│  │  DynamicToolset     │      │  McpClientAdapter        │ │
│  │  ├─ add_mcp_server()│      │  ├─ connect()           │ │
│  │  └─ Tools[]         │      │  ├─ Resources           │ │
│  │                     │      │  ├─ Prompts             │ │
│  │                     │      │  ├─ Sampling (HITL)     │ │
│  │                     │      │  └─ Elicitation (HITL)  │ │
│  └─────────────────────┘      └──────────────────────────┘ │
│           │                              │                  │
│           └──────────────┬───────────────┘                  │
│                          │                                  │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │   MCP Server         │
                │   (e.g., Synapse)    │
                │                      │
                │  Tools + Resources + │
                │  Prompts + Sampling  │
                └──────────────────────┘
```

---

## Connection Lifecycle

### 1. Registration (등록)

`RegistryService.register_endpoint()`가 호출되면 두 Track을 순차적으로 연결합니다:

```python
async def register_endpoint(self, url: str, ...) -> Endpoint:
    endpoint = Endpoint(url=url, type=EndpointType.MCP, ...)

    # Step 1: ADK Track - Tools
    tools = await self._toolset.add_mcp_server(endpoint)

    # Step 2: SDK Track - Resources/Prompts/Sampling/Elicitation
    if self._mcp_client:
        sampling_cb = self._create_sampling_callback(endpoint.id)
        elicitation_cb = self._create_elicitation_callback(endpoint.id)
        await self._mcp_client.connect(
            endpoint.id, url, sampling_cb, elicitation_cb
        )

    return endpoint
```

**결과:**
- ADK Track: LLM이 `summarize`, `search` 등의 도구를 호출 가능
- SDK Track: Resources 읽기, Prompts 렌더링, Sampling/Elicitation HITL 지원

### 2. Unregistration (해제)

`RegistryService.unregister_endpoint()`는 양쪽 Track을 모두 정리합니다:

```python
async def unregister_endpoint(self, endpoint_id: str) -> bool:
    # ADK Track 정리
    await self._toolset.remove_mcp_server(endpoint_id)

    # SDK Track 정리
    if self._mcp_client:
        await self._mcp_client.disconnect(endpoint_id)

    return await self._storage.delete_endpoint(endpoint_id)
```

### 3. Server Restart (복원)

서버 시작 시 `restore_endpoints()`가 저장된 엔드포인트를 복원합니다:

```python
async def restore_endpoints(self) -> dict[str, list[str]]:
    endpoints = await self._storage.list_endpoints()

    for endpoint in endpoints:
        if endpoint.type == EndpointType.MCP:
            # ADK Track 재연결
            await self._toolset.add_mcp_server(endpoint)

            # SDK Track 재연결
            if self._mcp_client:
                sampling_cb = self._create_sampling_callback(endpoint.id)
                elicitation_cb = self._create_elicitation_callback(endpoint.id)
                await self._mcp_client.connect(
                    endpoint.id, endpoint.url, sampling_cb, elicitation_cb
                )
```

---

## Callback Pattern (Method C)

SDK Track의 Sampling/Elicitation은 **Method C (Callback-Centric)** 패턴을 사용합니다:

```
MCP Server → Callback (await) → SamplingService → Route (LLM) → approve() → Callback (return)
```

**흐름:**

1. MCP 서버가 `sampling` 요청 시 callback 호출
2. Callback이 `SamplingRequest` 생성 및 큐에 추가
3. Short timeout (30s) 대기
4. Timeout 시 SSE 알림 전송 + Long timeout (270s) 대기
5. Route가 LLM 호출 후 `approve()` 시그널 전송
6. Callback이 LLM 결과를 MCP 서버에 반환

**코드 예시:**

```python
def _create_sampling_callback(self, endpoint_id: str) -> SamplingCallback:
    async def callback(
        request_id: str,
        endpoint_id: str,
        messages: list[dict],
        model_preferences: dict | None,
        system_prompt: str | None,
        max_tokens: int,
    ) -> dict:
        # 1. Create request
        request = SamplingRequest(...)
        await self._sampling_service.create_request(request)

        # 2. Short timeout (30s)
        result = await self._sampling_service.wait_for_response(
            request_id, timeout=self._short_timeout
        )

        # 3. If timeout, notify SSE + Long timeout (270s)
        if result is None:
            if self._hitl_notification:
                await self._hitl_notification.notify_sampling_request(request)
            result = await self._sampling_service.wait_for_response(
                request_id, timeout=self._long_timeout
            )

        # 4. Return LLM result or raise error
        if result is None or result.status == SamplingStatus.REJECTED:
            raise HitlTimeoutError(f"Sampling request {request_id} rejected or timed out")

        return result.llm_result

    return callback
```

**상세:** [ADR-A05 (Method C)](../../../project/decisions/architecture/ADR-A05-method-c-callback-centric.md)

---

## Resource Monitoring

### 로깅

`RegistryService`는 Dual-Track 연결 시 로그를 기록합니다:

```python
logger.info(f"MCP endpoint {endpoint.id} connected: ADK Track + SDK Track")
logger.debug(f"SDK Track callbacks: sampling={sampling_cb is not None}, elicitation={elicitation_cb is not None}")
```

**로그 예시:**

```
INFO: MCP endpoint abc123 connected: ADK Track + SDK Track
DEBUG: SDK Track callbacks: sampling=True, elicitation=True
```

### 메트릭 (향후)

다음 메트릭을 수집할 수 있습니다:

| 메트릭 | 설명 | 수집 위치 |
|--------|------|----------|
| `mcp_sdk_sessions_active` | 활성 SDK Track 세션 수 | `McpClientAdapter._sessions` |
| `sampling_request_duration_seconds` | Sampling 요청 처리 시간 | `SamplingService.wait_for_response()` |
| `sampling_timeout_short_count` | Short timeout (30s) 발생 횟수 | `_create_sampling_callback()` |
| `sampling_timeout_long_count` | Long timeout (270s) 발생 횟수 | `_create_sampling_callback()` |

**구현 예시 (Prometheus):**

```python
from prometheus_client import Gauge, Histogram

mcp_sdk_sessions = Gauge('mcp_sdk_sessions_active', 'Active SDK Track sessions')
sampling_duration = Histogram('sampling_request_duration_seconds', 'Sampling request duration')

# McpClientAdapter.connect() 내부
mcp_sdk_sessions.inc()

# SamplingService.wait_for_response() 내부
with sampling_duration.time():
    result = await self._wait_for_signal(request_id, timeout)
```

---

## Resource Overhead

### 메모리

각 MCP 엔드포인트당 두 개의 연결을 유지합니다:

- **ADK Track**: `DynamicToolset._mcp_servers[endpoint_id]` (MCP 클라이언트 세션)
- **SDK Track**: `McpClientAdapter._sessions[endpoint_id]` (MCP 클라이언트 세션)

**예상 오버헤드:**
- 엔드포인트당 ~2-5 MB (세션 2개 + 콜백 클로저)
- 10개 엔드포인트 기준 ~20-50 MB

### 네트워크

단일 MCP 서버에 두 개의 HTTP 연결이 유지됩니다:

- **ADK Track**: Tool 호출 시 HTTP POST (간헐적)
- **SDK Track**: Resources/Prompts 요청 시 HTTP POST (간헐적), Sampling/Elicitation 시 장시간 대기 (blocking)

**최적화 방안:**
- Resources/Prompts는 캐싱 가능 (향후 Phase)
- Sampling/Elicitation은 사용자 입력 대기이므로 네트워크 오버헤드 무시 가능

---

## Error Handling

### ADK Track 연결 실패

`DynamicToolset.add_mcp_server()`가 실패하면 SDK Track 연결을 시도하지 않습니다:

```python
if endpoint.type == EndpointType.MCP:
    # ADK Track 연결 실패 시 예외 발생
    tools = await self._toolset.add_mcp_server(endpoint)  # 여기서 예외 발생 가능

    # SDK Track은 실행되지 않음
    if self._mcp_client:
        ...
```

**결과:** ADK Track 필수, SDK Track 선택적

### SDK Track 연결 실패

SDK Track 연결 실패 시에도 ADK Track은 유지됩니다:

```python
if self._mcp_client:
    try:
        await self._mcp_client.connect(...)
    except Exception as e:
        logger.warning(f"SDK Track connection failed: {e}")
        # ADK Track은 유지됨
```

**결과:** Partial Degradation (도구만 사용 가능, Resources/Sampling 불가)

---

## Testing

### Unit Tests

`tests/unit/domain/services/test_registry_service.py`의 `TestRegistryServiceWithMcpClient` 클래스:

```python
async def test_register_mcp_connects_sdk_track(...):
    """MCP 등록 시 SDK Track 연결 확인"""
    endpoint = await service.register_endpoint("http://localhost:8080/mcp")

    assert mcp_client.is_connected(endpoint.id)
    assert mcp_client.get_sampling_callback(endpoint.id) is not None
```

### Integration Tests

`tests/integration/test_dual_track.py`:

```python
@pytest.mark.local_mcp
@pytest.mark.llm
async def test_adk_calls_synapse_with_sampling(client, synapse_url):
    """ADK → Synapse → Sampling → LLM 전체 흐름"""
    # 1. Synapse 등록 (Dual-Track)
    response = await client.post("/api/endpoints", json={"url": synapse_url, "type": "mcp"})

    # 2. ADK에게 Synapse summarize 도구 호출 지시
    response = await client.post("/api/chat", json={"message": "Summarize news using Synapse"})

    # 3. Sampling 요청 발생 확인
    requests = await client.get("/api/sampling/requests")
    assert len(requests["requests"]) > 0
```

**실행 방법:**

```bash
# Unit Tests (Fake Adapters)
pytest tests/unit/domain/services/test_registry_service.py::TestRegistryServiceWithMcpClient -v

# Integration Tests (실제 Synapse + LLM)
pytest tests/integration/test_dual_track.py -m "local_mcp and llm" -v
```

---

## References

- [ADR-A05: Method C (Callback-Centric)](../../../project/decisions/architecture/ADR-A05-method-c-callback-centric.md)
- [ADR-A06: Hybrid Timeout Strategy](../../../project/decisions/architecture/ADR-A06-hybrid-timeout-strategy.md)
- [ADR-A07: Dual-Track Architecture](../../../project/decisions/architecture/ADR-A07-dual-track-architecture.md)
- [Lifecycle Management Guide](../../guides/implementation/lifecycle-management.md)
- [MCP Client Port](../../../../src/domain/ports/outbound/mcp_client_port.py)

---

*Last Updated: 2026-02-07*
*Phase: Plan 07 Phase 5 (Integration)*
