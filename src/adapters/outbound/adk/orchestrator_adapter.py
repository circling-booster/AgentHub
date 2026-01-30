"""AdkOrchestratorAdapter - ADK LlmAgent 기반 오케스트레이터

TDD Phase: GREEN - Runner 패턴 적용
"""

import logging
from collections.abc import AsyncIterator

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset
from src.domain.ports.outbound.orchestrator_port import OrchestratorPort

logger = logging.getLogger(__name__)

APP_NAME = "agenthub"
DEFAULT_USER_ID = "default_user"


class AdkOrchestratorAdapter(OrchestratorPort):
    """
    ADK LlmAgent 기반 오케스트레이터 어댑터

    Async Factory Pattern:
    - 생성자에서는 비동기 초기화를 수행하지 않음
    - initialize() 메서드로 명시적 비동기 초기화
    - FastAPI startup 이벤트에서 호출

    특징:
    - Runner + InMemorySessionService로 ADK 런타임 정상 사용
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
        self._runner: Runner | None = None
        self._session_service: InMemorySessionService | None = None
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
        await self._dynamic_toolset.get_tools()

        # Agent 생성
        self._agent = LlmAgent(
            model=LiteLlm(model=self._model_name),
            name="agenthub_agent",
            instruction=self._instruction,
            tools=[self._dynamic_toolset],
        )

        # Runner + SessionService 생성
        self._session_service = InMemorySessionService()
        self._runner = Runner(
            agent=self._agent,
            app_name=APP_NAME,
            session_service=self._session_service,
        )

        self._initialized = True
        logger.info(f"AdkOrchestratorAdapter initialized with model: {self._model_name}")

    async def process_message(
        self,
        message: str,
        conversation_id: str,
    ) -> AsyncIterator[str]:
        """
        메시지 처리 및 스트리밍 응답

        Runner.run_async()를 통해 ADK 런타임을 정상적으로 사용합니다.
        conversation_id를 session_id로 매핑하여 대화 컨텍스트를 유지합니다.

        Args:
            message: 사용자 메시지
            conversation_id: 대화 ID (ADK session_id로 사용)

        Yields:
            텍스트 chunk (str)

        Raises:
            RuntimeError: Orchestrator가 초기화되지 않음
        """
        # 초기화 확인 (Lazy initialization 폴백)
        if not self._initialized:
            logger.warning("Orchestrator not initialized, performing lazy initialization")
            await self.initialize()

        runner = self._runner
        session_service = self._session_service
        if runner is None or session_service is None:
            raise RuntimeError("Orchestrator not initialized")

        # ADK 세션 생성/조회
        session_id = conversation_id
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=DEFAULT_USER_ID,
            session_id=session_id,
        )
        if session is None:
            session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=DEFAULT_USER_ID,
                session_id=session_id,
            )

        # 사용자 메시지를 Content로 변환
        user_content = types.Content(
            role="user",
            parts=[types.Part(text=message)],
        )

        # Runner를 통해 Agent 실행
        async for event in runner.run_async(
            user_id=DEFAULT_USER_ID,
            session_id=session_id,
            new_message=user_content,
        ):
            # 최종 응답 이벤트에서 텍스트 추출
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        yield part.text

    async def close(self) -> None:
        """리소스 정리"""
        await self._dynamic_toolset.close()
        self._agent = None
        self._runner = None
        self._session_service = None
        self._initialized = False
        logger.info("AdkOrchestratorAdapter closed")
