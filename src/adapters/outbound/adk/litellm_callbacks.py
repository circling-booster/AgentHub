"""LiteLLM Callback Logger - Step 5: Part B

LLM 호출 성공/실패 시 모델명, 토큰 수, 지연시간, 에러 상세 로깅
"""

import logging
from datetime import datetime

from litellm.integrations.custom_logger import CustomLogger

logger = logging.getLogger(__name__)


class AgentHubLogger(CustomLogger):
    """AgentHub LiteLLM 커스텀 로거

    LLM API 호출 성공/실패 이벤트를 로깅합니다.
    """

    def log_success_event(
        self, kwargs: dict, response_obj, start_time: datetime, end_time: datetime
    ) -> None:
        """LLM 호출 성공 시 로깅

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
