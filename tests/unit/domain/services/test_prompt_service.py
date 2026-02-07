"""PromptService 테스트 (TDD)

FakeMcpClient를 사용하여 Prompt 템플릿 조회 및 렌더링 기능을 테스트합니다.
"""

import pytest

from src.domain.entities.prompt_template import PromptTemplate
from src.domain.exceptions import EndpointNotFoundError, PromptNotFoundError
from src.domain.services.prompt_service import PromptService
from tests.unit.fakes.fake_mcp_client import FakeMcpClient


@pytest.fixture
def fake_mcp_client():
    """FakeMcpClient 픽스처"""
    return FakeMcpClient()


@pytest.fixture
def prompt_service(fake_mcp_client):
    """PromptService 픽스처"""
    return PromptService(mcp_client=fake_mcp_client)


class TestPromptService:
    """PromptService 테스트"""

    async def test_list_prompts_returns_templates(self, fake_mcp_client, prompt_service):
        """프롬프트 목록 조회"""
        # Given: FakeMcpClient에 프롬프트 설정 및 연결
        fake_mcp_client.set_prompts(
            "ep-1",
            [
                PromptTemplate(
                    name="greeting",
                    description="Greet user",
                    arguments=[{"name": "name", "description": "User name", "required": True}],
                )
            ],
        )
        await fake_mcp_client.connect("ep-1", "http://localhost:8080/mcp")

        # When: 프롬프트 목록 조회
        prompts = await prompt_service.list_prompts("ep-1")

        # Then: 프롬프트 목록 반환
        assert len(prompts) == 1
        assert prompts[0].name == "greeting"
        assert prompts[0].description == "Greet user"

    async def test_get_prompt_renders_with_arguments(self, fake_mcp_client, prompt_service):
        """프롬프트 렌더링 (arguments 적용)"""
        # Given: FakeMcpClient에 프롬프트 결과 설정 및 연결
        fake_mcp_client.set_prompt_result("ep-1", "greeting", "Hello, Alice!")
        await fake_mcp_client.connect("ep-1", "http://localhost:8080/mcp")

        # When: 프롬프트 렌더링
        result = await prompt_service.get_prompt("ep-1", "greeting", {"name": "Alice"})

        # Then: 렌더링 결과 반환
        assert "Hello, Alice!" in result

    async def test_get_prompt_not_found(self, fake_mcp_client, prompt_service):
        """존재하지 않는 prompt → PromptNotFoundError"""
        # Given: endpoint는 연결되어 있지만 프롬프트는 없음
        await fake_mcp_client.connect("ep-1", "http://localhost:8080/mcp")

        # When/Then: 존재하지 않는 프롬프트 조회 시 예외 발생
        with pytest.raises(PromptNotFoundError):
            await prompt_service.get_prompt("ep-1", "nonexistent")

    async def test_list_prompts_endpoint_not_found(self, prompt_service):
        """존재하지 않는 endpoint_id → EndpointNotFoundError"""
        # When/Then: 존재하지 않는 endpoint로 조회 시 예외 발생
        with pytest.raises(EndpointNotFoundError):
            await prompt_service.list_prompts("nonexistent")

    async def test_list_prompts_empty_endpoint(self, fake_mcp_client, prompt_service):
        """프롬프트가 없는 endpoint → 빈 리스트 반환"""
        # Given: 빈 프롬프트 목록 및 연결
        fake_mcp_client.set_prompts("ep-1", [])
        await fake_mcp_client.connect("ep-1", "http://localhost:8080/mcp")

        # When: 프롬프트 목록 조회
        prompts = await prompt_service.list_prompts("ep-1")

        # Then: 빈 리스트 반환
        assert prompts == []

    async def test_get_prompt_without_arguments(self, fake_mcp_client, prompt_service):
        """arguments 없이 프롬프트 렌더링"""
        # Given: FakeMcpClient에 프롬프트 결과 설정 및 연결
        fake_mcp_client.set_prompt_result("ep-1", "simple", "Simple prompt result")
        await fake_mcp_client.connect("ep-1", "http://localhost:8080/mcp")

        # When: arguments 없이 프롬프트 렌더링
        result = await prompt_service.get_prompt("ep-1", "simple")

        # Then: 렌더링 결과 반환
        assert result == "Simple prompt result"
