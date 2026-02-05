"""AdkOrchestratorAdapter - ADK LlmAgent 기반 오케스트레이터

TDD Phase: GREEN - Runner 패턴 적용 + A2A Sub-Agent 통합
"""

import contextlib
import logging
from collections.abc import AsyncIterator

import litellm
from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.adapters.outbound.adk.dynamic_toolset import DynamicToolset
from src.adapters.outbound.adk.litellm_callbacks import AgentHubLogger
from src.domain.entities.stream_chunk import StreamChunk
from src.domain.entities.workflow import Workflow
from src.domain.exceptions import WorkflowNotFoundError
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
        self._workflow_agents: dict[str, SequentialAgent | ParallelAgent] = {}  # workflow agents
        self._workflows: dict[str, Workflow] = {}  # workflow metadata
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

    def _format_page_context(self, page_context: dict) -> str:
        """
        페이지 컨텍스트를 메시지 형식으로 변환 (Phase 5 Part C)

        Args:
            page_context: {url, title, selectedText, metaDescription, mainContent}

        Returns:
            포맷된 컨텍스트 문자열
        """
        MAX_CONTENT_LENGTH = 1000  # Prevent context overflow

        parts = ["[Page Context]"]
        parts.append(f"URL: {page_context.get('url', '')}")
        parts.append(f"Title: {page_context.get('title', '')}")

        if page_context.get("metaDescription"):
            parts.append(f"Description: {page_context['metaDescription']}")

        if page_context.get("selectedText"):
            parts.append(f"Selected Text: {page_context['selectedText']}")

        if page_context.get("mainContent"):
            content = page_context["mainContent"][:MAX_CONTENT_LENGTH]
            parts.append(f"Content: {content}")

        return "\n".join(parts)

    async def process_message(
        self,
        message: str,
        conversation_id: str,
        page_context: dict | None = None,  # Phase 5 Part C
    ) -> AsyncIterator[StreamChunk]:
        """
        메시지 처리 및 스트리밍 응답

        Runner.run_async()를 통해 ADK 런타임을 정상적으로 사용합니다.
        conversation_id를 session_id로 매핑하여 대화 컨텍스트를 유지합니다.

        Args:
            message: 사용자 메시지
            conversation_id: 대화 ID (ADK session_id로 사용)
            page_context: 페이지 컨텍스트 (Phase 5 Part C, optional)

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

        # 페이지 컨텍스트 주입 (Phase 5 Part C)
        if page_context:
            context_block = self._format_page_context(page_context)
            augmented_message = f"{context_block}\n\n{message}"
        else:
            augmented_message = message

        # 사용자 메시지를 Content로 변환
        user_content = types.Content(
            role="user",
            parts=[types.Part(text=augmented_message)],
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

    async def add_a2a_agent(self, endpoint_id: str, url: str) -> None:  # pragma: no cover
        """
        A2A 에이전트를 sub_agent로 추가 (Phase 5 유산, Phase 6에서 미사용)

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

    async def remove_a2a_agent(self, endpoint_id: str) -> None:  # pragma: no cover
        """
        A2A sub_agent 제거 (Phase 5 유산, Phase 6에서 미사용)

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

    async def create_workflow_agent(self, workflow: Workflow) -> None:  # pragma: no cover
        """
        Workflow Agent 생성 (Phase 5 Part E 유산, Phase 6에서 미사용)

        SequentialAgent 또는 ParallelAgent 생성

        Args:
            workflow: Workflow 엔티티

        Raises:
            ValueError: workflow_type이 "sequential" 또는 "parallel"이 아닌 경우
            RuntimeError: 참조하는 A2A agent가 등록되지 않은 경우
        """
        if not self._initialized:
            raise RuntimeError("Orchestrator must be initialized before creating workflow")

        # Workflow 타입 검증
        if workflow.workflow_type not in ("sequential", "parallel"):
            raise ValueError(f"Invalid workflow_type: {workflow.workflow_type}")

        # Step의 agent들이 모두 등록되어 있는지 확인
        for step in workflow.steps:
            if step.agent_endpoint_id not in self._a2a_urls:
                raise RuntimeError(
                    f"Agent not registered: {step.agent_endpoint_id}. "
                    f"Register the A2A agent first via add_a2a_agent()"
                )

        # Sub-agents를 새로 생성 (re-parenting 에러 방지)
        # ADK는 Agent를 한 번 parent에 할당하면 재할당 불가하므로,
        # workflow agent용 새 RemoteA2aAgent 인스턴스를 생성해야 함
        sub_agents = []
        for step in workflow.steps:
            endpoint_id = step.agent_endpoint_id
            url = self._a2a_urls[endpoint_id]
            agent_card_url = url if url.endswith("agent.json") else f"{url}/.well-known/agent.json"
            agent_name = f"a2a_{endpoint_id}".replace("-", "_")

            try:
                remote_agent = RemoteA2aAgent(
                    name=agent_name,
                    description=f"Remote A2A agent: {endpoint_id}",
                    agent_card=agent_card_url,
                )
                sub_agents.append(remote_agent)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to create RemoteA2aAgent for workflow: {endpoint_id}"
                ) from e

        # Workflow Agent 생성 (name을 유효한 Python identifier로 정규화)
        # ADK Agent name은 하이픈(-)을 허용하지 않으므로 언더스코어로 변경
        normalized_name = f"workflow_{workflow.id}".replace("-", "_")

        if workflow.workflow_type == "sequential":
            workflow_agent = SequentialAgent(
                name=normalized_name,
                sub_agents=sub_agents,
            )
        else:  # parallel
            workflow_agent = ParallelAgent(
                name=normalized_name,
                sub_agents=sub_agents,
            )

        # 저장
        self._workflow_agents[workflow.id] = workflow_agent
        self._workflows[workflow.id] = workflow

        logger.info(
            f"Workflow agent created: {workflow.id} ({workflow.workflow_type}, {len(workflow.steps)} steps)"
        )

    async def execute_workflow(  # pragma: no cover
        self,
        workflow_id: str,
        message: str,
        conversation_id: str,
    ) -> AsyncIterator[StreamChunk]:
        """
        Workflow Agent 실행 및 이벤트 스트리밍 (Phase 5 Part E 유산, Phase 6에서 미사용)

        Args:
            workflow_id: Workflow ID
            message: 사용자 메시지
            conversation_id: 대화 세션 ID

        Yields:
            StreamChunk 이벤트

        Raises:
            WorkflowNotFoundError: workflow_id를 찾을 수 없을 때
        """
        if workflow_id not in self._workflow_agents:
            raise WorkflowNotFoundError(f"Workflow not found: {workflow_id}")

        workflow = self._workflows[workflow_id]
        workflow_agent = self._workflow_agents[workflow_id]

        # workflow_start 이벤트
        yield StreamChunk.workflow_start(
            workflow_id=workflow.id,
            workflow_type=workflow.workflow_type,
            total_steps=len(workflow.steps),
        )

        # Runner로 Workflow Agent 실행
        runner = Runner(
            agent=workflow_agent,
            app_name=APP_NAME,
            session_service=self._session_service,
        )

        # 세션 생성/조회
        session_id = f"{conversation_id}_workflow_{workflow_id}"
        session = await self._session_service.get_session(
            app_name=APP_NAME,
            user_id=DEFAULT_USER_ID,
            session_id=session_id,
        )
        if session is None:
            session = await self._session_service.create_session(
                app_name=APP_NAME,
                user_id=DEFAULT_USER_ID,
                session_id=session_id,
            )

        # 사용자 메시지
        user_content = types.Content(
            role="user",
            parts=[types.Part(text=message)],
        )

        # Workflow 실행
        current_step = 0
        async for event in runner.run_async(
            user_id=DEFAULT_USER_ID,
            session_id=session_id,
            new_message=user_content,
        ):
            # Agent Transfer 감지 → workflow_step_start/complete
            if (
                hasattr(event, "actions")
                and event.actions
                and getattr(event.actions, "transfer_to_agent", None)
            ):
                # Previous step complete (if any)
                if current_step > 0:
                    yield StreamChunk.workflow_step_complete(
                        workflow_id=workflow.id,
                        step_number=current_step,
                        agent_name=workflow.steps[current_step - 1].agent_endpoint_id,
                    )

                # Next step start
                current_step += 1
                if current_step <= len(workflow.steps):
                    yield StreamChunk.workflow_step_start(
                        workflow_id=workflow.id,
                        step_number=current_step,
                        agent_name=workflow.steps[current_step - 1].agent_endpoint_id,
                    )

            # 텍스트 응답
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        yield StreamChunk.text(part.text)

        # Last step complete
        if current_step > 0:
            yield StreamChunk.workflow_step_complete(
                workflow_id=workflow.id,
                step_number=current_step,
                agent_name=workflow.steps[current_step - 1].agent_endpoint_id,
            )

        # workflow_complete 이벤트
        yield StreamChunk.workflow_complete(
            workflow_id=workflow.id,
            status="success",
            total_steps=len(workflow.steps),
        )

    async def remove_workflow_agent(self, workflow_id: str) -> None:  # pragma: no cover
        """
        Workflow Agent 제거 (Phase 5 Part E 유산, Phase 6에서 미사용)

        Args:
            workflow_id: Workflow ID
        """
        self._workflow_agents.pop(workflow_id, None)
        self._workflows.pop(workflow_id, None)
        logger.info(f"Workflow agent removed: {workflow_id}")

    async def _call_llm_with_retry(self, message: str, max_retries: int = 3) -> dict:
        """
        LLM API 호출 with Exponential Backoff Retry (Chaos 테스트용)

        Args:
            message: User message
            max_retries: Maximum retry attempts (default: 3)

        Returns:
            LiteLLM completion response dict

        Raises:
            LlmRateLimitError: Rate limit exceeded after max retries
        """
        import asyncio

        from litellm.exceptions import RateLimitError

        from src.domain.exceptions import LlmRateLimitError

        attempt = 0
        while attempt <= max_retries:
            try:
                # litellm.completion 호출 (비동기)
                response = await asyncio.to_thread(
                    litellm.completion,
                    model=self._model_name,
                    messages=[{"role": "user", "content": message}],
                )
                return response
            except RateLimitError as e:
                attempt += 1
                if attempt > max_retries:
                    # 최대 재시도 초과
                    raise LlmRateLimitError(
                        f"LLM rate limit exceeded after {max_retries} retries"
                    ) from e

                # Exponential backoff: 1s, 2s, 4s, ...
                delay = 2 ** (attempt - 1)
                logger.warning(
                    f"Rate limit hit, retrying in {delay}s (attempt {attempt}/{max_retries})"
                )
                await asyncio.sleep(delay)

        # 도달 불가 (while 조건이 보장)
        raise RuntimeError("Unexpected retry loop exit")

    async def close(self) -> None:
        """리소스 정리

        명시적으로 모든 리소스를 정리합니다:
        - DynamicToolset (MCP 연결)
        - InMemorySessionService (세션 데이터)
        - Runner (ADK 런타임)
        - Workflow/Sub-agent 참조
        """
        await self._dynamic_toolset.close()

        # InMemorySessionService 명시적 정리
        if self._session_service is not None:
            if hasattr(self._session_service, "close"):
                with contextlib.suppress(Exception):
                    await self._session_service.close()
            self._session_service = None

        self._agent = None
        self._runner = None
        self._sub_agents.clear()
        self._a2a_urls.clear()
        self._workflow_agents.clear()
        self._workflows.clear()
        self._initialized = False
        logger.info("AdkOrchestratorAdapter closed")
