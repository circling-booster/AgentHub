"""
Unit tests for Workflow domain entities

Tests the pure Python Workflow and WorkflowStep entities
without any external dependencies (ADK, FastAPI, etc.)
"""

from datetime import datetime

from src.domain.entities.workflow import Workflow, WorkflowStep


class TestWorkflowStep:
    """Test WorkflowStep dataclass creation and validation"""

    def test_workflow_step_creation_with_required_fields(self):
        """
        Given: agent_endpoint_id and output_key
        When: WorkflowStep is created
        Then: WorkflowStep instance is created with default instruction
        """
        # When
        step = WorkflowStep(
            agent_endpoint_id="endpoint-123",
            output_key="result_key",
        )

        # Then
        assert step.agent_endpoint_id == "endpoint-123"
        assert step.output_key == "result_key"
        assert step.instruction == ""  # Default value

    def test_workflow_step_creation_with_optional_instruction(self):
        """
        Given: all fields including instruction
        When: WorkflowStep is created
        Then: WorkflowStep instance is created with custom instruction
        """
        # When
        step = WorkflowStep(
            agent_endpoint_id="endpoint-456",
            output_key="math_result",
            instruction="Calculate the sum of two numbers",
        )

        # Then
        assert step.agent_endpoint_id == "endpoint-456"
        assert step.output_key == "math_result"
        assert step.instruction == "Calculate the sum of two numbers"

    def test_workflow_step_equality(self):
        """
        Given: Two WorkflowStep instances with identical values
        When: Compared for equality
        Then: They are equal (dataclass auto-generated __eq__)
        """
        # Given
        step1 = WorkflowStep(
            agent_endpoint_id="endpoint-789",
            output_key="echo_result",
        )
        step2 = WorkflowStep(
            agent_endpoint_id="endpoint-789",
            output_key="echo_result",
        )

        # Then
        assert step1 == step2

    def test_workflow_step_inequality(self):
        """
        Given: Two WorkflowStep instances with different values
        When: Compared for equality
        Then: They are not equal
        """
        # Given
        step1 = WorkflowStep(
            agent_endpoint_id="endpoint-1",
            output_key="key1",
        )
        step2 = WorkflowStep(
            agent_endpoint_id="endpoint-2",
            output_key="key2",
        )

        # Then
        assert step1 != step2


class TestWorkflow:
    """Test Workflow dataclass creation and validation"""

    def test_workflow_creation_with_sequential_type(self):
        """
        Given: Required fields with sequential workflow_type
        When: Workflow is created
        Then: Workflow instance is created with default description and auto-generated created_at
        """
        # Given
        steps = [
            WorkflowStep(agent_endpoint_id="echo-1", output_key="echo_out"),
            WorkflowStep(agent_endpoint_id="math-1", output_key="math_out"),
        ]

        # When
        workflow = Workflow(
            id="workflow-123",
            name="Echo then Math",
            workflow_type="sequential",
            steps=steps,
        )

        # Then
        assert workflow.id == "workflow-123"
        assert workflow.name == "Echo then Math"
        assert workflow.workflow_type == "sequential"
        assert workflow.steps == steps
        assert workflow.description == ""
        assert isinstance(workflow.created_at, datetime)

    def test_workflow_creation_with_parallel_type(self):
        """
        Given: Required fields with parallel workflow_type
        When: Workflow is created
        Then: Workflow instance is created successfully
        """
        # Given
        steps = [
            WorkflowStep(agent_endpoint_id="echo-1", output_key="echo_out"),
            WorkflowStep(agent_endpoint_id="math-1", output_key="math_out"),
        ]

        # When
        workflow = Workflow(
            id="workflow-456",
            name="Echo and Math in parallel",
            workflow_type="parallel",
            steps=steps,
        )

        # Then
        assert workflow.workflow_type == "parallel"

    def test_workflow_creation_with_optional_description(self):
        """
        Given: All fields including description
        When: Workflow is created
        Then: Workflow instance is created with custom description
        """
        # Given
        steps = [
            WorkflowStep(agent_endpoint_id="agent-1", output_key="step1"),
        ]

        # When
        workflow = Workflow(
            id="workflow-789",
            name="Test Workflow",
            workflow_type="sequential",
            steps=steps,
            description="This is a test workflow for documentation",
        )

        # Then
        assert workflow.description == "This is a test workflow for documentation"

    def test_workflow_steps_are_mutable_list(self):
        """
        Given: Workflow with steps
        When: Steps list is modified
        Then: Modifications are reflected in the workflow
        """
        # Given
        steps = [
            WorkflowStep(agent_endpoint_id="agent-1", output_key="step1"),
        ]
        workflow = Workflow(
            id="workflow-mutable",
            name="Mutable Test",
            workflow_type="sequential",
            steps=steps,
        )

        # When
        workflow.steps.append(WorkflowStep(agent_endpoint_id="agent-2", output_key="step2"))

        # Then
        assert len(workflow.steps) == 2
        assert workflow.steps[1].agent_endpoint_id == "agent-2"

    def test_workflow_empty_steps_list(self):
        """
        Given: Empty steps list
        When: Workflow is created
        Then: Workflow is created (validation is adapter layer responsibility)
        """
        # When
        workflow = Workflow(
            id="workflow-empty",
            name="Empty Workflow",
            workflow_type="sequential",
            steps=[],
        )

        # Then
        assert workflow.steps == []

    def test_workflow_created_at_default_factory(self):
        """
        Given: Workflow without explicit created_at
        When: Two workflows are created with slight time delay
        Then: Each has its own created_at timestamp
        """
        # When
        workflow1 = Workflow(
            id="workflow-1",
            name="First",
            workflow_type="sequential",
            steps=[],
        )
        workflow2 = Workflow(
            id="workflow-2",
            name="Second",
            workflow_type="sequential",
            steps=[],
        )

        # Then
        assert workflow1.created_at is not None
        assert workflow2.created_at is not None
        # They should be different instances (not the same datetime object)
        assert workflow1.created_at is not workflow2.created_at

    def test_workflow_type_accepts_any_string(self):
        """
        Given: workflow_type as any string value
        When: Workflow is created
        Then: Workflow accepts the value (type validation is adapter layer responsibility)

        Note: Domain entities are pure Python with minimal validation.
        Type validation ("sequential" | "parallel" enum) should be in adapter layer.
        """
        # When
        workflow = Workflow(
            id="workflow-custom",
            name="Custom Type",
            workflow_type="custom_type",  # Not "sequential" or "parallel"
            steps=[],
        )

        # Then
        assert workflow.workflow_type == "custom_type"


class TestWorkflowStepIntegration:
    """Test Workflow and WorkflowStep integration"""

    def test_workflow_with_multiple_steps(self):
        """
        Given: Multiple WorkflowStep instances
        When: Workflow is created with these steps
        Then: All steps are correctly stored in order
        """
        # Given
        step1 = WorkflowStep(
            agent_endpoint_id="echo-agent",
            output_key="echo_result",
            instruction="Echo the user input",
        )
        step2 = WorkflowStep(
            agent_endpoint_id="math-agent",
            output_key="math_result",
            instruction="Calculate based on previous result",
        )
        step3 = WorkflowStep(
            agent_endpoint_id="echo-agent",
            output_key="final_echo",
            instruction="Echo the final result",
        )

        # When
        workflow = Workflow(
            id="workflow-multi",
            name="Echo → Math → Echo",
            workflow_type="sequential",
            steps=[step1, step2, step3],
            description="Three-step sequential workflow",
        )

        # Then
        assert len(workflow.steps) == 3
        assert workflow.steps[0].agent_endpoint_id == "echo-agent"
        assert workflow.steps[1].agent_endpoint_id == "math-agent"
        assert workflow.steps[2].agent_endpoint_id == "echo-agent"
        assert workflow.steps[0].output_key == "echo_result"
        assert workflow.steps[1].output_key == "math_result"
        assert workflow.steps[2].output_key == "final_echo"
