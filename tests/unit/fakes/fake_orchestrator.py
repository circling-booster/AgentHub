"""Fake Orchestrator Adapter - 테스트용 오케스트레이터

OrchestratorPort의 테스트용 구현입니다.
"""

from collections.abc import AsyncIterator

from src.domain.entities.stream_chunk import StreamChunk
from src.domain.entities.workflow import Workflow
from src.domain.exceptions import WorkflowNotFoundError
from src.domain.ports.outbound.orchestrator_port import OrchestratorPort


class FakeOrchestrator(OrchestratorPort):
    """
    테스트용 오케스트레이터

    테스트용 OrchestratorPort 구현입니다.
    설정된 응답을 스트리밍으로 반환합니다.
    """

    def __init__(
        self,
        responses: list[StreamChunk] | None = None,
        should_fail: bool = False,
        error_message: str = "Orchestrator error",
    ) -> None:
        """
        Args:
            responses: 반환할 StreamChunk 목록
            should_fail: True면 에러 발생
            error_message: 에러 발생 시 메시지
        """
        self.responses: list[StreamChunk] = responses or [
            StreamChunk.text("Hello! "),
            StreamChunk.text("How can I help you?"),
        ]
        self.should_fail = should_fail
        self.error_message = error_message
        self.initialized = False
        self.closed = False
        self.processed_messages: list[tuple[str, str]] = []  # (message, conv_id)
        self.added_a2a_agents: list[tuple[str, str]] = []  # (endpoint_id, url)
        self.removed_a2a_agents: list[str] = []  # endpoint_id
        self._workflows: dict[str, Workflow] = {}  # workflow_id -> Workflow

    async def initialize(self) -> None:
        """초기화"""
        self.initialized = True

    async def process_message(
        self,
        message: str,
        conversation_id: str,
        page_context: dict | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """
        메시지 처리 및 스트리밍 응답

        설정된 responses를 하나씩 yield합니다.
        """
        if self.should_fail:
            raise RuntimeError(self.error_message)

        self.processed_messages.append((message, conversation_id))

        for chunk in self.responses:
            yield chunk

    async def close(self) -> None:
        """리소스 정리"""
        self.closed = True

    def set_responses(self, responses: list[StreamChunk]) -> None:
        """응답 설정"""
        self.responses = responses

    def set_failure(self, should_fail: bool, message: str = "Orchestrator error") -> None:
        """실패 모드 설정"""
        self.should_fail = should_fail
        self.error_message = message

    async def add_a2a_agent(self, endpoint_id: str, url: str) -> None:
        """
        A2A 에이전트를 LLM sub_agents에 추가

        Args:
            endpoint_id: 엔드포인트 ID
            url: A2A 에이전트 URL
        """
        self.added_a2a_agents.append((endpoint_id, url))

    async def remove_a2a_agent(self, endpoint_id: str) -> None:
        """
        A2A 에이전트를 LLM sub_agents에서 제거

        Args:
            endpoint_id: 엔드포인트 ID
        """
        self.removed_a2a_agents.append(endpoint_id)

    async def create_workflow_agent(self, workflow: Workflow) -> None:
        """
        Workflow Agent 생성 (테스트용 간단 구현)

        Args:
            workflow: Workflow 엔티티
        """
        self._workflows[workflow.id] = workflow

    async def execute_workflow(
        self,
        workflow_id: str,
        message: str,
        conversation_id: str,
    ) -> AsyncIterator[StreamChunk]:
        """
        Workflow 실행 시뮬레이션

        Args:
            workflow_id: Workflow ID
            message: 사용자 메시지
            conversation_id: 대화 ID

        Yields:
            Workflow 이벤트들 (start, step_start, step_complete, complete)

        Raises:
            WorkflowNotFoundError: workflow_id를 찾을 수 없을 때
        """
        if workflow_id not in self._workflows:
            raise WorkflowNotFoundError(f"Workflow not found: {workflow_id}")

        workflow = self._workflows[workflow_id]

        # workflow_start 이벤트
        yield StreamChunk.workflow_start(
            workflow_id=workflow.id,
            workflow_type=workflow.workflow_type,
            total_steps=len(workflow.steps),
        )

        # 각 step 실행
        for i, step in enumerate(workflow.steps, start=1):
            # step_start
            yield StreamChunk.workflow_step_start(
                workflow_id=workflow.id,
                step_number=i,
                agent_name=step.agent_endpoint_id,
            )

            # 텍스트 응답 (시뮬레이션)
            yield StreamChunk.text(f"Step {i} response from {step.agent_endpoint_id}")

            # step_complete
            yield StreamChunk.workflow_step_complete(
                workflow_id=workflow.id,
                step_number=i,
                agent_name=step.agent_endpoint_id,
            )

        # workflow_complete 이벤트
        yield StreamChunk.workflow_complete(
            workflow_id=workflow.id,
            status="success",
            total_steps=len(workflow.steps),
        )

    async def remove_workflow_agent(self, workflow_id: str) -> None:
        """
        Workflow Agent 제거

        Args:
            workflow_id: Workflow ID
        """
        self._workflows.pop(workflow_id, None)

    def reset(self) -> None:
        """상태 초기화"""
        self.initialized = False
        self.closed = False
        self.processed_messages.clear()
        self.added_a2a_agents.clear()
        self.removed_a2a_agents.clear()
        self._workflows.clear()
        self.should_fail = False
