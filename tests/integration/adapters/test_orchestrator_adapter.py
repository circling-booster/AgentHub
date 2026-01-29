"""AdkOrchestratorAdapter Integration Tests

TDD Phase: RED - 테스트 먼저 작성
"""

import pytest

from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset
from src.adapters.outbound.adk.orchestrator_adapter import AdkOrchestratorAdapter


@pytest.fixture
def dynamic_toolset():
    """DynamicToolset 인스턴스 (빈 상태)"""
    return DynamicToolset(cache_ttl_seconds=300)


@pytest.fixture
def orchestrator(dynamic_toolset):
    """AdkOrchestratorAdapter 인스턴스"""
    return AdkOrchestratorAdapter(
        model="openai/gpt-4o-mini",  # 비용 최소화
        dynamic_toolset=dynamic_toolset,
        instruction="You are a test assistant.",
    )


class TestAdkOrchestratorAdapterAsyncFactory:
    """Async Factory Pattern 검증"""

    async def test_initialization_before_use(self, orchestrator):
        """initialize() 호출 전에는 Agent가 None"""
        # Then: Agent가 아직 생성되지 않음
        assert orchestrator._agent is None
        assert orchestrator._initialized is False

    async def test_initialize_creates_agent(self, orchestrator):
        """initialize() 호출 시 LlmAgent 생성"""
        # When: 초기화
        await orchestrator.initialize()

        # Then: Agent 생성됨
        assert orchestrator._agent is not None
        assert orchestrator._initialized is True

    async def test_initialize_idempotent(self, orchestrator):
        """initialize() 여러 번 호출해도 안전"""
        # When: 2회 초기화
        await orchestrator.initialize()
        agent1 = orchestrator._agent

        await orchestrator.initialize()
        agent2 = orchestrator._agent

        # Then: 동일한 Agent 인스턴스 (재생성 안 함)
        assert agent1 is agent2


class TestAdkOrchestratorAdapterProcessMessage:
    """메시지 처리 및 스트리밍 검증"""

    @pytest.mark.llm
    async def test_process_message_without_initialization(self, orchestrator, request):
        """initialize() 없이 process_message() 호출 시 자동 초기화"""
        if not request.config.getoption("--run-llm"):
            pytest.skip("LLM 테스트는 --run-llm 옵션 필요 (비용 발생)")

        # When: initialize 생략하고 바로 메시지 처리
        chunks = []
        async for chunk in orchestrator.process_message(
            message="Say 'test'", conversation_id="test-conv"
        ):
            chunks.append(chunk)

        # Then: 응답 수신 (자동 초기화됨)
        assert orchestrator._initialized is True
        assert len(chunks) > 0

    @pytest.mark.llm
    async def test_process_message_streaming(self, orchestrator, request):
        """메시지 처리 시 스트리밍 응답"""
        if not request.config.getoption("--run-llm"):
            pytest.skip("LLM 테스트는 --run-llm 옵션 필요 (비용 발생)")

        # Given: 초기화
        await orchestrator.initialize()

        # When: 간단한 메시지 처리
        chunks = []
        async for chunk in orchestrator.process_message(
            message="Say hello", conversation_id="test-conv"
        ):
            chunks.append(chunk)

        # Then: 텍스트 chunk 수신
        assert len(chunks) > 0
        assert all(isinstance(c, str) for c in chunks)


class TestAdkOrchestratorAdapterCleanup:
    """리소스 정리 검증"""

    async def test_close(self, orchestrator, dynamic_toolset):
        """close() 시 DynamicToolset 정리"""
        # Given: 초기화
        await orchestrator.initialize()

        # When: close 호출
        await orchestrator.close()

        # Then: Agent null, DynamicToolset 정리됨
        assert orchestrator._agent is None
        assert orchestrator._initialized is False
