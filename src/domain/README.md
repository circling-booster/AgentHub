# Domain Layer

> 순수 Python으로 작성된 핵심 비즈니스 로직

## Purpose

AgentHub의 핵심 비즈니스 규칙을 담당합니다. **외부 라이브러리에 의존하지 않는 순수 Python 코드**로, 프레임워크나 인프라 변경에 영향받지 않습니다.

## Design Philosophy

### 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **순수성** | 외부 라이브러리 import 금지 (ADK, FastAPI, aiosqlite 등) |
| **불변성** | 엔티티는 가능한 불변 (dataclass + frozen) |
| **자기 검증** | 엔티티 생성 시 유효성 검사 |
| **Port 의존** | 외부 통신은 Port 인터페이스를 통해서만 |

### 허용되는 Import

```python
# ✅ Python 표준 라이브러리만 허용
import uuid
import asyncio
import contextlib
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, AsyncIterator
from collections.abc import AsyncIterator
from urllib.parse import urlparse

# ✅ Domain 내부 모듈 참조
from src.domain.entities.enums import MessageRole
from src.domain.exceptions import ValidationError
```

### 금지되는 Import

```python
# ❌ 외부 라이브러리 금지
from google.adk import ...       # ADK
from fastapi import ...          # FastAPI
import aiosqlite                 # SQLite
from pydantic import ...         # Pydantic (validation은 자체 구현)
```

## Structure

```
domain/
├── entities/           # 도메인 엔티티
│   ├── __init__.py
│   ├── enums.py        # MessageRole, EndpointType, EndpointStatus
│   ├── agent.py        # Agent 모델
│   ├── tool.py         # Tool 모델
│   ├── tool_call.py    # ToolCall 모델
│   ├── endpoint.py     # Endpoint 모델 (MCP/A2A)
│   ├── message.py      # Message 모델
│   ├── conversation.py # Conversation 모델 (Aggregate Root)
│   └── stream_chunk.py # StreamChunk (SSE 이벤트) - Phase 4 Part A
│
├── services/           # 도메인 서비스
│   ├── __init__.py
│   ├── conversation_service.py    # 대화 처리 로직
│   ├── registry_service.py        # 엔드포인트 등록/관리
│   ├── orchestrator_service.py    # ChatPort 구현
│   └── health_monitor_service.py  # 상태 모니터링
│
├── ports/              # 포트 인터페이스 (ABC)
│   ├── __init__.py
│   ├── inbound/        # Driving Ports (외부 → 도메인)
│   │   ├── __init__.py
│   │   ├── chat_port.py        # 채팅 인터페이스
│   │   └── management_port.py  # 관리 인터페이스
│   │
│   └── outbound/       # Driven Ports (도메인 → 외부)
│       ├── __init__.py
│       ├── orchestrator_port.py  # LLM 오케스트레이터
│       ├── storage_port.py       # 저장소 (Conversation, Endpoint)
│       ├── toolset_port.py       # MCP 도구 관리
│       └── a2a_port.py           # A2A 프로토콜
│
├── constants.py        # 도메인 상수 (ErrorCode 등) - Phase 4 Part B
└── exceptions.py       # 도메인 예외
```

## Entities

### Entity 목록

| Entity | 역할 | 특징 |
|--------|------|------|
| `Agent` | LLM 에이전트 설정 | model, instruction |
| `Tool` | MCP 도구 정의 | name, input_schema, endpoint_id |
| `ToolCall` | 도구 호출 기록 | tool_name, input, output, duration_ms |
| `Endpoint` | MCP/A2A 서버 | url, type, status, health check |
| `Message` | 대화 메시지 | role, content, tool_calls |
| `Conversation` | 대화 세션 | messages[], title, Aggregate Root |
| `StreamChunk` | SSE 스트리밍 이벤트 | type (text/tool_call/tool_result/agent_transfer), frozen - Phase 4 Part A |

### Entity 패턴

```python
@dataclass
class Endpoint:
    """MCP/A2A 엔드포인트"""
    url: str
    name: str
    type: EndpointType = EndpointType.MCP
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    enabled: bool = True
    status: EndpointStatus = EndpointStatus.UNKNOWN

    def __post_init__(self) -> None:
        # 자기 검증
        self._validate_url()

    def _validate_url(self) -> None:
        parsed = urlparse(self.url)
        if not parsed.scheme or not parsed.netloc:
            raise InvalidUrlError(f"Invalid URL: {self.url}")
```

## Services

### Service 목록

| Service | 역할 | 의존 Port |
|---------|------|----------|
| `ConversationService` | 대화 처리, 메시지 저장 | StoragePort, OrchestratorPort |
| `RegistryService` | 엔드포인트 등록/해제 | StoragePort, ToolsetPort |
| `OrchestratorService` | ChatPort 구현, 위임 | ConversationService |
| `HealthMonitorService` | 주기적 상태 확인 | StoragePort, ToolsetPort |

### Service 패턴

```python
class ConversationService:
    """대화 처리 서비스"""

    def __init__(
        self,
        storage: ConversationStoragePort,  # Port 인터페이스만 의존
        orchestrator: OrchestratorPort,
    ) -> None:
        self._storage = storage
        self._orchestrator = orchestrator

    async def send_message(
        self,
        conversation_id: str | None,
        content: str,
    ) -> AsyncIterator[str]:
        # 비즈니스 로직...
        async for chunk in self._orchestrator.process_message(content, conv.id):
            yield chunk
```

## Ports

### Inbound Ports (Driving)

외부(Adapter)가 Domain 기능에 접근하기 위한 인터페이스.

| Port | 역할 | 구현체 |
|------|------|--------|
| `ChatPort` | 채팅 기능 | `OrchestratorService` |
| `ManagementPort` | 관리 기능 | `RegistryService` |

### Outbound Ports (Driven)

Domain이 외부 시스템을 사용하기 위한 인터페이스.

| Port | 역할 | 구현체 (Adapter) |
|------|------|-----------------|
| `OrchestratorPort` | LLM 호출 | `AdkOrchestratorAdapter` |
| `ConversationStoragePort` | 대화 저장 | `SqliteConversationStorage` |
| `EndpointStoragePort` | 엔드포인트 저장 | `JsonEndpointStorage` |
| `ToolsetPort` | MCP 도구 관리 | `DynamicToolset` |
| `A2aPort` | A2A 통신 | `A2aClientAdapter` |

## Constants (Phase 4 Part B)

**ErrorCode 클래스** (`src/domain/constants.py`):

Backend ↔ Extension 타입 안전성 보장을 위한 에러 코드 상수.

```python
class ErrorCode:
    """에러 코드 상수 (Backend ↔ Extension 일치)"""
    LLM_RATE_LIMIT = "LlmRateLimitError"
    LLM_AUTHENTICATION = "LlmAuthenticationError"
    ENDPOINT_CONNECTION = "EndpointConnectionError"
    ENDPOINT_TIMEOUT = "EndpointTimeoutError"
    ENDPOINT_NOT_FOUND = "EndpointNotFoundError"
    TOOL_NOT_FOUND = "ToolNotFoundError"
    CONVERSATION_NOT_FOUND = "ConversationNotFoundError"
    INVALID_URL = "InvalidUrlError"
    UNKNOWN = "UnknownError"
```

Extension 측 대응: `extension/lib/constants.ts` (ErrorCode enum)

## Exceptions

```python
# 예외 계층
DomainException (base)
├── EndpointNotFoundError
├── EndpointConnectionError
├── EndpointTimeoutError
├── ToolNotFoundError
├── ToolExecutionError
├── ConversationNotFoundError
├── InvalidUrlError
├── LlmRateLimitError
└── LlmAuthenticationError
```

각 예외는 `ErrorCode` 상수를 code 필드로 사용합니다 (Phase 4 Part B).

## Testing

Domain Layer는 **Fake Adapter**로 테스트합니다:

```python
from tests.unit.fakes.fake_storage import FakeConversationStorage
from tests.unit.fakes.fake_orchestrator import FakeOrchestrator

def test_conversation_service():
    # Fake Adapter 사용 (실제 DB, LLM 없이)
    storage = FakeConversationStorage()
    orchestrator = FakeOrchestrator(responses=["Hello!"])

    service = ConversationService(storage=storage, orchestrator=orchestrator)
    # 테스트 수행...
```

## References

- [docs/architecture.md](../../docs/architecture.md) - 헥사고날 아키텍처 전체 설계
- [docs/implementation-guide.md](../../docs/implementation-guide.md) - 구현 패턴 상세
- [tests/unit/fakes/](../../tests/unit/fakes/) - Fake Adapter 구현
