"""
Integration tests for Workflow Agent execution

Tests real ADK SequentialAgent/ParallelAgent with Echo and Math A2A agents.
"""

import pytest

from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset
from src.adapters.outbound.adk.orchestrator_adapter import AdkOrchestratorAdapter
from src.domain.entities.workflow import Workflow, WorkflowStep

# Test configuration
TEST_MODEL = "openai/gpt-4o-mini"  # Use fast, cheap model for tests


@pytest.mark.local_a2a
class TestSequentialWorkflowIntegration:
    """Test Sequential Workflow with real A2A agents (Echo → Math)"""

    @pytest.mark.asyncio
    async def test_echo_math_sequential_workflow(self, a2a_echo_agent, a2a_math_agent):
        """
        Given: Sequential workflow with Echo → Math agents
        When: Workflow is executed with message
        Then: Both agents execute sequentially and events are emitted

        This is a full integration test with real ADK + A2A agents.
        """
        # Setup
        dynamic_toolset = DynamicToolset(cache_ttl_seconds=60)
        orchestrator = AdkOrchestratorAdapter(
            model=TEST_MODEL,
            dynamic_toolset=dynamic_toolset,
            enable_llm_logging=False,  # Disable for test
        )

        try:
            await orchestrator.initialize()

            # Register A2A agents
            await orchestrator.add_a2a_agent("echo-agent", a2a_echo_agent)
            await orchestrator.add_a2a_agent("math-agent", a2a_math_agent)

            # Create workflow
            workflow = Workflow(
                id="wf-echo-math-seq",
                name="Echo then Math Sequential",
                workflow_type="sequential",
                steps=[
                    WorkflowStep(
                        agent_endpoint_id="echo-agent",
                        output_key="echo_result",
                        instruction="Echo the user message",
                    ),
                    WorkflowStep(
                        agent_endpoint_id="math-agent",
                        output_key="math_result",
                        instruction="Calculate based on the echo result",
                    ),
                ],
            )

            await orchestrator.create_workflow_agent(workflow)

            # Execute workflow
            events = []
            async for chunk in orchestrator.execute_workflow(
                workflow_id="wf-echo-math-seq",
                message="First echo 'Hello', then calculate 5+3",
                conversation_id="test-conv-seq",
            ):
                events.append(chunk)

            # Verify workflow events
            event_types = [e.type for e in events]

            # Must have workflow_start
            assert "workflow_start" in event_types
            workflow_start = [e for e in events if e.type == "workflow_start"][0]
            assert workflow_start.workflow_id == "wf-echo-math-seq"
            assert workflow_start.workflow_type == "sequential"
            assert workflow_start.total_steps == 2

            # Must have workflow_complete
            assert "workflow_complete" in event_types
            workflow_complete = [e for e in events if e.type == "workflow_complete"][0]
            assert workflow_complete.workflow_status == "success"
            assert workflow_complete.total_steps == 2

            # Should have text responses
            text_events = [e for e in events if e.type == "text"]
            assert len(text_events) > 0

        finally:
            await orchestrator.close()
            await dynamic_toolset.close()

    @pytest.mark.asyncio
    async def test_workflow_agent_lifecycle(self, a2a_echo_agent):
        """
        Given: Workflow agent created
        When: Workflow agent is removed
        Then: Workflow can no longer be executed

        Tests workflow agent lifecycle management.
        """
        # Setup
        dynamic_toolset = DynamicToolset(cache_ttl_seconds=60)
        orchestrator = AdkOrchestratorAdapter(
            model=TEST_MODEL,
            dynamic_toolset=dynamic_toolset,
            enable_llm_logging=False,
        )

        try:
            await orchestrator.initialize()
            await orchestrator.add_a2a_agent("echo-agent", a2a_echo_agent)

            # Create workflow
            workflow = Workflow(
                id="wf-lifecycle",
                name="Lifecycle Test",
                workflow_type="sequential",
                steps=[
                    WorkflowStep(
                        agent_endpoint_id="echo-agent",
                        output_key="echo_out",
                    ),
                ],
            )

            await orchestrator.create_workflow_agent(workflow)

            # Remove workflow
            await orchestrator.remove_workflow_agent("wf-lifecycle")

            # Verify workflow cannot be executed
            from src.domain.exceptions import WorkflowNotFoundError

            with pytest.raises(WorkflowNotFoundError):
                async for _chunk in orchestrator.execute_workflow(
                    workflow_id="wf-lifecycle",
                    message="Test",
                    conversation_id="test-conv",
                ):
                    pass

        finally:
            await orchestrator.close()
            await dynamic_toolset.close()


@pytest.mark.local_a2a
class TestWorkflowAgentCreationValidation:
    """Test workflow agent creation validation"""

    @pytest.mark.asyncio
    async def test_workflow_with_unregistered_agent_fails(self):
        """
        Given: Workflow referencing unregistered A2A agent
        When: create_workflow_agent() is called
        Then: RuntimeError is raised

        Validates that all agents must be registered before workflow creation.
        """
        # Setup
        dynamic_toolset = DynamicToolset(cache_ttl_seconds=60)
        orchestrator = AdkOrchestratorAdapter(
            model=TEST_MODEL,
            dynamic_toolset=dynamic_toolset,
            enable_llm_logging=False,
        )

        try:
            await orchestrator.initialize()

            # Create workflow WITHOUT registering agents
            workflow = Workflow(
                id="wf-invalid",
                name="Invalid Workflow",
                workflow_type="sequential",
                steps=[
                    WorkflowStep(
                        agent_endpoint_id="non-existent-agent",
                        output_key="out",
                    ),
                ],
            )

            # Should raise RuntimeError
            with pytest.raises(RuntimeError, match="Agent not registered: non-existent-agent"):
                await orchestrator.create_workflow_agent(workflow)

        finally:
            await orchestrator.close()
            await dynamic_toolset.close()

    @pytest.mark.asyncio
    async def test_invalid_workflow_type_fails(self, a2a_echo_agent):
        """
        Given: Workflow with invalid workflow_type
        When: create_workflow_agent() is called
        Then: ValueError is raised

        Validates workflow_type must be "sequential" or "parallel".
        """
        # Setup
        dynamic_toolset = DynamicToolset(cache_ttl_seconds=60)
        orchestrator = AdkOrchestratorAdapter(
            model=TEST_MODEL,
            dynamic_toolset=dynamic_toolset,
            enable_llm_logging=False,
        )

        try:
            await orchestrator.initialize()
            await orchestrator.add_a2a_agent("echo-agent", a2a_echo_agent)

            # Create workflow with invalid type
            workflow = Workflow(
                id="wf-invalid-type",
                name="Invalid Type Workflow",
                workflow_type="invalid_type",  # Invalid!
                steps=[
                    WorkflowStep(
                        agent_endpoint_id="echo-agent",
                        output_key="out",
                    ),
                ],
            )

            # Should raise ValueError
            with pytest.raises(ValueError, match="Invalid workflow_type: invalid_type"):
                await orchestrator.create_workflow_agent(workflow)

        finally:
            await orchestrator.close()
            await dynamic_toolset.close()
