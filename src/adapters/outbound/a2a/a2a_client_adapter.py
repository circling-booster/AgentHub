"""A2aClientAdapter - httpx 기반 A2A JSON-RPC 클라이언트

A2A (Agent-to-Agent) 프로토콜 JSON-RPC 2.0을 직접 구현합니다.
ADK의 RemoteA2aAgent는 sub_agent로만 동작하므로 httpx로 직접 호출합니다.
"""

from collections.abc import AsyncIterator
from typing import Any

import httpx

from src.domain.entities.endpoint import Endpoint
from src.domain.exceptions import EndpointConnectionError, EndpointNotFoundError
from src.domain.ports.outbound.a2a_port import A2aPort


class A2aClientAdapter(A2aPort):
    """
    httpx 기반 A2A 클라이언트

    A2A 프로토콜의 Agent Card 교환 및 JSON-RPC 2.0 통신을 구현합니다.

    주요 엔드포인트:
    - GET /.well-known/agent.json: Agent Card 조회
    - POST /: JSON-RPC 2.0 호출 (tasks/send)
    """

    AGENT_CARD_PATH = "/.well-known/agent.json"
    TIMEOUT_SECONDS = 30.0

    def __init__(self):
        # endpoint_id -> (url, agent_card) 매핑
        self._agents: dict[str, tuple[str, dict[str, Any]]] = {}

    async def register_agent(self, endpoint: Endpoint) -> dict[str, Any]:
        """
        A2A Agent 등록 - Agent Card 교환

        Args:
            endpoint: A2A 엔드포인트

        Returns:
            Agent Card (name, description, version, api, auth)

        Raises:
            EndpointConnectionError: Agent Card fetch 실패 시
        """
        url = endpoint.url
        agent_card_url = f"{url}{self.AGENT_CARD_PATH}"

        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                response = await client.get(agent_card_url)
                response.raise_for_status()
                agent_card = response.json()

            # 등록
            self._agents[endpoint.id] = (url, agent_card)
            return agent_card

        except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as e:
            raise EndpointConnectionError(f"Failed to fetch agent card from {url}: {e}") from e
        except Exception as e:
            raise EndpointConnectionError(f"Unexpected error connecting to {url}: {e}") from e

    async def call_agent(
        self,
        endpoint_id: str,
        _message: str,
    ) -> AsyncIterator[str]:
        """
        A2A Agent 호출 - JSON-RPC 2.0 tasks/send

        Args:
            endpoint_id: 호출할 에이전트 ID
            message: 전송할 메시지

        Yields:
            에이전트 응답 텍스트 조각 (스트리밍)

        Raises:
            EndpointNotFoundError: 에이전트가 등록되지 않았을 때
            EndpointConnectionError: 호출 실패 시

        NOTE: Phase 3에서는 call_agent()를 구현하지 않습니다.
        RemoteA2aAgent는 sub_agent로만 동작하며, Orchestrator 통합 시 사용됩니다.
        직접 호출은 Phase 4 이후 필요 시 구현 예정.
        """
        if endpoint_id not in self._agents:
            raise EndpointNotFoundError(f"Agent not found: {endpoint_id}")

        # Phase 3에서는 NotImplementedError
        # Phase 7 (Orchestrator 통합) 이후 필요 시 구현
        raise NotImplementedError(
            "call_agent() is not implemented. "
            "Use RemoteA2aAgent as sub_agent in Orchestrator (Phase 7)."
        )

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

        _, agent_card = self._agents[endpoint_id]
        return agent_card

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
        return True

    async def health_check(self, endpoint_id: str) -> bool:
        """
        Agent 상태 확인 - Agent Card 재조회

        Args:
            endpoint_id: 확인할 에이전트 ID

        Returns:
            에이전트 정상 여부
        """
        if endpoint_id not in self._agents:
            return False

        url, _ = self._agents[endpoint_id]
        agent_card_url = f"{url}{self.AGENT_CARD_PATH}"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(agent_card_url)
                return response.status_code == 200
        except Exception:
            return False
