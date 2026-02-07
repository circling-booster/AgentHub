"""FakeMcpClient 테스트 (TDD - Red Phase)

FakeMcpClient 자체의 동작을 검증합니다.
"""

import pytest

from src.domain.entities.prompt_template import PromptArgument, PromptTemplate
from src.domain.entities.resource import Resource, ResourceContent
from src.domain.exceptions import (
    EndpointNotFoundError,
    PromptNotFoundError,
    ResourceNotFoundError,
)
from tests.unit.fakes.fake_mcp_client import FakeMcpClient


class TestFakeMcpClient:
    """FakeMcpClient 자체 테스트"""

    async def test_connect_stores_connection(self):
        """connect 후 is_connected True"""
        fake = FakeMcpClient()
        await fake.connect("ep-1", "http://localhost:8080/mcp")
        assert fake.is_connected("ep-1")

    async def test_disconnect_removes_connection(self):
        """disconnect 후 is_connected False"""
        fake = FakeMcpClient()
        await fake.connect("ep-1", "http://localhost:8080/mcp")
        await fake.disconnect("ep-1")
        assert not fake.is_connected("ep-1")

    async def test_disconnect_all_removes_all_connections(self):
        """disconnect_all 후 모든 연결 해제"""
        fake = FakeMcpClient()
        await fake.connect("ep-1", "http://localhost:8080/mcp")
        await fake.connect("ep-2", "http://localhost:9000/mcp")
        await fake.disconnect_all()
        assert not fake.is_connected("ep-1")
        assert not fake.is_connected("ep-2")

    async def test_list_resources_returns_preset(self):
        """set_resources로 설정한 리소스 반환"""
        fake = FakeMcpClient()
        resources = [Resource(uri="file:///test.txt", name="test")]
        fake.set_resources("ep-1", resources)

        await fake.connect("ep-1", "http://localhost:8080/mcp")
        result = await fake.list_resources("ep-1")

        assert result == resources

    async def test_list_resources_raises_when_not_connected(self):
        """연결 안 된 상태에서 list_resources → 예외"""
        fake = FakeMcpClient()
        with pytest.raises(EndpointNotFoundError):
            await fake.list_resources("ep-1")

    async def test_read_resource_returns_content(self):
        """set_resource_content로 설정한 콘텐츠 반환"""
        fake = FakeMcpClient()
        content = ResourceContent(uri="file:///test.txt", text="Hello")
        fake.set_resource_content("ep-1", "file:///test.txt", content)

        await fake.connect("ep-1", "http://localhost:8080/mcp")
        result = await fake.read_resource("ep-1", "file:///test.txt")

        assert result.text == "Hello"

    async def test_read_resource_raises_when_not_found(self):
        """존재하지 않는 리소스 읽기 시도 시 예외"""
        fake = FakeMcpClient()
        await fake.connect("ep-1", "http://localhost:8080/mcp")

        with pytest.raises(ResourceNotFoundError):
            await fake.read_resource("ep-1", "file:///nonexistent.txt")

    async def test_list_prompts_returns_preset(self):
        """set_prompts로 설정한 프롬프트 반환"""
        fake = FakeMcpClient()
        prompts = [
            PromptTemplate(
                name="greeting",
                description="Say hello",
                arguments=[PromptArgument(name="name", description="User name", required=True)],
            )
        ]
        fake.set_prompts("ep-1", prompts)

        await fake.connect("ep-1", "http://localhost:8080/mcp")
        result = await fake.list_prompts("ep-1")

        assert len(result) == 1
        assert result[0].name == "greeting"

    async def test_get_prompt_renders_template(self):
        """set_prompt_result로 설정한 결과 반환"""
        fake = FakeMcpClient()
        fake.set_prompt_result("ep-1", "greeting", "Hello, Alice!")

        await fake.connect("ep-1", "http://localhost:8080/mcp")
        result = await fake.get_prompt("ep-1", "greeting", {"name": "Alice"})

        assert result == "Hello, Alice!"

    async def test_get_prompt_raises_when_not_found(self):
        """존재하지 않는 프롬프트 렌더링 시도 시 예외"""
        fake = FakeMcpClient()
        await fake.connect("ep-1", "http://localhost:8080/mcp")

        with pytest.raises(PromptNotFoundError):
            await fake.get_prompt("ep-1", "nonexistent", {})

    async def test_callback_stored_on_connect(self):
        """콜백이 connect 시 저장됨"""
        fake = FakeMcpClient()

        async def sample_callback(**kwargs):
            return {"role": "assistant", "content": "test"}

        await fake.connect("ep-1", "http://localhost:8080/mcp", sampling_callback=sample_callback)
        stored = fake.get_sampling_callback("ep-1")

        assert stored is sample_callback

    async def test_elicitation_callback_stored_on_connect(self):
        """Elicitation 콜백이 connect 시 저장됨"""
        fake = FakeMcpClient()

        async def elicit_callback(**kwargs):
            return {"value": "user input"}

        await fake.connect(
            "ep-1", "http://localhost:8080/mcp", elicitation_callback=elicit_callback
        )
        stored = fake.get_elicitation_callback("ep-1")

        assert stored is elicit_callback

    async def test_reset_clears_all_state(self):
        """reset()이 모든 상태 초기화"""
        fake = FakeMcpClient()

        # 상태 설정
        await fake.connect("ep-1", "http://localhost:8080/mcp")
        fake.set_resources("ep-1", [Resource(uri="file:///test.txt", name="test")])

        # 초기화
        fake.reset()

        # 검증
        assert not fake.is_connected("ep-1")
        with pytest.raises(EndpointNotFoundError):
            await fake.list_resources("ep-1")
