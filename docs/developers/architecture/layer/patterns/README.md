# Architecture Patterns

AgentHub에서 사용하는 아키텍처 설계 패턴 문서입니다.

---

## Hexagonal Architecture

### 개념

**Ports and Adapters** 패턴으로도 불리며, 비즈니스 로직을 외부 시스템으로부터 분리합니다.

```
                    ┌─────────────────────────────────────┐
                    │                                     │
    ┌───────────┐   │   ┌─────────────────────────┐      │   ┌───────────┐
    │  HTTP     │◀──┼──▶│                         │◀─────┼──▶│  Database │
    │  Adapter  │   │   │                         │      │   │  Adapter  │
    └───────────┘   │   │                         │      │   └───────────┘
                    │   │      Domain Core        │      │
    ┌───────────┐   │   │                         │      │   ┌───────────┐
    │  CLI      │◀──┼──▶│   (Business Logic)      │◀─────┼──▶│  LLM      │
    │  Adapter  │   │   │                         │      │   │  Adapter  │
    └───────────┘   │   │                         │      │   └───────────┘
                    │   └─────────────────────────┘      │
                    │                                     │
                    │            Ports                    │
                    └─────────────────────────────────────┘
```

### AgentHub 적용

| 레이어 | 역할 | 예시 |
|--------|------|------|
| **Domain Core** | 비즈니스 로직 | Entity, Service |
| **Inbound Ports** | 외부 → Domain | ChatPort, ManagementPort |
| **Outbound Ports** | Domain → 외부 | StoragePort, OrchestratorPort |
| **Inbound Adapters** | Port 구현 (진입) | FastAPI Routes |
| **Outbound Adapters** | Port 구현 (의존) | SQLite, ADK |

### 의존성 규칙

```
Adapters → Ports → Domain Core
   ↑                    ↓
   └────────── X ───────┘ (금지)
```

- **Domain Core**는 외부를 모름 (순수 Python)
- **Ports**는 Domain만 참조
- **Adapters**는 Ports 구현, 외부 라이브러리 사용

---

## Dependency Injection

### 개념

객체 생성을 외부에서 주입받아 결합도를 낮춥니다.

### 구현 (dependency-injector)

```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    # Configuration
    settings = providers.Singleton(Settings)

    # Outbound Adapters
    storage = providers.Singleton(
        SQLiteStorageAdapter,
        db_path=settings.provided.db_path,
    )

    # Domain Services (Port 주입)
    conversation_service = providers.Factory(
        ConversationService,
        storage_port=storage,
    )
```

### 사용

```python
# Route에서 주입
@inject
async def handler(
    service: ConversationService = Depends(Provide[Container.conversation_service]),
):
    return await service.get_conversation(id)
```

### 장점

| 장점 | 설명 |
|------|------|
| **테스트 용이** | 실제 구현 대신 Fake 주입 |
| **유연성** | 런타임에 구현체 교체 |
| **명시적 의존성** | 생성자에서 의존성 명확화 |

---

## Repository Pattern

### 개념

데이터 접근을 추상화하여 Domain이 저장소 구현을 모르게 합니다.

### AgentHub 적용

StoragePort가 Repository 역할:

```python
class StoragePort(ABC):
    @abstractmethod
    async def save_conversation(self, conversation: Conversation) -> None:
        pass

    @abstractmethod
    async def get_conversation(self, id: str) -> Optional[Conversation]:
        pass

    @abstractmethod
    async def list_conversations(self) -> list[Conversation]:
        pass

    @abstractmethod
    async def delete_conversation(self, id: str) -> None:
        pass
```

### 구현체

| 구현체 | 용도 |
|--------|------|
| **SQLiteStorageAdapter** | 프로덕션 (영구 저장) |
| **FakeStorageAdapter** | 테스트 (인메모리) |

---

## Adapter Pattern

### 개념

기존 인터페이스를 다른 인터페이스로 변환합니다.

### AgentHub 적용

외부 라이브러리 → Port 인터페이스 변환:

```python
# Google ADK → OrchestratorPort
class ADKOrchestratorAdapter(OrchestratorPort):
    def __init__(self):
        self._agent = LlmAgent(...)  # ADK 객체

    async def run(self, conversation: Conversation) -> AsyncIterator[StreamChunk]:
        # ADK 이벤트 → Domain StreamChunk 변환
        async for event in self._agent.run_async(...):
            yield self._convert_to_stream_chunk(event)
```

### 변환 대상

| 외부 시스템 | Adapter | Domain 타입 |
|-------------|---------|-------------|
| Google ADK Event | ADKOrchestratorAdapter | StreamChunk |
| SQLite Row | SQLiteStorageAdapter | Conversation |
| MCP Tool | DynamicToolset | Tool |
| A2A Response | A2AClientAdapter | StreamChunk |

---

## Observer Pattern

### 개념

객체 상태 변화를 다른 객체에게 알립니다.

### AgentHub 적용: SSE Streaming

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│   LLM    │────▶│ Observer │────▶│  Client  │
│  Agent   │     │ (SSE)    │     │(Extension)│
└──────────┘     └──────────┘     └──────────┘
     │
     │ StreamChunk 이벤트
     ↓
async for chunk in orchestrator.run():
    yield f"event: {chunk.event_type}\ndata: {chunk.data}\n\n"
```

### 이벤트 타입

| 이벤트 | 설명 |
|--------|------|
| `text` | LLM 텍스트 응답 |
| `tool_call` | 도구 호출 시작 |
| `tool_result` | 도구 실행 결과 |
| `agent_transfer` | 에이전트 전환 |
| `done` | 스트림 완료 |

---

## Factory Pattern

### 개념

객체 생성 로직을 분리합니다.

### AgentHub 적용

#### App Factory

```python
def create_app() -> FastAPI:
    """FastAPI 앱 생성"""
    container = Container()
    app = FastAPI(lifespan=lifespan)
    app.container = container
    # 미들웨어, 라우터 설정
    return app
```

#### Async Factory (Adapter 초기화)

```python
class ADKOrchestratorAdapter:
    def __init__(self, model: str):
        self._model = model
        self._agent = None  # 비동기 초기화 필요

    async def initialize(self) -> None:
        """비동기 팩토리 메서드"""
        self._agent = await self._create_agent()
```

---

## Circuit Breaker Pattern

### 개념

실패하는 외부 호출을 빠르게 실패시켜 시스템을 보호합니다.

### 상태 전이

```
       실패 누적 > 임계값
┌─────────┐────────────────▶┌─────────┐
│ CLOSED  │                 │  OPEN   │
└─────────┘◀────────────────└────┬────┘
     ▲      성공 > 임계값         │
     │                           │ 타임아웃
     │    ┌─────────────┐        │
     └────│ HALF_OPEN   │◀───────┘
          └─────────────┘
           일부 요청 허용
```

### CircuitState Enum

| 상태 | 설명 | 요청 허용 |
|------|------|----------|
| `CLOSED` | 정상 (기본 상태) | ✅ |
| `OPEN` | 차단 (실패 임계값 초과) | ❌ |
| `HALF_OPEN` | 복구 테스트 (타임아웃 후) | ✅ (제한적) |

### 상태 전이 규칙

| 전이 | 조건 |
|------|------|
| CLOSED → OPEN | `failure_count >= failure_threshold` |
| OPEN → HALF_OPEN | `recovery_timeout` 경과 후 자동 |
| HALF_OPEN → CLOSED | `record_success()` 호출 시 |
| HALF_OPEN → OPEN | `record_failure()` 호출 시 |

### AgentHub 적용 (Phase 6)

```python
@dataclass
class CircuitBreaker:
    """
    Circuit Breaker 패턴 구현 (순수 Python)

    Attributes:
        failure_threshold: 연속 실패 임계값 (default: 5)
        recovery_timeout: 복구 대기 시간 초 (default: 60.0)
    """
    failure_threshold: int = 5
    recovery_timeout: float = 60.0

    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0.0, init=False)

    @property
    def state(self) -> CircuitState:
        """현재 상태 반환 (자동 전이 포함)"""
        if self._state == CircuitState.OPEN:
            elapsed = time.time() - self._last_failure_time
            if elapsed >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def can_execute(self) -> bool:
        """실행 가능 여부 (OPEN이면 False)"""
        return self.state != CircuitState.OPEN

    def record_success(self) -> None:
        """성공 기록 (HALF_OPEN → CLOSED 복구)"""
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
        self._failure_count = 0

    def record_failure(self) -> None:
        """실패 기록 (임계값 초과 시 OPEN 전이)"""
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
```

**참조:** `src/domain/entities/circuit_breaker.py`

---

## Rate Limiting Pattern

### 개념

Token Bucket 알고리즘으로 요청 속도를 제한하여 시스템 과부하를 방지합니다.

### Token Bucket 알고리즘

```
┌─────────────────────────────────────┐
│          Token Bucket               │
│   ┌───┬───┬───┬───┬───┬───┬───┐   │
│   │ ● │ ● │ ● │ ● │ ○ │ ○ │ ○ │   │  ← capacity (burst_size)
│   └───┴───┴───┴───┴───┴───┴───┘   │
│   ● = 사용 가능 토큰                  │
│   ○ = 빈 슬롯                        │
│                                     │
│   rate: 5.0 tokens/second           │  ← 초당 충전 속도
└─────────────────────────────────────┘
```

### 주요 속성

| 속성 | 설명 | 예시 |
|------|------|------|
| `capacity` | 최대 토큰 수 (burst 허용) | `10` |
| `rate` | 초당 토큰 충전 속도 | `5.0` tokens/sec |
| `_lock` | asyncio 동시성 안전 Lock | `asyncio.Lock` |

### AgentHub 적용 (Phase 6)

```python
@dataclass
class TokenBucket:
    """Token Bucket Rate Limiting 알고리즘 (asyncio 동시성 안전)"""

    capacity: int    # burst_size (예: 10)
    rate: float      # tokens/second (예: 5.0)

    _tokens: float = field(init=False)
    _last_refill: float = field(default_factory=time.time, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def __post_init__(self) -> None:
        self._tokens = float(self.capacity)

    async def consume(self, tokens: int = 1) -> bool:
        """토큰 소비 (동시성 안전)"""
        async with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def _refill(self) -> None:
        """경과 시간에 따라 토큰 충전"""
        now = time.time()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now
```

**참조:** `src/domain/services/gateway_service.py`

---

## Fallback Pattern

### 개념

Primary 서버 장애 시 Fallback 서버로 자동 전환하여 서비스 가용성을 보장합니다.

### 동작 흐름

```
┌──────────────────────────────────────────────────┐
│                 get_active_url()                  │
└──────────────────────────────────────────────────┘
                        │
            Circuit Breaker가 OPEN인가?
                        │
          ┌─────────────┴─────────────┐
          ↓                           ↓
         No                          Yes
          │                           │
          │              fallback_url이 설정되어 있는가?
          │                           │
          │              ┌────────────┴────────────┐
          │              ↓                         ↓
          │             Yes                        No
          │              │                         │
          ↓              ↓                         ↓
    ┌──────────┐   ┌──────────┐             ┌──────────┐
    │ Primary  │   │ Fallback │             │ Primary  │
    │   URL    │   │   URL    │             │   URL    │
    └──────────┘   └──────────┘             └──────────┘
```

### 전환 조건

| 조건 | 결과 |
|------|------|
| Circuit CLOSED or HALF_OPEN | Primary URL 사용 |
| Circuit OPEN + fallback_url 존재 | Fallback URL 사용 |
| Circuit OPEN + fallback_url 없음 | Primary URL 사용 (실패 예상) |

### AgentHub 적용 (Phase 6)

```python
def get_active_url(self, endpoint_id: str) -> str:
    """현재 활성화된 URL 반환 (Primary or Fallback)"""
    endpoint = self._endpoints.get(endpoint_id)
    if not endpoint:
        return ""

    circuit_breaker = self._circuit_breakers.get(endpoint_id)
    if (circuit_breaker
        and circuit_breaker.state == CircuitState.OPEN
        and endpoint.fallback_url):
        return endpoint.fallback_url

    return endpoint.url

def has_fallback(self, endpoint_id: str) -> bool:
    """Fallback URL 설정 여부"""
    endpoint = self._endpoints.get(endpoint_id)
    return bool(endpoint and endpoint.fallback_url)
```

**참조:** `src/domain/services/gateway_service.py`

---

## Aggregate Pattern

### 개념

관련 Entity를 그룹화하고 일관성을 보장합니다.

### AgentHub 적용

**Conversation**이 Aggregate Root:

```
┌─────────────────────────────────────┐
│           Conversation              │ ◀── Aggregate Root
│  ┌─────────────────────────────┐   │
│  │         Messages            │   │
│  │   ┌─────┐ ┌─────┐ ┌─────┐  │   │
│  │   │ M1  │ │ M2  │ │ M3  │  │   │
│  │   └─────┘ └─────┘ └─────┘  │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │        ToolCalls            │   │
│  │   ┌─────┐ ┌─────┐          │   │
│  │   │ TC1 │ │ TC2 │          │   │
│  │   └─────┘ └─────┘          │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### 규칙

| 규칙 | 설명 |
|------|------|
| **단일 진입점** | Conversation을 통해서만 Message 접근 |
| **트랜잭션 경계** | Conversation 단위로 저장/조회 |
| **일관성 보장** | 내부 상태는 메서드로만 변경 |

---

*Last Updated: 2026-02-05*
