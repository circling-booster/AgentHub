"""Fake Orchestrator Adapter - 테스트용 오케스트레이터

OrchestratorPort의 테스트용 구현입니다.
"""

from collections.abc import AsyncIterator

from src.domain.ports.outbound.orchestrator_port import OrchestratorPort


class FakeOrchestrator(OrchestratorPort):
    """
    테스트용 오케스트레이터

    테스트용 OrchestratorPort 구현입니다.
    설정된 응답을 스트리밍으로 반환합니다.
    """

    def __init__(
        self,
        responses: list[str] | None = None,
        should_fail: bool = False,
        error_message: str = "Orchestrator error",
    ) -> None:
        """
        Args:
            responses: 반환할 응답 청크 목록
            should_fail: True면 에러 발생
            error_message: 에러 발생 시 메시지
        """
        self.responses = responses or ["Hello! ", "How can I help you?"]
        self.should_fail = should_fail
        self.error_message = error_message
        self.initialized = False
        self.closed = False
        self.processed_messages: list[tuple[str, str]] = []  # (message, conv_id)
        self.added_a2a_agents: list[tuple[str, str]] = []  # (endpoint_id, url)
        self.removed_a2a_agents: list[str] = []  # endpoint_id

    async def initialize(self) -> None:
        """초기화"""
        self.initialized = True

    async def process_message(
        self,
        message: str,
        conversation_id: str,
    ) -> AsyncIterator[str]:
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

    def set_responses(self, responses: list[str]) -> None:
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

    def reset(self) -> None:
        """상태 초기화"""
        self.initialized = False
        self.closed = False
        self.processed_messages.clear()
        self.added_a2a_agents.clear()
        self.removed_a2a_agents.clear()
        self.should_fail = False
