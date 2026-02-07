# Adapters Layer

헥사고날 아키텍처의 Adapters 레이어 설계 문서입니다.

---

## Adapter 개념

Adapter는 Port 인터페이스의 **구체적인 구현체**입니다.

```
┌─────────────────────────────────────────────────────────────┐
│                      Inbound Adapters                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  FastAPI HTTP Adapter                                    ││
│  │  - HTTP 요청 → Domain 호출                               ││
│  │  - Domain 결과 → HTTP 응답                               ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │  A2A Server Adapter                                      ││
│  │  - A2A 요청 → Domain 호출                                ││
│  │  - Domain 결과 → A2A 응답                                ││
│  └─────────────────────────────────────────────────────────┘│
└───────────────────────────┬─────────────────────────────────┘
                            │ Inbound Ports
                            ↓
                    ┌───────────────┐
                    │  Domain Core  │
                    └───────┬───────┘
                            │ Outbound Ports
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Outbound Adapters                        │
│  ┌──────────────┬──────────────┬──────────────┬───────────┐│
│  │ ADK Adapter  │Storage Adapter│A2A Adapter  │OAuth Adapter│
│  │ (LLM 호출)   │ (SQLite)     │ (Client)    │ (인증)      ││
│  └──────────────┴──────────────┴──────────────┴───────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## Inbound Adapters

외부 요청을 Domain으로 전달합니다.

### FastAPI HTTP Adapter

| 구성 요소 | 역할 |
|-----------|------|
| **Routes** | HTTP 엔드포인트 정의 |
| **Schemas** | Request/Response Pydantic 모델 |
| **Security** | 인증 미들웨어 |
| **Exceptions** | 예외 → HTTP 응답 변환 |

```
src/adapters/inbound/http/
├── __init__.py
├── app.py              # FastAPI 앱 팩토리
├── security.py         # 인증 미들웨어
├── exceptions.py       # 예외 핸들러
├── routes/
│   ├── auth.py         # /auth/*
│   ├── health.py       # /health
│   ├── chat.py         # /api/chat/*
│   ├── conversations.py # /api/conversations/*
│   ├── mcp.py          # /api/mcp/*
│   ├── a2a.py          # /api/a2a/*
│   ├── oauth.py        # /api/oauth/*
│   └── usage.py        # /api/usage/*
└── schemas/
    ├── auth.py
    ├── chat.py
    ├── conversations.py
    └── ...
```

### A2A Server Adapter

| 역할 | 설명 |
|------|------|
| **Agent Card 제공** | `/.well-known/agent.json` |
| **Task 수신** | A2A 프로토콜 요청 처리 |
| **응답 생성** | A2A 형식으로 응답 |

```
src/adapters/inbound/a2a/
├── __init__.py
└── a2a_server.py
```

---

## Outbound Adapters

Domain에서 외부 시스템으로 나가는 호출을 처리합니다.

### ADK Orchestrator Adapter

**OrchestratorPort** 구현:

| 구성 요소 | 역할 |
|-----------|------|
| **LlmAgent** | Google ADK Agent 래퍼 |
| **DynamicToolset** | MCP 도구 동적 관리 |
| **GatewayToolset** | Circuit Breaker + Lazy Loading |
| **LiteLLM Callbacks** | 사용량 추적 |

```
src/adapters/outbound/adk/
├── __init__.py
├── orchestrator_adapter.py  # OrchestratorPort 구현
├── dynamic_toolset.py       # ToolsetPort 구현
├── gateway_toolset.py       # Phase 6 Toolset
└── litellm_callbacks.py     # 사용량 콜백
```

### SQLite Storage Adapter

**StoragePort** 구현:

| 특징 | 설명 |
|------|------|
| **WAL 모드** | 동시 읽기/쓰기 지원 |
| **비동기** | aiosqlite 사용 |
| **테이블 분리** | conversations, messages, tool_calls |

```
src/adapters/outbound/storage/
├── __init__.py
├── sqlite_conversation_storage.py  # 대화 저장
├── sqlite_usage.py                 # 사용량 저장
└── json_endpoint_storage.py        # 엔드포인트 저장
```

### A2A Client Adapter

**A2APort** 구현:

| 기능 | 설명 |
|------|------|
| **Agent Card 조회** | `/.well-known/agent.json` fetch |
| **Task 전송** | `tasks/send` 호출 |
| **스트리밍 수신** | 비동기 응답 처리 |

```
src/adapters/outbound/a2a/
├── __init__.py
└── a2a_client_adapter.py
```

### OAuth Adapter

**OAuthPort** 구현:

| 기능 | 설명 |
|------|------|
| **Authorization URL** | PKCE 코드 챌린지 생성 |
| **Token Exchange** | 인가 코드 → 토큰 교환 |
| **Token Refresh** | 만료 토큰 갱신 |

```
src/adapters/outbound/oauth/
├── __init__.py
└── oauth_adapter.py
```

### MCP Client Adapter

**McpClientPort** 구현 (SDK Track):

| 기능 | 설명 |
|------|------|
| **MCP 서버 연결** | Streamable HTTP Transport (AsyncExitStack) |
| **Resources** | 리소스 목록 조회 및 읽기 |
| **Prompts** | 프롬프트 목록 조회 및 렌더링 |
| **콜백 변환** | Domain Protocol ↔ MCP SDK 타입 변환 |

**콜백 변환 로직:**
- **Sampling:** Domain `SamplingCallback` → MCP SDK `SamplingFnT`
  - `types.CreateMessageRequestParams` → Domain dict → `types.CreateMessageResult`
- **Elicitation:** Domain `ElicitationCallback` → MCP SDK `ElicitationFnT`
  - `types.ElicitRequestParams` → Domain dict → `types.ElicitResult`

```
src/adapters/outbound/mcp/
├── __init__.py
├── mcp_client_adapter.py   # McpClientPort 구현
└── README.md               # Component 문서
```

**상세:** [src/adapters/outbound/mcp/README.md](../../../../src/adapters/outbound/mcp/README.md)

### SSE Adapters

**EventBroadcastPort, HitlNotificationPort** 구현:

| Component | 역할 |
|-----------|------|
| **SseBroker** | SSE 이벤트 브로드캐스터 (Pub/Sub 패턴) |
| **HitlNotificationAdapter** | HITL 알림 SSE 전송 |

**Pub/Sub 패턴:**
```
         broadcast()
              │
              ▼
        ┌──────────┐
        │SseBroker │
        │  (Pub)   │
        └──────────┘
         │   │   │
         ▼   ▼   ▼
      Queue Queue Queue
         │   │   │
         ▼   ▼   ▼
     Client Client Client
```

**HITL Notification Flow:**
1. MCP 서버 Sampling/Elicitation 요청
2. McpClientAdapter 콜백 → Domain 형식 변환
3. HitlNotificationAdapter → SSE 이벤트 브로드캐스트
4. 모든 SSE 클라이언트(Extension, Playground)가 알림 수신

```
src/adapters/outbound/sse/
├── __init__.py
├── broker.py                        # EventBroadcastPort 구현
├── hitl_notification_adapter.py     # HitlNotificationPort 구현
└── README.md                        # Component 문서
```

**상세:** [src/adapters/outbound/sse/README.md](../../../../src/adapters/outbound/sse/README.md)

---

## Adapter 구현 원칙

### 1. Port 인터페이스 구현

```python
from src.domain.ports.outbound.storage_port import StoragePort

class SQLiteStorageAdapter(StoragePort):
    async def save_conversation(self, conversation: Conversation) -> None:
        # 구체적인 SQLite 저장 로직
        pass
```

### 2. 외부 라이브러리 사용 가능

```python
# Adapter에서만 외부 라이브러리 import
import aiosqlite
from google.adk.agents import LlmAgent
from fastapi import APIRouter
```

### 3. Domain 타입 변환

```python
class SQLiteStorageAdapter(StoragePort):
    async def get_conversation(self, id: str) -> Optional[Conversation]:
        # SQLite row → Domain Entity 변환
        row = await self._fetch_row(id)
        if row is None:
            return None
        return Conversation(
            id=row["id"],
            messages=self._parse_messages(row["messages"]),
        )
```

### 4. 비동기 초기화 패턴

```python
class AsyncAdapter:
    def __init__(self):
        self._initialized = False

    async def initialize(self) -> None:
        """비동기 초기화 (lifespan에서 호출)"""
        # DB 연결, 외부 서비스 초기화
        self._initialized = True

    async def close(self) -> None:
        """리소스 정리"""
        pass
```

---

## DI Container 통합

Adapter는 DI Container를 통해 주입됩니다:

```python
# src/config/container.py
class Container(containers.DeclarativeContainer):
    # Settings
    settings = providers.Singleton(Settings)

    # Storage Adapters
    conversation_storage = providers.Singleton(
        SQLiteConversationStorage,
        db_path=settings.provided.db_path,
    )

    # Orchestrator Adapter
    orchestrator_adapter = providers.Singleton(
        ADKOrchestratorAdapter,
        model=settings.provided.default_model,
        toolset=dynamic_toolset,
    )
```

### Wiring

```python
# 라우트에서 의존성 주입
from dependency_injector.wiring import inject, Provide

@router.post("/chat")
@inject
async def chat(
    storage: StoragePort = Depends(Provide[Container.conversation_storage]),
):
    pass
```

---

## Adapter 디렉토리 구조

```
src/adapters/
├── __init__.py
├── inbound/
│   ├── __init__.py
│   ├── http/           # FastAPI HTTP
│   │   ├── app.py
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   ├── routes/
│   │   └── schemas/
│   └── a2a/            # A2A Server
│       └── a2a_server.py
└── outbound/
    ├── __init__.py
    ├── adk/            # Google ADK
    │   ├── orchestrator_adapter.py
    │   ├── dynamic_toolset.py
    │   ├── gateway_toolset.py
    │   └── litellm_callbacks.py
    ├── storage/        # SQLite
    │   ├── sqlite_conversation_storage.py
    │   ├── sqlite_usage.py
    │   └── json_endpoint_storage.py
    ├── a2a/            # A2A Client
    │   └── a2a_client_adapter.py
    ├── oauth/          # OAuth
    │   └── oauth_adapter.py
    ├── mcp/            # MCP Client (SDK Track)
    │   ├── __init__.py
    │   ├── mcp_client_adapter.py
    │   └── README.md
    └── sse/            # SSE Event Broadcasting
        ├── __init__.py
        ├── broker.py
        ├── hitl_notification_adapter.py
        └── README.md
```

---

## Testing Adapters

### Integration Test

실제 외부 시스템과 통합 테스트:

```python
# tests/integration/test_sqlite_storage.py
async def test_save_and_load():
    adapter = SQLiteStorageAdapter(":memory:")
    await adapter.initialize()

    conversation = Conversation(id="test-1")
    await adapter.save_conversation(conversation)

    loaded = await adapter.get_conversation("test-1")
    assert loaded.id == "test-1"
```

### Unit Test (with Fake)

Domain 테스트에서 Fake Adapter 사용:

```python
# tests/unit/fakes/fake_storage.py
class FakeStorageAdapter(StoragePort):
    def __init__(self):
        self._data = {}

    async def save_conversation(self, conv: Conversation) -> None:
        self._data[conv.id] = conv
```

---

*Last Updated: 2026-02-05*
