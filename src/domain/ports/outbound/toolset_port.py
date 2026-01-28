"""ToolsetPort - MCP 도구 관리 인터페이스

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.domain.entities.endpoint import Endpoint
    from src.domain.entities.tool import Tool


class ToolsetPort(ABC):
    """
    MCP 도구 관리 포트

    MCP 서버 연결 및 도구 관리를 추상화합니다.
    DynamicToolset과 같은 어댑터가 이 인터페이스를 구현합니다.

    구현체 예시:
    - DynamicToolset (ADK BaseToolset 기반)
    - FakeToolset (테스트용)
    """

    @abstractmethod
    async def add_mcp_server(self, endpoint: "Endpoint") -> list["Tool"]:
        """
        MCP 서버 추가 및 도구 조회

        MCP 서버에 연결하고 사용 가능한 도구 목록을 반환합니다.

        Args:
            endpoint: MCP 엔드포인트

        Returns:
            등록된 도구 목록

        Raises:
            EndpointConnectionError: 연결 실패 시
            ToolLimitExceededError: 도구 수 제한 초과 시
        """
        pass

    @abstractmethod
    async def remove_mcp_server(self, endpoint_id: str) -> bool:
        """
        MCP 서버 제거

        Args:
            endpoint_id: 제거할 엔드포인트 ID

        Returns:
            제거 성공 여부
        """
        pass

    @abstractmethod
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """
        도구 실행

        Args:
            tool_name: 실행할 도구 이름
            arguments: 도구 인자

        Returns:
            도구 실행 결과

        Raises:
            ToolNotFoundError: 도구를 찾을 수 없을 때
            ToolExecutionError: 도구 실행 실패 시
        """
        pass

    @abstractmethod
    async def get_tools(self) -> list["Tool"]:
        """
        등록된 모든 도구 조회

        Returns:
            현재 사용 가능한 도구 목록
        """
        pass

    @abstractmethod
    async def health_check(self, endpoint_id: str) -> bool:
        """
        특정 MCP 서버 상태 확인

        Args:
            endpoint_id: 확인할 엔드포인트 ID

        Returns:
            서버 정상 여부
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        모든 MCP 연결 정리
        """
        pass
