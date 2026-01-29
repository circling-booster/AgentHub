"""Fake Toolset Adapter - 테스트용 도구셋

ToolsetPort의 테스트용 구현입니다.
"""

from typing import Any

from src.domain.entities.endpoint import Endpoint
from src.domain.entities.tool import Tool
from src.domain.exceptions import (
    EndpointConnectionError,
    ToolExecutionError,
    ToolNotFoundError,
)
from src.domain.ports.outbound.toolset_port import ToolsetPort


class FakeToolset(ToolsetPort):
    """
    테스트용 도구셋

    테스트용 ToolsetPort 구현입니다.
    인메모리에 도구와 엔드포인트 상태를 관리합니다.
    """

    def __init__(
        self,
        default_tools: list[Tool] | None = None,
        should_fail_connection: bool = False,
        should_fail_execution: bool = False,
    ) -> None:
        """
        Args:
            default_tools: 기본 도구 목록
            should_fail_connection: 연결 실패 모드
            should_fail_execution: 실행 실패 모드
        """
        self.default_tools = default_tools or [
            Tool(name="test_tool", description="A test tool"),
        ]
        self.should_fail_connection = should_fail_connection
        self.should_fail_execution = should_fail_execution

        self.registered_endpoints: dict[str, list[Tool]] = {}
        self.health_status: dict[str, bool] = {}
        self.tool_results: dict[str, Any] = {}  # tool_name -> result

    @property
    def tools(self) -> list[Tool]:
        """default_tools 호환 프로퍼티 (테스트 편의용)"""
        return self.default_tools

    @tools.setter
    def tools(self, value: list[Tool]) -> None:
        self.default_tools = value

    @property
    def added_servers(self) -> list[str]:
        """registered_endpoints 키 목록 호환 프로퍼티 (테스트 편의용)"""
        return list(self.registered_endpoints.keys())

    @property
    def should_fail(self) -> bool:
        """should_fail_connection 호환 프로퍼티 (테스트 편의용)"""
        return self.should_fail_connection

    @should_fail.setter
    def should_fail(self, value: bool) -> None:
        self.should_fail_connection = value

    async def add_mcp_server(self, endpoint: Endpoint) -> list[Tool]:
        """MCP 서버 추가"""
        if self.should_fail_connection:
            raise EndpointConnectionError(f"Failed to connect to {endpoint.url}")

        # 도구에 endpoint_id 설정
        tools = [
            Tool(
                name=t.name,
                description=t.description,
                input_schema=t.input_schema,
                endpoint_id=endpoint.id,
            )
            for t in self.default_tools
        ]

        self.registered_endpoints[endpoint.id] = tools
        self.health_status[endpoint.id] = True

        return tools

    async def remove_mcp_server(self, endpoint_id: str) -> bool:
        """MCP 서버 제거"""
        if endpoint_id in self.registered_endpoints:
            del self.registered_endpoints[endpoint_id]
            self.health_status.pop(endpoint_id, None)
            return True
        return False

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """도구 실행"""
        if self.should_fail_execution:
            raise ToolExecutionError(f"Failed to execute tool: {tool_name}")

        # 모든 등록된 도구에서 찾기
        for tools in self.registered_endpoints.values():
            for tool in tools:
                if tool.name == tool_name:
                    # 설정된 결과가 있으면 반환
                    if tool_name in self.tool_results:
                        return self.tool_results[tool_name]
                    # 기본 응답
                    return f"Result from {tool_name} with args: {arguments}"

        raise ToolNotFoundError(f"Tool not found: {tool_name}")

    async def get_tools(self) -> list[Tool]:
        """등록된 모든 도구 조회"""
        all_tools: list[Tool] = []
        for tools in self.registered_endpoints.values():
            all_tools.extend(tools)
        return all_tools

    async def health_check(self, endpoint_id: str) -> bool:
        """엔드포인트 상태 확인"""
        return self.health_status.get(endpoint_id, False)

    async def close(self) -> None:
        """모든 연결 정리"""
        self.registered_endpoints.clear()
        self.health_status.clear()

    # 테스트 헬퍼 메서드들

    def set_tools(self, tools: list[Tool]) -> None:
        """기본 도구 목록 설정"""
        self.default_tools = tools

    def set_tool_result(self, tool_name: str, result: Any) -> None:
        """특정 도구의 반환값 설정"""
        self.tool_results[tool_name] = result

    def set_health(self, endpoint_id: str, is_healthy: bool) -> None:
        """엔드포인트 상태 설정"""
        self.health_status[endpoint_id] = is_healthy

    def set_connection_failure(self, should_fail: bool) -> None:
        """연결 실패 모드 설정"""
        self.should_fail_connection = should_fail

    def set_execution_failure(self, should_fail: bool) -> None:
        """실행 실패 모드 설정"""
        self.should_fail_execution = should_fail

    def reset(self) -> None:
        """상태 초기화"""
        self.registered_endpoints.clear()
        self.health_status.clear()
        self.tool_results.clear()
        self.should_fail_connection = False
        self.should_fail_execution = False
