"""
Unit tests for OrchestratorAdapter workflow support

Tests workflow agent creation and execution using mocked dependencies.
"""

import pytest

from src.domain.entities.workflow import Workflow, WorkflowStep
from src.domain.exceptions import WorkflowNotFoundError


class TestWorkflowAgentCreation:
    """Test create_workflow_agent method"""

    async def test_create_sequential_workflow_agent(self, fake_orchestrator):
        """
        Given: Sequential workflow with 2 steps
        When: create_workflow_agent() is called
        Then: Workflow agent is created and stored

        This is a unit test with fake dependencies.
        """
        # Given
        workflow = Workflow(
            id="wf-seq-1",
            name="Echo then Math",
            workflow_type="sequential",
            steps=[
                WorkflowStep(
                    agent_endpoint_id="echo-1",
                    output_key="echo_result",
                ),
                WorkflowStep(
                    agent_endpoint_id="math-1",
                    output_key="math_result",
                ),
            ],
        )

        # When
        await fake_orchestrator.create_workflow_agent(workflow)

        # Then
        # Verify workflow was stored (implementation-specific check)
        assert workflow.id in fake_orchestrator._workflows

    async def test_create_parallel_workflow_agent(self, fake_orchestrator):
        """
        Given: Parallel workflow with 2 agents
        When: create_workflow_agent() is called
        Then: Parallel workflow agent is created
        """
        # Given
        workflow = Workflow(
            id="wf-par-1",
            name="Echo and Math in parallel",
            workflow_type="parallel",
            steps=[
                WorkflowStep(
                    agent_endpoint_id="echo-1",
                    output_key="echo_out",
                ),
                WorkflowStep(
                    agent_endpoint_id="math-1",
                    output_key="math_out",
                ),
            ],
        )

        # When
        await fake_orchestrator.create_workflow_agent(workflow)

        # Then
        assert workflow.id in fake_orchestrator._workflows
        assert fake_orchestrator._workflows[workflow.id].workflow_type == "parallel"


class TestWorkflowExecution:
    """Test execute_workflow method"""

    async def test_execute_workflow_streams_events(self, fake_orchestrator):
        """
        Given: Created sequential workflow
        When: execute_workflow() is called
        Then: Workflow events are streamed in order
        """
        # Given
        workflow = Workflow(
            id="wf-exec-1",
            name="Test Workflow",
            workflow_type="sequential",
            steps=[
                WorkflowStep(
                    agent_endpoint_id="echo-1",
                    output_key="step1_out",
                ),
                WorkflowStep(
                    agent_endpoint_id="math-1",
                    output_key="step2_out",
                ),
            ],
        )
        await fake_orchestrator.create_workflow_agent(workflow)

        # When
        events = []
        async for chunk in fake_orchestrator.execute_workflow(
            workflow_id="wf-exec-1",
            message="Test message",
            conversation_id="conv-123",
        ):
            events.append(chunk)

        # Then
        assert len(events) >= 4  # start, step_start, step_complete, complete
        assert events[0].type == "workflow_start"
        assert events[0].workflow_id == "wf-exec-1"
        assert events[0].workflow_type == "sequential"
        assert events[0].total_steps == 2

        # Find workflow_complete event
        complete_events = [e for e in events if e.type == "workflow_complete"]
        assert len(complete_events) == 1
        assert complete_events[0].workflow_status == "success"

    async def test_execute_workflow_step_events(self, fake_orchestrator):
        """
        Given: Created workflow
        When: execute_workflow() is called
        Then: workflow_step_start and workflow_step_complete events are emitted
        """
        # Given
        workflow = Workflow(
            id="wf-steps-1",
            name="Step Events Test",
            workflow_type="sequential",
            steps=[
                WorkflowStep(agent_endpoint_id="echo-1", output_key="out1"),
                WorkflowStep(agent_endpoint_id="math-1", output_key="out2"),
            ],
        )
        await fake_orchestrator.create_workflow_agent(workflow)

        # When
        events = []
        async for chunk in fake_orchestrator.execute_workflow(
            workflow_id="wf-steps-1",
            message="Test",
            conversation_id="conv-456",
        ):
            events.append(chunk)

        # Then
        step_start_events = [e for e in events if e.type == "workflow_step_start"]
        step_complete_events = [e for e in events if e.type == "workflow_step_complete"]

        assert len(step_start_events) == 2
        assert len(step_complete_events) == 2

        # Verify step numbers
        assert step_start_events[0].step_number == 1
        assert step_start_events[1].step_number == 2

    async def test_workflow_not_found_error(self, fake_orchestrator):
        """
        Given: Workflow not created
        When: execute_workflow() is called
        Then: WorkflowNotFoundError is raised
        """
        # When / Then
        with pytest.raises(WorkflowNotFoundError):
            async for _chunk in fake_orchestrator.execute_workflow(
                workflow_id="non-existent",
                message="Test",
                conversation_id="conv-789",
            ):
                pass


class TestWorkflowAgentRemoval:
    """Test workflow agent lifecycle"""

    async def test_remove_workflow_agent(self, fake_orchestrator):
        """
        Given: Created workflow
        When: remove_workflow_agent() is called
        Then: Workflow is removed from storage
        """
        # Given
        workflow = Workflow(
            id="wf-remove-1",
            name="To be removed",
            workflow_type="sequential",
            steps=[WorkflowStep(agent_endpoint_id="echo-1", output_key="out")],
        )
        await fake_orchestrator.create_workflow_agent(workflow)
        assert workflow.id in fake_orchestrator._workflows

        # When
        await fake_orchestrator.remove_workflow_agent(workflow.id)

        # Then
        assert workflow.id not in fake_orchestrator._workflows

    async def test_remove_nonexistent_workflow_no_error(self, fake_orchestrator):
        """
        Given: Workflow not created
        When: remove_workflow_agent() is called
        Then: No error is raised (idempotent)
        """
        # When / Then (should not raise)
        await fake_orchestrator.remove_workflow_agent("non-existent-wf")
