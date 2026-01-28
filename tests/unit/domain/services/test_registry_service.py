"""RegistryService 테스트"""

import pytest

from src.domain.entities.endpoint import Endpoint
from src.domain.entities.enums import EndpointStatus, EndpointType
from src.domain.entities.tool import Tool
from src.domain.exceptions import EndpointConnectionError, EndpointNotFoundError
from src.domain.services.registry_service import RegistryService


class FakeEndpointStorage:
    """테스트용 Fake EndpointStorage"""

    def __init__(self):
        self.endpoints: dict[str, Endpoint] = {}

    async def save_endpoint(self, endpoint: Endpoint) -> None:
        self.endpoints[endpoint.id] = endpoint

    async def get_endpoint(self, endpoint_id: str) -> Endpoint | None:
        return self.endpoints.get(endpoint_id)

    async def list_endpoints(self, type_filter: str | None = None) -> list[Endpoint]:
        endpoints = list(self.endpoints.values())
        if type_filter:
            endpoints = [e for e in endpoints if e.type.value == type_filter]
        return endpoints

    async def delete_endpoint(self, endpoint_id: str) -> bool:
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            return True
        return False

    async def update_endpoint_status(self, endpoint_id: str, status: str) -> bool:
        if endpoint_id in self.endpoints:
            self.endpoints[endpoint_id].status = EndpointStatus(status)
            return True
        return False


class FakeToolset:
    """테스트용 Fake Toolset"""

    def __init__(self, tools: list[Tool] | None = None, should_fail: bool = False):
        self.tools = tools or [
            Tool(name="test_tool", description="A test tool"),
        ]
        self.should_fail = should_fail
        self.added_servers: list[str] = []
        self.removed_servers: list[str] = []
        self.health_status: dict[str, bool] = {}

    async def add_mcp_server(self, endpoint: Endpoint) -> list[Tool]:
        if self.should_fail:
            raise EndpointConnectionError(f"Failed to connect to {endpoint.url}")
        self.added_servers.append(endpoint.id)
        self.health_status[endpoint.id] = True
        return self.tools

    async def remove_mcp_server(self, endpoint_id: str) -> bool:
        if endpoint_id in self.added_servers:
            self.added_servers.remove(endpoint_id)
            self.health_status.pop(endpoint_id, None)
            return True
        return False

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        return f"Result from {tool_name}"

    async def get_tools(self) -> list[Tool]:
        return self.tools

    async def health_check(self, endpoint_id: str) -> bool:
        return self.health_status.get(endpoint_id, False)

    async def close(self) -> None:
        self.added_servers.clear()
        self.health_status.clear()


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

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_register_endpoint_auto_detects_name(self, service):
        """이름 없이 등록 시 URL에서 추출"""
        # When
        endpoint = await service.register_endpoint(url="https://weather-api.example.com/mcp")

        # Then
        assert endpoint.name == "weather-api.example.com"

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_register_endpoint_connection_failure(self, storage):
        """연결 실패 시 에러"""
        # Given
        failing_toolset = FakeToolset(should_fail=True)
        service = RegistryService(storage=storage, toolset=failing_toolset)

        # When / Then
        with pytest.raises(EndpointConnectionError):
            await service.register_endpoint(url="https://bad-server.com/mcp")

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_unregister_nonexistent_endpoint(self, service):
        """존재하지 않는 엔드포인트 해제"""
        # When
        result = await service.unregister_endpoint("nonexistent")

        # Then
        assert result is False

    @pytest.mark.asyncio
    async def test_list_endpoints(self, service, storage):
        """엔드포인트 목록 조회"""
        # Given
        await service.register_endpoint(url="https://server1.com/mcp")
        await service.register_endpoint(url="https://server2.com/mcp")

        # When
        endpoints = await service.list_endpoints()

        # Then
        assert len(endpoints) == 2

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_get_endpoint(self, service, storage):
        """엔드포인트 조회"""
        # Given
        endpoint = await service.register_endpoint(url="https://server.com/mcp")

        # When
        result = await service.get_endpoint(endpoint.id)

        # Then
        assert result.id == endpoint.id

    @pytest.mark.asyncio
    async def test_get_endpoint_not_found(self, service):
        """존재하지 않는 엔드포인트 조회"""
        # When / Then
        with pytest.raises(EndpointNotFoundError):
            await service.get_endpoint("nonexistent")

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_check_endpoint_health(self, service, toolset):
        """엔드포인트 상태 확인"""
        # Given
        endpoint = await service.register_endpoint(url="https://server.com/mcp")

        # When
        is_healthy = await service.check_endpoint_health(endpoint.id)

        # Then
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_check_endpoint_health_not_found(self, service):
        """존재하지 않는 엔드포인트 상태 확인"""
        # When / Then
        with pytest.raises(EndpointNotFoundError):
            await service.check_endpoint_health("nonexistent")

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_disable_endpoint(self, service, storage):
        """엔드포인트 비활성화"""
        # Given
        endpoint = await service.register_endpoint(url="https://server.com/mcp")

        # When
        result = await service.disable_endpoint(endpoint.id)

        # Then
        assert result is True
        assert storage.endpoints[endpoint.id].enabled is False
