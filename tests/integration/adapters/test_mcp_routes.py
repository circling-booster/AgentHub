"""MCP Management Routes Integration Tests

TDD Phase: GREEN - 구현 완료
"""

from fastapi import status

from src.domain.entities.endpoint import EndpointType


class TestMcpServerRegistration:
    """POST /api/mcp/servers - MCP 서버 등록"""

    def test_register_mcp_server_success(self, authenticated_client):
        """
        Given: 유효한 MCP 서버 URL
        When: POST /api/mcp/servers 호출
        Then: 201 Created, 서버 정보 반환
        """
        # Given: 유효한 MCP 서버 URL
        payload = {
            "url": "http://localhost:9000/mcp",
            "name": "Test MCP Server",
        }

        # When: MCP 서버 등록
        response = authenticated_client.post("/api/mcp/servers", json=payload)

        # Then: 201 Created
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["url"] == payload["url"]
        assert data["name"] == payload["name"]
        assert data["type"] == EndpointType.MCP.value
        assert "id" in data
        assert "registered_at" in data
        assert data["enabled"] is True

    def test_register_mcp_server_without_name(self, authenticated_client):
        """
        Given: name 없이 URL만 제공
        When: POST /api/mcp/servers 호출
        Then: 201 Created, URL 기반 기본 이름 생성
        """
        # Given: name 없이 URL만
        payload = {"url": "http://localhost:9000/mcp"}

        # When: MCP 서버 등록
        response = authenticated_client.post("/api/mcp/servers", json=payload)

        # Then: 201 Created, 기본 이름 생성됨
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["url"] == payload["url"]
        assert data["name"]  # 기본 이름 존재

    def test_register_mcp_server_invalid_url(self, authenticated_client):
        """
        Given: 잘못된 URL 형식
        When: POST /api/mcp/servers 호출
        Then: 422 Unprocessable Entity
        """
        # Given: 잘못된 URL
        payload = {"url": "not-a-valid-url"}

        # When: MCP 서버 등록 시도
        response = authenticated_client.post("/api/mcp/servers", json=payload)

        # Then: 422 Validation Error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_duplicate_mcp_server(self, authenticated_client):
        """
        Given: 이미 등록된 MCP 서버 URL
        When: 동일 URL로 재등록 시도
        Then: 400 Bad Request
        """
        # Given: MCP 서버 1차 등록
        payload = {"url": "http://localhost:9000/mcp", "name": "Test Server"}
        authenticated_client.post("/api/mcp/servers", json=payload)

        # When: 동일 URL로 재등록 시도
        response = authenticated_client.post("/api/mcp/servers", json=payload)

        # Then: 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "already registered" in data["message"].lower()


class TestMcpServerList:
    """GET /api/mcp/servers - 등록된 서버 목록 조회"""

    def test_list_mcp_servers_empty(self, authenticated_client):
        """
        Given: 등록된 서버가 없음
        When: GET /api/mcp/servers 호출
        Then: 200 OK, 빈 리스트 반환
        """
        # When: 서버 목록 조회
        response = authenticated_client.get("/api/mcp/servers")

        # Then: 200 OK, 빈 리스트
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_mcp_servers_with_items(self, authenticated_client):
        """
        Given: MCP 서버 등록됨
        When: GET /api/mcp/servers 호출
        Then: 200 OK, 등록된 서버 정보 반환
        """
        # Given: 서버 등록
        authenticated_client.post(
            "/api/mcp/servers", json={"url": "http://localhost:9000/mcp", "name": "Server 1"}
        )

        # When: 서버 목록 조회
        response = authenticated_client.get("/api/mcp/servers")

        # Then: 200 OK, 1개 서버
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert all("id" in server for server in data)
        assert all("url" in server for server in data)


class TestMcpServerRemoval:
    """DELETE /api/mcp/servers/{server_id} - 서버 해제"""

    def test_remove_mcp_server_success(self, authenticated_client):
        """
        Given: 등록된 MCP 서버
        When: DELETE /api/mcp/servers/{id} 호출
        Then: 204 No Content
        """
        # Given: MCP 서버 등록
        register_response = authenticated_client.post(
            "/api/mcp/servers", json={"url": "http://localhost:9000/mcp"}
        )
        server_id = register_response.json()["id"]

        # When: 서버 제거
        response = authenticated_client.delete(f"/api/mcp/servers/{server_id}")

        # Then: 204 No Content
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify: 목록에서 제거됨
        list_response = authenticated_client.get("/api/mcp/servers")
        assert len(list_response.json()) == 0

    def test_remove_nonexistent_server(self, authenticated_client):
        """
        Given: 존재하지 않는 서버 ID
        When: DELETE /api/mcp/servers/{id} 호출
        Then: 404 Not Found
        """
        # When: 없는 서버 제거 시도
        response = authenticated_client.delete("/api/mcp/servers/nonexistent-id")

        # Then: 404 Not Found
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestMcpServerTools:
    """GET /api/mcp/servers/{server_id}/tools - 서버의 도구 목록 조회"""

    def test_get_server_tools_success(self, authenticated_client):
        """
        Given: 등록된 MCP 서버
        When: GET /api/mcp/servers/{id}/tools 호출
        Then: 200 OK, 도구 목록 반환
        """
        # Given: MCP 서버 등록
        register_response = authenticated_client.post(
            "/api/mcp/servers", json={"url": "http://localhost:9000/mcp"}
        )
        server_id = register_response.json()["id"]

        # When: 서버의 도구 목록 조회
        response = authenticated_client.get(f"/api/mcp/servers/{server_id}/tools")

        # Then: 200 OK, 도구 목록
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # 실제 도구 조회는 Mock MCP 서버에 따라 다름

    def test_get_tools_for_nonexistent_server(self, authenticated_client):
        """
        Given: 존재하지 않는 서버 ID
        When: GET /api/mcp/servers/{id}/tools 호출
        Then: 404 Not Found
        """
        # When: 없는 서버의 도구 조회
        response = authenticated_client.get("/api/mcp/servers/nonexistent-id/tools")

        # Then: 404 Not Found
        assert response.status_code == status.HTTP_404_NOT_FOUND
