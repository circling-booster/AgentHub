"""ManagementPort - 관리 인터페이스

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.entities.endpoint import Endpoint
    from src.domain.entities.tool import Tool


class ManagementPort(ABC):
    """
    관리 포트 (Driving/Inbound Port)

    MCP/A2A 엔드포인트 관리를 위한 인터페이스입니다.
    엔드포인트 등록, 해제, 상태 조회 등을 처리합니다.

    구현체 예시:
    - RegistryService (도메인 서비스)
    """

    @abstractmethod
    async def register_endpoint(
        self,
        url: str,
        name: str | None = None,
    ) -> "Endpoint":
        """
        엔드포인트 등록

        MCP 또는 A2A 서버를 등록합니다.
        URL 스킴에 따라 타입이 자동 결정됩니다.

        Args:
            url: 엔드포인트 URL
            name: 이름 (선택, 없으면 URL에서 추출)

        Returns:
            등록된 엔드포인트 객체

        Raises:
            InvalidUrlError: 유효하지 않은 URL
            EndpointConnectionError: 연결 실패
            ToolLimitExceededError: 도구 수 제한 초과 (MCP)
        """
        pass

    @abstractmethod
    async def unregister_endpoint(self, endpoint_id: str) -> bool:
        """
        엔드포인트 등록 해제

        Args:
            endpoint_id: 해제할 엔드포인트 ID

        Returns:
            해제 성공 여부
        """
        pass

    @abstractmethod
    async def list_endpoints(
        self,
        type_filter: str | None = None,
    ) -> list["Endpoint"]:
        """
        엔드포인트 목록 조회

        Args:
            type_filter: 타입 필터 ('mcp', 'a2a', None=전체)

        Returns:
            엔드포인트 목록
        """
        pass

    @abstractmethod
    async def get_endpoint(self, endpoint_id: str) -> "Endpoint":
        """
        엔드포인트 조회

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            엔드포인트 객체

        Raises:
            EndpointNotFoundError: 엔드포인트를 찾을 수 없을 때
        """
        pass

    @abstractmethod
    async def get_endpoint_tools(self, endpoint_id: str) -> list["Tool"]:
        """
        엔드포인트의 도구 목록 조회

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            도구 목록

        Raises:
            EndpointNotFoundError: 엔드포인트를 찾을 수 없을 때
        """
        pass

    @abstractmethod
    async def check_endpoint_health(self, endpoint_id: str) -> bool:
        """
        엔드포인트 상태 확인

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            정상 여부

        Raises:
            EndpointNotFoundError: 엔드포인트를 찾을 수 없을 때
        """
        pass

    @abstractmethod
    async def enable_endpoint(self, endpoint_id: str) -> bool:
        """
        엔드포인트 활성화

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            성공 여부
        """
        pass

    @abstractmethod
    async def disable_endpoint(self, endpoint_id: str) -> bool:
        """
        엔드포인트 비활성화

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            성공 여부
        """
        pass
