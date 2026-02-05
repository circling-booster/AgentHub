# A2A Standards Guide

Agent-to-Agent (A2A) 프로토콜 구현 가이드입니다. 에이전트 간 통신 표준을 기반으로 클라이언트 및 서버 구현 방법을 다룹니다.

---

## A2A Protocol Overview

### Core Concepts

- **Agent Card**: 에이전트 메타데이터 (이름, 설명, capabilities)
- **Task**: 에이전트에게 요청하는 작업 단위
- **Message**: 에이전트 간 통신 메시지

### AgentHub의 A2A 역할

AgentHub는 A2A Client와 A2A Server 역할을 모두 수행합니다.

```
[외부 A2A 에이전트] ←→ [AgentHub A2A Server]
                              ↓
                      [AgentHub A2A Client] → [다른 A2A 에이전트]
```

---

## A2A Client Implementation

### Agent Card Discovery

```python
from a2a.client import A2AClient
from a2a.types import AgentCard

async def discover_agent(agent_url: str) -> AgentCard:
    """A2A 에이전트 Agent Card 조회."""
    client = A2AClient(base_url=agent_url)

    # /.well-known/agent.json 엔드포인트 호출
    card = await client.get_agent_card()

    return AgentCard(
        name=card.name,
        description=card.description,
        url=agent_url,
        capabilities=card.capabilities,
        skills=card.skills,
    )
```

### Task Submission

```python
async def submit_task(
    client: A2AClient,
    message: str,
    context: dict | None = None,
) -> Task:
    """A2A 에이전트에게 작업 요청."""
    task = await client.send_task(
        message=Message(
            role="user",
            content=message,
        ),
        context=context,
    )

    return task
```

### Streaming Response

```python
async def stream_task_response(
    client: A2AClient,
    task_id: str,
) -> AsyncIterator[StreamChunk]:
    """A2A 작업 응답 스트리밍."""
    async for event in client.stream_task(task_id):
        match event.type:
            case "text":
                yield StreamChunk(
                    type="text",
                    content=event.content,
                )
            case "artifact":
                yield StreamChunk(
                    type="artifact",
                    artifact_id=event.artifact_id,
                    data=event.data,
                )
            case "done":
                yield StreamChunk(type="done")
                break
```

---

## A2A Server Implementation

### Agent Card Endpoint

```python
from fastapi import APIRouter
from a2a.types import AgentCard

router = APIRouter()

@router.get("/.well-known/agent.json")
async def get_agent_card() -> AgentCard:
    """Agent Card 반환."""
    return AgentCard(
        name="AgentHub",
        description="MCP + A2A 통합 에이전트 허브",
        url="http://localhost:8000",
        version="1.0.0",
        capabilities=AgentCapabilities(
            streaming=True,
            push_notifications=False,
        ),
        skills=[
            Skill(
                name="mcp_tool_execution",
                description="등록된 MCP 서버의 도구 실행",
            ),
            Skill(
                name="a2a_delegation",
                description="다른 A2A 에이전트에게 작업 위임",
            ),
        ],
    )
```

### Task Handler

```python
@router.post("/tasks")
async def create_task(
    request: CreateTaskRequest,
    orchestrator: OrchestratorService = Depends(get_orchestrator),
) -> Task:
    """A2A 작업 생성."""
    task_id = generate_task_id()

    # 백그라운드에서 작업 처리
    background_tasks.add_task(
        process_task,
        task_id=task_id,
        message=request.message,
        orchestrator=orchestrator,
    )

    return Task(
        id=task_id,
        status=TaskStatus.PENDING,
    )

@router.get("/tasks/{task_id}/stream")
async def stream_task(task_id: str) -> StreamingResponse:
    """작업 결과 스트리밍."""
    async def generate():
        async for chunk in get_task_stream(task_id):
            yield f"data: {chunk.model_dump_json()}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )
```

---

## Agent Card Definition

### Required Fields

```python
@dataclass
class AgentCard:
    """A2A Agent Card."""

    # 필수 필드
    name: str                    # 에이전트 이름
    description: str             # 에이전트 설명
    url: str                     # 에이전트 URL
    version: str                 # 프로토콜 버전

    # 선택 필드
    capabilities: AgentCapabilities | None = None
    skills: list[Skill] = field(default_factory=list)
    authentication: AuthInfo | None = None
```

### Capabilities

```python
@dataclass
class AgentCapabilities:
    """에이전트 기능."""

    streaming: bool = True           # 스트리밍 응답 지원
    push_notifications: bool = False # 푸시 알림 지원
    state_management: bool = True    # 상태 관리 지원
```

### Skills

```python
@dataclass
class Skill:
    """에이전트 스킬."""

    name: str                        # 스킬 이름
    description: str                 # 스킬 설명
    input_schema: dict | None = None # 입력 스키마
    output_schema: dict | None = None # 출력 스키마
```

---

## Integration with ADK

### A2A as Sub-Agent

ADK에서 A2A 에이전트를 sub_agents로 사용할 수 있습니다.

```python
from google.adk import Agent

class A2ASubAgent:
    """A2A 에이전트를 ADK sub-agent로 래핑."""

    def __init__(self, a2a_client: A2AClient, agent_card: AgentCard) -> None:
        self._client = a2a_client
        self._card = agent_card

    @property
    def name(self) -> str:
        return self._card.name

    @property
    def description(self) -> str:
        return self._card.description

    async def run(self, message: str) -> AsyncIterator[str]:
        """A2A 에이전트 실행."""
        task = await self._client.send_task(
            message=Message(role="user", content=message),
        )

        async for event in self._client.stream_task(task.id):
            if event.type == "text":
                yield event.content
```

### Dynamic Sub-Agent Registration

```python
async def register_a2a_agents(
    storage: StoragePort,
) -> list[A2ASubAgent]:
    """등록된 A2A 에이전트를 sub-agent로 변환."""
    endpoints = await storage.list_endpoints(type=EndpointType.A2A)

    sub_agents = []
    for endpoint in endpoints:
        client = A2AClient(base_url=endpoint.url)
        card = await client.get_agent_card()
        sub_agents.append(A2ASubAgent(client, card))

    return sub_agents
```

---

## Testing with Echo Agent

### Start Echo Agent

```bash
# conftest.py에서 자동 시작됨 (포트 9003)
# 또는 수동 시작:
python tests/fixtures/a2a_agents/echo_agent.py
```

### Echo Agent Implementation

```python
# tests/fixtures/a2a_agents/echo_agent.py
from fastapi import FastAPI
from a2a.types import AgentCard, Task

app = FastAPI()

@app.get("/.well-known/agent.json")
async def agent_card() -> AgentCard:
    return AgentCard(
        name="Echo Agent",
        description="입력을 그대로 반환하는 테스트 에이전트",
        url="http://127.0.0.1:9003",
        version="1.0.0",
    )

@app.post("/tasks")
async def create_task(request: CreateTaskRequest) -> Task:
    # 단순히 입력을 그대로 반환
    return Task(
        id="echo-task",
        status=TaskStatus.COMPLETED,
        result=request.message.content,
    )
```

### Integration Test Example

```python
@pytest.mark.local_a2a
async def test_a2a_agent_discovery(a2a_echo_agent_url):
    """A2A Agent Card 조회 테스트."""
    client = A2AClient(base_url=a2a_echo_agent_url)
    card = await client.get_agent_card()

    assert card.name == "Echo Agent"
    assert card.version == "1.0.0"

@pytest.mark.local_a2a
async def test_a2a_task_execution(a2a_echo_agent_url):
    """A2A 작업 실행 테스트."""
    client = A2AClient(base_url=a2a_echo_agent_url)

    task = await client.send_task(
        message=Message(role="user", content="Hello, A2A!"),
    )

    assert task.status == TaskStatus.COMPLETED
    assert task.result == "Hello, A2A!"
```

---

## Health Check

### A2A Agent Health Monitoring

```python
async def check_a2a_health(endpoint: Endpoint) -> HealthStatus:
    """A2A 에이전트 상태 확인."""
    try:
        client = A2AClient(base_url=endpoint.url)
        card = await asyncio.wait_for(
            client.get_agent_card(),
            timeout=5.0,
        )
        return HealthStatus(
            status="healthy",
            agent_name=card.name,
            last_checked=datetime.now(),
        )
    except asyncio.TimeoutError:
        return HealthStatus(
            status="timeout",
            error="Agent Card 조회 시간 초과",
            last_checked=datetime.now(),
        )
    except Exception as e:
        return HealthStatus(
            status="unhealthy",
            error=str(e),
            last_checked=datetime.now(),
        )
```

### Periodic Health Check

```python
class A2AHealthMonitor:
    """A2A 에이전트 상태 모니터링."""

    def __init__(self, storage: StoragePort, interval: int = 60) -> None:
        self._storage = storage
        self._interval = interval
        self._running = False

    async def start(self) -> None:
        """상태 모니터링 시작."""
        self._running = True
        while self._running:
            endpoints = await self._storage.list_endpoints(type=EndpointType.A2A)
            for endpoint in endpoints:
                status = await check_a2a_health(endpoint)
                await self._storage.update_endpoint_health(endpoint.id, status)
            await asyncio.sleep(self._interval)

    def stop(self) -> None:
        """상태 모니터링 중지."""
        self._running = False
```

---

*Last Updated: 2026-02-05*
