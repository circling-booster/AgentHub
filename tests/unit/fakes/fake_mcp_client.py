"""FakeMcpClient - 테스트용 MCP Client Fake

시나리오 기반 응답을 설정할 수 있습니다.
"""

from src.domain.entities.prompt_template import PromptTemplate
from src.domain.entities.resource import Resource, ResourceContent
from src.domain.exceptions import (
    EndpointNotFoundError,
    PromptNotFoundError,
    ResourceNotFoundError,
)
from src.domain.ports.outbound.mcp_client_port import (
    ElicitationCallback,
    McpClientPort,
    SamplingCallback,
)


class FakeMcpClient(McpClientPort):
    """테스트용 MCP Client Fake

    시나리오 기반 응답을 설정할 수 있습니다.
    """

    def __init__(self) -> None:
        self._connections: dict[str, bool] = {}
        self._resources: dict[str, list[Resource]] = {}
        self._resource_contents: dict[str, dict[str, ResourceContent]] = {}
        self._prompts: dict[str, list[PromptTemplate]] = {}
        self._prompt_results: dict[str, dict[str, str]] = {}
        self._sampling_callbacks: dict[str, SamplingCallback] = {}
        self._elicitation_callbacks: dict[str, ElicitationCallback] = {}

    # ============================================================
    # 테스트 설정 메서드
    # ============================================================

    def set_resources(self, endpoint_id: str, resources: list[Resource]) -> None:
        """엔드포인트의 리소스 목록 설정"""
        self._resources[endpoint_id] = resources

    def set_resource_content(self, endpoint_id: str, uri: str, content: ResourceContent) -> None:
        """특정 리소스의 콘텐츠 설정"""
        if endpoint_id not in self._resource_contents:
            self._resource_contents[endpoint_id] = {}
        self._resource_contents[endpoint_id][uri] = content

    def set_prompts(self, endpoint_id: str, prompts: list[PromptTemplate]) -> None:
        """엔드포인트의 프롬프트 목록 설정"""
        self._prompts[endpoint_id] = prompts

    def set_prompt_result(self, endpoint_id: str, name: str, result: str) -> None:
        """특정 프롬프트의 렌더링 결과 설정"""
        if endpoint_id not in self._prompt_results:
            self._prompt_results[endpoint_id] = {}
        self._prompt_results[endpoint_id][name] = result

    def is_connected(self, endpoint_id: str) -> bool:
        """연결 상태 확인 (테스트 검증용)"""
        return self._connections.get(endpoint_id, False)

    def get_sampling_callback(self, endpoint_id: str) -> SamplingCallback | None:
        """저장된 sampling 콜백 반환 (테스트 검증용)"""
        return self._sampling_callbacks.get(endpoint_id)

    def get_elicitation_callback(self, endpoint_id: str) -> ElicitationCallback | None:
        """저장된 elicitation 콜백 반환 (테스트 검증용)"""
        return self._elicitation_callbacks.get(endpoint_id)

    def reset(self) -> None:
        """모든 상태 초기화 (테스트 간 격리)"""
        self._connections.clear()
        self._resources.clear()
        self._resource_contents.clear()
        self._prompts.clear()
        self._prompt_results.clear()
        self._sampling_callbacks.clear()
        self._elicitation_callbacks.clear()

    # ============================================================
    # Port 구현
    # ============================================================

    async def connect(
        self,
        endpoint_id: str,
        url: str,
        sampling_callback: SamplingCallback | None = None,
        elicitation_callback: ElicitationCallback | None = None,
    ) -> None:
        self._connections[endpoint_id] = True
        if sampling_callback:
            self._sampling_callbacks[endpoint_id] = sampling_callback
        if elicitation_callback:
            self._elicitation_callbacks[endpoint_id] = elicitation_callback

    async def disconnect(self, endpoint_id: str) -> None:
        self._connections.pop(endpoint_id, None)
        self._sampling_callbacks.pop(endpoint_id, None)
        self._elicitation_callbacks.pop(endpoint_id, None)

    async def disconnect_all(self) -> None:
        """모든 세션 정리 (서버 종료 시)"""
        self._connections.clear()
        self._sampling_callbacks.clear()
        self._elicitation_callbacks.clear()

    async def list_resources(self, endpoint_id: str) -> list[Resource]:
        if not self._connections.get(endpoint_id):
            raise EndpointNotFoundError(f"Not connected: {endpoint_id}")
        return self._resources.get(endpoint_id, [])

    async def read_resource(self, endpoint_id: str, uri: str) -> ResourceContent:
        if not self._connections.get(endpoint_id):
            raise EndpointNotFoundError(f"Not connected: {endpoint_id}")
        contents = self._resource_contents.get(endpoint_id, {})
        if uri not in contents:
            raise ResourceNotFoundError(f"Resource not found: {uri}")
        return contents[uri]

    async def list_prompts(self, endpoint_id: str) -> list[PromptTemplate]:
        if not self._connections.get(endpoint_id):
            raise EndpointNotFoundError(f"Not connected: {endpoint_id}")
        return self._prompts.get(endpoint_id, [])

    async def get_prompt(self, endpoint_id: str, name: str, arguments: dict | None) -> str:
        if not self._connections.get(endpoint_id):
            raise EndpointNotFoundError(f"Not connected: {endpoint_id}")
        results = self._prompt_results.get(endpoint_id, {})
        if name not in results:
            raise PromptNotFoundError(f"Prompt not found: {name}")
        return results[name]
