"""RegistryService - 엔드포인트 등록 관리 서비스

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""

from src.domain.entities.endpoint import Endpoint
from src.domain.entities.enums import EndpointType
from src.domain.entities.tool import Tool
from src.domain.exceptions import DuplicateEndpointError, EndpointNotFoundError
from src.domain.ports.outbound.a2a_port import A2aPort
from src.domain.ports.outbound.storage_port import EndpointStoragePort
from src.domain.ports.outbound.toolset_port import ToolsetPort


class RegistryService:
    """
    엔드포인트 등록 관리 서비스

    MCP/A2A 엔드포인트의 등록, 해제, 조회를 담당합니다.
    ToolsetPort를 통해 MCP 서버와 연결하고,
    EndpointStoragePort를 통해 엔드포인트 정보를 저장합니다.

    Attributes:
        _storage: 엔드포인트 저장소 포트
        _toolset: 도구셋 포트 (MCP용)
        _a2a_client: A2A 클라이언트 포트 (A2A용, 선택)
    """

    def __init__(
        self,
        storage: EndpointStoragePort,
        toolset: ToolsetPort,
        a2a_client: A2aPort | None = None,
    ) -> None:
        """
        Args:
            storage: 엔드포인트 저장소 포트
            toolset: 도구셋 포트 (MCP용)
            a2a_client: A2A 클라이언트 포트 (선택, None이면 A2A 미지원)
        """
        self._storage = storage
        self._toolset = toolset
        self._a2a_client = a2a_client

    async def register_endpoint(
        self,
        url: str,
        name: str | None = None,
        endpoint_type: EndpointType = EndpointType.MCP,
    ) -> Endpoint:
        """
        엔드포인트 등록

        MCP 또는 A2A 서버를 등록합니다.

        Args:
            url: 엔드포인트 URL
            name: 이름 (선택, 없으면 URL에서 추출)
            endpoint_type: 엔드포인트 타입 (MCP 또는 A2A, 기본값 MCP)

        Returns:
            등록된 엔드포인트 객체

        Raises:
            InvalidUrlError: 유효하지 않은 URL
            DuplicateEndpointError: 이미 등록된 URL
            EndpointConnectionError: 연결 실패
            ToolLimitExceededError: 도구 수 제한 초과 (MCP만)
            ValueError: A2A 클라이언트 미설정 상태에서 A2A 등록 시도
        """
        # 중복 URL 검사
        existing = await self._storage.list_endpoints()
        for ep in existing:
            if ep.url == url:
                raise DuplicateEndpointError(f"Endpoint already registered: {url}")

        # 엔드포인트 생성 (URL 검증은 Endpoint에서 수행)
        endpoint = Endpoint(
            url=url,
            type=endpoint_type,
            name=name or "",
        )

        # 타입별 처리
        if endpoint_type == EndpointType.MCP:
            # MCP 서버 연결 및 도구 조회
            tools = await self._toolset.add_mcp_server(endpoint)

            # 도구를 엔드포인트에 연결
            for tool in tools:
                endpoint.tools.append(
                    Tool(
                        name=tool.name,
                        description=tool.description,
                        input_schema=tool.input_schema,
                        endpoint_id=endpoint.id,
                    )
                )

        elif endpoint_type == EndpointType.A2A:
            # A2A 클라이언트 확인
            if self._a2a_client is None:
                raise ValueError("A2A client not configured")

            # A2A Agent 등록 및 Agent Card 조회
            agent_card = await self._a2a_client.register_agent(endpoint)
            endpoint.agent_card = agent_card

        # 저장
        await self._storage.save_endpoint(endpoint)

        return endpoint

    async def unregister_endpoint(self, endpoint_id: str) -> bool:
        """
        엔드포인트 등록 해제

        Args:
            endpoint_id: 해제할 엔드포인트 ID

        Returns:
            해제 성공 여부
        """
        # 엔드포인트 조회 (타입 확인용)
        endpoint = await self._storage.get_endpoint(endpoint_id)
        if not endpoint:
            return False

        # 타입별 해제 처리
        if endpoint.type == EndpointType.A2A and self._a2a_client:
            await self._a2a_client.unregister_agent(endpoint_id)
        elif endpoint.type == EndpointType.MCP:
            await self._toolset.remove_mcp_server(endpoint_id)

        # 저장소에서 삭제
        return await self._storage.delete_endpoint(endpoint_id)

    async def list_endpoints(
        self,
        type_filter: str | None = None,
    ) -> list[Endpoint]:
        """
        엔드포인트 목록 조회

        Args:
            type_filter: 타입 필터 ('mcp', 'a2a', None=전체)

        Returns:
            엔드포인트 목록
        """
        return await self._storage.list_endpoints(type_filter=type_filter)

    async def get_endpoint(self, endpoint_id: str) -> Endpoint:
        """
        엔드포인트 조회

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            엔드포인트 객체

        Raises:
            EndpointNotFoundError: 엔드포인트를 찾을 수 없을 때
        """
        endpoint = await self._storage.get_endpoint(endpoint_id)
        if endpoint is None:
            raise EndpointNotFoundError(f"Endpoint not found: {endpoint_id}")
        return endpoint

    async def get_endpoint_tools(self, endpoint_id: str) -> list[Tool]:
        """
        엔드포인트의 도구 목록 조회

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            도구 목록

        Raises:
            EndpointNotFoundError: 엔드포인트를 찾을 수 없을 때
        """
        endpoint = await self.get_endpoint(endpoint_id)
        return endpoint.tools

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
        # 엔드포인트 존재 확인
        await self.get_endpoint(endpoint_id)

        # 상태 확인
        return await self._toolset.health_check(endpoint_id)

    async def enable_endpoint(self, endpoint_id: str) -> bool:
        """
        엔드포인트 활성화

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            성공 여부
        """
        endpoint = await self._storage.get_endpoint(endpoint_id)
        if endpoint is None:
            return False

        endpoint.enable()
        await self._storage.save_endpoint(endpoint)
        return True

    async def disable_endpoint(self, endpoint_id: str) -> bool:
        """
        엔드포인트 비활성화

        Args:
            endpoint_id: 엔드포인트 ID

        Returns:
            성공 여부
        """
        endpoint = await self._storage.get_endpoint(endpoint_id)
        if endpoint is None:
            return False

        endpoint.disable()
        await self._storage.save_endpoint(endpoint)
        return True
