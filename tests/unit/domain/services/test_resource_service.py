"""ResourceService 테스트 (TDD)

FakeMcpClient를 사용하여 Resource 조회 기능을 테스트합니다.
"""

import pytest

from src.domain.entities.resource import Resource, ResourceContent
from src.domain.exceptions import EndpointNotFoundError, ResourceNotFoundError
from src.domain.services.resource_service import ResourceService
from tests.unit.fakes.fake_mcp_client import FakeMcpClient


@pytest.fixture
def fake_mcp_client():
    """FakeMcpClient 픽스처"""
    return FakeMcpClient()


@pytest.fixture
def resource_service(fake_mcp_client):
    """ResourceService 픽스처"""
    return ResourceService(mcp_client=fake_mcp_client)


class TestResourceService:
    """ResourceService 테스트"""

    async def test_list_resources_returns_list(self, fake_mcp_client, resource_service):
        """리소스 목록 조회 성공"""
        # Given: FakeMcpClient에 리소스 설정 및 연결
        fake_mcp_client.set_resources(
            "ep-1",
            [Resource(uri="file:///test.txt", name="test.txt", mime_type="text/plain")],
        )
        await fake_mcp_client.connect("ep-1", "http://localhost:8080/mcp")

        # When: 리소스 목록 조회
        resources = await resource_service.list_resources("ep-1")

        # Then: 리소스 목록 반환
        assert len(resources) == 1
        assert resources[0].uri == "file:///test.txt"
        assert resources[0].name == "test.txt"

    async def test_read_resource_returns_content(self, fake_mcp_client, resource_service):
        """리소스 읽기 성공"""
        # Given: FakeMcpClient에 리소스 콘텐츠 설정 및 연결
        fake_mcp_client.set_resource_content(
            "ep-1",
            "file:///test.txt",
            ResourceContent(uri="file:///test.txt", text="Hello", mime_type="text/plain"),
        )
        await fake_mcp_client.connect("ep-1", "http://localhost:8080/mcp")

        # When: 리소스 읽기
        content = await resource_service.read_resource("ep-1", "file:///test.txt")

        # Then: 콘텐츠 반환
        assert content.uri == "file:///test.txt"
        assert content.text == "Hello"
        assert content.mime_type == "text/plain"

    async def test_list_resources_endpoint_not_found(self, resource_service):
        """존재하지 않는 endpoint_id → EndpointNotFoundError"""
        # When/Then: 존재하지 않는 endpoint로 조회 시 예외 발생
        with pytest.raises(EndpointNotFoundError):
            await resource_service.list_resources("nonexistent")

    async def test_read_resource_not_found(self, fake_mcp_client, resource_service):
        """존재하지 않는 리소스 → ResourceNotFoundError"""
        # Given: endpoint는 연결되어 있지만 리소스는 없음
        fake_mcp_client.set_resources("ep-1", [])
        await fake_mcp_client.connect("ep-1", "http://localhost:8080/mcp")

        # When/Then: 존재하지 않는 리소스 읽기 시 예외 발생
        with pytest.raises(ResourceNotFoundError):
            await resource_service.read_resource("ep-1", "file:///nonexistent.txt")

    async def test_list_resources_empty_endpoint(self, fake_mcp_client, resource_service):
        """리소스가 없는 endpoint → 빈 리스트 반환"""
        # Given: 빈 리소스 목록 및 연결
        fake_mcp_client.set_resources("ep-1", [])
        await fake_mcp_client.connect("ep-1", "http://localhost:8080/mcp")

        # When: 리소스 목록 조회
        resources = await resource_service.list_resources("ep-1")

        # Then: 빈 리스트 반환
        assert resources == []
