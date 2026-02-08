"""Integration tests for AdkOrchestratorAdapter.generate_response()

generate_response()는 Method C에서 Route가 단일 LLM 호출을 위해 사용하는 메서드입니다.
실제 LLM API를 호출하므로 @pytest.mark.llm으로 마킹되어 기본적으로 제외됩니다.
"""

import pytest

from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset
from src.adapters.outbound.adk.orchestrator_adapter import AdkOrchestratorAdapter


@pytest.mark.llm  # 실제 LLM 호출 (기본 제외)
class TestOrchestratorGenerate:
    @pytest.fixture
    async def orchestrator_adapter(self):
        """AdkOrchestratorAdapter 인스턴스 생성"""
        # generate_response()는 tools를 사용하지 않으므로 빈 DynamicToolset 전달
        dynamic_toolset = DynamicToolset()
        adapter = AdkOrchestratorAdapter(
            model="openai/gpt-4o-mini",
            dynamic_toolset=dynamic_toolset,
        )
        await adapter.initialize()
        return adapter

    async def test_generate_response_returns_llm_result(self, orchestrator_adapter):
        """generate_response() - 단일 LLM 응답"""
        messages = [{"role": "user", "content": "Say hello"}]

        result = await orchestrator_adapter.generate_response(messages=messages, max_tokens=50)

        assert result["role"] == "assistant"
        assert len(result["content"]) > 0
        assert "model" in result
        assert isinstance(result["content"], str)

    async def test_generate_response_with_system_prompt(self, orchestrator_adapter):
        """generate_response() - system_prompt 적용"""
        messages = [{"role": "user", "content": "What is 2+2?"}]

        result = await orchestrator_adapter.generate_response(
            messages=messages,
            system_prompt="You are a math tutor. Answer concisely.",
            max_tokens=50,
        )

        assert "4" in result["content"]

    async def test_generate_response_with_custom_model(self, orchestrator_adapter):
        """generate_response() - 커스텀 모델 지정"""
        messages = [{"role": "user", "content": "Hi"}]

        result = await orchestrator_adapter.generate_response(
            messages=messages, model="openai/gpt-4o-mini", max_tokens=30
        )

        assert result["role"] == "assistant"
        assert len(result["content"]) > 0
