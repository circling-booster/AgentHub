# Phase 5: Integration (Method C)

## 개요

RegistryService를 수정하여 Method C(Callback-Centric) 패턴을 구현하고, Dual-Track 통합 테스트를 수행합니다.

**핵심:**
- RegistryService: MCP 등록 시 ADK Track + SDK Track 이중 연결
- Method C 콜백: LLM 호출은 Route에서, 결과는 Signal로 전달
- DI Container: Provide[] 패턴 사용 (lambda 아님)
- Dual-Track 테스트: Synapse + ADK 상호작용 검증

---

## Step 5.1: RegistryService 수정 (Method C 핵심)

**파일:** `src/domain/services/registry_service.py` (기존 파일 확장)
**테스트:** `tests/unit/domain/services/test_registry_service.py` (기존 파일 확장)

### 변경사항

```python
from src.domain.ports.outbound.mcp_client_port import McpClientPort, SamplingCallback, ElicitationCallback
from src.domain.services.sampling_service import SamplingService
from src.domain.services.elicitation_service import ElicitationService
from src.domain.ports.outbound.hitl_notification_port import HitlNotificationPort
from src.domain.entities.sampling_request import SamplingRequest, SamplingStatus
from src.domain.entities.elicitation_request import ElicitationRequest, ElicitationAction
from src.domain.exceptions import HitlTimeoutError

class RegistryService:
    """엔드포인트 등록 관리 (ADK Track + SDK Track 통합)"""

    def __init__(
        self,
        storage: EndpointStoragePort,
        toolset: ToolsetPort,
        a2a_client: A2aPort | None = None,
        orchestrator: OrchestratorPort | None = None,
        gateway_service: GatewayService | None = None,
        # 신규 의존성 (Method C)
        mcp_client: McpClientPort | None = None,
        sampling_service: SamplingService | None = None,
        elicitation_service: ElicitationService | None = None,
        hitl_notification: HitlNotificationPort | None = None,
        # Timeout 설정 (H2 수정: 테스트에서 주입 가능)
        short_timeout: float = 30.0,
        long_timeout: float = 270.0,
    ) -> None:
        """
        Args:
            ...기존 인자...
            mcp_client: MCP SDK Track 어댑터 (신규)
            sampling_service: Sampling HITL 큐 (신규)
            elicitation_service: Elicitation HITL 큐 (신규)
            hitl_notification: SSE 브로드캐스트 어댑터 (신규)
            short_timeout: Short timeout 초 (기본 30초, 테스트에서 조정 가능)
            long_timeout: Long timeout 초 (기본 270초, 테스트에서 조정 가능)
        """
        # 기존 코드
        self._storage = storage
        self._toolset = toolset
        self._a2a_client = a2a_client
        self._orchestrator = orchestrator
        self._gateway_service = gateway_service

        # 신규
        self._mcp_client = mcp_client
        self._sampling_service = sampling_service
        self._elicitation_service = elicitation_service
        self._hitl_notification = hitl_notification
        self._short_timeout = short_timeout
        self._long_timeout = long_timeout

    async def register_endpoint(
        self,
        url: str,
        ...  # 기존 파라미터
    ) -> Endpoint:
        """엔드포인트 등록 (Dual-Track)"""
        endpoint = Endpoint(...)  # 기존 코드
        await self._storage.save_endpoint(endpoint)

        if endpoint.type == EndpointType.MCP:
            # ADK Track (기존 - Tools)
            tools = await self._toolset.add_mcp_server(endpoint)
            # ... 기존 코드 ...

            # SDK Track (신규 - Resources/Prompts/Sampling/Elicitation)
            if self._mcp_client:
                sampling_cb = self._create_sampling_callback(endpoint.id)
                elicitation_cb = self._create_elicitation_callback(endpoint.id)
                await self._mcp_client.connect(
                    endpoint.id, url, sampling_cb, elicitation_cb
                )

        elif endpoint.type == EndpointType.A2A:
            # ... 기존 A2A 코드 ...

        return endpoint

    async def unregister_endpoint(self, endpoint_id: str) -> bool:
        """엔드포인트 해제 (Dual-Track)"""
        endpoint = await self._storage.get_endpoint(endpoint_id)
        if not endpoint:
            return False

        # 기존 정리 코드
        if endpoint.type == EndpointType.MCP:
            await self._toolset.remove_mcp_server(endpoint_id)

        elif endpoint.type == EndpointType.A2A:
            if self._a2a_client:
                await self._a2a_client.disconnect(endpoint_id)

        # SDK Track 연결 해제 (신규)
        if endpoint.type == EndpointType.MCP and self._mcp_client:
            await self._mcp_client.disconnect(endpoint_id)

        return await self._storage.delete_endpoint(endpoint_id)

    async def restore_endpoints(self) -> dict[str, list[str]]:
        """서버 시작 시 저장된 엔드포인트 복원 (M1 수정: SDK Track 추가)

        기존 restore_endpoints()에 SDK Track 복원 로직 추가.
        ADK Track (Tools)과 SDK Track (Resources/Prompts/Sampling/Elicitation)을 모두 복원합니다.

        Returns:
            {"restored": [...], "failed": [...]}
        """
        endpoints = await self._storage.list_endpoints()
        restored: list[str] = []
        failed: list[str] = []

        for endpoint in endpoints:
            try:
                if endpoint.type == EndpointType.MCP:
                    # ADK Track 재연결 (기존)
                    await self._toolset.add_mcp_server(endpoint)

                    # SDK Track 재연결 (M1 신규)
                    if self._mcp_client:
                        sampling_cb = self._create_sampling_callback(endpoint.id)
                        elicitation_cb = self._create_elicitation_callback(endpoint.id)
                        await self._mcp_client.connect(
                            endpoint.id, endpoint.url, sampling_cb, elicitation_cb
                        )

                    restored.append(endpoint.url)

                elif endpoint.type == EndpointType.A2A:
                    # A2A 재등록 (기존 코드)
                    if self._a2a_client and self._orchestrator:
                        agent_card = await self._a2a_client.register_agent(endpoint)
                        endpoint.agent_card = agent_card
                        await self._orchestrator.add_a2a_agent(endpoint.id, endpoint.url)
                        restored.append(endpoint.url)
                    else:
                        failed.append(endpoint.url)

            except Exception as e:
                logger.warning(f"Failed to restore endpoint {endpoint.url}: {e}")
                failed.append(endpoint.url)

        logger.info(f"Endpoints restored: {len(restored)}, failed: {len(failed)}")
        return {"restored": restored, "failed": failed}

    def _create_sampling_callback(self, endpoint_id: str) -> SamplingCallback:
        """Sampling 콜백 생성 (Method C 클로저)

        MCP SDK callback은 blocking(await)이므로, callback 내에서:
        1. SamplingRequest 생성 및 큐에 추가
        2. 30초 wait (Short timeout)
        3. Timeout 시 SSE 알림 전송 + 270초 wait (Long timeout)
        4. approve 시그널 수신하면 결과 반환
        5. Reject 또는 최종 timeout 시 예외 발생

        Route는 approve() 호출로 시그널만 전송 (LLM 호출 후).
        """
        async def callback(
            request_id: str,
            endpoint_id: str,
            messages: list[dict],
            model_preferences: dict | None,
            system_prompt: str | None,
            max_tokens: int,
        ) -> dict:
            # 1. SamplingRequest 생성
            request = SamplingRequest(
                id=request_id,
                endpoint_id=endpoint_id,
                messages=messages,
                model_preferences=model_preferences,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
            )

            # 2. 큐에 추가
            await self._sampling_service.create_request(request)

            # 3. Short timeout (기본 30초, 테스트에서 조정 가능)
            result = await self._sampling_service.wait_for_response(request_id, timeout=self._short_timeout)

            # 4. Timeout 시 SSE 알림 전송
            if result is None:
                if self._hitl_notification:
                    await self._hitl_notification.notify_sampling_request(request)

                # 5. Long timeout (기본 270초, 테스트에서 조정 가능)
                result = await self._sampling_service.wait_for_response(request_id, timeout=self._long_timeout)

            # 6. 여전히 None이거나 REJECTED → 예외
            if result is None or result.status == SamplingStatus.REJECTED:
                raise HitlTimeoutError(f"Sampling request {request_id} rejected or timed out")

            # 7. LLM 결과 반환 (MCP 서버에 전달)
            return result.llm_result

        return callback

    def _create_elicitation_callback(self, endpoint_id: str) -> ElicitationCallback:
        """Elicitation 콜백 생성 (동일한 패턴)"""
        async def callback(
            request_id: str,
            endpoint_id: str,
            message: str,
            requested_schema: dict,
        ) -> dict:
            # 1. ElicitationRequest 생성
            request = ElicitationRequest(
                id=request_id,
                endpoint_id=endpoint_id,
                message=message,
                requested_schema=requested_schema,
            )

            # 2. 큐에 추가
            await self._elicitation_service.create_request(request)

            # 3. Short timeout (기본 30초, 테스트에서 조정 가능)
            result = await self._elicitation_service.wait_for_response(request_id, timeout=self._short_timeout)

            # 4. Timeout 시 SSE 알림 전송
            if result is None:
                if self._hitl_notification:
                    await self._hitl_notification.notify_elicitation_request(request)

                # 5. Long timeout (기본 270초, 테스트에서 조정 가능)
                result = await self._elicitation_service.wait_for_response(request_id, timeout=self._long_timeout)

            # 6. 여전히 None이거나 DECLINE/CANCEL → 예외 (H3 수정: HitlTimeoutError 사용)
            if result is None:
                raise HitlTimeoutError(f"Elicitation request {request_id} timed out")

            if result.action in (ElicitationAction.DECLINE, ElicitationAction.CANCEL):
                raise HitlTimeoutError(f"Elicitation request {request_id} {result.action.value}")

            # 7. 사용자 입력 반환 (MCP 서버에 전달)
            return {
                "action": result.action.value,
                "content": result.content,
            }

        return callback
```

### 테스트 시나리오 (추가)

```python
# tests/unit/domain/services/test_registry_service.py

class TestRegistryServiceWithMcpClient:
    """SDK Track 통합 테스트 (Method C)"""

    async def test_register_mcp_connects_sdk_track(
        self,
        fake_storage,
        fake_toolset,
        fake_mcp_client,
        fake_sampling_service,
        fake_elicitation_service,
    ):
        """MCP 등록 시 SDK Track도 연결됨"""
        service = RegistryService(
            storage=fake_storage,
            toolset=fake_toolset,
            mcp_client=fake_mcp_client,
            sampling_service=fake_sampling_service,
            elicitation_service=fake_elicitation_service,
        )

        endpoint = await service.register_endpoint("http://localhost:8080/mcp")

        # SDK Track 연결 확인
        assert fake_mcp_client.is_connected(endpoint.id)
        # 콜백이 설정되었는지 확인
        assert fake_mcp_client.get_sampling_callback(endpoint.id) is not None
        assert fake_mcp_client.get_elicitation_callback(endpoint.id) is not None

    async def test_unregister_disconnects_sdk_track(
        self,
        fake_storage,
        fake_toolset,
        fake_mcp_client,
    ):
        """MCP 해제 시 SDK Track도 연결 해제됨"""
        service = RegistryService(
            storage=fake_storage,
            toolset=fake_toolset,
            mcp_client=fake_mcp_client,
        )
        endpoint = await service.register_endpoint("http://localhost:8080/mcp")

        await service.unregister_endpoint(endpoint.id)

        assert not fake_mcp_client.is_connected(endpoint.id)

    async def test_sampling_callback_waits_for_approval(
        self,
        fake_storage,
        fake_toolset,
        fake_mcp_client,
        fake_sampling_service,
    ):
        """콜백 호출 시 SamplingService에 요청 생성 및 대기"""
        service = RegistryService(
            storage=fake_storage,
            toolset=fake_toolset,
            mcp_client=fake_mcp_client,
            sampling_service=fake_sampling_service,
        )
        endpoint = await service.register_endpoint("http://localhost:8080/mcp")

        # 콜백 트리거 (백그라운드 태스크)
        callback = fake_mcp_client.get_sampling_callback(endpoint.id)
        import asyncio
        async def delayed_approve():
            await asyncio.sleep(0.5)
            await fake_sampling_service.approve("test-req-1", {"content": "LLM response"})
        asyncio.create_task(delayed_approve())

        # 콜백 실행 (30초 timeout이지만 0.5초 내 반환됨)
        result = await callback(
            request_id="test-req-1",
            endpoint_id=endpoint.id,
            messages=[{"role": "user", "content": "test"}],
            model_preferences=None,
            system_prompt=None,
            max_tokens=1024,
        )

        assert result == {"content": "LLM response"}

    async def test_sampling_callback_timeout_notifies_sse(
        self,
        fake_storage,
        fake_toolset,
        fake_mcp_client,
        fake_sampling_service,
        fake_hitl_notification,
    ):
        """Short timeout 시 SSE 알림 전송 (H2 수정: 설정 가능한 timeout)"""
        # short_timeout을 0.05초로 설정하여 빠른 테스트
        service = RegistryService(
            storage=fake_storage,
            toolset=fake_toolset,
            mcp_client=fake_mcp_client,
            sampling_service=fake_sampling_service,
            hitl_notification=fake_hitl_notification,
            short_timeout=0.05,  # 테스트용 짧은 timeout
            long_timeout=0.1,
        )
        endpoint = await service.register_endpoint("http://localhost:8080/mcp")

        callback = fake_mcp_client.get_sampling_callback(endpoint.id)

        # Long timeout 초과까지 대기 (SSE 알림 발생 확인)
        with pytest.raises(HitlTimeoutError):
            await callback(
                request_id="test-req-timeout",
                endpoint_id=endpoint.id,
                messages=[{"role": "user", "content": "timeout test"}],
                model_preferences=None,
                system_prompt=None,
                max_tokens=1024,
            )

        # SSE 알림 검증 (FakeHitlNotification, L2 수정)
        assert len(fake_hitl_notification.sampling_notifications) > 0
        notified_request = fake_hitl_notification.sampling_notifications[0]
        assert notified_request.id == "test-req-timeout"
```

---

## Step 5.2: DI Container 수정

**파일:** `src/config/container.py` (기존 파일 확장)

### 추가할 Provider

```python
from dependency_injector import containers, providers
from src.adapters.outbound.mcp.mcp_client_adapter import McpClientAdapter
from src.adapters.outbound.sse.broker import SseBroker
from src.adapters.outbound.sse.hitl_notification_adapter import HitlNotificationAdapter
from src.domain.services.sampling_service import SamplingService
from src.domain.services.elicitation_service import ElicitationService
from src.domain.services.resource_service import ResourceService
from src.domain.services.prompt_service import PromptService

class Container(containers.DeclarativeContainer):
    # ... 기존 providers ...

    # SSE Broker (Singleton - 전역 이벤트 브로드캐스터)
    sse_broker = providers.Singleton(SseBroker)

    # MCP SDK Track
    mcp_client_adapter = providers.Singleton(McpClientAdapter)

    # HITL Services (Singleton - 전역 큐)
    sampling_service = providers.Singleton(SamplingService, ttl_seconds=600)
    elicitation_service = providers.Singleton(ElicitationService, ttl_seconds=600)

    # HITL Notification Adapter (SSE)
    hitl_notification_adapter = providers.Singleton(
        HitlNotificationAdapter,
        sse_broker=sse_broker,
    )

    # Resource/Prompt Services (Factory - 요청마다 생성)
    resource_service = providers.Factory(
        ResourceService,
        mcp_client=mcp_client_adapter,
    )
    prompt_service = providers.Factory(
        PromptService,
        mcp_client=mcp_client_adapter,
    )

    # RegistryService 수정 (Provide[] 패턴 사용)
    registry_service = providers.Factory(
        RegistryService,
        storage=endpoint_storage,
        toolset=gateway_toolset,
        a2a_client=a2a_client_adapter,
        orchestrator=orchestrator_adapter,
        gateway_service=gateway_service,
        # 신규 의존성
        mcp_client=mcp_client_adapter,
        sampling_service=sampling_service,
        elicitation_service=elicitation_service,
        hitl_notification=hitl_notification_adapter,
    )
```

**주의:**
- **lambda 사용 금지**: `Provide[Container.mcp_client_adapter]` 패턴 사용
- `sse_broker`는 기존 provider 참조 (Phase 1-6에서 이미 정의됨)

---

## Step 5.3: 서버 종료 시 세션 정리 + cleanup 스케줄러 (M2 추가)

**파일:** `src/adapters/inbound/http/app.py` (기존 파일 확장)

### Lifespan startup/shutdown 수정

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio

# 주기적 cleanup 태스크 (M2 신규)
cleanup_task = None

async def _periodic_cleanup(sampling_service, elicitation_service, interval=60):
    """만료된 HITL 요청 주기적 정리

    Args:
        sampling_service: SamplingService 인스턴스
        elicitation_service: ElicitationService 인스턴스
        interval: 정리 주기 (초, 기본 60초)
    """
    while True:
        await asyncio.sleep(interval)
        try:
            await sampling_service.cleanup_expired()
            await elicitation_service.cleanup_expired()
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global cleanup_task

    # Startup
    from src.config.container import Container

    # cleanup 스케줄러 시작 (M2 신규)
    sampling_service = Container.sampling_service()
    elicitation_service = Container.elicitation_service()
    cleanup_task = asyncio.create_task(
        _periodic_cleanup(sampling_service, elicitation_service, interval=60)
    )

    yield

    # Shutdown
    # cleanup 태스크 취소 (M2 신규)
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

    # MCP SDK Track 세션 정리 (기존)
    mcp_client = Container.mcp_client_adapter()
    await mcp_client.disconnect_all()

app = FastAPI(lifespan=lifespan)
```

### 테스트

```python
# tests/integration/test_app_lifecycle.py

async def test_shutdown_disconnects_all_mcp_sessions(client):
    """서버 종료 시 모든 MCP 세션 정리됨"""
    # 1. MCP 엔드포인트 등록
    response = await client.post("/api/endpoints", json={
        "url": "http://localhost:9000/mcp",
        "type": "mcp",
    })
    endpoint_id = response.json()["id"]

    # 2. 세션 활성 확인
    mcp_client = Container.mcp_client_adapter()
    assert endpoint_id in mcp_client._sessions

    # 3. 서버 종료 트리거 (lifespan shutdown)
    # AsyncClient는 자동으로 lifespan 실행

    # 4. 세션 정리 확인 (이 테스트는 E2E 레벨에서 수행하기 어려움)
    # Integration 레벨에서는 disconnect_all() 단위 테스트로 대체
```

---

## Step 5.4: Dual-Track 상호작용 테스트 (신규 - 핵심)

**파일:** `tests/integration/test_dual_track.py`
**마커:** `@pytest.mark.local_mcp` + `@pytest.mark.llm`

### 시나리오

```
1. Synapse 등록 (Dual-Track: ADK + SDK)
2. ADK가 summarize 도구 호출
3. Synapse가 sampling 콜백 요청
4. AgentHub가 LLM 호출 후 결과 반환
5. ADK가 최종 응답 반환
```

### 테스트 코드

```python
import pytest
from src.adapters.inbound.http.app import app
from httpx import AsyncClient

@pytest.mark.local_mcp
@pytest.mark.llm
class TestDualTrack:
    """Dual-Track 상호작용 테스트 (Synapse + ADK + LLM)

    주의: Synapse Streamable HTTP에서 sampling 요청 시 hang 가능성
    → timeout 설정 필수
    """

    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture
    def synapse_url(self):
        return "http://localhost:9000/mcp"

    async def test_adk_calls_synapse_with_sampling(self, client, synapse_url):
        """ADK → Synapse 도구 호출 → Sampling 콜백 → LLM 호출 → 결과 반환"""
        # 1. Synapse 등록
        response = await client.post("/api/endpoints", json={
            "url": synapse_url,
            "type": "mcp",
        })
        assert response.status_code == 200
        endpoint_id = response.json()["id"]

        # 2. ADK에게 Synapse 도구 사용 지시
        # (summarize 도구가 sampling을 요청한다고 가정)
        response = await client.post("/api/chat", json={
            "message": "Summarize the latest news using Synapse",
            "conversation_id": "test-conv-1",
        })
        assert response.status_code == 200

        # 3. SSE 스트림에서 sampling_request 이벤트 확인
        # (이 테스트는 E2E Playwright로 구현하는 것이 더 적절)
        # Integration 레벨에서는 로그나 SamplingService 상태로 확인

        # 4. Sampling 요청 목록 확인
        response = await client.get("/api/sampling/requests")
        requests = response.json()["requests"]
        assert len(requests) > 0
        sampling_request = requests[0]

        # 5. Approve (LLM 호출 + 시그널)
        response = await client.post(f"/api/sampling/requests/{sampling_request['id']}/approve")
        assert response.status_code == 200

        # 6. ADK가 최종 응답 반환
        # (실제로는 chat SSE를 구독하여 확인해야 함)

    async def test_sampling_callback_timeout_sends_sse(self, client, synapse_url):
        """Sampling Short timeout 시 SSE 알림 전송"""
        # 1. Synapse 등록
        response = await client.post("/api/endpoints", json={
            "url": synapse_url,
            "type": "mcp",
        })
        endpoint_id = response.json()["id"]

        # 2. Sampling 요청 트리거 (approve 없이 30초 대기)
        # (이 테스트는 실제 30초를 기다려야 하므로, mock 또는 timeout 단축 필요)
        # 실제 구현 시에는 SamplingService.wait_for_response의 timeout을 mock

        # 3. SSE 이벤트 확인 (Playwright E2E로 구현 권장)
```

**주의사항:**
- Synapse Streamable HTTP에서 sampling 요청 시 hang 가능성 확인
- timeout 설정 필수 (30초 short, 270초 long)
- 실제 LLM 호출 비용 발생 → `@pytest.mark.llm` 마커 사용

---

## Verification

```bash
# Phase 1-4 복습 (Unit + Integration)
pytest tests/unit/ -q --tb=line -x
pytest tests/integration/test_mcp_client_adapter.py -m local_mcp -v

# Phase 5 Unit Tests (RegistryService)
pytest tests/unit/domain/services/test_registry_service.py::TestRegistryServiceWithMcpClient -v

# Phase 5 Dual-Track Tests (Synapse + LLM)
pytest tests/integration/test_dual_track.py -m "local_mcp and llm" -v

# 전체 Integration Tests
pytest tests/integration/ -m "local_mcp or llm" -v
```

---

## Step 5.5: Documentation Update

**목표:** Phase 5에서 구현된 Integration 레이어 문서화

**문서화 항목:**

| 작업 | 대상 파일 | 유형 | 내용 |
|------|----------|------|------|
| Create | docs/developers/architecture/integrations/dual-track.md | Integration Architecture | Dual-Track 아키텍처 상세 설명 (ADK Tools + SDK Resources/Prompts/Sampling/Elicitation) |
| Modify | docs/developers/architecture/integrations/dual-track.md | Integration Architecture | 동일 MCP 서버 이중 연결 구조, 리소스 모니터링 계획 포함 |
| Modify | docs/developers/guides/implementation/README.md | Implementation Guide | DI Container Provide[] 패턴 섹션 추가 (lambda 사용 금지 이유) |
| Create | docs/developers/guides/implementation/lifecycle-management.md | Implementation Guide | 서버 시작/종료 시 리소스 정리 패턴 (AsyncExitStack, disconnect_all(), cleanup 스케줄러) |
| Modify | tests/docs/EXECUTION.md | Test Documentation | Dual-Track 통합 테스트 실행 방법 추가 (마커 조합: local_mcp and llm) |
| Modify | docs/MAP.md | Directory Structure | docs/developers/architecture/integrations/ 내용 업데이트 |

**ADR 참조:**
- [ADR-A05 (Method C)](../../decisions/architecture/ADR-A05-method-c-callback-centric.md) — RegistryService 콜백 구현
- [ADR-A06 (Hybrid Timeout)](../../decisions/architecture/ADR-A06-hybrid-timeout-strategy.md) — 30s/270s timeout 전략
- [ADR-A07 (Dual-Track)](../../decisions/architecture/ADR-A07-dual-track-architecture.md) — 이중 연결 아키텍처

**주의사항:**
- dual-track.md는 신규 파일 생성 (복잡한 통합 패턴, 20+ 줄 필요)
- 리소스 오버헤드 모니터링 방법 포함 (로깅, 메트릭 수집 포인트)

---

## Checklist

- [ ] **Phase 시작**: Status 변경 (⏸️ → 🔄)
- [ ] Step 5.1: RegistryService 수정 (Method C 콜백, TDD)
- [ ] Step 5.2: DI Container 수정 (Provide[] 패턴)
- [ ] Step 5.3: 서버 종료 시 세션 정리 + cleanup 스케줄러
- [ ] Step 5.4: Dual-Track 통합 테스트 작성 및 통과
- [ ] Step 5.5: Documentation Update (Integration Architecture + Implementation Guides + ADR References)
- [ ] 모든 테스트 통과 확인
- [ ] **Phase 완료**: Status 변경 (🔄 → ✅)
- [ ] Git 커밋: `docs: complete phase N - {phase_name}`

---

## 이중 연결 리소스 모니터링

### 로깅 추가

```python
# src/domain/services/registry_service.py

logger.info(f"MCP endpoint {endpoint.id} connected: ADK Track + SDK Track")
logger.debug(f"SDK Track callbacks: sampling={sampling_cb is not None}, elicitation={elicitation_cb is not None}")
```

### 메트릭 (추후)

- 활성 SDK 세션 수
- 세션당 메모리 사용량 (프로파일링 필요 시)
- Sampling 요청 평균 응답 시간 (Short timeout vs Long timeout)

---

*Last Updated: 2026-02-07*
*Method C: Callback awaits Signal, Route calls LLM + approves*
