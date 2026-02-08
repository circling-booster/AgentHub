"""ResourceService - MCP Resource 조회 서비스

McpClientPort를 통해 리소스 목록 및 콘텐츠를 조회합니다.
Domain 레이어 순수 Python (외부 라이브러리 의존 없음).
"""

from src.domain.entities.resource import Resource, ResourceContent
from src.domain.ports.outbound.mcp_client_port import McpClientPort


class ResourceService:
    """MCP Resource 조회 서비스

    McpClientPort를 통해 리소스 목록 및 콘텐츠를 조회합니다.
    """

    def __init__(self, mcp_client: McpClientPort) -> None:
        """서비스 초기화

        Args:
            mcp_client: MCP 클라이언트 포트
        """
        self._mcp_client = mcp_client

    async def list_resources(self, endpoint_id: str) -> list[Resource]:
        """엔드포인트의 리소스 목록 조회

        Args:
            endpoint_id: MCP 서버 엔드포인트 ID

        Returns:
            Resource 목록

        Raises:
            EndpointNotFoundError: 연결되지 않은 엔드포인트
        """
        return await self._mcp_client.list_resources(endpoint_id)

    async def read_resource(self, endpoint_id: str, uri: str) -> ResourceContent:
        """리소스 콘텐츠 읽기

        Args:
            endpoint_id: MCP 서버 엔드포인트 ID
            uri: 리소스 URI (file://, ui:// 등)

        Returns:
            ResourceContent (text 또는 blob)

        Raises:
            EndpointNotFoundError: 연결되지 않은 엔드포인트
            ResourceNotFoundError: 존재하지 않는 리소스
        """
        return await self._mcp_client.read_resource(endpoint_id, uri)
