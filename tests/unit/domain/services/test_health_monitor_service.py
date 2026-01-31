"""HealthMonitorService 테스트"""

import asyncio

import pytest

from src.domain.entities.endpoint import Endpoint
from src.domain.entities.enums import EndpointStatus, EndpointType
from src.domain.services.health_monitor_service import HealthMonitorService
from tests.unit.fakes import FakeA2aClient, FakeEndpointStorage, FakeToolset


class TestHealthMonitorService:
    """HealthMonitorService 테스트"""

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
    def service(self, storage, toolset):
        return HealthMonitorService(
            storage=storage,
            toolset=toolset,
            check_interval_seconds=1,  # 빠른 테스트를 위해 짧게
        )

    @pytest.fixture
    def service_with_a2a(self, storage, toolset, a2a_client):
        return HealthMonitorService(
            storage=storage,
            toolset=toolset,
            a2a_client=a2a_client,
            check_interval_seconds=1,
        )

    @pytest.mark.asyncio
    async def test_check_all_endpoints(self, service, storage, toolset):
        """모든 엔드포인트 상태 확인"""
        # Given
        ep1 = Endpoint(id="ep-1", url="https://server1.com/mcp", type=EndpointType.MCP)
        ep2 = Endpoint(id="ep-2", url="https://server2.com/mcp", type=EndpointType.MCP)
        storage.endpoints["ep-1"] = ep1
        storage.endpoints["ep-2"] = ep2
        toolset.health_status = {"ep-1": True, "ep-2": False}

        # When
        results = await service.check_all_endpoints()

        # Then
        assert results["ep-1"] is True
        assert results["ep-2"] is False

    @pytest.mark.asyncio
    async def test_check_all_endpoints_updates_status(self, service, storage, toolset):
        """상태 확인 후 엔드포인트 상태 갱신"""
        # Given
        ep = Endpoint(
            id="ep-1",
            url="https://server.com/mcp",
            type=EndpointType.MCP,
            status=EndpointStatus.UNKNOWN,
        )
        storage.endpoints["ep-1"] = ep
        toolset.health_status = {"ep-1": True}

        # When
        await service.check_all_endpoints()

        # Then
        assert storage.endpoints["ep-1"].status == EndpointStatus.CONNECTED

    @pytest.mark.asyncio
    async def test_check_all_endpoints_marks_error(self, service, storage, toolset):
        """실패한 엔드포인트는 ERROR 상태로"""
        # Given
        ep = Endpoint(
            id="ep-1",
            url="https://server.com/mcp",
            type=EndpointType.MCP,
            status=EndpointStatus.CONNECTED,
        )
        storage.endpoints["ep-1"] = ep
        toolset.health_status = {"ep-1": False}

        # When
        await service.check_all_endpoints()

        # Then
        assert storage.endpoints["ep-1"].status == EndpointStatus.ERROR

    @pytest.mark.asyncio
    async def test_check_single_endpoint(self, service, storage, toolset):
        """단일 엔드포인트 상태 확인"""
        # Given
        ep = Endpoint(id="ep-1", url="https://server.com/mcp", type=EndpointType.MCP)
        storage.endpoints["ep-1"] = ep
        toolset.health_status = {"ep-1": True}

        # When
        result = await service.check_endpoint("ep-1")

        # Then
        assert result is True

    @pytest.mark.asyncio
    async def test_check_nonexistent_endpoint(self, service):
        """존재하지 않는 엔드포인트 확인"""
        # When
        result = await service.check_endpoint("nonexistent")

        # Then
        assert result is False

    @pytest.mark.asyncio
    async def test_start_and_stop(self, service):
        """모니터 시작 및 중지"""
        # When
        await service.start()

        # Then
        assert service.is_running is True

        # When
        await service.stop()

        # Then
        assert service.is_running is False

    @pytest.mark.asyncio
    async def test_start_runs_initial_check(self, service, storage, toolset):
        """시작 시 초기 상태 확인 실행"""
        # Given
        ep = Endpoint(
            id="ep-1",
            url="https://server.com/mcp",
            type=EndpointType.MCP,
            status=EndpointStatus.UNKNOWN,
        )
        storage.endpoints["ep-1"] = ep
        toolset.health_status = {"ep-1": True}

        # When
        await service.start()
        await asyncio.sleep(0.1)  # 비동기 작업 완료 대기
        await service.stop()

        # Then
        assert storage.endpoints["ep-1"].status == EndpointStatus.CONNECTED

    @pytest.mark.asyncio
    async def test_only_checks_enabled_endpoints(self, service, storage, toolset):
        """활성화된 엔드포인트만 확인"""
        # Given
        ep1 = Endpoint(
            id="ep-1",
            url="https://server1.com/mcp",
            type=EndpointType.MCP,
            enabled=True,
        )
        ep2 = Endpoint(
            id="ep-2",
            url="https://server2.com/mcp",
            type=EndpointType.MCP,
            enabled=False,
        )
        storage.endpoints["ep-1"] = ep1
        storage.endpoints["ep-2"] = ep2
        toolset.health_status = {"ep-1": True, "ep-2": True}

        # When
        results = await service.check_all_endpoints()

        # Then
        assert "ep-1" in results
        assert "ep-2" not in results  # 비활성화된 엔드포인트는 제외


class TestHealthMonitorServiceA2aSupport:
    """HealthMonitorService A2A 지원 테스트"""

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
    def service_with_a2a(self, storage, toolset, a2a_client):
        return HealthMonitorService(
            storage=storage,
            toolset=toolset,
            a2a_client=a2a_client,
            check_interval_seconds=1,
        )

    @pytest.mark.asyncio
    async def test_check_a2a_agent_healthy(self, service_with_a2a, storage, a2a_client):
        """
        RED: A2A 에이전트 health check - 정상

        Given: A2A 에이전트가 등록됨
        When: check_endpoint() 호출
        Then: True 반환 및 CONNECTED 상태로 갱신
        """
        # Given
        endpoint = Endpoint(
            id="a2a-1",
            url="https://agent.com/a2a",
            type=EndpointType.A2A,
            status=EndpointStatus.UNKNOWN,
        )
        storage.endpoints["a2a-1"] = endpoint
        # A2A 에이전트 등록
        await a2a_client.register_agent(endpoint)

        # When
        result = await service_with_a2a.check_endpoint("a2a-1")

        # Then
        assert result is True
        assert storage.endpoints["a2a-1"].status == EndpointStatus.CONNECTED

    @pytest.mark.asyncio
    async def test_check_a2a_agent_unhealthy(self, service_with_a2a, storage, a2a_client):
        """
        RED: A2A 에이전트 health check - 비정상

        Given: A2A 에이전트가 미등록됨
        When: check_endpoint() 호출
        Then: False 반환 및 ERROR 상태로 갱신
        """
        # Given
        endpoint = Endpoint(
            id="a2a-1",
            url="https://agent.com/a2a",
            type=EndpointType.A2A,
            status=EndpointStatus.CONNECTED,
        )
        storage.endpoints["a2a-1"] = endpoint
        # A2A 에이전트 미등록 상태

        # When
        result = await service_with_a2a.check_endpoint("a2a-1")

        # Then
        assert result is False
        assert storage.endpoints["a2a-1"].status == EndpointStatus.ERROR

    @pytest.mark.asyncio
    async def test_check_all_endpoints_with_mixed_types(
        self, service_with_a2a, storage, toolset, a2a_client
    ):
        """
        RED: MCP와 A2A 엔드포인트 혼합 health check

        Given: MCP 서버 1개, A2A 에이전트 1개
        When: check_all_endpoints() 호출
        Then: 각각의 포트로 health check 수행
        """
        # Given: MCP 엔드포인트
        mcp_ep = Endpoint(
            id="mcp-1",
            url="https://server.com/mcp",
            type=EndpointType.MCP,
        )
        storage.endpoints["mcp-1"] = mcp_ep
        toolset.health_status = {"mcp-1": True}

        # Given: A2A 엔드포인트
        a2a_ep = Endpoint(
            id="a2a-1",
            url="https://agent.com/a2a",
            type=EndpointType.A2A,
        )
        storage.endpoints["a2a-1"] = a2a_ep
        await a2a_client.register_agent(a2a_ep)

        # When
        results = await service_with_a2a.check_all_endpoints()

        # Then
        assert results["mcp-1"] is True
        assert results["a2a-1"] is True
        assert storage.endpoints["mcp-1"].status == EndpointStatus.CONNECTED
        assert storage.endpoints["a2a-1"].status == EndpointStatus.CONNECTED
