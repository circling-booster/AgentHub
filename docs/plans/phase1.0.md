# Phase 1: Domain Core 구현 계획

> AgentHub 헥사고날 아키텍처의 핵심 Domain Layer 구축

**작성일:** 2026-01-28
**예상 소요:** 22시간 (TDD 포함)
**검증 완료:** 2026-01-28

---

## 1. 목표

순수 Python으로 Domain Layer를 구축하고, SQLite Adapter까지 구현합니다:
- Domain Layer: 외부 라이브러리 import 금지
- Adapter Layer: aiosqlite 사용 가능
- TDD 방식: Red-Green-Refactor 사이클 엄수
- 테스트 커버리지 80% 이상

---

## 2. 현재 완료된 항목 (Phase 0)

| 항목 | 파일 | 상태 |
|------|------|:----:|
| Domain Exceptions | `src/domain/exceptions.py` | ✅ 완료 |
| Exception Tests | `tests/unit/domain/test_exceptions.py` | ✅ 완료 |
| Test Fixtures | `tests/conftest.py` | ✅ 완료 |
| TDD Agent | `.claude/agents/tdd-agent.md` | ✅ 완료 |
| Code Reviewer | `.claude/agents/code-reviewer.md` | ✅ 완료 |

**이미 정의된 예외 (11개):**
- `DomainException` (기본)
- `EndpointNotFoundError`, `EndpointConnectionError`, `EndpointTimeoutError`
- `ToolNotFoundError`, `ToolExecutionError`, `ToolLimitExceededError`
- `LlmRateLimitError`, `LlmAuthenticationError`
- `ConversationNotFoundError`
- `InvalidUrlError`, `ValidationError`

---

## 3. 구현 순서 (의존성 기반)

```
1. Enums → 2. Entities → 3. Ports → 4. Services → 5. Fake Adapters → 6. SQLite Adapter
```

| 순서 | 컴포넌트 | 파일 | 예상 |
|:---:|---------|------|:---:|
| 1 | Enums | `entities/enums.py` | 0.5h |
| 2 | Tool | `entities/tool.py` | 1h |
| 3 | ToolCall | `entities/tool_call.py` | 0.5h |
| 4 | Endpoint | `entities/endpoint.py` | 1h |
| 5 | Message | `entities/message.py` | 1h |
| 6 | Conversation | `entities/conversation.py` | 1h |
| 7 | Agent | `entities/agent.py` | 0.5h |
| 8 | Outbound Ports | `ports/outbound/*.py` | 2h |
| 9 | Inbound Ports | `ports/inbound/*.py` | 1h |
| 10 | ConversationService | `services/conversation.py` | 2h |
| 11 | RegistryService | `services/registry.py` | 2h |
| 12 | OrchestratorService | `services/orchestrator.py` | 2h |
| 13 | HealthMonitorService | `services/health_monitor.py` | 1.5h |
| 14 | Fake Adapters | `tests/unit/fakes/*.py` | 2h |
| 15 | **SQLite Adapter** | `adapters/outbound/storage/*.py` | 3h |
| **총계** | | | **22h** |

---

## 4. 서브에이전트 워크플로우 (필수)

roadmap.md에 정의된 서브에이전트 호출 시점:

| 시점 | 서브에이전트 | 목적 |
|------|-------------|------|
| 엔티티/서비스 **구현 전** | `tdd-agent` | 테스트 먼저 작성 |
| 구현 **완료 후** | `code-reviewer` | 헥사고날 원칙 준수 검토 |

### TDD 워크플로우 (각 컴포넌트마다)

```
1. tdd-agent 호출 → 테스트 코드 작성 (Red)
2. 구현 코드 작성 (Green)
3. 리팩토링 (Refactor)
4. code-reviewer 호출 → 아키텍처 검토
```

---

## 5. 엔티티 설계

### 5.1 Enums (`src/domain/entities/enums.py`)

```python
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class EndpointType(str, Enum):
    MCP = "mcp"
    A2A = "a2a"

class EndpointStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    UNKNOWN = "unknown"
```

### 5.2 Tool (`src/domain/entities/tool.py`)

```python
@dataclass(frozen=True, slots=True)
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    endpoint_id: str = ""

    def __post_init__(self):
        if not self.name:
            raise ValidationError("Tool name cannot be empty")
```

### 5.3 ToolCall (`src/domain/entities/tool_call.py`)

```python
@dataclass(frozen=True, slots=True)
class ToolCall:
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    result: Any = None
    error: str | None = None
    duration_ms: int | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def is_success(self) -> bool:
        return self.error is None
```

### 5.4 Endpoint (`src/domain/entities/endpoint.py`)

```python
@dataclass
class Endpoint:
    url: str
    type: EndpointType
    name: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    enabled: bool = True
    status: EndpointStatus = EndpointStatus.UNKNOWN
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_health_check: datetime | None = None
    tools: list[Tool] = field(default_factory=list)

    def __post_init__(self):
        if not self.url:
            raise InvalidUrlError("URL cannot be empty")
        if not self.url.startswith(("http://", "https://")):
            raise InvalidUrlError(f"Invalid URL scheme: {self.url}")
        if not self.name:
            self.name = self._extract_name_from_url()

    def update_status(self, status: EndpointStatus) -> None:
        self.status = status
        self.last_health_check = datetime.utcnow()

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False
```

### 5.5 Message (`src/domain/entities/message.py`)

```python
@dataclass
class Message:
    role: MessageRole
    content: str
    conversation_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool_calls: list[ToolCall] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def user(cls, content: str, conversation_id: str = "") -> "Message":
        return cls(role=MessageRole.USER, content=content, conversation_id=conversation_id)

    @classmethod
    def assistant(cls, content: str, conversation_id: str = "") -> "Message":
        return cls(role=MessageRole.ASSISTANT, content=content, conversation_id=conversation_id)

    @classmethod
    def system(cls, content: str, conversation_id: str = "") -> "Message":
        return cls(role=MessageRole.SYSTEM, content=content, conversation_id=conversation_id)

    def add_tool_call(self, tool_call: ToolCall) -> None:
        if self.role != MessageRole.ASSISTANT:
            raise ValidationError("Only assistant messages can have tool calls")
        self.tool_calls.append(tool_call)
```

### 5.6 Conversation (`src/domain/entities/conversation.py`) - **Aggregate Root**

```python
@dataclass
class Conversation:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, message: Message) -> None:
        message.conversation_id = self.id
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        if not self.title and message.role == MessageRole.USER:
            self.title = self._generate_title(message.content)

    def get_context_messages(self, limit: int = 20) -> list[Message]:
        return self.messages[-limit:]

    @property
    def message_count(self) -> int:
        return len(self.messages)
```

### 5.7 Agent (`src/domain/entities/agent.py`)

```python
@dataclass
class Agent:
    name: str
    model: str = "anthropic/claude-sonnet-4-20250514"
    instruction: str = "You are a helpful assistant with access to various tools."
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        if not self.name:
            raise ValidationError("Agent name cannot be empty")
```

---

## 6. Port Interfaces

### 6.1 Outbound Ports

#### OrchestratorPort (`ports/outbound/orchestrator_port.py`)

```python
class OrchestratorPort(ABC):
    @abstractmethod
    async def initialize(self) -> None: ...

    @abstractmethod
    async def process_message(self, message: str, conversation_id: str) -> AsyncIterator[str]: ...

    @abstractmethod
    async def close(self) -> None: ...
```

#### StoragePort (`ports/outbound/storage_port.py`)

```python
class ConversationStoragePort(ABC):
    @abstractmethod
    async def save_conversation(self, conversation: Conversation) -> None: ...

    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> Conversation | None: ...

    @abstractmethod
    async def list_conversations(self, limit: int = 20, offset: int = 0) -> list[Conversation]: ...

    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool: ...

    @abstractmethod
    async def save_message(self, message: Message) -> None: ...

    @abstractmethod
    async def get_messages(self, conversation_id: str) -> list[Message]: ...


class EndpointStoragePort(ABC):
    @abstractmethod
    async def save_endpoint(self, endpoint: Endpoint) -> None: ...

    @abstractmethod
    async def get_endpoint(self, endpoint_id: str) -> Endpoint | None: ...

    @abstractmethod
    async def list_endpoints(self, type_filter: str | None = None) -> list[Endpoint]: ...

    @abstractmethod
    async def delete_endpoint(self, endpoint_id: str) -> bool: ...

    @abstractmethod
    async def update_endpoint_status(self, endpoint_id: str, status: str) -> bool: ...
```

#### ToolsetPort (`ports/outbound/toolset_port.py`)

```python
class ToolsetPort(ABC):
    @abstractmethod
    async def add_mcp_server(self, endpoint: Endpoint) -> list[Tool]: ...

    @abstractmethod
    async def remove_mcp_server(self, endpoint_id: str) -> bool: ...

    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any: ...

    @abstractmethod
    async def get_tools(self) -> list[Tool]: ...

    @abstractmethod
    async def health_check(self, endpoint_id: str) -> bool: ...
```

#### A2aPort (`ports/outbound/a2a_port.py`) - **추가됨**

```python
class A2aPort(ABC):
    """A2A Agent 통신 포트 (Phase 3에서 구현)"""

    @abstractmethod
    async def register_agent(self, endpoint: Endpoint) -> dict: ...

    @abstractmethod
    async def call_agent(self, endpoint_id: str, message: str) -> AsyncIterator[str]: ...

    @abstractmethod
    async def get_agent_card(self, endpoint_id: str) -> dict: ...
```

### 6.2 Inbound Ports

#### ChatPort (`ports/inbound/chat_port.py`)

```python
class ChatPort(ABC):
    @abstractmethod
    async def send_message(self, conversation_id: str, message: str) -> AsyncIterator[str]: ...

    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> Conversation: ...

    @abstractmethod
    async def list_conversations(self, limit: int = 20) -> list[Conversation]: ...

    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool: ...
```

#### ManagementPort (`ports/inbound/management_port.py`)

```python
class ManagementPort(ABC):
    @abstractmethod
    async def register_endpoint(self, url: str, name: str | None = None) -> Endpoint: ...

    @abstractmethod
    async def unregister_endpoint(self, endpoint_id: str) -> bool: ...

    @abstractmethod
    async def list_endpoints(self) -> list[Endpoint]: ...

    @abstractmethod
    async def get_endpoint_tools(self, endpoint_id: str) -> list[Tool]: ...

    @abstractmethod
    async def check_endpoint_health(self, endpoint_id: str) -> bool: ...
```

---

## 7. Domain Services

### 7.1 ConversationService

```python
class ConversationService:
    def __init__(self, storage: ConversationStoragePort, orchestrator: OrchestratorPort):
        self._storage = storage
        self._orchestrator = orchestrator

    async def send_message(self, conversation_id: str | None, content: str) -> AsyncIterator[str]:
        # 1. 대화 조회/생성
        # 2. 사용자 메시지 저장
        # 3. LLM 호출 + 스트리밍
        # 4. 어시스턴트 메시지 저장
```

### 7.2 RegistryService

```python
class RegistryService:
    def __init__(self, storage: EndpointStoragePort, toolset: ToolsetPort):
        self._storage = storage
        self._toolset = toolset

    async def register_mcp(self, url: str, name: str | None = None) -> Endpoint: ...
    async def unregister(self, endpoint_id: str) -> bool: ...
    async def list_endpoints(self, type_filter: EndpointType | None = None) -> list[Endpoint]: ...
```

### 7.3 OrchestratorService (ChatPort 구현)

```python
class OrchestratorService(ChatPort):
    def __init__(self, conversation_service: ConversationService):
        self._conversation_service = conversation_service

    # ChatPort 메서드 위임
```

### 7.4 HealthMonitorService

```python
class HealthMonitorService:
    def __init__(self, storage: EndpointStoragePort, toolset: ToolsetPort, check_interval_seconds: int = 30):
        ...

    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def check_all_endpoints(self) -> dict[str, bool]: ...
```

---

## 8. Fake Adapters (테스트용)

| Fake | 파일 | 용도 |
|------|------|------|
| `FakeConversationStorage` | `tests/unit/fakes/fake_storage.py` | 인메모리 대화 저장 |
| `FakeEndpointStorage` | `tests/unit/fakes/fake_storage.py` | 인메모리 엔드포인트 저장 |
| `FakeOrchestrator` | `tests/unit/fakes/fake_orchestrator.py` | 테스트 응답 반환 |
| `FakeToolset` | `tests/unit/fakes/fake_toolset.py` | 가짜 도구 관리 |

---

## 9. SQLite Adapter (Phase 1 포함)

### 9.1 파일 구조

```
src/adapters/outbound/storage/
├── __init__.py
├── sqlite_conversation_storage.py  # ConversationStoragePort 구현
└── json_endpoint_storage.py        # EndpointStoragePort 구현 (JSON 파일)
```

### 9.2 SQLite Schema

```sql
-- PRAGMA 설정
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;
PRAGMA foreign_keys=ON;

-- conversations 테이블
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- messages 테이블
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation
ON messages(conversation_id);

-- tool_calls 테이블
CREATE TABLE IF NOT EXISTS tool_calls (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    arguments JSON,
    result JSON,
    error TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
);
```

### 9.3 SQLite Adapter 구현 핵심

```python
# src/adapters/outbound/storage/sqlite_conversation_storage.py
class SqliteConversationStorage(ConversationStoragePort):
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._connection: aiosqlite.Connection | None = None
        self._write_lock = asyncio.Lock()  # 쓰기 직렬화

    async def initialize(self) -> None:
        conn = await self._get_connection()
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA busy_timeout=5000")
        # 테이블 생성...
```

---

## 10. 테스트 전략

### 10.1 테스트 파일 구조

```
tests/
├── conftest.py                       # ✅ 완료
├── unit/
│   ├── fakes/
│   │   ├── __init__.py
│   │   ├── fake_storage.py
│   │   ├── fake_orchestrator.py
│   │   └── fake_toolset.py
│   └── domain/
│       ├── test_exceptions.py        # ✅ 완료
│       ├── entities/
│       │   ├── test_enums.py
│       │   ├── test_tool.py
│       │   ├── test_tool_call.py
│       │   ├── test_endpoint.py
│       │   ├── test_message.py
│       │   ├── test_conversation.py
│       │   └── test_agent.py
│       └── services/
│           ├── test_conversation_service.py
│           ├── test_registry_service.py
│           ├── test_orchestrator_service.py
│           └── test_health_monitor.py
└── integration/
    └── adapters/
        └── test_sqlite_storage.py    # SQLite WAL 모드 검증
```

### 10.2 테스트 케이스 요약

| 컴포넌트 | 테스트 수 | 핵심 케이스 |
|---------|:--------:|----------|
| Enums | 3 | 값 검증, str 변환 |
| Tool | 5 | 생성, 불변성, 유효성 |
| ToolCall | 4 | 생성, is_success |
| Endpoint | 8 | URL 검증, 상태, 활성화 |
| Message | 7 | 팩토리, ToolCall 추가 |
| Conversation | 8 | 메시지 관리, 제목 생성 |
| Agent | 4 | 생성, 유효성 |
| Services | 24 | CRUD, 스트리밍, 에러 |
| SQLite Adapter | 8 | WAL, CRUD, 동시성 |
| **총계** | **71+** | |

---

## 11. 구현 체크리스트

### Phase 1.1: Enums
- [ ] `src/domain/entities/enums.py`
- [ ] `tests/unit/domain/entities/test_enums.py`

### Phase 1.2: Entities (TDD - tdd-agent 사용)
- [ ] Tool: 테스트 → 구현 → code-reviewer
- [ ] ToolCall: 테스트 → 구현 → code-reviewer
- [ ] Endpoint: 테스트 → 구현 → code-reviewer
- [ ] Message: 테스트 → 구현 → code-reviewer
- [ ] Conversation: 테스트 → 구현 → code-reviewer
- [ ] Agent: 테스트 → 구현 → code-reviewer

### Phase 1.3: Ports
- [ ] `ports/outbound/orchestrator_port.py`
- [ ] `ports/outbound/storage_port.py`
- [ ] `ports/outbound/toolset_port.py`
- [ ] `ports/outbound/a2a_port.py`
- [ ] `ports/inbound/chat_port.py`
- [ ] `ports/inbound/management_port.py`

### Phase 1.4: Services (TDD)
- [ ] ConversationService
- [ ] RegistryService
- [ ] OrchestratorService
- [ ] HealthMonitorService

### Phase 1.5: Fake Adapters
- [ ] `tests/unit/fakes/fake_storage.py`
- [ ] `tests/unit/fakes/fake_orchestrator.py`
- [ ] `tests/unit/fakes/fake_toolset.py`

### Phase 1.6: SQLite Adapter
- [ ] `src/adapters/outbound/storage/sqlite_conversation_storage.py`
- [ ] `tests/integration/adapters/test_sqlite_storage.py`
- [ ] WAL 모드 동작 확인 (.wal, .shm 파일 생성)

---

## 12. DoD (Definition of Done) - roadmap.md 기준

- [ ] Domain Layer에 외부 라이브러리 import 없음 (ADK, FastAPI 등)
- [ ] 모든 엔티티/서비스에 대한 단위 테스트 존재
- [ ] Fake Adapter 기반 테스트 통과
- [ ] 테스트 커버리지 80% 이상
- [ ] **SQLite WAL 모드 동작 확인 (-wal, -shm 파일 생성)**

---

## 13. 검증 명령어

```bash
# 테스트 실행
pytest tests/unit/ tests/integration/ -v

# 커버리지 확인 (80% 이상)
pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# 린트 검사
ruff check src/

# Domain Layer 외부 import 검사 (결과 없어야 함)
grep -rE "^from (google|fastapi|aiosqlite|httpx)" src/domain/
```

---

## 14. Critical Files

| 파일 | 중요도 | 이유 |
|------|:------:|------|
| `entities/conversation.py` | ⭐⭐⭐ | Aggregate Root |
| `services/conversation.py` | ⭐⭐⭐ | 핵심 비즈니스 로직 |
| `ports/outbound/storage_port.py` | ⭐⭐⭐ | Adapter 계약 정의 |
| `adapters/outbound/storage/sqlite_conversation_storage.py` | ⭐⭐⭐ | SQLite WAL 구현 |
| `entities/endpoint.py` | ⭐⭐ | MCP/A2A 연결 관리 |
| `tests/unit/fakes/fake_storage.py` | ⭐⭐ | 테스트 기반 |

---

## 참고 자료

- [Google ADK Custom Tools](https://google.github.io/adk-docs/tools-custom/)
- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [aiosqlite](https://aiosqlite.omnilib.dev/)
- [SQLite WAL Mode](https://www.sqlite.org/wal.html)

---

*Phase 1 완료 후 Phase 1.5 (Security Layer) 진행*
