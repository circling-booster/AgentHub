"""Fake A2A Client - Unit Test용 A2aPort 구현

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""

from collections.abc import AsyncIterator
from typing import Any

from src.domain.entities.endpoint import Endpoint
from src.domain.exceptions import EndpointConnectionError, EndpointNotFoundError
from src.domain.ports.outbound.a2a_port import A2aPort


class FakeA2aClient(A2aPort):
    """
    Fake A2A Client - Unit Test용 구현

    메모리 기반 Agent Card 저장소를 사용하여 A2A 통신을 시뮬레이션합니다.
    """

    def __init__(self):
        # endpoint_id -> agent_card 매핑
        self._agents: dict[str, dict[str, Any]] = {}
        # endpoint_id -> Endpoint 매핑
        self._endpoints: dict[str, Endpoint] = {}
        # 연결 실패 시뮬레이션용 (테스트에서 설정 가능)
        self._fail_on_register: set[str] = set()
        self._fail_on_call: set[str] = set()

    async def register_agent(self, endpoint: Endpoint) -> dict[str, Any]:
        """
        Agent 등록 - Agent Card 반환

        Args:
            endpoint: A2A 엔드포인트

        Returns:
            Agent Card (name, description, version, api, auth)

        Raises:
            EndpointConnectionError: URL이 실패 목록에 있을 때
        """
        if endpoint.url in self._fail_on_register:
            raise EndpointConnectionError(f"Failed to connect to {endpoint.url}")

        # Fake Agent Card 생성
        agent_card = {
            "name": endpoint.name or "fake_agent",
            "description": f"Fake A2A agent for {endpoint.url}",
            "version": "1.0.0",
            "api": {"protocol": "a2a", "version": "1.0"},
            "auth": {"type": "none"},
        }

        self._agents[endpoint.id] = agent_card
        self._endpoints[endpoint.id] = endpoint

        return agent_card

    async def call_agent(
        self,
        endpoint_id: str,
        message: str,
    ) -> AsyncIterator[str]:
        """
        Agent 호출 - Echo 응답 스트리밍

        Args:
            endpoint_id: 호출할 에이전트 ID
            message: 전송할 메시지

        Yields:
            에이전트 응답 텍스트 조각

        Raises:
            EndpointNotFoundError: 에이전트가 등록되지 않았을 때
            EndpointConnectionError: endpoint_id가 실패 목록에 있을 때
        """
        if endpoint_id not in self._agents:
            raise EndpointNotFoundError(f"Agent not found: {endpoint_id}")

        if endpoint_id in self._fail_on_call:
            raise EndpointConnectionError(f"Failed to call agent: {endpoint_id}")

        # Fake 응답: 입력 메시지를 에코
        response_text = f"Fake A2A Response: {message}"
        # 스트리밍 시뮬레이션: 단어별로 yield
        for word in response_text.split():
            yield word + " "

    async def get_agent_card(self, endpoint_id: str) -> dict[str, Any]:
        """
        Agent Card 조회

        Args:
            endpoint_id: 에이전트 ID

        Returns:
            Agent Card

        Raises:
            EndpointNotFoundError: 에이전트가 등록되지 않았을 때
        """
        if endpoint_id not in self._agents:
            raise EndpointNotFoundError(f"Agent not found: {endpoint_id}")

        return self._agents[endpoint_id]

    async def unregister_agent(self, endpoint_id: str) -> bool:
        """
        Agent 등록 해제

        Args:
            endpoint_id: 해제할 에이전트 ID

        Returns:
            해제 성공 여부
        """
        if endpoint_id not in self._agents:
            return False

        del self._agents[endpoint_id]
        del self._endpoints[endpoint_id]
        return True

    async def health_check(self, endpoint_id: str) -> bool:
        """
        Agent 상태 확인

        Args:
            endpoint_id: 확인할 에이전트 ID

        Returns:
            에이전트 존재 여부
        """
        return endpoint_id in self._agents

    # Test Helper Methods

    def set_fail_on_register(self, url: str) -> None:
        """테스트용: 특정 URL 등록 시 실패 시뮬레이션"""
        self._fail_on_register.add(url)

    def set_fail_on_call(self, endpoint_id: str) -> None:
        """테스트용: 특정 에이전트 호출 시 실패 시뮬레이션"""
        self._fail_on_call.add(endpoint_id)
