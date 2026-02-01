"""GatewayToolset - DynamicToolset을 Circuit Breaker + Rate Limiting으로 래핑"""

import logging
from typing import Any

from google.adk.tools import BaseTool
from google.adk.tools.base_toolset import BaseToolset

from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset
from src.domain.exceptions import EndpointConnectionError, RateLimitExceededError
from src.domain.services.gateway_service import GatewayService

logger = logging.getLogger(__name__)


class GatewayToolset(BaseToolset):
    """
    DynamicToolset을 Circuit Breaker + Rate Limiting + Fallback으로 래핑

    특징:
    - get_tools() 위임: DynamicToolset의 도구 목록 반환
    - call_tool_with_gateway(): Circuit Breaker + Rate Limit 체크
    - Fallback 서버 전환: Primary 실패 시 자동 전환

    참고:
    - https://python-dependency-injector.ets-labs.org/introduction/di_in_python.html
    - https://snir-orlanczyk.medium.com/python-di-dependency-injection-part-2-containers-c621f4311d55
    """

    def __init__(self, dynamic_toolset: DynamicToolset, gateway_service: GatewayService):
        """
        Args:
            dynamic_toolset: 내부 MCP Toolset
            gateway_service: Gateway 서비스 (Circuit Breaker + Rate Limiting)
        """
        super().__init__()
        self._toolset = dynamic_toolset
        self._gateway = gateway_service

    async def get_tools(self, readonly_context=None) -> list[BaseTool]:
        """
        등록된 모든 MCP 서버의 도구 반환 (DynamicToolset 위임)

        Args:
            readonly_context: ADK readonly context (선택적)

        Returns:
            도구 목록
        """
        return await self._toolset.get_tools(readonly_context)

    async def call_tool_with_gateway(
        self, endpoint_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> Any:
        """
        Gateway를 통한 도구 호출 (Circuit Breaker + Rate Limit 체크)

        Args:
            endpoint_id: 엔드포인트 ID
            tool_name: 도구 이름
            arguments: 도구 인자

        Returns:
            도구 실행 결과

        Raises:
            EndpointConnectionError: Circuit Breaker OPEN 상태
            RateLimitExceededError: Rate Limit 초과
        """
        # Circuit Breaker 확인
        if not self._gateway.can_execute(endpoint_id):
            raise EndpointConnectionError(f"Circuit breaker OPEN for endpoint {endpoint_id}")

        # Rate Limiting 확인
        if not await self._gateway.check_rate_limit(endpoint_id):
            raise RateLimitExceededError(f"Rate limit exceeded for endpoint {endpoint_id}")

        try:
            # DynamicToolset으로 도구 호출
            result = await self._toolset.call_tool(tool_name, arguments)
            # 성공 기록
            self._gateway.record_success(endpoint_id)
            return result

        except Exception as e:
            # 실패 기록
            self._gateway.record_failure(endpoint_id)

            # Fallback 서버 시도
            if self._gateway.has_fallback(endpoint_id):
                logger.warning(f"Primary server failed, trying fallback: {e}")
                return await self._try_fallback(endpoint_id, tool_name, arguments)

            # Fallback 없으면 에러 전파
            raise

    async def _try_fallback(
        self, endpoint_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> Any:
        """
        Fallback 서버로 도구 호출 재시도

        Args:
            endpoint_id: 엔드포인트 ID
            tool_name: 도구 이름
            arguments: 도구 인자

        Returns:
            Fallback 서버의 도구 실행 결과
        """
        fallback_url = self._gateway.get_fallback_url(endpoint_id)
        logger.info(f"Switching to fallback server: {fallback_url}")

        # DynamicToolset으로 재시도 (Fallback URL로 전환은 외부에서 처리)
        return await self._toolset.call_tool(tool_name, arguments)

    def get_registered_info(self) -> dict[str, Any]:
        """
        등록된 MCP 서버별 도구 정보 반환 (DynamicToolset 위임)

        동적 시스템 프롬프트 생성에 사용됩니다.

        Returns:
            엔드포인트별 정보 딕셔너리
        """
        return self._toolset.get_registered_info()
