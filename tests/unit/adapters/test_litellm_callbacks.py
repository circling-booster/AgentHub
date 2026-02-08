"""LiteLLM Callback Logging 테스트 - Step 5: Part B

AgentHubLogger가 LLM 호출 성공/실패 시 상세 정보를 로깅하는지 검증
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_logger(monkeypatch):
    """로거 모킹"""
    mock_log = MagicMock()
    monkeypatch.setattr("src.adapters.outbound.adk.litellm_callbacks.logger", mock_log)
    return mock_log


async def test_log_success_event_logs_model_and_tokens(mock_logger):
    """LLM 호출 성공 시 모델명, 토큰 수, 지연시간 로깅"""
    from src.adapters.outbound.adk.litellm_callbacks import AgentHubLogger

    logger = AgentHubLogger()

    # Given: LLM 호출 성공 응답
    kwargs = {"model": "openai/gpt-4o-mini"}
    response_obj = MagicMock()
    response_obj.usage = MagicMock()
    response_obj.usage.total_tokens = 150

    start_time = datetime.now()
    end_time = start_time + timedelta(milliseconds=250)

    # When: log_success_event 호출
    await logger.log_success_event(kwargs, response_obj, start_time, end_time)

    # Then: INFO 레벨로 모델, 토큰, 지연시간 로깅
    mock_logger.info.assert_called_once()
    log_message = mock_logger.info.call_args[0][0]
    assert "openai/gpt-4o-mini" in log_message
    assert "150" in log_message
    assert "250" in log_message or "ms" in log_message


async def test_log_success_event_handles_missing_usage(mock_logger):
    """LLM 응답에 usage 정보가 없는 경우 처리"""
    from src.adapters.outbound.adk.litellm_callbacks import AgentHubLogger

    logger = AgentHubLogger()

    # Given: usage 정보가 없는 응답
    kwargs = {"model": "openai/gpt-4o-mini"}
    response_obj = MagicMock()
    response_obj.usage = None

    start_time = datetime.now()
    end_time = start_time + timedelta(milliseconds=100)

    # When: log_success_event 호출
    await logger.log_success_event(kwargs, response_obj, start_time, end_time)

    # Then: "N/A" 또는 "unknown" 포함하여 로깅
    mock_logger.info.assert_called_once()
    log_message = mock_logger.info.call_args[0][0]
    assert "N/A" in log_message or "unknown" in log_message.lower()


def test_log_failure_event_logs_error(mock_logger):
    """LLM 호출 실패 시 에러 상세 로깅"""
    from src.adapters.outbound.adk.litellm_callbacks import AgentHubLogger

    logger = AgentHubLogger()

    # Given: LLM 호출 실패
    kwargs = {"model": "openai/gpt-4o-mini", "exception": "Rate limit exceeded"}
    response_obj = None

    start_time = datetime.now()
    end_time = start_time + timedelta(milliseconds=50)

    # When: log_failure_event 호출
    logger.log_failure_event(kwargs, response_obj, start_time, end_time)

    # Then: ERROR 레벨로 모델과 에러 로깅
    mock_logger.error.assert_called_once()
    log_message = mock_logger.error.call_args[0][0]
    assert "openai/gpt-4o-mini" in log_message
    assert "Rate limit exceeded" in log_message


def test_callback_disabled_by_config():
    """설정으로 콜백 비활성화 가능 여부 검증"""
    from src.config.settings import Settings

    # Given: log_llm_requests = false 설정
    settings = Settings(observability={"log_llm_requests": False})

    # Then: 설정값이 False로 저장됨
    assert settings.observability.log_llm_requests is False
