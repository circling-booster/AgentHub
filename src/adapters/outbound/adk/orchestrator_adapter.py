"""AdkOrchestratorAdapter - ADK LlmAgent 기반 오케스트레이터

TDD Phase: GREEN - Runner 패턴 적용 + A2A Sub-Agent 통합
"""

import logging
from collections.abc import AsyncIterator

import litellm
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset
from src.adapters.outbound.adk.litellm_callbacks import AgentHubLogger
from src.domain.entities.stream_chunk import StreamChunk
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
        enable_llm_logging: bool = True,
    ):
        """
        Args:
            model: LiteLLM 모델 문자열 (예: "openai/gpt-4o-mini")
            dynamic_toolset: DynamicToolset 인스턴스
            instruction: 시스템 프롬프트
            enable_llm_logging: LLM 호출 로깅 활성화 여부 (Step 5: Part B)
        """
        self._model_name = model
        self._dynamic_toolset = dynamic_toolset
        self._instruction = instruction
        self._enable_llm_logging = enable_llm_logging
        self._agent: LlmAgent | None = None
        self._runner: Runner | None = None
        self._session_service: InMemorySessionService | None = None
        self._sub_agents: dict[str, RemoteA2aAgent] = {}  # A2A sub-agents
        self._a2a_urls: dict[str, str] = {}  # endpoint_id -> url (for rebuilding)
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

        # Step 5: LiteLLM callbacks 등록 (설정에 따라 활성화)
        if self._enable_llm_logging:
            litellm.callbacks = [AgentHubLogger()]
            logger.info("LiteLLM callbacks registered: AgentHubLogger")

        # 도구 로딩 완료 대기 (비동기)
        await self._dynamic_toolset.get_tools()

        # SessionService 생성 (Agent 재구성 시 유지)
        self._session_service = InMemorySessionService()

        # Agent + Runner 생성
        await self._rebuild_agent()

        self._initialized = True
        logger.info(f"AdkOrchestratorAdapter initialized with model: {self._model_name}")

    async def _rebuild_agent(self) -> None:
        """
        Agent + Runner 재구성

        A2A sub-agent 추가/제거 시 호출됩니다.
        SessionService는 유지하여 대화 컨텍스트를 보존합니다.

        동적 시스템 프롬프트:
        - 등록된 MCP 도구 목록 포함
        - 등록된 A2A 에이전트 정보 포함

        Bug Fix (Phase 5 Step 3):
        - RemoteA2aAgent 인스턴스를 매번 새로 생성하여 re-parenting 에러 방지
        - ADK는 Agent를 한 번 parent에 할당하면 재할당 불가
        """
        # RemoteA2aAgent 인스턴스 재생성 (re-parenting 에러 방지)
        new_sub_agents: dict[str, RemoteA2aAgent] = {}
        for endpoint_id, url in self._a2a_urls.items():
            # Agent Card URL 추출
            agent_card_url = url if url.endswith("agent.json") else f"{url}/.well-known/agent.json"

            # Agent name 정규화 (하이픈을 언더스코어로 변경)
            agent_name = f"a2a_{endpoint_id}".replace("-", "_")

            try:
                new_sub_agents[endpoint_id] = RemoteA2aAgent(
                    name=agent_name,
                    description=f"Remote A2A agent: {endpoint_id}",
                    agent_card=agent_card_url,
                )
            except Exception as e:
                logger.warning(f"Failed to recreate RemoteA2aAgent for {endpoint_id}: {e}")
                continue

        # sub_agents 갱신
        self._sub_agents = new_sub_agents

        # 동적 instruction 생성
        dynamic_instruction = self._build_dynamic_instruction()

        # Agent 생성 (sub_agents 포함)
        self._agent = LlmAgent(
            model=LiteLlm(model=self._model_name),
            name="agenthub_agent",
            instruction=dynamic_instruction,
            tools=[self._dynamic_toolset],
            sub_agents=list(self._sub_agents.values()),  # A2A sub-agents
        )

        # 도구 및 에이전트 수 계산
        mcp_info = self._dynamic_toolset.get_registered_info()
        total_tools = sum(len(info["tools"]) for info in mcp_info.values())

        # Runner 재생성 (기존 session_service 유지)
        self._runner = Runner(
            agent=self._agent,
            app_name=APP_NAME,
            session_service=self._session_service,
        )

        logger.info(
            f"Agent rebuilt: {total_tools} MCP tools, {len(self._sub_agents)} A2A sub-agents",
            extra={
                "mcp_endpoints": len(mcp_info),
                "total_mcp_tools": total_tools,
                "a2a_agents": len(self._sub_agents),
            },
        )

    def _build_dynamic_instruction(self) -> str:
        """
        컨텍스트 인식 동적 시스템 프롬프트 생성

        Returns:
            등록된 도구/에이전트 정보를 포함한 instruction
        """
        # 기본 instruction
        instruction_parts = [
            "You are AgentHub, an intelligent assistant with access to external tools and agents.",
            "",
        ]

        # MCP 도구 섹션
        mcp_info = self._dynamic_toolset.get_registered_info()
        if mcp_info:
            instruction_parts.append("## Available MCP Tools:")
            for _endpoint_id, info in mcp_info.items():
                server_name = info["name"]
                tools = info["tools"]
                if tools:
                    tools_str = ", ".join(tools)
                    instruction_parts.append(f'- Server "{server_name}": {tools_str}')
                else:
                    instruction_parts.append(f'- Server "{server_name}": (no tools available)')
            instruction_parts.append("")

        # A2A 에이전트 섹션
        if self._sub_agents:
            instruction_parts.append("## Available A2A Agents:")
            for _endpoint_id, agent in self._sub_agents.items():
                agent_name = agent.name
                agent_desc = agent.description or "Remote A2A agent"
                instruction_parts.append(f'- Agent "{agent_name}": {agent_desc}')
            instruction_parts.append("")

        # 사용 가이드라인
        instruction_parts.extend(
            [
                "## Usage Guidelines:",
                "- Use MCP tools for specific actions (data queries, file operations, API calls)",
                "- Delegate to A2A agents when the task matches their specialization",
                "- You can use multiple tools in sequence to complete complex tasks",
                "- Always report which tools/agents you used in your response",
            ]
        )

        return "\n".join(instruction_parts)

    async def process_message(
        self,
        message: str,
        conversation_id: str,
    ) -> AsyncIterator[StreamChunk]:
        """
        메시지 처리 및 스트리밍 응답

        Runner.run_async()를 통해 ADK 런타임을 정상적으로 사용합니다.
        conversation_id를 session_id로 매핑하여 대화 컨텍스트를 유지합니다.

        Args:
            message: 사용자 메시지
            conversation_id: 대화 ID (ADK session_id로 사용)

        Yields:
            StreamChunk 이벤트 (text, tool_call, tool_result, agent_transfer)

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
            # Tool Call 이벤트
            if event.get_function_calls():
                for fc in event.get_function_calls():
                    yield StreamChunk.tool_call(fc.name, dict(fc.args or {}))

            # Tool Result 이벤트
            if event.get_function_responses():
                for fr in event.get_function_responses():
                    yield StreamChunk.tool_result(fr.name, str(fr.response))

            # Agent Transfer 이벤트
            if (
                hasattr(event, "actions")
                and event.actions
                and getattr(event.actions, "transfer_to_agent", None)
            ):
                yield StreamChunk.agent_transfer(event.actions.transfer_to_agent)

            # 최종 응답 텍스트
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        yield StreamChunk.text(part.text)

    async def add_a2a_agent(self, endpoint_id: str, url: str) -> None:
        """
        A2A 에이전트를 sub_agent로 추가

        Args:
            endpoint_id: Endpoint ID (sub_agents dict의 key)
            url: A2A 에이전트 URL (Agent Card URL로 변환됨)

        Raises:
            RuntimeError: Orchestrator가 초기화되지 않음
        """
        # Agent Card URL 추출 (A2A 표준: {url}/.well-known/agent.json)
        agent_card_url = url if url.endswith("agent.json") else f"{url}/.well-known/agent.json"
        if not self._initialized:
            raise RuntimeError("Orchestrator must be initialized before adding A2A agents")

        # Agent name 정규화 (하이픈을 언더스코어로 변경)
        # RemoteA2aAgent는 유효한 Python identifier를 요구함
        agent_name = f"a2a_{endpoint_id}".replace("-", "_")

        # RemoteA2aAgent 생성
        remote_agent = RemoteA2aAgent(
            name=agent_name,
            description=f"Remote A2A agent: {endpoint_id}",
            agent_card=agent_card_url,
        )

        # sub_agents에 추가
        self._sub_agents[endpoint_id] = remote_agent

        # URL 저장 (재구성 시 사용)
        self._a2a_urls[endpoint_id] = url

        # Agent 재구성 (sub_agents 업데이트)
        await self._rebuild_agent()

        logger.info(f"A2A agent added: {endpoint_id} ({agent_card_url})")

    async def remove_a2a_agent(self, endpoint_id: str) -> None:
        """
        A2A sub_agent 제거

        Args:
            endpoint_id: Endpoint ID

        Raises:
            RuntimeError: Orchestrator가 초기화되지 않음
        """
        if not self._initialized:
            raise RuntimeError("Orchestrator must be initialized before removing A2A agents")

        # sub_agents에서 제거
        if endpoint_id not in self._sub_agents:
            return

        del self._sub_agents[endpoint_id]
        self._a2a_urls.pop(endpoint_id, None)  # URL도 제거

        # Agent 재구성 (sub_agents 업데이트)
        await self._rebuild_agent()

        logger.info(f"A2A agent removed: {endpoint_id}")

    async def close(self) -> None:
        """리소스 정리"""
        await self._dynamic_toolset.close()
        self._agent = None
        self._runner = None
        self._session_service = None
        self._sub_agents.clear()
        self._initialized = False
        logger.info("AdkOrchestratorAdapter closed")
