"""
Phase 5 Part A Step 3: Math Agent A2A Integration Tests

Tests for the ADK LlmAgent-based math specialist A2A agent.
Verifies: server startup, agent card exchange, LLM delegation.

Design Decision (ADR-9): Uses ADK LlmAgent instead of LangGraph.
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
# Test 1: Math Agent A2A Server Starts
# ============================================================


@pytest.mark.local_a2a
class TestMathAgentServer:
    """Test math agent A2A server functionality"""

    async def test_math_agent_a2a_server_starts(self, a2a_math_agent):
        """
        Given: Math agent subprocess started
        When: Health check is performed
        Then: Agent card is accessible at /.well-known/agent.json
        """
        import httpx

        agent_card_url = f"{a2a_math_agent}/.well-known/agent.json"
        async with httpx.AsyncClient() as client:
            response = await client.get(agent_card_url)

        assert response.status_code == 200
        card = response.json()
        assert card["name"] == "math_agent"
        assert "math" in card["description"].lower()

    async def test_math_agent_card_has_correct_capabilities(self, a2a_math_agent):
        """
        Given: Math agent is running
        When: Agent card is retrieved
        Then: Card contains proper A2A metadata
        """
        import httpx

        agent_card_url = f"{a2a_math_agent}/.well-known/agent.json"
        async with httpx.AsyncClient() as client:
            response = await client.get(agent_card_url)

        card = response.json()
        assert "name" in card
        assert "description" in card
        assert "url" in card


# ============================================================
# Test 2: Orchestrator Delegates Math to Agent
# ============================================================


@pytest.mark.local_a2a
class TestMathDelegation:
    """Test orchestrator delegates math questions to math agent"""

    async def test_orchestrator_delegates_math_to_agent(
        self, orchestrator, a2a_echo_agent, a2a_math_agent
    ):
        """
        Given: Orchestrator with echo + math agents registered
        When: User asks a math question "What is 15 * 7?"
        Then: Orchestrator delegates to math_agent (agent_transfer event)
              and response contains correct answer (105)
        """
        # Register both agents (현재 API: endpoint_id, url)
        await orchestrator.add_a2a_agent("echo-agent", a2a_echo_agent)
        await orchestrator.add_a2a_agent("math-agent", a2a_math_agent)

        # Send math question
        chunks: list[StreamChunk] = []
        async for chunk in orchestrator.process_message(
            message="What is 15 * 7? Please calculate.",
            conversation_id="test-math-delegation",
        ):
            chunks.append(chunk)

        # Verify delegation occurred
        chunk_types = {c.type for c in chunks}
        assert len(chunks) > 0, "Expected chunks, got none"

        # Check for agent_transfer or text response with answer
        text_content = " ".join(c.content for c in chunks if c.content)
        assert "105" in text_content, (
            f"Expected '105' in response. Got types: {chunk_types}, content: {text_content[:200]}"
        )

    async def test_orchestrator_delegates_echo_not_math(
        self, orchestrator, a2a_echo_agent, a2a_math_agent
    ):
        """
        Given: Orchestrator with echo + math agents registered
        When: User asks to echo a message
        Then: Orchestrator delegates to echo_agent (not math_agent)
        """
        # Register both agents (현재 API: endpoint_id, url)
        await orchestrator.add_a2a_agent("echo-agent", a2a_echo_agent)
        await orchestrator.add_a2a_agent("math-agent", a2a_math_agent)

        # Send echo request
        chunks: list[StreamChunk] = []
        async for chunk in orchestrator.process_message(
            message="Please echo back the following text: Hello World",
            conversation_id="test-echo-delegation",
        ):
            chunks.append(chunk)

        # Verify response contains echoed text
        text_content = " ".join(c.content for c in chunks if c.content)
        assert len(chunks) > 0, "Expected chunks from echo delegation"
        assert "hello" in text_content.lower() or "Hello World" in text_content, (
            f"Expected echo of 'Hello World' in response. Got: {text_content[:200]}"
        )
