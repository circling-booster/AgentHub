# Domain Core Layer

헥사고날 아키텍처의 Domain Core 레이어 설계 문서입니다.

---

## Layer Position

```
        ┌─────────────────────────────┐
        │      Inbound Adapters       │
        └──────────────┬──────────────┘
                       ↓
        ┌─────────────────────────────┐
        │       Inbound Ports         │
        └──────────────┬──────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│                   DOMAIN CORE                        │  ◀── 이 문서
│  ┌───────────────────────────────────────────────┐  │
│  │                 Services                       │  │
│  │     OrchestratorService, ConversationService   │  │
│  └───────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────┐  │
│  │                 Entities                       │  │
│  │   Conversation, Message, Agent, Tool, etc.    │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                       ↓
        ┌─────────────────────────────┐
        │       Outbound Ports        │
        └──────────────┬──────────────┘
                       ↓
        ┌─────────────────────────────┐
        │      Outbound Adapters      │
        └─────────────────────────────┘
```

---

## Core Principle: 순수 Python

Domain Core는 **외부 라이브러리 import 금지**입니다.

### 허용

```python
# 표준 라이브러리
from dataclasses import dataclass, field
from typing import Optional, AsyncIterator
from abc import ABC, abstractmethod
from enum import Enum
from uuid import uuid4
from datetime import datetime
```

### 금지

```python
# 외부 라이브러리 (헥사고날 위반)
from google.adk import Agent          # ❌
from fastapi import HTTPException     # ❌
from sqlalchemy import Column         # ❌
from pydantic import BaseModel        # ❌ (Domain에서)
```

---

## Entities

### 설계 원칙

| 원칙 | 설명 |
|------|------|
| **@dataclass** | 불변 데이터 구조 (`frozen=True` 권장) |
| **순수 Python** | 외부 의존성 없음 |
| **Self-contained** | 자체 검증 로직 포함 가능 |
| **ID 생성** | `field(default_factory=...)` 사용 |

### Entity 구조

```python
@dataclass
class Entity:
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
```

### 주요 Entities

| Entity | 역할 | 특징 |
|--------|------|------|
| **Conversation** | 대화 세션 | Aggregate Root, 메시지 관리 |
| **Message** | 개별 메시지 | role, content 포함 |
| **Agent** | 에이전트 정보 | name, description |
| **Tool** | 도구 정보 | name, parameters |
| **Endpoint** | MCP/A2A 엔드포인트 | url, type, status, fallback_url |
| **StreamChunk** | SSE 청크 | event_type, content |
| **ToolCall** | 도구 호출 기록 | tool_name, arguments, result |
| **AuthConfig** | OAuth 설정 | client_id, scopes |
| **CircuitBreaker** | 서킷 브레이커 | state, failure_threshold, recovery_timeout |
| **Usage** | LLM 사용량 | model, tokens, cost_usd |
| **BudgetStatus** | 예산 상태 | alert_level, can_proceed |
| **Workflow** | 멀티스텝 워크플로우 | steps, workflow_type |
| **WorkflowStep** | 워크플로우 단계 | agent_endpoint_id, output_key |
| **Resource** | MCP 리소스 메타데이터 | uri, name, description |
| **ResourceContent** | MCP 리소스 콘텐츠 | text, blob, mime_type |
| **PromptTemplate** | MCP 프롬프트 템플릿 | name, arguments |
| **PromptArgument** | 프롬프트 인자 | name, required, description |
| **SamplingRequest** | MCP HITL Sampling 요청 | messages, status, llm_result |
| **ElicitationRequest** | MCP HITL Elicitation 요청 | message, action, content |

### Entity Details (Phase 6)

#### CircuitBreaker

Circuit Breaker 패턴 엔티티:

```python
@dataclass
class CircuitBreaker:
    failure_threshold: int = 5        # 연속 실패 임계값
    recovery_timeout: float = 60.0    # 복구 대기 시간 (초)

    _state: CircuitState              # CLOSED | OPEN | HALF_OPEN
    _failure_count: int               # 현재 실패 횟수
    _last_failure_time: float         # 마지막 실패 시간

    def can_execute(self) -> bool     # 실행 가능 여부
    def record_success() -> None      # 성공 기록
    def record_failure() -> None      # 실패 기록
```

**상태 전이:** `src/domain/entities/circuit_breaker.py`

#### Usage

LLM 호출 사용량 엔티티:

```python
@dataclass
class Usage:
    model: str               # LLM 모델명 (예: "openai/gpt-4o-mini")
    prompt_tokens: int       # 입력 토큰 수
    completion_tokens: int   # 출력 토큰 수
    total_tokens: int        # 총 토큰 수 (검증: prompt + completion)
    cost_usd: float          # 비용 (USD, 음수 불가)
    created_at: datetime     # 생성 시간
```

**검증 로직:** `__post_init__`에서 토큰 수, 비용 음수 검증 및 total_tokens 일치 검증

#### BudgetStatus

예산 상태 엔티티:

```python
@dataclass
class BudgetStatus:
    monthly_budget: float     # 월 예산 (USD)
    current_spending: float   # 현재 지출 (USD)
    usage_percentage: float   # 사용률 (%)
    alert_level: str          # "safe" | "warning" | "critical" | "blocked"
    can_proceed: bool         # API 호출 허용 여부

    def get_alert_message() -> str  # 경고 메시지 생성
```

| alert_level | usage_percentage | can_proceed |
|-------------|------------------|-------------|
| `safe` | < 90% | ✅ |
| `warning` | 90-100% | ✅ |
| `critical` | 100-110% | ⚠️ |
| `blocked` | > 110% | ❌ |

#### SDK Track Entities (Plan 07)

SDK Track (Resources, Prompts, Sampling, Elicitation) 엔티티:

**Resource & ResourceContent**

```python
@dataclass(frozen=True, slots=True)
class Resource:
    uri: str              # 리소스 URI (file://, http://, custom://)
    name: str             # 리소스 이름
    description: str = "" # 리소스 설명
    mime_type: str = ""   # MIME 타입

@dataclass(frozen=True, slots=True)
class ResourceContent:
    uri: str                   # 리소스 URI
    text: str | None = None    # 텍스트 콘텐츠 (text 리소스)
    blob: bytes | None = None  # 바이너리 콘텐츠 (blob 리소스)
    mime_type: str = ""        # MIME 타입
```

**PromptTemplate & PromptArgument**

```python
@dataclass(frozen=True, slots=True)
class PromptArgument:
    name: str                 # 인자 이름
    required: bool = True     # 필수 여부
    description: str = ""     # 인자 설명

@dataclass(frozen=True, slots=True)
class PromptTemplate:
    name: str                                      # 템플릿 이름
    description: str = ""                          # 템플릿 설명
    arguments: list[PromptArgument] = field(...)   # 인자 목록
```

**HITL Entities (SamplingRequest & ElicitationRequest)**

HITL (Human-in-the-Loop) 패턴을 사용하는 엔티티입니다:

```python
@dataclass
class SamplingRequest:
    id: str                           # 요청 ID
    endpoint_id: str                  # MCP 엔드포인트 ID
    messages: list[dict]              # LLM 메시지 목록
    status: SamplingStatus            # PENDING | APPROVED | REJECTED | TIMED_OUT
    llm_result: dict | None = None    # LLM 응답 결과
    created_at: datetime = field(...)  # 생성 시각 (UTC, timezone-aware)

@dataclass
class ElicitationRequest:
    id: str                              # 요청 ID
    endpoint_id: str                     # MCP 엔드포인트 ID
    message: str                         # 사용자 메시지
    requested_schema: dict               # JSON Schema
    action: ElicitationAction | None     # ACCEPT | DECLINE | CANCEL
    content: dict | None = None          # 사용자 입력
    status: ElicitationStatus            # PENDING | ACCEPTED | DECLINED | ...
    created_at: datetime = field(...)    # 생성 시각 (UTC)
```

**HITL 특징:**
- **Timezone-aware datetime**: `datetime.now(timezone.utc)` 사용
- **State Machine**: Status Enum으로 상태 관리
- **Phase 3 Service에서 Signal 패턴**: asyncio.Event로 비동기 대기 구현 예정

---

## Aggregate Root Pattern

**Conversation**이 Aggregate Root 역할 수행:

```python
@dataclass
class Conversation:
    id: str
    messages: list[Message] = field(default_factory=list)

    def add_message(self, message: Message) -> None:
        """메시지 추가 (일관성 보장)"""
        self.messages.append(message)

    def get_last_message(self) -> Optional[Message]:
        """마지막 메시지 조회"""
        return self.messages[-1] if self.messages else None
```

### Aggregate 규칙

| 규칙 | 설명 |
|------|------|
| **단일 진입점** | Conversation을 통해서만 Message 접근 |
| **트랜잭션 경계** | Conversation 단위로 저장 |
| **일관성 보장** | 내부 상태 변경은 메서드 통해서만 |

---

## Services

### 설계 원칙

| 원칙 | 설명 |
|------|------|
| **Port 의존성** | 구체 구현 대신 Port 인터페이스 주입 |
| **비즈니스 로직** | Entity 조합, 워크플로우 조율 |
| **Stateless** | 상태는 Entity나 Storage에 위임 |

### Service 구조

```python
class DomainService:
    def __init__(
        self,
        storage_port: StoragePort,
        orchestrator_port: OrchestratorPort,
    ):
        self._storage = storage_port
        self._orchestrator = orchestrator_port

    async def execute(self, input: Input) -> Output:
        # Port를 통한 외부 시스템 접근
        data = await self._storage.load(input.id)
        result = await self._orchestrator.process(data)
        await self._storage.save(result)
        return result
```

### 주요 Services

| Service | 역할 |
|---------|------|
| **OrchestratorService** | LLM 오케스트레이션, 도구 실행 조율 |
| **ConversationService** | 대화 관리, 메시지 저장/조회 |
| **RegistryService** | MCP/A2A 엔드포인트 등록 관리 |
| **OAuthService** | OAuth 인증 흐름 처리 |
| **GatewayService** | Circuit Breaker, 재시도 로직 |
| **CostService** | 비용 계산 |
| **HealthMonitorService** | 엔드포인트 상태 모니터링 |

---

## Exceptions

Domain 예외도 순수 Python으로 정의:

```python
class DomainException(Exception):
    """Domain 기본 예외"""
    pass

class ConversationNotFoundError(DomainException):
    """대화를 찾을 수 없음"""
    pass

class ToolExecutionError(DomainException):
    """도구 실행 실패"""
    pass
```

### 예외 계층

```
DomainException
├── ConversationNotFoundError
├── EndpointNotFoundError
├── ToolExecutionError
├── AuthenticationError
└── ValidationError
```

---

## Constants

도메인 상수 정의:

```python
# src/domain/constants.py
MAX_ACTIVE_TOOLS = 100
DEFAULT_RETRY_COUNT = 3
CIRCUIT_BREAKER_THRESHOLD = 5
```

---

## Enums

상태, 타입 열거형:

```python
class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class EndpointType(Enum):
    MCP = "mcp"
    A2A = "a2a"

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"
```

---

## Directory Structure

```
src/domain/
├── __init__.py
├── constants.py          # 도메인 상수
├── exceptions.py         # 도메인 예외
├── entities/
│   ├── __init__.py
│   ├── enums.py                   # 열거형
│   ├── conversation.py
│   ├── message.py
│   ├── agent.py
│   ├── tool.py
│   ├── endpoint.py
│   ├── stream_chunk.py
│   ├── tool_call.py
│   ├── auth_config.py
│   ├── circuit_breaker.py
│   ├── usage.py
│   ├── resource.py                # SDK Track: Resource, ResourceContent
│   ├── prompt_template.py         # SDK Track: PromptTemplate, PromptArgument
│   ├── sampling_request.py        # SDK Track: SamplingRequest (HITL)
│   └── elicitation_request.py     # SDK Track: ElicitationRequest (HITL)
├── services/
│   ├── __init__.py
│   ├── orchestrator_service.py
│   ├── conversation_service.py
│   ├── registry_service.py
│   ├── oauth_service.py
│   ├── gateway_service.py
│   ├── cost_service.py
│   └── health_monitor_service.py
└── ports/
    ├── __init__.py
    ├── inbound/
    └── outbound/
```

---

*Last Updated: 2026-02-05*
