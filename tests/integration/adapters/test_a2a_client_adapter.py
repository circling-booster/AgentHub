"""A2aClientAdapter Integration Tests

httpx 기반 A2A JSON-RPC 클라이언트가 실제 A2A 에이전트와 통신하는지 검증합니다.
Step 2의 a2a_echo_agent fixture를 사용합니다.
"""

import pytest

from src.adapters.outbound.a2a.a2a_client_adapter import A2aClientAdapter
from src.domain.entities.endpoint import Endpoint, EndpointType
from src.domain.exceptions import EndpointConnectionError, EndpointNotFoundError


@pytest.mark.local_a2a
class TestA2aClientAdapterRegister:
    """Agent 등록 테스트"""

    async def test_register_agent_fetches_agent_card(self, a2a_echo_agent):
        """
        Given: 실행 중인 A2A Echo Agent (fixture)
        When: A2aClientAdapter로 에이전트 등록 시
        Then: Agent Card가 반환됨
        """
        # Given
        client = A2aClientAdapter()
        endpoint = Endpoint(
            id="echo-agent-1",
            name="Echo Agent",
            url=a2a_echo_agent,
            type=EndpointType.A2A,
        )

        # When
        agent_card = await client.register_agent(endpoint)

        # Then
        assert agent_card is not None
        assert "name" in agent_card or "agentId" in agent_card
        assert isinstance(agent_card, dict)

    async def test_register_agent_connection_failure(self):
        """
        Given: A2aClientAdapter 인스턴스
        When: 연결할 수 없는 URL로 등록 시도 시
        Then: EndpointConnectionError 발생
        """
        # Given
        client = A2aClientAdapter()
        endpoint = Endpoint(
            id="unreachable-agent",
            name="Unreachable Agent",
            url="http://localhost:19999",  # 존재하지 않는 포트
            type=EndpointType.A2A,
        )

        # When & Then
        with pytest.raises(EndpointConnectionError):
            await client.register_agent(endpoint)


@pytest.mark.local_a2a
class TestA2aClientAdapterQuery:
    """Agent Card 조회 테스트"""

    async def test_get_agent_card(self, a2a_echo_agent):
        """
        Given: 등록된 A2A 에이전트
        When: get_agent_card()로 조회 시
        Then: Agent Card가 반환됨
        """
        # Given
        client = A2aClientAdapter()
        endpoint = Endpoint(
            id="echo-agent-2",
            name="Echo Agent",
            url=a2a_echo_agent,
            type=EndpointType.A2A,
        )
        await client.register_agent(endpoint)

        # When
        agent_card = await client.get_agent_card("echo-agent-2")

        # Then
        assert agent_card is not None
        assert isinstance(agent_card, dict)

    async def test_get_agent_card_not_found(self):
        """
        Given: A2aClientAdapter 인스턴스
        When: 등록되지 않은 에이전트 조회 시
        Then: EndpointNotFoundError 발생
        """
        # Given
        client = A2aClientAdapter()

        # When & Then
        with pytest.raises(EndpointNotFoundError):
            await client.get_agent_card("nonexistent-agent")


@pytest.mark.local_a2a
class TestA2aClientAdapterUnregister:
    """Agent 등록 해제 테스트"""

    async def test_unregister_agent(self, a2a_echo_agent):
        """
        Given: 등록된 A2A 에이전트
        When: unregister_agent() 호출 시
        Then: True 반환 및 에이전트 제거됨
        """
        # Given
        client = A2aClientAdapter()
        endpoint = Endpoint(
            id="echo-agent-3",
            name="Echo Agent",
            url=a2a_echo_agent,
            type=EndpointType.A2A,
        )
        await client.register_agent(endpoint)

        # When
        result = await client.unregister_agent("echo-agent-3")

        # Then
        assert result is True
        # 삭제 확인
        with pytest.raises(EndpointNotFoundError):
            await client.get_agent_card("echo-agent-3")

    async def test_unregister_nonexistent_agent(self):
        """
        Given: A2aClientAdapter 인스턴스
        When: 등록되지 않은 에이전트 해제 시도 시
        Then: False 반환
        """
        # Given
        client = A2aClientAdapter()

        # When
        result = await client.unregister_agent("nonexistent-agent")

        # Then
        assert result is False


@pytest.mark.local_a2a
class TestA2aClientAdapterHealth:
    """Agent Health Check 테스트"""

    async def test_health_check_registered_agent(self, a2a_echo_agent):
        """
        Given: 등록된 A2A 에이전트
        When: health_check() 호출 시
        Then: True 반환
        """
        # Given
        client = A2aClientAdapter()
        endpoint = Endpoint(
            id="echo-agent-4",
            name="Echo Agent",
            url=a2a_echo_agent,
            type=EndpointType.A2A,
        )
        await client.register_agent(endpoint)

        # When
        is_healthy = await client.health_check("echo-agent-4")

        # Then
        assert is_healthy is True

    async def test_health_check_nonexistent_agent(self):
        """
        Given: A2aClientAdapter 인스턴스
        When: 등록되지 않은 에이전트 health check 시
        Then: False 반환
        """
        # Given
        client = A2aClientAdapter()

        # When
        is_healthy = await client.health_check("nonexistent-agent")

        # Then
        assert is_healthy is False
