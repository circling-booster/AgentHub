"""RegistryService 테스트"""

import pytest

from src.domain.entities.endpoint import Endpoint
from src.domain.entities.enums import EndpointType
from src.domain.entities.tool import Tool
from src.domain.exceptions import EndpointConnectionError, EndpointNotFoundError
from src.domain.services.registry_service import RegistryService
from tests.unit.fakes import FakeEndpointStorage, FakeToolset
from tests.unit.fakes.fake_a2a_client import FakeA2aClient
from tests.unit.fakes.fake_orchestrator import FakeOrchestrator


class TestRegistryService:
    """RegistryService 테스트"""

    @pytest.fixture
    def storage(self):
        return FakeEndpointStorage()

    @pytest.fixture
    def toolset(self):
        return FakeToolset()

    @pytest.fixture
    def service(self, storage, toolset):
        return RegistryService(storage=storage, toolset=toolset)

    async def test_register_mcp_endpoint(self, service, toolset):
        """MCP 엔드포인트 등록"""
        # When
        endpoint = await service.register_endpoint(
            url="https://mcp.example.com/server",
            name="Test MCP",
        )

        # Then
        assert endpoint.type == EndpointType.MCP
        assert endpoint.name == "Test MCP"
        assert endpoint.url == "https://mcp.example.com/server"
        assert endpoint.id in toolset.added_servers

    async def test_register_endpoint_auto_detects_name(self, service):
        """이름 없이 등록 시 URL에서 추출"""
        # When
        endpoint = await service.register_endpoint(url="https://weather-api.example.com/mcp")

        # Then
        assert endpoint.name == "weather-api.example.com"

    async def test_register_endpoint_returns_tools(self, service, toolset):
        """등록 시 도구 목록이 엔드포인트에 포함됨"""
        # Given
        toolset.tools = [
            Tool(name="tool1", description="Tool 1"),
            Tool(name="tool2", description="Tool 2"),
        ]

        # When
        endpoint = await service.register_endpoint(url="https://mcp.example.com/server")

        # Then
        assert len(endpoint.tools) == 2
        assert endpoint.tools[0].name == "tool1"

    async def test_register_endpoint_connection_failure(self, storage):
        """연결 실패 시 에러"""
        # Given
        failing_toolset = FakeToolset(should_fail_connection=True)
        service = RegistryService(storage=storage, toolset=failing_toolset)

        # When / Then
        with pytest.raises(EndpointConnectionError):
            await service.register_endpoint(url="https://bad-server.com/mcp")

    async def test_unregister_endpoint(self, service, storage, toolset):
        """엔드포인트 등록 해제"""
        # Given
        endpoint = await service.register_endpoint(url="https://mcp.example.com/server")

        # When
        result = await service.unregister_endpoint(endpoint.id)

        # Then
        assert result is True
        assert endpoint.id not in storage.endpoints
        assert endpoint.id not in toolset.added_servers

    async def test_unregister_nonexistent_endpoint(self, service):
        """존재하지 않는 엔드포인트 해제"""
        # When
        result = await service.unregister_endpoint("nonexistent")

        # Then
        assert result is False

    async def test_list_endpoints(self, service, storage):
        """엔드포인트 목록 조회"""
        # Given
        await service.register_endpoint(url="https://server1.com/mcp")
        await service.register_endpoint(url="https://server2.com/mcp")

        # When
        endpoints = await service.list_endpoints()

        # Then
        assert len(endpoints) == 2

    async def test_list_endpoints_with_type_filter(self, service, storage):
        """타입 필터링으로 엔드포인트 조회"""
        # Given
        await service.register_endpoint(url="https://mcp-server.com/mcp")
        storage.endpoints["a2a-1"] = Endpoint(
            url="https://a2a-agent.com/a2a",
            type=EndpointType.A2A,
        )

        # When
        mcp_endpoints = await service.list_endpoints(type_filter="mcp")

        # Then
        assert len(mcp_endpoints) == 1
        assert mcp_endpoints[0].type == EndpointType.MCP

    async def test_get_endpoint(self, service, storage):
        """엔드포인트 조회"""
        # Given
        endpoint = await service.register_endpoint(url="https://server.com/mcp")

        # When
        result = await service.get_endpoint(endpoint.id)

        # Then
        assert result.id == endpoint.id

    async def test_get_endpoint_not_found(self, service):
        """존재하지 않는 엔드포인트 조회"""
        # When / Then
        with pytest.raises(EndpointNotFoundError):
            await service.get_endpoint("nonexistent")

    async def test_get_endpoint_tools(self, service, toolset):
        """엔드포인트 도구 조회"""
        # Given
        toolset.tools = [
            Tool(name="tool1", description="Tool 1"),
            Tool(name="tool2", description="Tool 2"),
        ]
        endpoint = await service.register_endpoint(url="https://server.com/mcp")

        # When
        tools = await service.get_endpoint_tools(endpoint.id)

        # Then
        assert len(tools) == 2

    async def test_check_endpoint_health(self, service, toolset):
        """엔드포인트 상태 확인"""
        # Given
        endpoint = await service.register_endpoint(url="https://server.com/mcp")

        # When
        is_healthy = await service.check_endpoint_health(endpoint.id)

        # Then
        assert is_healthy is True

    async def test_check_endpoint_health_not_found(self, service):
        """존재하지 않는 엔드포인트 상태 확인"""
        # When / Then
        with pytest.raises(EndpointNotFoundError):
            await service.check_endpoint_health("nonexistent")

    async def test_enable_endpoint(self, service, storage):
        """엔드포인트 활성화"""
        # Given
        endpoint = await service.register_endpoint(url="https://server.com/mcp")
        storage.endpoints[endpoint.id].enabled = False

        # When
        result = await service.enable_endpoint(endpoint.id)

        # Then
        assert result is True
        assert storage.endpoints[endpoint.id].enabled is True

    async def test_disable_endpoint(self, service, storage):
        """엔드포인트 비활성화"""
        # Given
        endpoint = await service.register_endpoint(url="https://server.com/mcp")

        # When
        result = await service.disable_endpoint(endpoint.id)

        # Then
        assert result is True
        assert storage.endpoints[endpoint.id].enabled is False


class TestRegistryServiceA2A:
    """RegistryService A2A 지원 테스트"""

    @pytest.fixture
    def storage(self):
        return FakeEndpointStorage()

    @pytest.fixture
    def toolset(self):
        return FakeToolset()

    @pytest.fixture
    def a2a_client(self):
        return FakeA2aClient()

    @pytest.fixture
    def service(self, storage, toolset, a2a_client):
        return RegistryService(storage=storage, toolset=toolset, a2a_client=a2a_client)

    async def test_register_a2a_endpoint(self, service, a2a_client):
        """
        Given: A2A 클라이언트가 설정된 RegistryService
        When: A2A 타입으로 엔드포인트 등록 시
        Then: agent_card가 포함된 A2A 엔드포인트 반환
        """
        # When
        endpoint = await service.register_endpoint(
            url="http://localhost:9001",
            name="Test A2A Agent",
            endpoint_type=EndpointType.A2A,
        )

        # Then
        assert endpoint.type == EndpointType.A2A
        assert endpoint.name == "Test A2A Agent"
        assert endpoint.agent_card is not None
        assert "name" in endpoint.agent_card
        assert endpoint.id in a2a_client._agents

    async def test_list_endpoints_a2a_filter(self, service):
        """
        Given: MCP와 A2A 엔드포인트가 등록된 상태
        When: type_filter="A2A"로 조회 시
        Then: A2A 엔드포인트만 반환
        """
        # Given
        await service.register_endpoint(url="https://mcp.example.com/server")
        await service.register_endpoint(
            url="http://localhost:9001",
            endpoint_type=EndpointType.A2A,
        )

        # When
        endpoints = await service.list_endpoints(type_filter=EndpointType.A2A)

        # Then
        assert len(endpoints) == 1
        assert endpoints[0].type == EndpointType.A2A

    async def test_unregister_a2a_endpoint(self, service, a2a_client):
        """
        Given: 등록된 A2A 엔드포인트
        When: unregister_endpoint() 호출 시
        Then: A2A 클라이언트에서도 제거됨
        """
        # Given
        endpoint = await service.register_endpoint(
            url="http://localhost:9001",
            endpoint_type=EndpointType.A2A,
        )

        # When
        result = await service.unregister_endpoint(endpoint.id)

        # Then
        assert result is True
        assert endpoint.id not in a2a_client._agents

    async def test_register_a2a_without_client_raises_error(self, storage, toolset):
        """
        Given: A2A 클라이언트 없는 RegistryService
        When: A2A 엔드포인트 등록 시도 시
        Then: ValueError 발생
        """
        # Given
        service_without_a2a = RegistryService(storage=storage, toolset=toolset)

        # When / Then
        with pytest.raises(ValueError, match="A2A client not configured"):
            await service_without_a2a.register_endpoint(
                url="http://localhost:9001",
                endpoint_type=EndpointType.A2A,
            )

    async def test_register_a2a_calls_orchestrator_add_agent(self, storage, toolset, a2a_client):
        """
        Given: orchestrator가 주입된 RegistryService
        When: A2A 엔드포인트 등록 시
        Then: orchestrator.add_a2a_agent()가 호출됨
        """
        # Given
        orchestrator = FakeOrchestrator()
        service = RegistryService(
            storage=storage,
            toolset=toolset,
            a2a_client=a2a_client,
            orchestrator=orchestrator,
        )

        # When
        endpoint = await service.register_endpoint(
            url="http://localhost:9001",
            endpoint_type=EndpointType.A2A,
        )

        # Then
        assert len(orchestrator.added_a2a_agents) == 1
        assert orchestrator.added_a2a_agents[0] == (endpoint.id, "http://localhost:9001")

    async def test_unregister_a2a_calls_orchestrator_remove_agent(
        self, storage, toolset, a2a_client
    ):
        """
        Given: orchestrator가 주입된 RegistryService + 등록된 A2A 엔드포인트
        When: A2A 엔드포인트 삭제 시
        Then: orchestrator.remove_a2a_agent()가 호출됨
        """
        # Given
        orchestrator = FakeOrchestrator()
        service = RegistryService(
            storage=storage,
            toolset=toolset,
            a2a_client=a2a_client,
            orchestrator=orchestrator,
        )
        endpoint = await service.register_endpoint(
            url="http://localhost:9001",
            endpoint_type=EndpointType.A2A,
        )

        # When
        await service.unregister_endpoint(endpoint.id)

        # Then
        assert len(orchestrator.removed_a2a_agents) == 1
        assert orchestrator.removed_a2a_agents[0] == endpoint.id

    async def test_register_a2a_without_orchestrator_graceful(self, storage, toolset, a2a_client):
        """
        Given: orchestrator=None인 RegistryService
        When: A2A 엔드포인트 등록 시
        Then: 에러 없이 정상 등록 (graceful skip)
        """
        # Given
        service = RegistryService(
            storage=storage,
            toolset=toolset,
            a2a_client=a2a_client,
            orchestrator=None,
        )

        # When
        endpoint = await service.register_endpoint(
            url="http://localhost:9001",
            endpoint_type=EndpointType.A2A,
        )

        # Then
        assert endpoint.type == EndpointType.A2A
        assert endpoint.agent_card is not None

    async def test_register_mcp_ignores_orchestrator(self, storage, toolset, a2a_client):
        """
        Given: orchestrator가 주입된 RegistryService
        When: MCP 엔드포인트 등록 시
        Then: orchestrator.add_a2a_agent()가 호출되지 않음 (regression 방지)
        """
        # Given
        orchestrator = FakeOrchestrator()
        service = RegistryService(
            storage=storage,
            toolset=toolset,
            a2a_client=a2a_client,
            orchestrator=orchestrator,
        )

        # When
        await service.register_endpoint(
            url="https://mcp.example.com/server",
            endpoint_type=EndpointType.MCP,
        )

        # Then
        assert len(orchestrator.added_a2a_agents) == 0


class TestRegistryServiceRestore:
    """RegistryService 엔드포인트 복원 테스트"""

    @pytest.fixture
    def storage(self):
        return FakeEndpointStorage()

    @pytest.fixture
    def toolset(self):
        return FakeToolset()

    @pytest.fixture
    def a2a_client(self):
        return FakeA2aClient()

    @pytest.fixture
    def orchestrator(self):
        return FakeOrchestrator()

    @pytest.fixture
    def service(self, storage, toolset, a2a_client, orchestrator):
        return RegistryService(
            storage=storage,
            toolset=toolset,
            a2a_client=a2a_client,
            orchestrator=orchestrator,
        )

    async def test_restore_mcp_endpoints_reconnects(self, service, storage, toolset):
        """
        Given: 저장소에 MCP 엔드포인트 존재
        When: restore_endpoints() 호출
        Then: DynamicToolset에 재연결됨
        """
        # Given: 저장소에 MCP 엔드포인트 저장
        mcp_endpoint = Endpoint(
            url="https://mcp.example.com/server",
            type=EndpointType.MCP,
            name="Test MCP",
        )
        await storage.save_endpoint(mcp_endpoint)

        # When: 복원
        result = await service.restore_endpoints()

        # Then: 재연결 성공
        assert mcp_endpoint.url in result["restored"]
        assert len(result["failed"]) == 0
        assert mcp_endpoint.id in toolset.added_servers

    async def test_restore_a2a_endpoints_rewires(self, service, storage, a2a_client, orchestrator):
        """
        Given: 저장소에 A2A 엔드포인트 존재
        When: restore_endpoints() 호출
        Then: A2A 클라이언트 + Orchestrator에 재등록됨
        """
        # Given: 저장소에 A2A 엔드포인트 저장
        a2a_endpoint = Endpoint(
            url="http://localhost:9001",
            type=EndpointType.A2A,
            name="Test A2A",
        )
        await storage.save_endpoint(a2a_endpoint)

        # When: 복원
        result = await service.restore_endpoints()

        # Then: 재등록 성공
        assert a2a_endpoint.url in result["restored"]
        assert len(result["failed"]) == 0
        assert a2a_endpoint.id in a2a_client._agents
        assert len(orchestrator.added_a2a_agents) == 1
        assert orchestrator.added_a2a_agents[0] == (
            a2a_endpoint.id,
            "http://localhost:9001",
        )

    async def test_restore_failed_endpoint_skipped(self, storage, a2a_client, orchestrator):
        """
        Given: 연결 실패하는 MCP 엔드포인트
        When: restore_endpoints() 호출
        Then: failed 목록에 포함되고 graceful 처리
        """
        # Given: 연결 실패하는 Toolset
        failing_toolset = FakeToolset(should_fail_connection=True)
        service = RegistryService(
            storage=storage,
            toolset=failing_toolset,
            a2a_client=a2a_client,
            orchestrator=orchestrator,
        )

        mcp_endpoint = Endpoint(
            url="https://bad-server.com/mcp",
            type=EndpointType.MCP,
        )
        await storage.save_endpoint(mcp_endpoint)

        # When: 복원
        result = await service.restore_endpoints()

        # Then: 실패 처리 (에러 없음)
        assert mcp_endpoint.url in result["failed"]
        assert len(result["restored"]) == 0

    async def test_restore_empty_storage(self, service):
        """
        Given: 저장소가 비어있음
        When: restore_endpoints() 호출
        Then: 빈 결과 반환
        """
        # When: 복원
        result = await service.restore_endpoints()

        # Then: 빈 결과
        assert len(result["restored"]) == 0
        assert len(result["failed"]) == 0


class TestRegistryServiceWithMcpClient:
    """SDK Track 통합 테스트 (Method C)"""

    @pytest.fixture
    def storage(self):
        return FakeEndpointStorage()

    @pytest.fixture
    def toolset(self):
        return FakeToolset()

    @pytest.fixture
    def mcp_client(self):
        from tests.unit.fakes.fake_mcp_client import FakeMcpClient

        return FakeMcpClient()

    @pytest.fixture
    def sampling_service(self):
        from src.domain.services.sampling_service import SamplingService

        return SamplingService(ttl_seconds=600)

    @pytest.fixture
    def elicitation_service(self):
        from src.domain.services.elicitation_service import ElicitationService

        return ElicitationService(ttl_seconds=600)

    @pytest.fixture
    def hitl_notification(self):
        from tests.unit.fakes.fake_hitl_notification import FakeHitlNotification

        return FakeHitlNotification()

    @pytest.fixture
    def service(self, storage, toolset, mcp_client, sampling_service, elicitation_service):
        return RegistryService(
            storage=storage,
            toolset=toolset,
            mcp_client=mcp_client,
            sampling_service=sampling_service,
            elicitation_service=elicitation_service,
        )

    async def test_register_mcp_connects_sdk_track(self, service, mcp_client):
        """
        Given: MCP Client가 설정된 RegistryService
        When: MCP 엔드포인트 등록 시
        Then: SDK Track도 연결되고 콜백이 설정됨
        """
        # When
        endpoint = await service.register_endpoint("http://localhost:8080/mcp")

        # Then: SDK Track 연결 확인
        assert mcp_client.is_connected(endpoint.id)
        # 콜백이 설정되었는지 확인
        assert mcp_client.get_sampling_callback(endpoint.id) is not None
        assert mcp_client.get_elicitation_callback(endpoint.id) is not None

    async def test_unregister_disconnects_sdk_track(self, service, mcp_client):
        """
        Given: SDK Track이 연결된 MCP 엔드포인트
        When: 엔드포인트 해제 시
        Then: SDK Track도 연결 해제됨
        """
        # Given
        endpoint = await service.register_endpoint("http://localhost:8080/mcp")
        assert mcp_client.is_connected(endpoint.id)

        # When
        await service.unregister_endpoint(endpoint.id)

        # Then
        assert not mcp_client.is_connected(endpoint.id)

    async def test_sampling_callback_waits_for_approval(
        self, storage, toolset, mcp_client, sampling_service
    ):
        """
        Given: SDK Track이 연결된 상태
        When: Sampling 콜백 호출 시
        Then: SamplingService에 요청이 생성되고 approve 대기 후 결과 반환
        """
        # Given
        service = RegistryService(
            storage=storage,
            toolset=toolset,
            mcp_client=mcp_client,
            sampling_service=sampling_service,
        )
        endpoint = await service.register_endpoint("http://localhost:8080/mcp")

        # 콜백 가져오기
        callback = mcp_client.get_sampling_callback(endpoint.id)
        assert callback is not None

        # 백그라운드에서 approve 실행 (0.1초 후)
        import asyncio

        async def delayed_approve():
            await asyncio.sleep(0.1)
            await sampling_service.approve("test-req-1", {"content": "LLM response"})

        asyncio.create_task(delayed_approve())

        # When: 콜백 실행
        result = await callback(
            request_id="test-req-1",
            endpoint_id=endpoint.id,
            messages=[{"role": "user", "content": "test"}],
            model_preferences=None,
            system_prompt=None,
            max_tokens=1024,
        )

        # Then: LLM 결과 반환됨
        assert result == {"content": "LLM response"}
        # SamplingService에 요청이 생성되었는지 확인
        request = sampling_service.get_request("test-req-1")
        assert request is not None
        assert request.id == "test-req-1"

    async def test_sampling_callback_timeout_notifies_sse(
        self, storage, toolset, mcp_client, sampling_service, hitl_notification
    ):
        """
        Given: SDK Track + HITL Notification이 설정된 상태
        When: Short timeout 초과 시
        Then: SSE 알림 전송됨
        """
        from src.domain.exceptions import HitlTimeoutError

        # Given: short_timeout=0.05초로 설정하여 빠른 테스트
        service = RegistryService(
            storage=storage,
            toolset=toolset,
            mcp_client=mcp_client,
            sampling_service=sampling_service,
            hitl_notification=hitl_notification,
            short_timeout=0.05,
            long_timeout=0.1,
        )
        endpoint = await service.register_endpoint("http://localhost:8080/mcp")

        callback = mcp_client.get_sampling_callback(endpoint.id)

        # When: Long timeout까지 대기 (approve 없음)
        with pytest.raises(HitlTimeoutError):
            await callback(
                request_id="test-req-timeout",
                endpoint_id=endpoint.id,
                messages=[{"role": "user", "content": "timeout test"}],
                model_preferences=None,
                system_prompt=None,
                max_tokens=1024,
            )

        # Then: SSE 알림 검증
        assert len(hitl_notification.sampling_notifications) > 0
        notified_request = hitl_notification.sampling_notifications[0]
        assert notified_request.id == "test-req-timeout"

    async def test_restore_endpoints_connects_sdk_track(self, storage, toolset, mcp_client):
        """
        Given: 저장소에 MCP 엔드포인트 존재
        When: restore_endpoints() 호출
        Then: SDK Track도 재연결됨 (M1 수정)
        """
        from src.domain.services.sampling_service import SamplingService
        from src.domain.services.elicitation_service import ElicitationService

        # Given: 저장소에 MCP 엔드포인트 저장
        mcp_endpoint = Endpoint(
            url="https://mcp.example.com/server",
            type=EndpointType.MCP,
            name="Test MCP",
        )
        await storage.save_endpoint(mcp_endpoint)

        # SDK Track 의존성 포함된 서비스
        service = RegistryService(
            storage=storage,
            toolset=toolset,
            mcp_client=mcp_client,
            sampling_service=SamplingService(),
            elicitation_service=ElicitationService(),
        )

        # When: 복원
        result = await service.restore_endpoints()

        # Then: 재연결 성공
        assert mcp_endpoint.url in result["restored"]
        assert len(result["failed"]) == 0
        # SDK Track 연결 확인
        assert mcp_client.is_connected(mcp_endpoint.id)
        assert mcp_client.get_sampling_callback(mcp_endpoint.id) is not None
        assert mcp_client.get_elicitation_callback(mcp_endpoint.id) is not None
