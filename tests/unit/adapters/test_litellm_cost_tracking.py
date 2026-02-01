"""LiteLLM Cost Tracking 테스트"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.adapters.outbound.adk.litellm_callbacks import AgentHubLogger
from src.domain.entities.usage import Usage


class TestLiteLLMCostTracking:
    """LiteLLM Cost Tracking 테스트"""

    @pytest.fixture
    def cost_service_mock(self):
        """Mock CostService"""
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def logger(self, cost_service_mock):
        """AgentHubLogger 픽스처"""
        return AgentHubLogger(cost_service=cost_service_mock)

    @pytest.mark.asyncio
    async def test_log_success_records_usage(self, logger, cost_service_mock):
        """성공 시 사용량 기록"""
        # Given
        kwargs = {"model": "openai/gpt-4o-mini"}
        response_obj = MagicMock()
        response_obj.usage = MagicMock(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        # LiteLLM cost 필드 (모의)
        response_obj._hidden_params = {"response_cost": 0.01}

        start_time = datetime(2025, 1, 1, 10, 0, 0)
        end_time = datetime(2025, 1, 1, 10, 0, 5)

        # When
        await logger.log_success_event(kwargs, response_obj, start_time, end_time)

        # Then
        cost_service_mock.record_usage.assert_called_once()
        usage: Usage = cost_service_mock.record_usage.call_args[0][0]

        assert usage.model == "openai/gpt-4o-mini"
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
        assert usage.cost_usd == 0.01

    @pytest.mark.asyncio
    async def test_log_success_without_cost(self, logger, cost_service_mock):
        """비용 정보 없이도 기록 (비용 0으로 처리)"""
        # Given
        kwargs = {"model": "openai/gpt-4o-mini"}
        response_obj = MagicMock()
        response_obj.usage = MagicMock(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        response_obj._hidden_params = {}  # 비용 정보 없음

        start_time = datetime(2025, 1, 1, 10, 0, 0)
        end_time = datetime(2025, 1, 1, 10, 0, 5)

        # When
        await logger.log_success_event(kwargs, response_obj, start_time, end_time)

        # Then
        cost_service_mock.record_usage.assert_called_once()
        usage: Usage = cost_service_mock.record_usage.call_args[0][0]

        assert usage.cost_usd == 0.0  # 비용 정보 없을 때 기본값
