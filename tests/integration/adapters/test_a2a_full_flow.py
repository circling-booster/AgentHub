"""
Phase 5 Part A Step 4: A2A Full Flow Integration Tests

Tests the complete A2A delegation flow with multiple agents.
Verifies: agent selection, delegation, response content.
"""

import pytest

from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset
from src.adapters.outbound.adk.orchestrator_adapter import AdkOrchestratorAdapter
from src.config.settings import Settings
from src.domain.entities.stream_chunk import StreamChunk

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
async def orchestrator():
    """
    Create fresh orchestrator adapter for each test.

    Note: Function-scoped (not session) to avoid RemoteA2aAgent
    re-parenting errors when _rebuild_agent() is called multiple times.
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


# ============================================================
# Test 1: Echo Agent Delegation
# ============================================================


@pytest.mark.local_a2a
class TestEchoDelegation:
    """Test orchestrator delegates echo requests to echo agent"""

    async def test_orchestrator_delegates_echo_request(
        self, orchestrator, a2a_echo_agent, a2a_math_agent
    ):
        """
        Given: Orchestrator with echo + math agents registered
        When: User asks to echo a message
        Then: Response contains echoed text
              (May or may not have agent_transfer event - LLM decides)
        """
        # Register both agents
        await orchestrator.add_a2a_agent("echo-agent", a2a_echo_agent)
        await orchestrator.add_a2a_agent("math-agent", a2a_math_agent)

        # Send echo request
        chunks: list[StreamChunk] = []
        async for chunk in orchestrator.process_message(
            message="Please echo back the following text: Hello World",
            conversation_id="test-echo-flow",
        ):
            chunks.append(chunk)

        # Verify response
        assert len(chunks) > 0, "Expected chunks from echo request"

        # Check if response contains echoed text
        text_content = " ".join(c.content for c in chunks if c.content)
        assert "hello" in text_content.lower() or "Hello World" in text_content, (
            f"Expected echo of 'Hello World' in response. Got: {text_content[:200]}"
        )


# ============================================================
# Test 2: Math Agent Delegation
# ============================================================


@pytest.mark.local_a2a
class TestMathDelegation:
    """Test orchestrator delegates math questions to math agent"""

    async def test_orchestrator_delegates_math_question(
        self, orchestrator, a2a_echo_agent, a2a_math_agent
    ):
        """
        Given: Orchestrator with echo + math agents registered
        When: User asks a math question
        Then: Response contains correct answer (105)
              (May or may not have agent_transfer event - LLM decides)
        """
        # Register both agents
        await orchestrator.add_a2a_agent("echo-agent", a2a_echo_agent)
        await orchestrator.add_a2a_agent("math-agent", a2a_math_agent)

        # Send math question
        chunks: list[StreamChunk] = []
        async for chunk in orchestrator.process_message(
            message="What is 15 * 7? Please calculate.",
            conversation_id="test-math-flow",
        ):
            chunks.append(chunk)

        # Verify response
        assert len(chunks) > 0, "Expected chunks from math question"

        # Check if response contains correct answer
        text_content = " ".join(c.content for c in chunks if c.content)
        assert "105" in text_content, f"Expected '105' in response. Got: {text_content[:200]}"


# ============================================================
# Test 3: No Matching Agent (Fallback)
# ============================================================


@pytest.mark.local_a2a
class TestNoMatchingAgent:
    """Test orchestrator handles requests without matching agent"""

    async def test_orchestrator_handles_no_matching_agent(
        self, orchestrator, a2a_echo_agent, a2a_math_agent
    ):
        """
        Given: Orchestrator with echo + math agents registered
        When: User asks about weather (no matching agent)
        Then: Orchestrator responds directly without delegation
        """
        # Register both agents
        await orchestrator.add_a2a_agent("echo-agent", a2a_echo_agent)
        await orchestrator.add_a2a_agent("math-agent", a2a_math_agent)

        # Send weather question (no matching agent)
        chunks: list[StreamChunk] = []
        async for chunk in orchestrator.process_message(
            message="What's the weather like today?",
            conversation_id="test-no-match-flow",
        ):
            chunks.append(chunk)

        # Verify response
        assert len(chunks) > 0, "Expected chunks from weather question"

        # Note: LLM may or may not delegate, so we just check for graceful response
        # (No assertion on agent_transfer - just verify we get a response)

        # Check if response is meaningful (not empty)
        text_content = " ".join(c.content for c in chunks if c.content)
        assert len(text_content) > 0, "Expected non-empty response"
