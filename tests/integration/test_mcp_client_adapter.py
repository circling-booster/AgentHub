"""Integration tests for McpClientAdapter

McpClientAdapter는 MCP Python SDK를 사용하여 MCP 서버와 통신합니다.
실제 MCP 서버(Synapse)가 localhost:9000에서 실행 중이어야 합니다.

테스트 실행:
    pytest tests/integration/test_mcp_client_adapter.py -m local_mcp -v
"""

import contextlib

import anyio
import pytest

from src.adapters.outbound.mcp.mcp_client_adapter import McpClientAdapter
from src.domain.exceptions import EndpointNotFoundError


@pytest.mark.local_mcp  # 로컬 MCP 서버 필요
class TestMcpClientAdapter:
    """McpClientAdapter Integration 테스트

    Note: 실제 MCP 서버(Synapse)가 필요합니다.
    """

    @pytest.fixture
    async def adapter(self):
        """McpClientAdapter fixture with safe teardown

        Note: anyio plugin의 fixture teardown과 MCP SDK의 cancel scope 충돌을 방지하기 위해
        ClosedResourceError를 명시적으로 catch합니다.
        """
        adapter = McpClientAdapter()
        yield adapter
        # 테스트에서 이미 disconnect_all()을 호출한 경우
        # anyio plugin이 닫힌 리소스에 접근하려고 할 때 발생
        # 이는 정상적인 cleanup이므로 무시
        with contextlib.suppress(anyio.ClosedResourceError):
            await adapter.disconnect_all()

    @pytest.fixture
    def synapse_url(self):
        return "http://localhost:9000/mcp"  # Synapse Streamable HTTP

    async def test_connect_and_list_resources(self, adapter, synapse_url):
        """연결 후 리소스 목록 조회"""
        await adapter.connect("synapse", synapse_url)

        resources = await adapter.list_resources("synapse")

        assert isinstance(resources, list)
        # Synapse는 최소 1개 이상의 리소스 제공
        assert len(resources) > 0
        assert all(hasattr(r, "uri") for r in resources)

    async def test_read_resource_returns_content(self, adapter, synapse_url):
        """리소스 읽기 성공"""
        await adapter.connect("synapse", synapse_url)
        resources = await adapter.list_resources("synapse")
        test_uri = resources[0].uri  # 첫 번째 리소스

        content = await adapter.read_resource("synapse", test_uri)

        assert content.uri == test_uri
        assert (content.text is not None) or (content.blob is not None)

    async def test_list_prompts_returns_templates(self, adapter, synapse_url):
        """프롬프트 목록 조회"""
        await adapter.connect("synapse", synapse_url)

        prompts = await adapter.list_prompts("synapse")

        assert isinstance(prompts, list)
        # Synapse는 summarize 등 프롬프트 제공
        assert len(prompts) > 0
        assert all(hasattr(p, "name") for p in prompts)

    async def test_get_prompt_renders(self, adapter, synapse_url):
        """프롬프트 렌더링"""
        await adapter.connect("synapse", synapse_url)
        prompts = await adapter.list_prompts("synapse")

        # 필수 인자가 없는 프롬프트 찾기
        test_prompt = next((p for p in prompts if not any(a.required for a in p.arguments)), None)
        if test_prompt is None:
            # 모든 프롬프트가 필수 인자를 요구하면 건너뛰기
            pytest.skip("No prompts without required arguments available")

        result = await adapter.get_prompt("synapse", test_prompt.name, {})

        assert isinstance(result, str)
        assert len(result) > 0

    async def test_disconnect_cleans_up_session(self, adapter, synapse_url):
        """disconnect 후 세션 정리"""
        await adapter.connect("synapse", synapse_url)
        await adapter.disconnect("synapse")

        with pytest.raises(EndpointNotFoundError):
            await adapter.list_resources("synapse")

    async def test_disconnect_all_cleans_everything(self, synapse_url):
        """disconnect_all 후 모든 세션 정리

        Note: 이 테스트는 fixture를 사용하지 않고 독립적인 adapter를 생성합니다.
        이는 anyio plugin의 fixture teardown과 MCP SDK cancel scope 간 충돌을 피하기 위함입니다.
        """
        # Fixture 대신 로컬 adapter 생성
        adapter = McpClientAdapter()

        try:
            await adapter.connect("synapse-1", synapse_url)
            await adapter.connect("synapse-2", synapse_url)

            await adapter.disconnect_all()

            with pytest.raises(EndpointNotFoundError):
                await adapter.list_resources("synapse-1")
            with pytest.raises(EndpointNotFoundError):
                await adapter.list_resources("synapse-2")
        finally:
            # 명시적 cleanup (anyio ClosedResourceError 무시)
            # 이미 정리되었거나 anyio teardown 충돌 시 무시
            with contextlib.suppress(anyio.ClosedResourceError, Exception):
                await adapter.disconnect_all()

    # Sampling 콜백 테스트는 Phase 5에서 수행 (callback 설정 필요)
