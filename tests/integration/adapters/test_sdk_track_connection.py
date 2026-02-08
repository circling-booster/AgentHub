"""SDK Track 연결 테스트 (TDD 디버깅)

근본 원인 파악을 위한 단순화된 테스트
"""

import pytest


@pytest.mark.local_mcp
class TestSdkTrackConnection:
    """SDK Track 연결이 제대로 되는지 검증"""

    async def test_mcp_server_registration_connects_sdk_track(self, authenticated_client):
        """MCP 서버 등록 시 SDK Track이 연결되는지 확인

        Given: Synapse MCP 서버가 실행 중
        When: MCP 서버를 등록
        Then: SDK Track (MCP Client)가 연결되어야 함
        """
        # When: MCP 서버 등록
        response = authenticated_client.post(
            "/api/mcp/servers",
            json={
                "url": "http://localhost:9000/mcp",
                "name": "Test Synapse",
            },
        )

        # Then: 등록 성공
        assert response.status_code == 201
        endpoint_data = response.json()
        endpoint_id = endpoint_data["id"]

        # Then: SDK Track 연결 확인 (McpClientAdapter에 세션이 있는지 확인)
        # 방법 1: Container에서 mcp_client_adapter 가져와서 _sessions 확인

        container = authenticated_client.app.container
        mcp_client = container.mcp_client_adapter()

        # 세션이 등록되어 있어야 함
        assert endpoint_id in mcp_client._sessions, f"SDK Track not connected for {endpoint_id}"

    async def test_registry_service_has_mcp_client(self, authenticated_client):
        """registry_service에 mcp_client가 주입되어 있는지 확인

        Given: authenticated_client
        When: registry_service를 가져옴
        Then: mcp_client가 None이 아니어야 함 (Dual-Track 활성화)
        """

        container = authenticated_client.app.container
        registry_service = container.registry_service()

        # mcp_client가 주입되어 있어야 함
        assert registry_service._mcp_client is not None, (
            "mcp_client is None (Dual-Track not enabled)"
        )
