"""PromptService - MCP Prompt 템플릿 서비스

McpClientPort를 통해 프롬프트 목록 및 렌더링 결과를 조회합니다.
Domain 레이어 순수 Python (외부 라이브러리 의존 없음).
"""

from src.domain.entities.prompt_template import PromptTemplate
from src.domain.ports.outbound.mcp_client_port import McpClientPort


class PromptService:
    """MCP Prompt 템플릿 서비스

    McpClientPort를 통해 프롬프트 목록 및 렌더링 결과를 조회합니다.
    """

    def __init__(self, mcp_client: McpClientPort) -> None:
        """서비스 초기화

        Args:
            mcp_client: MCP 클라이언트 포트
        """
        self._mcp_client = mcp_client

    async def list_prompts(self, endpoint_id: str) -> list[PromptTemplate]:
        """엔드포인트의 프롬프트 목록 조회

        Args:
            endpoint_id: MCP 서버 엔드포인트 ID

        Returns:
            PromptTemplate 목록

        Raises:
            EndpointNotFoundError: 연결되지 않은 엔드포인트
        """
        return await self._mcp_client.list_prompts(endpoint_id)

    async def get_prompt(
        self,
        endpoint_id: str,
        name: str,
        arguments: dict | None = None,
    ) -> str:
        """프롬프트 렌더링

        Args:
            endpoint_id: MCP 서버 엔드포인트 ID
            name: 프롬프트 이름
            arguments: 템플릿 인자 (optional)

        Returns:
            렌더링된 프롬프트 문자열

        Raises:
            EndpointNotFoundError: 연결되지 않은 엔드포인트
            PromptNotFoundError: 존재하지 않는 프롬프트
        """
        return await self._mcp_client.get_prompt(endpoint_id, name, arguments)
