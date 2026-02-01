"""
Workflow domain entities

Pure Python dataclasses representing multi-step agent workflows.
No external dependencies (ADK, FastAPI, etc.) - Domain Layer purity.

A Workflow defines a sequence of agent execution steps, where each step
invokes a registered A2A agent endpoint with optional state sharing.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class WorkflowStep:
    """
    A single execution step within a Workflow

    Attributes:
        agent_endpoint_id: ID of the registered A2A agent endpoint
        output_key: Key to store this step's result in session.state
        instruction: Optional step-specific instruction override
    """

    agent_endpoint_id: str
    output_key: str
    instruction: str = ""


@dataclass
class Workflow:
    """
    Multi-step Agent Workflow definition

    Represents a sequence of agent invocations that can be executed
    either sequentially (SequentialAgent) or in parallel (ParallelAgent).

    Attributes:
        id: Unique workflow identifier
        name: Human-readable workflow name
        workflow_type: Execution strategy ("sequential" | "parallel")
        steps: Ordered list of WorkflowStep to execute
        description: Optional workflow description
        created_at: Timestamp when workflow was created
    """

    id: str
    name: str
    workflow_type: str  # "sequential" | "parallel"
    steps: list[WorkflowStep]
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
