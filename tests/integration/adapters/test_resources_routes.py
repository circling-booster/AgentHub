"""Integration tests for Resources API routes

Tests the Resources HTTP API endpoints with FastAPI TestClient.
Follows TDD Red-Green-Refactor cycle.
"""

import pytest


class TestResourcesRoutes:
    """Resources API integration tests"""

    @pytest.fixture
    def registered_mcp_endpoint(self, authenticated_client):
        """Synapse 엔드포인트 등록 fixture"""
        response = authenticated_client.post(
            "/api/mcp/servers",
            json={
                "url": "http://localhost:9000/mcp",
                "name": "Test MCP Server",
            },
        )
        assert response.status_code == 201
        return response.json()

    @pytest.mark.local_mcp
    async def test_list_resources_returns_list(self, authenticated_client, registered_mcp_endpoint):
        """리소스 목록 조회 성공"""
        endpoint_id = registered_mcp_endpoint["id"]
        response = authenticated_client.get(f"/api/mcp/servers/{endpoint_id}/resources")

        if response.status_code != 200:
            print(f"Error detail: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert "resources" in data
        assert isinstance(data["resources"], list)
        assert len(data["resources"]) > 0

        # 첫 리소스 구조 검증
        resource = data["resources"][0]
        assert "uri" in resource
        assert "name" in resource
        assert "description" in resource

    async def test_list_resources_not_found(self, authenticated_client):
        """존재하지 않는 엔드포인트 → 404"""
        response = authenticated_client.get("/api/mcp/servers/nonexistent/resources")
        assert response.status_code == 404

    @pytest.mark.local_mcp
    async def test_read_resource_returns_content(
        self, authenticated_client, registered_mcp_endpoint
    ):
        """리소스 읽기 성공"""
        endpoint_id = registered_mcp_endpoint["id"]

        # 먼저 목록 조회
        list_response = authenticated_client.get(f"/api/mcp/servers/{endpoint_id}/resources")
        assert list_response.status_code == 200
        resources = list_response.json()["resources"]
        assert len(resources) > 0

        test_uri = resources[0]["uri"]

        # 리소스 읽기
        response = authenticated_client.get(f"/api/mcp/servers/{endpoint_id}/resources/{test_uri}")

        assert response.status_code == 200
        content = response.json()
        assert "uri" in content
        assert content["uri"] == test_uri
        # text 또는 blob 중 하나는 있어야 함
        assert ("text" in content and content["text"]) or ("blob" in content and content["blob"])

    @pytest.mark.local_mcp
    async def test_read_resource_not_found(self, authenticated_client, registered_mcp_endpoint):
        """존재하지 않는 리소스 → 404"""
        endpoint_id = registered_mcp_endpoint["id"]
        response = authenticated_client.get(
            f"/api/mcp/servers/{endpoint_id}/resources/nonexistent://resource"
        )
        assert response.status_code == 404

    async def test_read_resource_endpoint_not_found(self, authenticated_client):
        """존재하지 않는 엔드포인트로 리소스 읽기 → 404"""
        response = authenticated_client.get("/api/mcp/servers/nonexistent/resources/some://uri")
        assert response.status_code == 404
