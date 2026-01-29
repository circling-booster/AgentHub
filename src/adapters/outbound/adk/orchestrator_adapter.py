"""AdkOrchestratorAdapter - ADK LlmAgent 기반 오케스트레이터

TDD Phase: GREEN - 최소 구현
"""

import logging
from collections.abc import AsyncIterator

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset
from src.domain.ports.outbound.orchestrator_port import OrchestratorPort

logger = logging.getLogger(__name__)


class AdkOrchestratorAdapter(OrchestratorPort):
    """
    ADK LlmAgent 기반 오케스트레이터 어댑터

    Async Factory Pattern:
    - 생성자에서는 비동기 초기화를 수행하지 않음
    - initialize() 메서드로 명시적 비동기 초기화
    - FastAPI startup 이벤트에서 호출

    특징:
    - LlmAgent + DynamicToolset 통합
    - 텍스트 스트리밍 응답 (AsyncIterator[str])
    - Lazy initialization 지원 (process_message에서 자동 초기화)
    """

    def __init__(
        self,
        model: str,
        dynamic_toolset: DynamicToolset,
        instruction: str = "You are a helpful assistant with access to various tools.",
    ):
        """
        Args:
            model: LiteLLM 모델 문자열 (예: "openai/gpt-4o-mini")
            dynamic_toolset: DynamicToolset 인스턴스
            instruction: 시스템 프롬프트
        """
        self._model_name = model
        self._dynamic_toolset = dynamic_toolset
        self._instruction = instruction
        self._agent: LlmAgent | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """
        명시적 비동기 초기화

        FastAPI lifespan에서 호출:

        ```python
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            orchestrator = container.orchestrator_adapter()
            await orchestrator.initialize()
            yield
            await orchestrator.close()
        ```
        """
        if self._initialized:
            return

        # 도구 로딩 완료 대기 (비동기)
        # DynamicToolset이 MCP 서버 연결 상태 확인
        await self._dynamic_toolset.get_tools()

        # Agent 생성
        self._agent = LlmAgent(
            model=LiteLlm(model=self._model_name),
            name="agenthub_agent",  # 하이픈 불가, underscore만 가능
            instruction=self._instruction,
            tools=[self._dynamic_toolset],
        )

        self._initialized = True
        logger.info(f"AdkOrchestratorAdapter initialized with model: {self._model_name}")

    async def process_message(
        self,
        message: str,
        _conversation_id: str,
    ) -> AsyncIterator[str]:
        """
        메시지 처리 및 스트리밍 응답

        Tool Call Loop는 ADK Agent 내부에서 자동 처리됩니다.

        Args:
            message: 사용자 메시지
            _conversation_id: 대화 ID (현재 미사용, 향후 세션 관리용)

        Yields:
            텍스트 chunk (str)

        Raises:
            RuntimeError: Orchestrator가 초기화되지 않음
        """
        # 초기화 확인 (Lazy initialization 폴백)
        if not self._initialized:
            logger.warning("Orchestrator not initialized, performing lazy initialization")
            await self.initialize()

        agent = self._agent
        if agent is None:
            raise RuntimeError("Orchestrator not initialized")

        # ADK Agent 실행 및 스트리밍
        # run_async()는 이벤트 스트림을 반환
        async for event in agent.run_async(message):
            # 이벤트에서 텍스트 추출
            # ADK 이벤트 구조에 따라 다를 수 있음
            if hasattr(event, "text") and event.text:
                yield event.text
            elif hasattr(event, "content") and isinstance(event.content, str):
                # 일부 ADK 버전은 content 속성 사용
                yield event.content

    async def close(self) -> None:
        """리소스 정리"""
        await self._dynamic_toolset.close()
        self._agent = None
        self._initialized = False
        logger.info("AdkOrchestratorAdapter closed")
