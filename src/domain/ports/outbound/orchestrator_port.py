"""OrchestratorPort - LLM 오케스트레이터 인터페이스

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from src.domain.entities.stream_chunk import StreamChunk
from src.domain.entities.workflow import Workflow


class OrchestratorPort(ABC):
    """
    LLM 오케스트레이터 포트

    ADK LlmAgent와 같은 LLM 오케스트레이터를 추상화합니다.
    도메인 서비스는 이 인터페이스를 통해 LLM과 상호작용합니다.

    구현체 예시:
    - AdkOrchestratorAdapter (Google ADK LlmAgent)
    - FakeOrchestrator (테스트용)
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        오케스트레이터 초기화

        비동기 초기화가 필요한 경우 이 메서드에서 수행합니다.
        FastAPI startup 이벤트에서 호출됩니다.
        """
        pass

    @abstractmethod
    async def process_message(
        self,
        message: str,
        conversation_id: str,
    ) -> AsyncIterator[StreamChunk]:
        """
        메시지 처리 및 스트리밍 응답 반환

        사용자 메시지를 처리하고 LLM 응답을 스트리밍합니다.
        Tool Call Loop는 구현체 내부에서 자동 처리됩니다.

        Args:
            message: 사용자 메시지
            conversation_id: 대화 세션 ID

        Yields:
            StreamChunk 이벤트 (text, tool_call, tool_result, agent_transfer, error, done)

        Raises:
            LlmRateLimitError: API Rate Limit 초과 시
            LlmAuthenticationError: API 인증 실패 시
        """
        pass

    @abstractmethod
    async def add_a2a_agent(self, endpoint_id: str, url: str) -> None:
        """
        A2A 에이전트를 LLM sub_agents에 추가

        Args:
            endpoint_id: 엔드포인트 ID
            url: A2A 에이전트 URL
        """
        pass

    @abstractmethod
    async def remove_a2a_agent(self, endpoint_id: str) -> None:
        """
        A2A 에이전트를 LLM sub_agents에서 제거

        Args:
            endpoint_id: 엔드포인트 ID
        """
        pass

    @abstractmethod
    async def create_workflow_agent(self, workflow: Workflow) -> None:
        """
        Workflow Agent 생성 (SequentialAgent 또는 ParallelAgent)

        Args:
            workflow: Workflow 엔티티 (id, type, steps)

        Raises:
            ValueError: workflow_type이 "sequential" 또는 "parallel"이 아닌 경우
        """
        pass

    @abstractmethod
    async def execute_workflow(
        self,
        workflow_id: str,
        message: str,
        conversation_id: str,
    ) -> AsyncIterator[StreamChunk]:
        """
        Workflow Agent 실행 및 이벤트 스트리밍

        Args:
            workflow_id: Workflow ID
            message: 사용자 메시지
            conversation_id: 대화 세션 ID

        Yields:
            StreamChunk 이벤트 (workflow_start, workflow_step_start,
            workflow_step_complete, workflow_complete, text, done)

        Raises:
            WorkflowNotFoundError: workflow_id에 해당하는 workflow가 없을 때
        """
        pass

    @abstractmethod
    async def remove_workflow_agent(self, workflow_id: str) -> None:
        """
        Workflow Agent 제거

        Args:
            workflow_id: Workflow ID
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        리소스 정리

        오케스트레이터가 사용하는 리소스(연결 등)를 정리합니다.
        FastAPI shutdown 이벤트에서 호출됩니다.
        """
        pass
