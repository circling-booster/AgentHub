"""DynamicToolset - ADK BaseToolset 기반 동적 도구 관리

TDD Phase: GREEN - 최소 구현
"""

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any

from google.adk.tools import BaseTool
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    SseConnectionParams,
    StreamableHTTPConnectionParams,
)

from src.domain.entities.endpoint import Endpoint, EndpointType
from src.domain.entities.tool import Tool

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Context Explosion 방지
MAX_ACTIVE_TOOLS = 30
TOOL_TOKEN_WARNING_THRESHOLD = 10000  # 약 10k 토큰


class ToolLimitExceededError(Exception):
    """활성 도구 수가 제한을 초과함"""

    pass


class DynamicToolset(BaseToolset):
    """
    ADK BaseToolset 기반 동적 MCP 도구 관리

    특징:
    - BaseToolset 상속으로 ADK Agent와 자연스럽게 통합
    - get_tools() 호출 시마다 현재 등록된 모든 도구 반환
    - MCP 서버 추가/제거 시 Agent 재생성 불필요
    - TTL 기반 캐싱으로 성능 최적화
    - 레거시 SSE 서버 폴백 지원
    - 도구 개수 제한으로 Context Explosion 방지
    """

    def __init__(self, cache_ttl_seconds: int = 300):
        """
        Args:
            cache_ttl_seconds: 도구 캐시 TTL (기본 300초 = 5분)
        """
        super().__init__()
        self._mcp_toolsets: dict[str, MCPToolset] = {}
        self._endpoints: dict[str, Endpoint] = {}

        # 캐싱 관련
        self._cache_ttl = cache_ttl_seconds
        self._tool_cache: dict[str, list[BaseTool]] = {}
        self._cache_timestamps: dict[str, float] = {}
        self._cache_lock = asyncio.Lock()

    async def get_tools(self, readonly_context=None) -> list[BaseTool]:
        """
        현재 등록된 모든 MCP 서버의 도구 반환 (캐싱 적용)

        ADK Agent가 각 turn마다 이 메서드를 호출합니다.
        TTL 기반 캐싱으로 불필요한 MCP 서버 조회를 방지합니다.

        Args:
            readonly_context: ReadonlyContext (선택적, ADK에서 제공)

        Returns:
            등록된 모든 MCP 서버의 도구 목록
        """
        all_tools: list[BaseTool] = []
        current_time = time.time()

        async with self._cache_lock:
            for endpoint_id, toolset in self._mcp_toolsets.items():
                # 캐시 유효성 확인
                if self._is_cache_valid(endpoint_id, current_time):
                    all_tools.extend(self._tool_cache[endpoint_id])
                    continue

                # 캐시 미스: MCP 서버에서 도구 조회
                try:
                    tools = await toolset.get_tools(readonly_context)
                    self._tool_cache[endpoint_id] = tools
                    self._cache_timestamps[endpoint_id] = current_time
                    all_tools.extend(tools)
                except Exception as e:
                    logger.warning(f"Failed to get tools from endpoint {endpoint_id}: {e}")
                    # 실패 시 기존 캐시 사용 (있으면)
                    if endpoint_id in self._tool_cache:
                        all_tools.extend(self._tool_cache[endpoint_id])
                    continue

        return all_tools

    def _is_cache_valid(self, endpoint_id: str, current_time: float) -> bool:
        """캐시 유효성 확인"""
        if endpoint_id not in self._cache_timestamps:
            return False
        return (current_time - self._cache_timestamps[endpoint_id]) < self._cache_ttl

    def invalidate_cache(self, endpoint_id: str | None = None) -> None:
        """
        캐시 무효화

        Args:
            endpoint_id: 특정 엔드포인트만 무효화 (None이면 전체)
        """
        if endpoint_id:
            self._tool_cache.pop(endpoint_id, None)
            self._cache_timestamps.pop(endpoint_id, None)
        else:
            self._tool_cache.clear()
            self._cache_timestamps.clear()

    async def add_mcp_server(self, endpoint: Endpoint) -> list[Tool]:
        """
        MCP 서버 추가 (Streamable HTTP 우선, SSE 폴백)

        Context Explosion 방지:
        - 활성 도구 수가 MAX_ACTIVE_TOOLS 초과 시 에러
        - 도구 정의 토큰 수 경고 로깅

        Args:
            endpoint: MCP 엔드포인트 정보

        Returns:
            도구 목록 (Domain Tool 엔티티)

        Raises:
            ValueError: 엔드포인트 타입이 MCP가 아닐 때
            ToolLimitExceededError: 도구 개수 제한 초과
            ConnectionError: MCP 서버 연결 실패
        """
        if endpoint.type != EndpointType.MCP:
            raise ValueError("Endpoint type must be MCP")

        toolset = await self._create_mcp_toolset(endpoint.url)

        # 연결 테스트 및 도구 목록 조회
        adk_tools = await toolset.get_tools()

        # Context Explosion 방지: 도구 개수 제한
        current_tool_count = sum(len(tools) for tools in self._tool_cache.values())
        total_tools = current_tool_count + len(adk_tools)

        if total_tools > MAX_ACTIVE_TOOLS:
            await toolset.close()
            raise ToolLimitExceededError(
                f"Active tools ({total_tools}) exceed limit ({MAX_ACTIVE_TOOLS}). "
                f"Consider removing unused MCP servers before adding new ones."
            )

        # 토큰 추정 경고 (대략적 계산: 도구당 평균 300토큰 가정)
        estimated_tokens = total_tools * 300
        if estimated_tokens > TOOL_TOKEN_WARNING_THRESHOLD:
            logger.warning(
                f"Tool definitions may use ~{estimated_tokens} tokens. "
                f"Consider reducing active tools to avoid context overflow."
            )

        self._mcp_toolsets[endpoint.id] = toolset
        self._endpoints[endpoint.id] = endpoint

        # 캐시 갱신
        self._tool_cache[endpoint.id] = adk_tools
        self._cache_timestamps[endpoint.id] = time.time()

        # 도메인 Tool 엔티티로 변환
        return [
            Tool(
                name=t.name,
                description=t.description or "",
                input_schema=getattr(t, "input_schema", {}) or {},
                endpoint_id=endpoint.id,
            )
            for t in adk_tools
        ]

    async def _create_mcp_toolset(self, url: str) -> MCPToolset:
        """
        MCP Toolset 생성 (Streamable HTTP 우선, SSE 폴백)

        2025년 3월 이후 Streamable HTTP가 권장 프로토콜이지만,
        레거시 SSE 서버 호환을 위해 폴백 로직 포함

        Args:
            url: MCP 서버 URL

        Returns:
            MCPToolset 인스턴스

        Raises:
            ConnectionError: 모든 transport 시도 실패
        """
        # 1. Streamable HTTP 시도 (권장)
        try:
            toolset = MCPToolset(
                connection_params=StreamableHTTPConnectionParams(
                    url=url,
                    timeout=120,
                ),
            )
            # 연결 테스트
            await toolset.get_tools()
            logger.info(f"Connected to MCP server via Streamable HTTP: {url}")
            return toolset
        except Exception as e:
            logger.debug(f"Streamable HTTP failed for {url}: {e}")

        # 2. 레거시 SSE 폴백
        try:
            toolset = MCPToolset(
                connection_params=SseConnectionParams(
                    url=url,
                    timeout=120,
                ),
            )
            await toolset.get_tools()
            logger.info(f"Connected to MCP server via SSE (fallback): {url}")
            return toolset
        except Exception as e:
            logger.error(f"SSE fallback also failed for {url}: {e}")
            raise ConnectionError(f"Failed to connect to MCP server: {url}") from e

    async def remove_mcp_server(self, endpoint_id: str) -> bool:
        """
        MCP 서버 제거

        Args:
            endpoint_id: 제거할 엔드포인트 ID

        Returns:
            제거 성공 여부
        """
        if endpoint_id not in self._mcp_toolsets:
            return False

        toolset = self._mcp_toolsets.pop(endpoint_id)
        self._endpoints.pop(endpoint_id, None)
        self.invalidate_cache(endpoint_id)

        try:
            await toolset.close()
        except Exception as e:
            logger.warning(f"Error closing toolset {endpoint_id}: {e}")

        return True

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """
        도구 직접 실행

        비동기 블로킹 방지:
        - 동기식 I/O나 CPU 집약적 도구가 메인 이벤트 루프를 차단하지 않도록
        - asyncio.to_thread로 별도 스레드에서 실행

        Args:
            tool_name: 실행할 도구 이름
            arguments: 도구 인자

        Returns:
            도구 실행 결과

        Raises:
            RuntimeError: 도구를 찾을 수 없음
        """
        for toolset in self._mcp_toolsets.values():
            adk_tools = await toolset.get_tools()
            for tool in adk_tools:
                if tool.name == tool_name:
                    # 블로킹 방지: 스레드 풀에서 실행
                    # lambda 기본 인자로 tool 바인딩 (loop 변수 캡처 방지)
                    return await asyncio.to_thread(
                        lambda t=tool: asyncio.run(t.run_async(arguments, None))
                    )

        raise RuntimeError(f"Tool not found: {tool_name}")

    async def health_check(self, endpoint_id: str) -> bool:
        """
        특정 MCP 서버 상태 확인

        Args:
            endpoint_id: 확인할 엔드포인트 ID

        Returns:
            서버 정상 여부
        """
        if endpoint_id not in self._mcp_toolsets:
            return False

        try:
            toolset = self._mcp_toolsets[endpoint_id]
            await toolset.get_tools()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """모든 MCP 연결 정리"""
        for toolset in self._mcp_toolsets.values():
            try:
                await toolset.close()
            except Exception as e:
                logger.warning(f"Error closing toolset: {e}")

        self._mcp_toolsets.clear()
        self._endpoints.clear()
        self._tool_cache.clear()
        self._cache_timestamps.clear()
