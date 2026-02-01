"""FakeA2aClient Unit Tests

Fake A2A Client가 A2aPort 인터페이스를 올바르게 구현하는지 검증합니다.
"""

import pytest

from src.domain.entities.endpoint import Endpoint, EndpointType
from src.domain.exceptions import EndpointConnectionError, EndpointNotFoundError
from tests.unit.fakes.fake_a2a_client import FakeA2aClient


class TestFakeA2aClientRegister:
    """Agent 등록 테스트"""

    @pytest.mark.asyncio
    async def test_register_agent_returns_agent_card(self):
        """
        Given: FakeA2aClient 인스턴스
        When: A2A 엔드포인트를 등록하면
        Then: Agent Card가 반환됨
        """
        # Given
        client = FakeA2aClient()
        endpoint = Endpoint(
            id="test-agent-1",
            name="Test Agent",
            url="http://localhost:9001",
            type=EndpointType.A2A,
        )

        # When
        agent_card = await client.register_agent(endpoint)

        # Then
        assert agent_card is not None
        assert "name" in agent_card
        assert "description" in agent_card
        assert "version" in agent_card
        assert agent_card["name"] == "Test Agent"

    @pytest.mark.asyncio
    async def test_register_agent_connection_failure(self):
        """
        Given: 특정 URL이 실패하도록 설정된 FakeA2aClient
        When: 해당 URL로 등록 시도하면
        Then: EndpointConnectionError 발생
        """
        # Given
        client = FakeA2aClient()
        fail_url = "http://unreachable:9999"
        client.set_fail_on_register(fail_url)

        endpoint = Endpoint(
            id="fail-agent",
            name="Failing Agent",
            url=fail_url,
            type=EndpointType.A2A,
        )

        # When & Then
        with pytest.raises(EndpointConnectionError):
            await client.register_agent(endpoint)


class TestFakeA2aClientCall:
    """Agent 호출 테스트"""

    @pytest.mark.asyncio
    async def test_call_agent_returns_response_stream(self):
        """
        Given: 등록된 A2A 에이전트
        When: call_agent()로 메시지를 전송하면
        Then: 응답이 스트리밍으로 반환됨
        """
        # Given
        client = FakeA2aClient()
        endpoint = Endpoint(
            id="test-agent-2",
            name="Echo Agent",
            url="http://localhost:9002",
            type=EndpointType.A2A,
        )
        await client.register_agent(endpoint)

        # When
        response_chunks = []
        async for chunk in client.call_agent("test-agent-2", "Hello World"):
            response_chunks.append(chunk)

        # Then
        response = "".join(response_chunks).strip()
        assert "Hello World" in response
        assert len(response_chunks) > 1  # 스트리밍 확인

    @pytest.mark.asyncio
    async def test_call_agent_not_found(self):
        """
        Given: FakeA2aClient 인스턴스
        When: 등록되지 않은 에이전트를 호출하면
        Then: EndpointNotFoundError 발생
        """
        # Given
        client = FakeA2aClient()

        # When & Then
        with pytest.raises(EndpointNotFoundError):
            async for _ in client.call_agent("nonexistent-agent", "test"):
                pass

    @pytest.mark.asyncio
    async def test_call_agent_connection_failure(self):
        """
        Given: 호출 실패하도록 설정된 에이전트
        When: call_agent() 호출 시
        Then: EndpointConnectionError 발생
        """
        # Given
        client = FakeA2aClient()
        endpoint = Endpoint(
            id="fail-agent-call",
            name="Failing Agent",
            url="http://localhost:9003",
            type=EndpointType.A2A,
        )
        await client.register_agent(endpoint)
        client.set_fail_on_call("fail-agent-call")

        # When & Then
        with pytest.raises(EndpointConnectionError):
            async for _ in client.call_agent("fail-agent-call", "test"):
                pass


class TestFakeA2aClientQuery:
    """Agent Card 조회 테스트"""

    @pytest.mark.asyncio
    async def test_get_agent_card(self):
        """
        Given: 등록된 A2A 에이전트
        When: get_agent_card()로 조회하면
        Then: Agent Card가 반환됨
        """
        # Given
        client = FakeA2aClient()
        endpoint = Endpoint(
            id="test-agent-3",
            name="Query Agent",
            url="http://localhost:9004",
            type=EndpointType.A2A,
        )
        await client.register_agent(endpoint)

        # When
        agent_card = await client.get_agent_card("test-agent-3")

        # Then
        assert agent_card["name"] == "Query Agent"

    @pytest.mark.asyncio
    async def test_get_agent_card_not_found(self):
        """
        Given: FakeA2aClient 인스턴스
        When: 등록되지 않은 에이전트 Card 조회 시
        Then: EndpointNotFoundError 발생
        """
        # Given
        client = FakeA2aClient()

        # When & Then
        with pytest.raises(EndpointNotFoundError):
            await client.get_agent_card("nonexistent-agent")


class TestFakeA2aClientUnregister:
    """Agent 등록 해제 테스트"""

    @pytest.mark.asyncio
    async def test_unregister_agent(self):
        """
        Given: 등록된 A2A 에이전트
        When: unregister_agent() 호출 시
        Then: True 반환 및 에이전트 삭제됨
        """
        # Given
        client = FakeA2aClient()
        endpoint = Endpoint(
            id="test-agent-4",
            name="Temp Agent",
            url="http://localhost:9005",
            type=EndpointType.A2A,
        )
        await client.register_agent(endpoint)

        # When
        result = await client.unregister_agent("test-agent-4")

        # Then
        assert result is True
        # 삭제 확인
        with pytest.raises(EndpointNotFoundError):
            await client.get_agent_card("test-agent-4")

    @pytest.mark.asyncio
    async def test_unregister_nonexistent_agent(self):
        """
        Given: FakeA2aClient 인스턴스
        When: 등록되지 않은 에이전트 해제 시도 시
        Then: False 반환
        """
        # Given
        client = FakeA2aClient()

        # When
        result = await client.unregister_agent("nonexistent-agent")

        # Then
        assert result is False


class TestFakeA2aClientHealth:
    """Agent Health Check 테스트"""

    @pytest.mark.asyncio
    async def test_health_check_registered_agent(self):
        """
        Given: 등록된 A2A 에이전트
        When: health_check() 호출 시
        Then: True 반환
        """
        # Given
        client = FakeA2aClient()
        endpoint = Endpoint(
            id="test-agent-5",
            name="Healthy Agent",
            url="http://localhost:9006",
            type=EndpointType.A2A,
        )
        await client.register_agent(endpoint)

        # When
        is_healthy = await client.health_check("test-agent-5")

        # Then
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_nonexistent_agent(self):
        """
        Given: FakeA2aClient 인스턴스
        When: 등록되지 않은 에이전트 health check 시
        Then: False 반환
        """
        # Given
        client = FakeA2aClient()

        # When
        is_healthy = await client.health_check("nonexistent-agent")

        # Then
        assert is_healthy is False
