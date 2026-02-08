# Implementation Guide

AgentHub 구현 패턴과 체크리스트입니다. 헥사고날 아키텍처에 맞는 코드 작성 방법을 다룹니다.

---

## Domain Entity Creation

### Checklist

- [ ] `src/domain/entities/` 에 파일 생성
- [ ] `@dataclass` 또는 순수 Python 클래스 사용
- [ ] 외부 라이브러리 import 금지 (ADK, FastAPI, SQLite 등)
- [ ] 불변성 유지 (`frozen=True` 권장)
- [ ] 타입 힌트 필수

### Example

```python
# src/domain/entities/agent.py
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass(frozen=True)
class Agent:
    """AI Agent 엔티티."""

    id: str
    name: str
    model: str
    instruction: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def with_instruction(self, instruction: str) -> "Agent":
        """Instruction을 변경한 새 Agent 반환 (불변성 유지)."""
        return Agent(
            id=self.id,
            name=self.name,
            model=self.model,
            instruction=instruction,
            created_at=self.created_at,
        )
```

### Aggregate Root Pattern

```python
# src/domain/entities/conversation.py
@dataclass
class Conversation:
    """대화 Aggregate Root."""

    id: str
    messages: list[Message] = field(default_factory=list)
    tool_calls: list[ToolCallRecord] = field(default_factory=list)

    def add_message(self, role: str, content: str) -> Message:
        """메시지 추가 (Aggregate 내부 일관성 유지)."""
        message = Message(
            id=f"msg-{len(self.messages)}",
            role=role,
            content=content,
        )
        self.messages.append(message)
        return message

    def record_tool_call(self, tool_name: str, arguments: dict, result: str) -> None:
        """도구 호출 기록."""
        record = ToolCallRecord(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
        )
        self.tool_calls.append(record)
```

---

## Domain Service Creation

### Checklist

- [ ] `src/domain/services/` 에 파일 생성
- [ ] Port 인터페이스를 의존성으로 주입받음
- [ ] 비즈니스 로직만 포함 (인프라 로직 X)
- [ ] 외부 라이브러리 import 금지

### Example

```python
# src/domain/services/orchestrator_service.py
from src.domain.ports.outbound.orchestrator_port import OrchestratorPort
from src.domain.ports.outbound.storage_port import StoragePort
from src.domain.entities.conversation import Conversation

class OrchestratorService:
    """대화 오케스트레이션 서비스."""

    def __init__(
        self,
        orchestrator_port: OrchestratorPort,
        storage_port: StoragePort,
    ) -> None:
        self._orchestrator = orchestrator_port
        self._storage = storage_port

    async def process_message(
        self,
        conversation_id: str,
        user_message: str,
    ) -> AsyncIterator[StreamChunk]:
        """사용자 메시지 처리 및 응답 스트리밍."""
        # 대화 조회 또는 생성
        conversation = await self._storage.get_conversation(conversation_id)
        if conversation is None:
            conversation = Conversation(id=conversation_id)

        # 메시지 추가
        conversation.add_message(role="user", content=user_message)

        # LLM 호출 및 스트리밍
        async for chunk in self._orchestrator.run(conversation):
            yield chunk

        # 대화 저장
        await self._storage.save_conversation(conversation)
```

---

## Port Interface Definition

### Checklist

- [ ] `src/domain/ports/inbound/` 또는 `src/domain/ports/outbound/` 에 파일 생성
- [ ] `abc.ABC` 와 `@abstractmethod` 사용
- [ ] 순수 Python 타입만 사용 (Domain Entity 포함)
- [ ] 문서화 (docstring) 필수

### Inbound Port Example

```python
# src/domain/ports/inbound/chat_port.py
from abc import ABC, abstractmethod
from typing import AsyncIterator
from src.domain.entities.stream_chunk import StreamChunk

class ChatPort(ABC):
    """채팅 인바운드 포트."""

    @abstractmethod
    async def send_message(
        self,
        conversation_id: str,
        message: str,
    ) -> AsyncIterator[StreamChunk]:
        """메시지를 전송하고 응답을 스트리밍으로 받습니다.

        Args:
            conversation_id: 대화 식별자
            message: 사용자 메시지

        Yields:
            응답 스트림 청크
        """
        ...
```

### Outbound Port Example

```python
# src/domain/ports/outbound/storage_port.py
from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.conversation import Conversation
from src.domain.entities.endpoint import Endpoint

class StoragePort(ABC):
    """저장소 아웃바운드 포트."""

    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """대화를 조회합니다."""
        ...

    @abstractmethod
    async def save_conversation(self, conversation: Conversation) -> None:
        """대화를 저장합니다."""
        ...

    @abstractmethod
    async def list_endpoints(self) -> list[Endpoint]:
        """등록된 모든 Endpoint를 조회합니다."""
        ...
```

---

## Adapter Implementation

### Checklist

- [ ] `src/adapters/inbound/` 또는 `src/adapters/outbound/` 에 파일 생성
- [ ] Port 인터페이스를 상속받아 구현
- [ ] 외부 라이브러리 사용 가능 (ADK, FastAPI, SQLite 등)
- [ ] DI Container에 등록

### Inbound Adapter Example

```python
# src/adapters/inbound/http_adapter.py
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from src.domain.ports.inbound.chat_port import ChatPort

router = APIRouter()

@router.post("/api/chat/{conversation_id}")
async def chat(
    conversation_id: str,
    request: ChatRequest,
    chat_port: ChatPort = Depends(get_chat_port),
) -> StreamingResponse:
    """채팅 엔드포인트."""

    async def generate():
        async for chunk in chat_port.send_message(
            conversation_id=conversation_id,
            message=request.message,
        ):
            yield f"data: {chunk.model_dump_json()}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )
```

### Outbound Adapter Example

```python
# src/adapters/outbound/sqlite_storage.py
import aiosqlite
from src.domain.ports.outbound.storage_port import StoragePort
from src.domain.entities.conversation import Conversation

class SqliteStorageAdapter(StoragePort):
    """SQLite 저장소 어댑터."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "SELECT data FROM conversations WHERE id = ?",
                (conversation_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return Conversation.from_dict(json.loads(row[0]))

    async def save_conversation(self, conversation: Conversation) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO conversations (id, data, updated_at)
                VALUES (?, ?, ?)
                """,
                (conversation.id, json.dumps(conversation.to_dict()), datetime.now()),
            )
            await db.commit()
```

---

## Fake Adapter for Testing

### Checklist

- [ ] `tests/unit/fakes/` 에 파일 생성
- [ ] Port 인터페이스를 상속받아 구현
- [ ] 메모리 기반으로 동작 (외부 의존성 X)
- [ ] 테스트 검증을 위한 헬퍼 메서드 추가

### Example

```python
# tests/unit/fakes/fake_storage.py
from src.domain.ports.outbound.storage_port import StoragePort
from src.domain.entities.conversation import Conversation

class FakeStorageAdapter(StoragePort):
    """테스트용 Fake 저장소."""

    def __init__(self) -> None:
        self._conversations: dict[str, Conversation] = {}
        self._endpoints: list[Endpoint] = []

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        return self._conversations.get(conversation_id)

    async def save_conversation(self, conversation: Conversation) -> None:
        self._conversations[conversation.id] = conversation

    # 테스트 헬퍼 메서드
    def get_saved_conversations(self) -> list[Conversation]:
        """저장된 모든 대화 반환 (테스트 검증용)."""
        return list(self._conversations.values())

    def clear(self) -> None:
        """저장소 초기화 (테스트 격리용)."""
        self._conversations.clear()
        self._endpoints.clear()
```

---

## DI Container Registration

### Checklist

- [ ] `src/config/container.py` 에 Provider 등록
- [ ] Singleton/Factory 스코프 적절히 선택
- [ ] 환경변수 기반 설정 주입

### Example

```python
# src/config/container.py
from dependency_injector import containers, providers
from src.adapters.outbound.sqlite_storage import SqliteStorageAdapter
from src.adapters.outbound.adk_orchestrator import AdkOrchestratorAdapter
from src.domain.services.orchestrator_service import OrchestratorService

class Container(containers.DeclarativeContainer):
    """DI Container."""

    config = providers.Configuration()

    # Outbound Adapters
    storage_adapter = providers.Singleton(
        SqliteStorageAdapter,
        db_path=config.database.path,
    )

    orchestrator_adapter = providers.Singleton(
        AdkOrchestratorAdapter,
        model=config.llm.model,
        api_key=config.llm.api_key,
    )

    # Domain Services
    orchestrator_service = providers.Factory(
        OrchestratorService,
        orchestrator_port=orchestrator_adapter,
        storage_port=storage_adapter,
    )
```

### Conditional Dependency Injection (Phase 5+)

**문제:** 일부 의존성은 설정에 따라 조건부로 주입해야 함 (예: `MCP__ENABLE_DUAL_TRACK=false`일 때 SDK Track 비활성화)

**❌ 잘못된 방법 (lambda 사용):**

```python
# WRONG: lambda는 디버깅 어렵고, 타입 힌트 없음
registry_service = providers.Factory(
    RegistryService,
    mcp_client=lambda: mcp_client_adapter() if settings().mcp.enable_dual_track else None,
)
```

**✅ 올바른 방법 (Callable provider):**

```python
# CORRECT: providers.Callable 사용, 타입 안전성 유지
registry_service = providers.Factory(
    RegistryService,
    mcp_client=providers.Callable(
        lambda s, m: m if s.mcp.enable_dual_track else None,
        settings,
        mcp_client_adapter,
    ),
)
```

**장점:**
- 타입 힌트 유지
- 디버깅 가능 (provider 이름 표시)
- 의존성 명시적 선언 (settings, mcp_client_adapter)

---

## TDD Workflow

### Red-Green-Refactor Cycle

1. **Red**: 실패하는 테스트 작성
2. **Green**: 테스트를 통과하는 최소한의 코드 작성
3. **Refactor**: 중복 제거 및 코드 개선

### Test First Example

```python
# tests/unit/domain/services/test_orchestrator_service.py

class TestOrchestratorService:
    """OrchestratorService 단위 테스트."""

    async def test_process_message_creates_conversation_if_not_exists(self):
        """대화가 없으면 새로 생성한다."""
        # Arrange
        fake_storage = FakeStorageAdapter()
        fake_orchestrator = FakeOrchestratorAdapter()
        service = OrchestratorService(
            orchestrator_port=fake_orchestrator,
            storage_port=fake_storage,
        )

        # Act
        chunks = [chunk async for chunk in service.process_message(
            conversation_id="new-conv",
            user_message="Hello",
        )]

        # Assert
        saved = fake_storage.get_saved_conversations()
        assert len(saved) == 1
        assert saved[0].id == "new-conv"
```

---

## GatewayService Integration (Phase 6)

### 개요

GatewayService는 Circuit Breaker, Rate Limiting, Fallback 패턴을 통합 제공합니다.

### 사용 예시

```python
from src.domain.services.gateway_service import GatewayService
from src.domain.entities.endpoint import Endpoint

# 1. Gateway 생성
gateway = GatewayService(
    rate_limit_rps=5.0,           # 초당 5 요청
    burst_size=10,                # 버스트 허용 10
    circuit_failure_threshold=5,  # 5회 실패 시 차단
    circuit_recovery_timeout=60.0, # 60초 후 복구 시도
)

# 2. 엔드포인트 등록
endpoint = Endpoint(
    id="mcp-server-1",
    url="http://primary.example.com/mcp",
    fallback_url="http://fallback.example.com/mcp",  # Optional
)
gateway.register_endpoint(endpoint)

# 3. 요청 실행
async def execute_with_gateway(endpoint_id: str):
    # Circuit Breaker 체크
    if not gateway.can_execute(endpoint_id):
        raise CircuitOpenError("Circuit is OPEN")

    # Rate Limit 체크
    if not await gateway.check_rate_limit(endpoint_id):
        raise RateLimitExceeded("Rate limit exceeded")

    # 활성 URL 가져오기 (Primary or Fallback)
    url = gateway.get_active_url(endpoint_id)

    try:
        result = await call_endpoint(url)
        gateway.record_success(endpoint_id)
        return result
    except Exception:
        gateway.record_failure(endpoint_id)
        raise
```

### 설정 참조

| 설정 | 환경변수 | 기본값 |
|------|----------|--------|
| 초당 요청 제한 | `GATEWAY__RATE_LIMIT_RPS` | `5.0` |
| 버스트 크기 | `GATEWAY__BURST_SIZE` | `10` |
| 실패 임계값 | `GATEWAY__CIRCUIT_FAILURE_THRESHOLD` | `5` |
| 복구 타임아웃 | `GATEWAY__CIRCUIT_RECOVERY_TIMEOUT` | `60.0` |

**참조:** `src/domain/services/gateway_service.py`

---

## CostService Integration (Phase 6)

### 개요

CostService는 LLM 호출 비용 추적 및 예산 관리를 제공합니다.

### Budget Status Levels

| alert_level | usage_percentage | can_proceed | 설명 |
|-------------|------------------|-------------|------|
| `safe` | < 90% | ✅ | 정상 범위 |
| `warning` | 90-100% | ✅ | 예산 경고 |
| `critical` | 100-110% | ⚠️ | 예산 초과 (허용) |
| `blocked` | > 110% | ❌ | API 호출 차단 |

### 사용 예시

```python
from src.domain.services.cost_service import CostService
from src.domain.entities.usage import Usage

# CostService 생성 (DI Container에서 주입)
cost_service = CostService(
    usage_port=storage,
    monthly_budget_usd=100.0,
)

# 1. 사용량 기록
usage = Usage(
    model="openai/gpt-4o-mini",
    prompt_tokens=100,
    completion_tokens=50,
    total_tokens=150,
    cost_usd=0.00015,
)
await cost_service.record_usage(usage)

# 2. 예산 상태 확인
status = await cost_service.check_budget()
print(f"Alert: {status.alert_level}, Can proceed: {status.can_proceed}")

# 3. LLM 호출 전 예산 강제 (110% 초과 시 예외)
try:
    await cost_service.enforce_budget()
    # LLM 호출 진행
except BudgetExceededError as e:
    # 예산 초과로 차단됨
    print(f"Blocked: {e}")

# 4. 월간 요약 조회
summary = await cost_service.get_monthly_summary()
print(f"Total: ${summary['total_cost']:.2f}, Calls: {summary['call_count']}")
```

### 설정 참조

| 설정 | 환경변수 | 기본값 |
|------|----------|--------|
| 월간 예산 | `COST__MONTHLY_BUDGET_USD` | `100.0` |
| 경고 임계값 | `COST__WARNING_THRESHOLD` | `0.9` |
| 심각 임계값 | `COST__CRITICAL_THRESHOLD` | `1.0` |
| 차단 임계값 | `COST__HARD_LIMIT_THRESHOLD` | `1.1` |

**참조:** `src/domain/services/cost_service.py`

---

*Last Updated: 2026-02-05*
