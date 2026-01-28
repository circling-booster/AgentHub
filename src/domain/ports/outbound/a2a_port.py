"""A2aPort - A2A Agent 통신 인터페이스

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.

NOTE: Phase 3에서 구현 예정. 현재는 인터페이스 정의만 포함.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.domain.entities.endpoint import Endpoint


class A2aPort(ABC):
    """
    A2A Agent 통신 포트

    A2A (Agent-to-Agent) 프로토콜을 통한 외부 에이전트 통신을 추상화합니다.
    JSON-RPC 2.0 기반의 A2A 프로토콜을 구현합니다.

    구현체 예시:
    - A2aClientAdapter (실제 A2A 클라이언트)
    - FakeA2aClient (테스트용)

    NOTE: Phase 3에서 구현 예정
    """

    @abstractmethod
    async def register_agent(self, endpoint: "Endpoint") -> dict[str, Any]:
        """
        A2A Agent 등록

        Agent Card를 교환하고 연결을 설정합니다.

        Args:
            endpoint: A2A 엔드포인트

        Returns:
            Agent Card 정보 (name, description, capabilities 등)

        Raises:
            EndpointConnectionError: 연결 실패 시
        """
        pass

    @abstractmethod
    async def call_agent(
        self,
        endpoint_id: str,
        message: str,
    ) -> AsyncIterator[str]:
        """
        Agent 호출 및 스트리밍 응답

        A2A Agent에 메시지를 보내고 응답을 스트리밍합니다.

        Args:
            endpoint_id: 호출할 에이전트의 엔드포인트 ID
            message: 전송할 메시지

        Yields:
            에이전트 응답 텍스트 조각 (스트리밍)

        Raises:
            EndpointNotFoundError: 에이전트를 찾을 수 없을 때
            EndpointConnectionError: 통신 실패 시
        """
        pass

    @abstractmethod
    async def get_agent_card(self, endpoint_id: str) -> dict[str, Any]:
        """
        Agent Card 조회

        등록된 A2A Agent의 정보를 조회합니다.

        Args:
            endpoint_id: 에이전트 엔드포인트 ID

        Returns:
            Agent Card 정보

        Raises:
            EndpointNotFoundError: 에이전트를 찾을 수 없을 때
        """
        pass

    @abstractmethod
    async def unregister_agent(self, endpoint_id: str) -> bool:
        """
        Agent 등록 해제

        Args:
            endpoint_id: 해제할 에이전트 엔드포인트 ID

        Returns:
            해제 성공 여부
        """
        pass

    @abstractmethod
    async def health_check(self, endpoint_id: str) -> bool:
        """
        Agent 상태 확인

        Args:
            endpoint_id: 확인할 에이전트 엔드포인트 ID

        Returns:
            에이전트 정상 여부
        """
        pass
