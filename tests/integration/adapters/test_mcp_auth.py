r"""
Integration tests for MCP authenticated connections

Synapse 다중 포트 모드 필요:
- Port 9000: 인증 없음 (기본)
- Port 9001: API Key 인증
- Port 9002: OAuth 2.0 (Step 8에서 추가)

실행 방법:
cd C:\Users\sungb\Documents\GitHub\MCP_SERVER\MCP_Streamable_HTTP
python -m synapse --multi
"""

import pytest

from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset
from src.domain.entities.auth_config import AuthConfig
from src.domain.entities.endpoint import Endpoint
from src.domain.entities.enums import EndpointType


@pytest.mark.asyncio
@pytest.mark.integration
class TestMcpAuthenticatedConnection:
    """MCP 서버 인증 연결 통합 테스트"""

    async def test_port_9000_no_auth_works(self):
        """
        Given: Synapse Port 9000 (인증 없음)
        When: auth_config 없이 연결
        Then: 정상 연결 및 도구 조회
        """
        # Given
        toolset = DynamicToolset()
        endpoint = Endpoint(
            url="http://127.0.0.1:9000/mcp",
            type=EndpointType.MCP,
            name="Synapse No Auth",
        )

        # When
        tools = await toolset.add_mcp_server(endpoint)

        # Then
        assert len(tools) > 0
        assert any(tool.name == "echo" for tool in tools)

        # Cleanup
        await toolset.close()

    async def test_port_9001_api_key_valid_succeeds(self):
        """
        Given: Synapse Port 9001 (API Key 인증)
        When: 올바른 API Key로 연결
        Then: 정상 연결 및 도구 조회
        """
        # Given
        toolset = DynamicToolset()
        auth = AuthConfig(
            auth_type="api_key",
            api_key="test-key-1",  # Synapse 설정에서 허용된 키
            api_key_header="X-API-Key",
            api_key_prefix="",
        )
        endpoint = Endpoint(
            url="http://127.0.0.1:9001/mcp",
            type=EndpointType.MCP,
            name="Synapse API Key",
            auth_config=auth,
        )

        # When
        tools = await toolset.add_mcp_server(endpoint)

        # Then
        assert len(tools) > 0
        assert any(tool.name == "echo" for tool in tools)

        # Cleanup
        await toolset.close()

    async def test_port_9001_api_key_invalid_fails(self):
        """
        Given: Synapse Port 9001 (API Key 인증)
        When: 잘못된 API Key로 연결
        Then: ConnectionError 발생
        """
        # Given
        toolset = DynamicToolset()
        auth = AuthConfig(
            auth_type="api_key",
            api_key="wrong-key",  # 잘못된 키
            api_key_header="X-API-Key",
            api_key_prefix="",
        )
        endpoint = Endpoint(
            url="http://127.0.0.1:9001/mcp",
            type=EndpointType.MCP,
            name="Synapse API Key",
            auth_config=auth,
        )

        # When/Then
        with pytest.raises(ConnectionError, match="Failed to connect to MCP server"):
            await toolset.add_mcp_server(endpoint)

        # Cleanup
        await toolset.close()

    async def test_port_9001_no_auth_fails(self):
        """
        Given: Synapse Port 9001 (API Key 필수)
        When: auth_config 없이 연결
        Then: ConnectionError 발생 (401 Unauthorized)
        """
        # Given
        toolset = DynamicToolset()
        endpoint = Endpoint(
            url="http://127.0.0.1:9001/mcp",
            type=EndpointType.MCP,
            name="Synapse API Key",
            # auth_config 없음
        )

        # When/Then
        with pytest.raises(ConnectionError, match="Failed to connect to MCP server"):
            await toolset.add_mcp_server(endpoint)

        # Cleanup
        await toolset.close()

    async def test_bearer_token_format(self):
        """
        Given: API Key with Bearer prefix
        When: auth_type="api_key", api_key_prefix="Bearer"
        Then: Authorization: Bearer xxx 헤더로 연결 (Port 9000에서 테스트)
        """
        # Given
        toolset = DynamicToolset()
        # Port 9000은 인증 optional이므로 Bearer 포맷도 허용
        auth = AuthConfig(
            auth_type="api_key",
            api_key="any-value",  # Port 9000은 인증 체크 안함
            api_key_header="Authorization",
            api_key_prefix="Bearer",
        )
        endpoint = Endpoint(
            url="http://127.0.0.1:9000/mcp",
            type=EndpointType.MCP,
            name="Synapse No Auth",
            auth_config=auth,
        )

        # When
        tools = await toolset.add_mcp_server(endpoint)

        # Then
        assert len(tools) > 0

        # Cleanup
        await toolset.close()

    async def test_custom_headers_auth(self):
        """
        Given: 커스텀 헤더 인증
        When: auth_type="header"
        Then: 커스텀 헤더로 연결 (Port 9000에서 테스트)
        """
        # Given
        toolset = DynamicToolset()
        auth = AuthConfig(
            auth_type="header",
            headers={"X-Custom-Auth": "value123"},
        )
        endpoint = Endpoint(
            url="http://127.0.0.1:9000/mcp",
            type=EndpointType.MCP,
            name="Synapse Custom Header",
            auth_config=auth,
        )

        # When
        tools = await toolset.add_mcp_server(endpoint)

        # Then
        assert len(tools) > 0

        # Cleanup
        await toolset.close()
