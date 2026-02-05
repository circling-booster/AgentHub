# ADK Standards Guide

Google Agent Development Kit (ADK) 사용 가이드입니다. LiteLLM 기반 다중 LLM 지원 및 Agent 구현 방법을 다룹니다.

---

## ADK Overview

### Key Components

- **Agent**: LLM과 도구를 결합한 AI 에이전트
- **Runner**: Agent 실행 및 이벤트 스트리밍 관리
- **Toolset**: 동적 도구 로딩 (MCP 통합)
- **SessionService**: 대화 세션 관리

### AgentHub ADK Integration

```
User Message → ADK Runner → LlmAgent (LiteLLM) → MCP Tools / A2A SubAgents
                  ↓
            Event Streaming → StreamChunk → SSE → Extension
```

---

## Agent Creation

### Basic Agent

```python
from google.adk import Agent, LlmAgent

def create_agent(
    model: str,
    instruction: str,
    tools: list | None = None,
) -> Agent:
    """ADK Agent 생성."""
    return LlmAgent(
        name="AgentHub Assistant",
        model=model,
        instruction=instruction,
        tools=tools or [],
    )
```

### Agent with Sub-Agents

```python
from google.adk import Agent, LlmAgent

def create_orchestrator_agent(
    model: str,
    sub_agents: list[Agent],
) -> Agent:
    """Sub-Agent를 포함한 오케스트레이터 Agent."""
    return LlmAgent(
        name="Orchestrator",
        model=model,
        instruction="""
        You are an orchestrator that delegates tasks to specialized agents.
        Available agents:
        - Echo Agent: Echoes back user input
        - Math Agent: Performs mathematical calculations
        """,
        sub_agents=sub_agents,
    )
```

### Agent with Dynamic Instruction

```python
async def create_dynamic_agent(
    model: str,
    storage: StoragePort,
) -> Agent:
    """등록된 도구/에이전트 정보를 instruction에 포함."""
    # 등록된 MCP 도구 목록
    mcp_tools = await get_registered_mcp_tools(storage)

    # 등록된 A2A 에이전트 목록
    a2a_agents = await get_registered_a2a_agents(storage)

    instruction = f"""
    You are AgentHub Assistant.

    Available MCP Tools:
    {format_tools(mcp_tools)}

    Available A2A Agents:
    {format_agents(a2a_agents)}

    Use these tools and agents to help the user.
    """

    return LlmAgent(
        name="AgentHub Assistant",
        model=model,
        instruction=instruction,
    )
```

---

## LiteLLM Configuration

### Model Parameter Format

LiteLLM은 `provider/model` 형식의 model 파라미터를 사용합니다.

```python
# OpenAI
model = "openai/gpt-4o-mini"
model = "openai/gpt-4o"

# Anthropic
model = "anthropic/claude-3-5-sonnet-20241022"
model = "anthropic/claude-3-haiku-20240307"

# Google
model = "gemini/gemini-2.0-flash"
model = "gemini/gemini-1.5-pro"
```

### Environment Variables

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...
```

### Custom LiteLLM Settings

```python
import litellm

# 디버그 로깅
litellm.set_verbose = True

# 타임아웃 설정
litellm.request_timeout = 60

# 재시도 설정
litellm.num_retries = 3
```

### Model Fallback

```python
from litellm import Router

router = Router(
    model_list=[
        {
            "model_name": "primary",
            "litellm_params": {
                "model": "openai/gpt-4o-mini",
                "api_key": os.getenv("OPENAI_API_KEY"),
            },
        },
        {
            "model_name": "fallback",
            "litellm_params": {
                "model": "anthropic/claude-3-haiku-20240307",
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
            },
        },
    ],
    fallbacks=[{"primary": ["fallback"]}],
)
```

---

## DynamicToolset Usage

### Creating DynamicToolset

```python
from google.adk.toolsets import DynamicToolset

class McpToolset(DynamicToolset):
    """MCP 기반 동적 도구셋."""

    def __init__(self, endpoints: list[str]) -> None:
        super().__init__()
        self._endpoints = endpoints

    async def get_tools(self) -> list:
        """MCP 서버에서 도구 로드."""
        tools = []
        for endpoint in self._endpoints:
            async with create_mcp_client(endpoint) as session:
                mcp_tools = await session.list_tools()
                tools.extend(self._convert_to_adk_tools(mcp_tools))
        return tools
```

### Registering Toolset with Agent

```python
from google.adk import LlmAgent

async def create_agent_with_toolset(
    model: str,
    mcp_endpoints: list[str],
) -> Agent:
    """DynamicToolset을 사용하는 Agent."""
    toolset = McpToolset(endpoints=mcp_endpoints)

    return LlmAgent(
        name="AgentHub Assistant",
        model=model,
        instruction="You are a helpful assistant.",
        toolsets=[toolset],
    )
```

### Tool Limit (MAX_ACTIVE_TOOLS)

대규모 도구 지원을 위한 Defer Loading 패턴:

```python
MAX_ACTIVE_TOOLS = 100

class DeferredToolset(DynamicToolset):
    """지연 로딩 도구셋."""

    def __init__(self, all_tools: list) -> None:
        self._all_tools = all_tools
        self._active_tools: list = []

    async def get_tools(self) -> list:
        """활성화된 도구만 반환."""
        return self._active_tools[:MAX_ACTIVE_TOOLS]

    async def activate_tool(self, tool_name: str) -> None:
        """도구 활성화."""
        tool = next((t for t in self._all_tools if t.name == tool_name), None)
        if tool and tool not in self._active_tools:
            self._active_tools.append(tool)
```

---

## Event Handling

### ADK Event Types

```python
from google.adk.events import (
    TextDelta,
    ToolCallStart,
    ToolCallEnd,
    AgentTransfer,
    RunComplete,
)

async def handle_adk_events(
    runner: Runner,
    session_id: str,
    message: str,
) -> AsyncIterator[StreamChunk]:
    """ADK 이벤트를 StreamChunk로 변환."""
    async for event in runner.run_async(session_id, message):
        match event:
            case TextDelta(content=content):
                yield StreamChunk(type="text", content=content)

            case ToolCallStart(tool_name=name, arguments=args):
                yield StreamChunk(
                    type="tool_call",
                    tool_name=name,
                    arguments=args,
                )

            case ToolCallEnd(tool_name=name, result=result):
                yield StreamChunk(
                    type="tool_result",
                    tool_name=name,
                    result=result,
                )

            case AgentTransfer(from_agent=from_a, to_agent=to_a):
                yield StreamChunk(
                    type="agent_transfer",
                    from_agent=from_a,
                    to_agent=to_a,
                )

            case RunComplete():
                yield StreamChunk(type="done")
```

### Custom Event Handler

```python
class EventLogger:
    """ADK 이벤트 로거."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    async def log_events(
        self,
        events: AsyncIterator,
    ) -> AsyncIterator:
        """이벤트 로깅 후 패스스루."""
        async for event in events:
            self._logger.info(f"ADK Event: {type(event).__name__}")
            yield event
```

---

## Runner Usage

### Basic Runner

```python
from google.adk import Runner, InMemorySessionService

def create_runner(agent: Agent) -> Runner:
    """ADK Runner 생성."""
    session_service = InMemorySessionService()

    return Runner(
        agent=agent,
        session_service=session_service,
    )
```

### Runner with Custom Session

```python
from google.adk import Runner

class SqliteSessionService:
    """SQLite 기반 세션 서비스."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    async def get_session(self, session_id: str) -> Session | None:
        """세션 조회."""
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "SELECT data FROM sessions WHERE id = ?",
                (session_id,),
            )
            row = await cursor.fetchone()
            if row:
                return Session.from_dict(json.loads(row[0]))
            return None

    async def save_session(self, session: Session) -> None:
        """세션 저장."""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO sessions (id, data) VALUES (?, ?)",
                (session.id, json.dumps(session.to_dict())),
            )
            await db.commit()

def create_persistent_runner(
    agent: Agent,
    db_path: str,
) -> Runner:
    """영구 세션 저장을 사용하는 Runner."""
    session_service = SqliteSessionService(db_path)

    return Runner(
        agent=agent,
        session_service=session_service,
    )
```

### Running Agent

```python
async def run_agent(
    runner: Runner,
    conversation_id: str,
    user_message: str,
) -> AsyncIterator[StreamChunk]:
    """Agent 실행 및 응답 스트리밍."""
    async for event in runner.run_async(
        session_id=conversation_id,
        message=user_message,
    ):
        chunk = convert_event_to_chunk(event)
        if chunk:
            yield chunk
```

---

## LLM Call Logging

### Token Usage Tracking

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class LlmCallLog:
    """LLM 호출 로그."""

    id: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    timestamp: datetime

class LlmCallLogger:
    """LLM 호출 로깅."""

    def __init__(self, storage: StoragePort) -> None:
        self._storage = storage

    async def log_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
    ) -> None:
        """LLM 호출 기록."""
        log = LlmCallLog(
            id=generate_id(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            timestamp=datetime.now(),
        )
        await self._storage.save_llm_call_log(log)
```

### LiteLLM Callbacks

```python
import litellm

def setup_logging_callbacks() -> None:
    """LiteLLM 로깅 콜백 설정."""

    async def log_success(kwargs, response, start_time, end_time):
        """성공 콜백."""
        usage = response.get("usage", {})
        await llm_logger.log_call(
            model=kwargs.get("model"),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            latency_ms=int((end_time - start_time) * 1000),
        )

    litellm.success_callback = [log_success]
```

---

*Last Updated: 2026-02-05*
