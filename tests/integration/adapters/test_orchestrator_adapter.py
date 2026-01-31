"""AdkOrchestratorAdapter Integration Tests

TDD Phase: RED - 테스트 먼저 작성
"""

import pytest

from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset
from src.adapters.outbound.adk.orchestrator_adapter import AdkOrchestratorAdapter
from src.domain.entities.stream_chunk import StreamChunk


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

        # Then: StreamChunk 수신
        assert len(chunks) > 0
        assert all(isinstance(c, StreamChunk) for c in chunks)
        # 최소 하나의 text 타입 chunk 존재
        text_chunks = [c for c in chunks if c.type == "text"]
        assert len(text_chunks) > 0


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


class TestAdkOrchestratorAdapterA2aIntegration:
    """A2A Sub-Agent 통합 테스트 (TDD Step 7)"""

    async def test_add_a2a_sub_agent(self, orchestrator, a2a_echo_agent: str):
        """
        Given: Orchestrator가 초기화됨
        When: A2A 에이전트를 sub_agent로 추가
        Then: RemoteA2aAgent가 sub_agents에 추가되고 Agent 재구성됨
        """
        # Given: 초기화
        await orchestrator.initialize()
        initial_agent = orchestrator._agent

        # When: A2A sub_agent 추가
        endpoint_id = "test-a2a-echo"
        # Port 인터페이스는 base URL을 받아서 Agent Card URL로 변환
        await orchestrator.add_a2a_agent(endpoint_id, a2a_echo_agent)

        # Then: sub_agents에 추가됨
        assert endpoint_id in orchestrator._sub_agents
        assert len(orchestrator._sub_agents) == 1

        # Agent가 재구성됨 (새로운 인스턴스)
        assert orchestrator._agent is not initial_agent
        assert orchestrator._agent is not None

    async def test_remove_a2a_sub_agent(self, orchestrator, a2a_echo_agent: str):
        """
        Given: A2A sub_agent가 추가됨
        When: sub_agent 제거
        Then: sub_agents에서 제거되고 Agent 재구성됨
        """
        # Given: A2A sub_agent 추가
        await orchestrator.initialize()
        endpoint_id = "test-a2a-echo"
        await orchestrator.add_a2a_agent(endpoint_id, a2a_echo_agent)
        assert endpoint_id in orchestrator._sub_agents

        # When: sub_agent 제거
        await orchestrator.remove_a2a_agent(endpoint_id)

        # Then: 제거 성공
        assert endpoint_id not in orchestrator._sub_agents
        assert len(orchestrator._sub_agents) == 0

    async def test_remove_nonexistent_a2a_agent(self, orchestrator):
        """
        Given: 존재하지 않는 A2A agent ID
        When: 제거 시도
        Then: 에러 없이 정상 동작 (graceful skip)
        """
        # Given: 초기화
        await orchestrator.initialize()

        # When: 존재하지 않는 agent 제거 (에러 없음)
        await orchestrator.remove_a2a_agent("nonexistent-id")

        # Then: sub_agents 비어있음
        assert len(orchestrator._sub_agents) == 0

    async def test_orchestrator_preserves_session_after_rebuild(
        self, orchestrator, a2a_echo_agent: str
    ):
        """
        Given: 대화 세션이 존재함
        When: A2A agent 추가로 Agent 재구성
        Then: 세션 서비스가 유지됨 (대화 컨텍스트 보존)
        """
        # Given: 초기화 및 세션 생성
        await orchestrator.initialize()
        initial_session_service = orchestrator._session_service

        # When: A2A agent 추가 (Agent 재구성)
        endpoint_id = "test-echo"
        agent_card_url = f"{a2a_echo_agent}/.well-known/agent.json"
        await orchestrator.add_a2a_agent(endpoint_id, agent_card_url)

        # Then: 동일한 session_service 유지
        assert orchestrator._session_service is initial_session_service
        assert orchestrator._session_service is not None
