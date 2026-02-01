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

from src.config.settings import Settings
from src.domain.entities.auth_config import AuthConfig
from src.domain.entities.endpoint import Endpoint, EndpointType
from src.domain.entities.tool import Tool

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Context Explosion 방지 (Step 11: 30 → 100)
MAX_ACTIVE_TOOLS = 100
TOOL_TOKEN_WARNING_THRESHOLD = 10000  # 약 10k 토큰

# 재시도 대상 에러 (일시적 에러)
TRANSIENT_ERRORS = (ConnectionError, TimeoutError, asyncio.TimeoutError)


class ToolLimitExceededError(Exception):
    """활성 도구 수가 제한을 초과함"""

    pass


class DeferredToolProxy:
    """
    메타데이터만 로드된 도구 프록시 (Step 11: Defer Loading)

    도구 수가 defer_loading_threshold를 초과할 때,
    name과 description만 로드하고 실행 시 풀 스키마를 lazy load합니다.
    """

    def __init__(self, name: str, description: str, endpoint_id: str, toolset: "MCPToolset"):
        self.name = name
        self.description = description
        self._endpoint_id = endpoint_id
        self._toolset = toolset
        self._full_tool: BaseTool | None = None  # lazy

    async def run_async(self, arguments: dict[str, Any], context: Any) -> Any:
        """
        도구 실행 시 풀 스키마 lazy load

        첫 실행 시 _toolset.get_tools()를 호출하여 풀 도구를 로드합니다.
        """
        if self._full_tool is None:
            # Lazy load: 풀 도구 조회
            tools = await self._toolset.get_tools()
            self._full_tool = next(t for t in tools if t.name == self.name)

        return await self._full_tool.run_async(arguments, context)


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

    def __init__(self, settings: Settings | None = None, cache_ttl_seconds: int = 300):
        """
        Args:
            settings: Settings 인스턴스 (선택적, 테스트용)
            cache_ttl_seconds: 도구 캐시 TTL (기본 300초 = 5분, settings 우선)
        """
        super().__init__()
        self._mcp_toolsets: dict[str, MCPToolset] = {}
        self._endpoints: dict[str, Endpoint] = {}

        # Settings 주입 (DI)
        if settings is None:
            settings = Settings()
        self._settings = settings

        # 캐싱 관련 (settings 값 우선)
        self._cache_ttl = settings.mcp.cache_ttl_seconds if settings else cache_ttl_seconds
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
        cache_hits = 0
        cache_misses = 0

        async with self._cache_lock:
            for endpoint_id, toolset in self._mcp_toolsets.items():
                # 캐시 유효성 확인
                if self._is_cache_valid(endpoint_id, current_time):
                    cached_tools = self._tool_cache[endpoint_id]
                    all_tools.extend(cached_tools)
                    cache_hits += 1
                    logger.debug(
                        f"Tool cache HIT for endpoint {endpoint_id}",
                        extra={"endpoint_id": endpoint_id, "tool_count": len(cached_tools)},
                    )
                    continue

                # 캐시 미스: MCP 서버에서 도구 조회
                cache_misses += 1
                try:
                    tools = await toolset.get_tools(readonly_context)
                    self._tool_cache[endpoint_id] = tools
                    self._cache_timestamps[endpoint_id] = current_time
                    all_tools.extend(tools)
                    logger.debug(
                        f"Tool cache MISS for endpoint {endpoint_id}",
                        extra={
                            "endpoint_id": endpoint_id,
                            "tool_count": len(tools),
                            "refreshed": True,
                        },
                    )
                except Exception as e:
                    logger.warning(f"Failed to get tools from endpoint {endpoint_id}: {e}")
                    # 실패 시 기존 캐시 사용 (있으면)
                    if endpoint_id in self._tool_cache:
                        all_tools.extend(self._tool_cache[endpoint_id])
                    continue

        logger.info(
            f"get_tools() completed: {len(all_tools)} tools from {len(self._mcp_toolsets)} endpoints",
            extra={
                "total_tools": len(all_tools),
                "endpoints_count": len(self._mcp_toolsets),
                "cache_hits": cache_hits,
                "cache_misses": cache_misses,
            },
        )

        # Step 11: Defer Loading Logic
        total_tool_count = len(all_tools)
        defer_threshold = self._settings.mcp.defer_loading_threshold

        if total_tool_count > defer_threshold:
            # Defer mode: 메타데이터만 반환
            logger.info(
                f"Defer loading activated: {total_tool_count} tools > {defer_threshold} threshold"
            )
            deferred_tools: list[BaseTool] = []

            for endpoint_id, cached_tools in self._tool_cache.items():
                toolset = self._mcp_toolsets[endpoint_id]
                for tool in cached_tools:
                    # DeferredToolProxy 생성 (name, description만)
                    proxy = DeferredToolProxy(
                        name=tool.name,
                        description=tool.description or "",
                        endpoint_id=endpoint_id,
                        toolset=toolset,
                    )
                    deferred_tools.append(proxy)  # type: ignore

            return deferred_tools
        else:
            # Normal mode: 풀 도구 반환
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

        toolset = await self._create_mcp_toolset(endpoint.url, endpoint.auth_config)

        # 연결 테스트 및 도구 목록 조회
        adk_tools = await toolset.get_tools()

        # Context Explosion 방지: 도구 개수 제한 (Step 11: settings에서 가져옴)
        max_active_tools = self._settings.mcp.max_active_tools
        current_tool_count = sum(len(tools) for tools in self._tool_cache.values())
        total_tools = current_tool_count + len(adk_tools)

        if total_tools > max_active_tools:
            await toolset.close()
            raise ToolLimitExceededError(
                f"Active tools ({total_tools}) exceed limit ({max_active_tools}). "
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

        # 로깅
        logger.info(
            f"MCP server added: {endpoint.url}",
            extra={
                "endpoint_id": endpoint.id,
                "endpoint_url": endpoint.url,
                "tool_count": len(adk_tools),
                "total_endpoints": len(self._mcp_toolsets),
            },
        )

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

    async def _create_mcp_toolset(
        self, url: str, auth_config: AuthConfig | None = None
    ) -> MCPToolset:
        """
        MCP Toolset 생성 (Streamable HTTP 우선, SSE 폴백)

        2025년 3월 이후 Streamable HTTP가 권장 프로토콜이지만,
        레거시 SSE 서버 호환을 위해 폴백 로직 포함

        Args:
            url: MCP 서버 URL
            auth_config: 인증 설정 (선택적)

        Returns:
            MCPToolset 인스턴스

        Raises:
            ConnectionError: 모든 transport 시도 실패
        """
        # 인증 헤더 생성
        headers = auth_config.get_auth_headers() if auth_config else {}

        # 1. Streamable HTTP 시도 (권장)
        try:
            toolset = MCPToolset(
                connection_params=StreamableHTTPConnectionParams(
                    url=url,
                    timeout=120,
                    headers=headers,
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
                    headers=headers,
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

        # 제거 전 정보 로깅
        endpoint = self._endpoints.get(endpoint_id)
        tool_count = len(self._tool_cache.get(endpoint_id, []))

        toolset = self._mcp_toolsets.pop(endpoint_id)
        self._endpoints.pop(endpoint_id, None)
        self.invalidate_cache(endpoint_id)

        try:
            await toolset.close()
        except Exception as e:
            logger.warning(f"Error closing toolset {endpoint_id}: {e}")

        logger.info(
            f"MCP server removed: {endpoint.url if endpoint else endpoint_id}",
            extra={
                "endpoint_id": endpoint_id,
                "removed_tool_count": tool_count,
                "remaining_endpoints": len(self._mcp_toolsets),
            },
        )

        return True

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """
        도구 직접 실행 (재시도 로직 포함)

        일시적 에러 시 exponential backoff로 재시도합니다.
        - 일시적 에러: ConnectionError, TimeoutError, asyncio.TimeoutError
        - 영구 에러: ValueError, RuntimeError 등 → 즉시 실패

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
            TRANSIENT_ERRORS: 재시도 횟수 초과
            기타 에러: 영구 에러는 즉시 실패
        """
        # 재시도 설정
        max_retries = self._settings.mcp.max_retries
        backoff = self._settings.mcp.retry_backoff_seconds

        # 도구 찾기
        tool_to_execute = None
        for toolset in self._mcp_toolsets.values():
            adk_tools = await toolset.get_tools()
            for tool in adk_tools:
                if tool.name == tool_name:
                    tool_to_execute = tool
                    break
            if tool_to_execute:
                break

        if tool_to_execute is None:
            raise RuntimeError(f"Tool not found: {tool_name}")

        # 재시도 루프
        for attempt in range(max_retries + 1):
            try:
                # 블로킹 방지: 스레드 풀에서 실행
                return await asyncio.to_thread(
                    lambda t=tool_to_execute: asyncio.run(t.run_async(arguments, None))
                )
            except TRANSIENT_ERRORS as e:
                # 마지막 시도였으면 에러 발생
                if attempt == max_retries:
                    logger.error(f"Tool {tool_name} failed after {max_retries + 1} attempts: {e}")
                    raise

                # 재시도 대기 (exponential backoff)
                wait_time = backoff * (2**attempt)
                logger.warning(
                    f"Tool {tool_name} failed (attempt {attempt + 1}/{max_retries + 1}), "
                    f"retrying in {wait_time:.2f}s: {e}"
                )
                await asyncio.sleep(wait_time)
            except Exception as e:
                # 영구 에러 (ValueError, RuntimeError 등)는 즉시 실패
                logger.error(f"Tool {tool_name} failed with permanent error: {e}")
                raise

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

    def get_registered_info(self) -> dict[str, dict[str, Any]]:
        """
        등록된 MCP 서버별 도구 정보 반환

        동적 시스템 프롬프트 생성에 사용됩니다.

        Returns:
            엔드포인트별 정보 딕셔너리
            {
                "endpoint-id": {
                    "name": "서버이름",
                    "url": "서버 URL",
                    "tools": ["tool1", "tool2", ...]
                }
            }
        """
        info: dict[str, dict[str, Any]] = {}

        for endpoint_id, endpoint in self._endpoints.items():
            # 캐시에서 도구 목록 추출
            cached_tools = self._tool_cache.get(endpoint_id, [])
            tool_names = [tool.name for tool in cached_tools]

            info[endpoint_id] = {
                "name": endpoint.name,
                "url": endpoint.url,
                "tools": tool_names,
            }

        return info

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
