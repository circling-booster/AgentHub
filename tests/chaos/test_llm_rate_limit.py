"""Chaos Test: LLM Rate Limit 429 시나리오

재시도 로직 검증:
- LLM API Rate Limit 발생 (429)
- Exponential Backoff 재시도
- 최종 성공 또는 최대 재시도 초과
"""

from unittest.mock import AsyncMock, patch

import pytest
from litellm.exceptions import RateLimitError

from src.domain.exceptions import LlmRateLimitError


@pytest.mark.chaos
class TestLlmRateLimitRetry:
    """LLM Rate Limit Chaos 테스트"""

    async def test_llm_rate_limit_retries_with_exponential_backoff(self):
        """
        Given: LLM API가 처음 2번 Rate Limit (429) 반환
        When: 3번째 호출
        Then: Exponential Backoff으로 재시도 후 성공
        """
        # Given: Mock LLM API (처음 2번 실패, 3번째 성공)
        with patch("litellm.completion") as mock_llm:
            mock_llm.side_effect = [
                RateLimitError(
                    message="Rate limit exceeded", llm_provider="openai", model="gpt-4o-mini"
                ),  # 1st call
                RateLimitError(
                    message="Rate limit exceeded", llm_provider="openai", model="gpt-4o-mini"
                ),  # 2nd call (retry 1)
                {  # 3rd call (retry 2) - 성공
                    "choices": [{"message": {"content": "success", "role": "assistant"}}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                },
            ]

            # When: LLM 호출 (재시도 로직 포함)
            # TODO: OrchestratorAdapter 또는 DynamicToolset의 재시도 로직 호출
            # 현재 구현이 없으므로 RED 상태
            from src.adapters.outbound.adk.orchestrator_adapter import AdkOrchestratorAdapter

            # Mock toolset
            mock_toolset = AsyncMock()
            orchestrator = AdkOrchestratorAdapter(
                model="openai/gpt-4o-mini",
                dynamic_toolset=mock_toolset,
            )

            # 재시도 로직이 구현되어야 테스트 통과
            # 현재 미구현 → RED
            result = await orchestrator._call_llm_with_retry("test message")

            # Then: 3번째 호출에서 성공
            assert result is not None
            assert mock_llm.call_count == 3  # 2번 실패 + 1번 성공

    async def test_llm_rate_limit_exceeds_max_retries(self):
        """
        Given: LLM API가 계속 Rate Limit (429) 반환
        When: max_retries(3회) 초과
        Then: LlmRateLimitError 발생
        """
        # Given: Mock LLM API (계속 실패)
        with patch("litellm.completion") as mock_llm:
            mock_llm.side_effect = RateLimitError(
                message="Rate limit exceeded", llm_provider="openai", model="gpt-4o-mini"
            )

            # When: LLM 호출 (최대 3회 재시도)
            from src.adapters.outbound.adk.orchestrator_adapter import AdkOrchestratorAdapter

            mock_toolset = AsyncMock()
            orchestrator = AdkOrchestratorAdapter(
                model="openai/gpt-4o-mini",
                dynamic_toolset=mock_toolset,
            )

            # Then: 최대 재시도 초과 → LlmRateLimitError
            with pytest.raises(LlmRateLimitError):
                await orchestrator._call_llm_with_retry("test message")

            # 1회 원본 + 3회 재시도 = 총 4회 호출
            assert mock_llm.call_count == 4

    async def test_exponential_backoff_delays(self):
        """
        Given: LLM API Rate Limit 발생
        When: 재시도 수행
        Then: Exponential Backoff 지연 시간 증가 (1s, 2s, 4s)
        """
        # Given: Mock LLM API
        with patch("litellm.completion") as mock_llm:
            mock_llm.side_effect = [
                RateLimitError(
                    message="Rate limit exceeded", llm_provider="openai", model="gpt-4o-mini"
                ),  # 1st
                RateLimitError(
                    message="Rate limit exceeded", llm_provider="openai", model="gpt-4o-mini"
                ),  # 2nd (1초 대기 후)
                RateLimitError(
                    message="Rate limit exceeded", llm_provider="openai", model="gpt-4o-mini"
                ),  # 3rd (2초 대기 후)
                {  # 4th (4초 대기 후) - 성공
                    "choices": [{"message": {"content": "success", "role": "assistant"}}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                },
            ]

            # When: 시간 추적하며 재시도
            import time

            start_time = time.time()

            from src.adapters.outbound.adk.orchestrator_adapter import AdkOrchestratorAdapter

            mock_toolset = AsyncMock()
            orchestrator = AdkOrchestratorAdapter(
                model="openai/gpt-4o-mini",
                dynamic_toolset=mock_toolset,
            )

            result = await orchestrator._call_llm_with_retry("test message")

            elapsed = time.time() - start_time

            # Then: Exponential Backoff 지연 (1 + 2 + 4 = 7초 이상)
            # 실제로는 약간의 오버헤드 포함 → 6.5초 이상으로 검증
            assert elapsed >= 6.5
            assert result is not None
