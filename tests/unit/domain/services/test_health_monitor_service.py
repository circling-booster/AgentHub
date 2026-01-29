"""HealthMonitorService 테스트"""

import asyncio

import pytest

from src.domain.entities.endpoint import Endpoint
from src.domain.entities.enums import EndpointStatus, EndpointType
from src.domain.services.health_monitor_service import HealthMonitorService
from tests.unit.fakes import FakeEndpointStorage, FakeToolset


class TestHealthMonitorService:
    """HealthMonitorService 테스트"""

    @pytest.fixture
    def storage(self):
        return FakeEndpointStorage()

    @pytest.fixture
    def toolset(self):
        return FakeToolset()

    @pytest.fixture
    def service(self, storage, toolset):
        return HealthMonitorService(
            storage=storage,
            toolset=toolset,
            check_interval_seconds=1,  # 빠른 테스트를 위해 짧게
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
