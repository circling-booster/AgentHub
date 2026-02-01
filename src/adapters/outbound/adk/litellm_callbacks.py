"""LiteLLM Callback Logger - Step 3: Cost Tracking

LLM 호출 성공/실패 시 모델명, 토큰 수, 지연시간, 에러 상세 로깅 + 비용 추적
"""

import logging
from datetime import datetime

from litellm.integrations.custom_logger import CustomLogger

from src.domain.entities.usage import Usage
from src.domain.services.cost_service import CostService

logger = logging.getLogger(__name__)


class AgentHubLogger(CustomLogger):
    """AgentHub LiteLLM 커스텀 로거

    LLM API 호출 성공/실패 이벤트를 로깅하고 비용을 추적합니다.
    """

    def __init__(self, cost_service: CostService | None = None):
        """
        Args:
            cost_service: 비용 추적 서비스 (선택적)
        """
        super().__init__()
        self._cost_service = cost_service

    async def log_success_event(
        self, kwargs: dict, response_obj, start_time: datetime, end_time: datetime
    ) -> None:
        """LLM 호출 성공 시 로깅 + 비용 기록

        Args:
            kwargs: 호출 파라미터 (model, messages, user 등)
            response_obj: API 응답 객체
            start_time: 요청 시작 시간
            end_time: 요청 종료 시간
        """
        model = kwargs.get("model", "unknown")

        # 토큰 수 추출
        usage = getattr(response_obj, "usage", None)
        tokens = getattr(usage, "total_tokens", "N/A") if usage else "N/A"

        # 지연시간 계산 (ms)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        logger.info(f"LLM call success: model={model} tokens={tokens} duration={duration_ms}ms")

        # 비용 추적
        if self._cost_service and usage:
            prompt_tokens = getattr(usage, "prompt_tokens", 0)
            completion_tokens = getattr(usage, "completion_tokens", 0)
            total_tokens = getattr(usage, "total_tokens", 0)

            # LiteLLM response_cost 추출 (있으면)
            hidden_params = getattr(response_obj, "_hidden_params", {})
            cost_usd = hidden_params.get("response_cost", 0.0)

            usage_entity = Usage(
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost_usd,
                created_at=end_time,
            )

            await self._cost_service.record_usage(usage_entity)

    def log_failure_event(
        self,
        kwargs: dict,
        response_obj,  # noqa: ARG002 - LiteLLM API 시그니처 준수
        start_time: datetime,  # noqa: ARG002 - LiteLLM API 시그니처 준수
        end_time: datetime,  # noqa: ARG002 - LiteLLM API 시그니처 준수
    ) -> None:
        """LLM 호출 실패 시 로깅

        Args:
            kwargs: 호출 파라미터 (model, exception 등)
            response_obj: API 응답 객체 (실패 시 None일 수 있음)
            start_time: 요청 시작 시간
            end_time: 요청 종료 시간
        """
        model = kwargs.get("model", "unknown")
        error = kwargs.get("exception", "unknown")

        logger.error(f"LLM call failed: model={model} error={error}")
