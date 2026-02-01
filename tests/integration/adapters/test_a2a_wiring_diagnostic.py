"""
A2A Wiring Diagnostic Tests

Phase 5 Part A - Step 1: A2A 에이전트가 LlmAgent에 올바르게 연결되는지 진단

검증 항목:
1. sub_agents 딕셔너리가 채워지는지
2. _rebuild_agent() 후 LlmAgent.sub_agents에 포함되는지
3. 동적 instruction에 A2A 섹션이 포함되는지
4. LLM이 실제로 agent_transfer 이벤트를 생성하는지 (integration)
"""

import pytest

from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset
from src.adapters.outbound.adk.orchestrator_adapter import AdkOrchestratorAdapter
from src.config.settings import Settings


@pytest.fixture
async def orchestrator():
    """
    Orchestrator 어댑터 fixture (초기화된 상태)
    """
    settings = Settings()
    toolset = DynamicToolset(cache_ttl_seconds=300)

    adapter = AdkOrchestratorAdapter(
        model=settings.llm.default_model,
        dynamic_toolset=toolset,
        instruction="You are a helpful assistant.",
    )

    await adapter.initialize()

    yield adapter

    await adapter.close()


@pytest.mark.asyncio
async def test_sub_agents_populated_after_registration(orchestrator, a2a_echo_agent):
    """
    진단 1: A2A 에이전트 등록 후 sub_agents 딕셔너리가 채워지는지 확인

    Given: 초기화된 Orchestrator
    When: A2A 에이전트를 등록
    Then: _sub_agents 딕셔너리에 해당 endpoint_id로 RemoteA2aAgent가 저장됨
    """
    # Given: 초기 상태 - sub_agents 비어있음
    assert len(orchestrator._sub_agents) == 0

    # When: A2A 에이전트 등록
    endpoint_id = "echo-agent-test"
    await orchestrator.add_a2a_agent(endpoint_id, a2a_echo_agent)

    # Then: sub_agents에 추가됨
    assert len(orchestrator._sub_agents) == 1
    assert endpoint_id in orchestrator._sub_agents

    # RemoteA2aAgent 타입 확인
    remote_agent = orchestrator._sub_agents[endpoint_id]
    assert remote_agent.name == f"a2a_{endpoint_id}".replace("-", "_")


@pytest.mark.asyncio
async def test_rebuild_agent_includes_sub_agents(orchestrator, a2a_echo_agent):
    """
    진단 2: _rebuild_agent() 후 LlmAgent.sub_agents에 포함되는지 확인

    Given: A2A 에이전트가 등록된 Orchestrator
    When: _rebuild_agent() 호출
    Then: LlmAgent의 sub_agents 속성에 RemoteA2aAgent가 포함됨
    """
    # Given: A2A 에이전트 등록 (내부적으로 _rebuild_agent 호출됨)
    endpoint_id = "echo-agent-test"
    await orchestrator.add_a2a_agent(endpoint_id, a2a_echo_agent)

    # Then: LlmAgent.sub_agents에 포함되는지 확인
    assert orchestrator._agent is not None
    assert hasattr(orchestrator._agent, "sub_agents")

    # sub_agents가 None이 아니고, 1개 이상 포함
    agent_sub_agents = orchestrator._agent.sub_agents
    assert agent_sub_agents is not None
    assert len(agent_sub_agents) > 0

    # 등록한 RemoteA2aAgent가 포함되는지 확인
    remote_agent = orchestrator._sub_agents[endpoint_id]
    assert remote_agent in agent_sub_agents


@pytest.mark.asyncio
async def test_dynamic_instruction_contains_a2a_section(orchestrator, a2a_echo_agent):
    """
    진단 3: 동적 instruction에 A2A 에이전트 정보가 포함되는지 확인

    Given: A2A 에이전트가 등록된 Orchestrator
    When: _build_dynamic_instruction() 호출
    Then: instruction에 "A2A" 또는 "agent" 키워드 포함
    """
    # Given: A2A 에이전트 등록
    endpoint_id = "echo-agent-test"
    await orchestrator.add_a2a_agent(endpoint_id, a2a_echo_agent)

    # When: 동적 instruction 생성
    instruction = orchestrator._build_dynamic_instruction()

    # Then: A2A 관련 섹션 포함 확인
    instruction_lower = instruction.lower()

    # "A2A Agents Available" 섹션이 있어야 함
    assert "a2a" in instruction_lower or "agent" in instruction_lower

    # 등록한 에이전트 이름이 포함되어야 함
    assert "echo" in instruction_lower or endpoint_id in instruction_lower


@pytest.mark.asyncio
@pytest.mark.llm
async def test_llm_delegates_to_a2a_agent(orchestrator, a2a_echo_agent):
    """
    진단 4: LLM이 실제로 A2A 에이전트에 태스크를 위임하는지 확인 (integration)

    Given: Echo 에이전트가 등록된 Orchestrator
    When: "Echo this: hello world" 메시지 전송
    Then: SSE 스트림에 agent_transfer 이벤트가 포함되어야 함

    주의: 이 테스트는 실제 LLM을 호출하므로 API 키가 필요하고,
          LLM의 판단에 따라 불안정할 수 있음 (flaky test)
    """
    # Given: Echo 에이전트 등록
    endpoint_id = "echo-agent-test"
    await orchestrator.add_a2a_agent(endpoint_id, a2a_echo_agent)

    # When: 명시적으로 Echo 요청하는 메시지 전송
    # (Echo agent description에 "echo", "repeat" 키워드가 있어야 LLM이 위임함)
    conversation_id = "diagnostic-test-conv"
    message = "Please echo this message: hello world"

    # Then: 스트림 수집
    chunks = []
    async for chunk in orchestrator.process_message(message, conversation_id):
        chunks.append(chunk)

    # agent_transfer 이벤트가 있는지 확인
    agent_transfer_chunks = [c for c in chunks if c.type == "agent_transfer"]

    # 현재 구현 검증: agent_transfer가 있으면 성공
    # 없으면 실패 (wiring 문제 또는 Echo agent description 문제)
    chunk_types = {c.type for c in chunks}
    assert len(agent_transfer_chunks) > 0, (
        f"No agent_transfer events found. Total chunks: {len(chunks)}, Types: {chunk_types}"
    )

    # agent_transfer 이벤트의 agent_name 확인
    transfer_event = agent_transfer_chunks[0]
    assert transfer_event.agent_name != "", (
        f"agent_transfer event has empty agent_name: {transfer_event}"
    )
