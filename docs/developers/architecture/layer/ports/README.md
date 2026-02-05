# Ports Layer

헥사고날 아키텍처의 Ports 레이어 설계 문서입니다.

---

## Port 개념

Port는 Domain과 외부 세계 사이의 **인터페이스(계약)**입니다.

```
외부 세계                    Domain                    외부 세계
    │                          │                          │
    │    ┌────────────────┐    │    ┌────────────────┐    │
    │    │  Inbound Port  │    │    │ Outbound Port  │    │
    ├───▶│   (진입점)      │───▶│───▶│   (의존성)      │───▶│
    │    └────────────────┘    │    └────────────────┘    │
    │                          │                          │
  HTTP                    비즈니스                    Database
  gRPC                    로직                       LLM
  CLI                                               MCP
```

---

## Inbound Ports

외부에서 Domain으로 들어오는 요청을 정의합니다.

### ChatPort

채팅 요청 처리 인터페이스:

```python
class ChatPort(ABC):
    @abstractmethod
    async def chat_stream(
        self,
        conversation_id: str,
        message: str,
    ) -> AsyncIterator[StreamChunk]:
        """채팅 스트리밍 응답"""
        pass
```

### ManagementPort

관리 API 인터페이스:

```python
class ManagementPort(ABC):
    @abstractmethod
    async def register_endpoint(
        self,
        url: str,
        endpoint_type: EndpointType,
    ) -> Endpoint:
        """MCP/A2A 엔드포인트 등록"""
        pass

    @abstractmethod
    async def unregister_endpoint(self, url: str) -> None:
        """엔드포인트 해제"""
        pass

    @abstractmethod
    async def list_endpoints(self) -> list[Endpoint]:
        """등록된 엔드포인트 목록"""
        pass
```

### Inbound Port 목록

| Port | 설명 | 파일 |
|------|------|------|
| **ChatPort** | 채팅 요청 처리 | `chat_port.py` |
| **ManagementPort** | 엔드포인트 관리 | `management_port.py` |

---

## Outbound Ports

Domain에서 외부 시스템으로 나가는 의존성을 정의합니다.

### OrchestratorPort

LLM 오케스트레이션 인터페이스:

```python
class OrchestratorPort(ABC):
    @abstractmethod
    async def run(
        self,
        conversation: Conversation,
    ) -> AsyncIterator[StreamChunk]:
        """LLM 실행 및 스트리밍 응답"""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """초기화 (비동기)"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """리소스 정리"""
        pass
```

### StoragePort

데이터 저장 인터페이스:

```python
class StoragePort(ABC):
    @abstractmethod
    async def save_conversation(self, conversation: Conversation) -> None:
        """대화 저장"""
        pass

    @abstractmethod
    async def get_conversation(self, id: str) -> Optional[Conversation]:
        """대화 조회"""
        pass

    @abstractmethod
    async def list_conversations(self) -> list[Conversation]:
        """대화 목록"""
        pass

    @abstractmethod
    async def delete_conversation(self, id: str) -> None:
        """대화 삭제"""
        pass
```

### ToolsetPort

도구 관리 인터페이스:

```python
class ToolsetPort(ABC):
    @abstractmethod
    async def add_mcp_server(self, url: str, auth: Optional[AuthConfig]) -> list[Tool]:
        """MCP 서버 추가, 도구 목록 반환"""
        pass

    @abstractmethod
    async def remove_mcp_server(self, url: str) -> None:
        """MCP 서버 제거"""
        pass

    @abstractmethod
    def get_tools(self) -> list[Tool]:
        """현재 사용 가능한 도구 목록"""
        pass
```

### A2APort

A2A 클라이언트 인터페이스:

```python
class A2APort(ABC):
    @abstractmethod
    async def get_agent_card(self, url: str) -> AgentCard:
        """에이전트 카드 조회"""
        pass

    @abstractmethod
    async def send_task(
        self,
        url: str,
        message: str,
    ) -> AsyncIterator[StreamChunk]:
        """태스크 전송"""
        pass
```

### OAuthPort

OAuth 인증 인터페이스:

```python
class OAuthPort(ABC):
    @abstractmethod
    async def get_authorization_url(
        self,
        endpoint_url: str,
    ) -> str:
        """인증 URL 생성"""
        pass

    @abstractmethod
    async def exchange_code(
        self,
        endpoint_url: str,
        code: str,
    ) -> TokenResponse:
        """인가 코드 교환"""
        pass

    @abstractmethod
    async def refresh_token(
        self,
        endpoint_url: str,
    ) -> TokenResponse:
        """토큰 갱신"""
        pass
```

### UsagePort

사용량 저장 인터페이스:

```python
class UsagePort(ABC):
    @abstractmethod
    async def save_usage(self, usage: Usage) -> None:
        """사용량 저장"""
        pass

    @abstractmethod
    async def get_usage_summary(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> UsageSummary:
        """사용량 요약 조회"""
        pass
```

### Outbound Port 목록

| Port | 설명 | 파일 |
|------|------|------|
| **OrchestratorPort** | LLM 오케스트레이션 | `orchestrator_port.py` |
| **StoragePort** | 데이터 저장 | `storage_port.py` |
| **ToolsetPort** | 도구 관리 | `toolset_port.py` |
| **A2APort** | A2A 클라이언트 | `a2a_port.py` |
| **OAuthPort** | OAuth 인증 | `oauth_port.py` |
| **UsagePort** | 사용량 저장 | `usage_port.py` |

---

## Port 설계 원칙

### 1. 추상 클래스 사용

```python
from abc import ABC, abstractmethod

class SomePort(ABC):
    @abstractmethod
    async def operation(self) -> Result:
        pass
```

### 2. Domain 타입만 사용

```python
# Good: Domain Entity 사용
async def save(self, conversation: Conversation) -> None: ...

# Bad: 외부 타입 사용
async def save(self, data: SQLAlchemyModel) -> None: ...  # ❌
```

### 3. 비동기 우선

```python
# 대부분의 Port 메서드는 async
async def get(self, id: str) -> Entity: ...
```

### 4. 명확한 계약

```python
# 반환 타입, 예외 명시
async def get(self, id: str) -> Optional[Entity]:
    """
    Returns:
        Entity if found, None otherwise
    Raises:
        StorageError: on connection failure
    """
    pass
```

---

## Port 네이밍 컨벤션

| 접미사 | 용도 | 예시 |
|--------|------|------|
| **Port** | 일반적인 Port | `StoragePort` |
| **Port** | Inbound/Outbound 구분 | `ChatPort`, `OrchestratorPort` |

### 파일 구조

```
src/domain/ports/
├── __init__.py
├── inbound/
│   ├── __init__.py
│   ├── chat_port.py
│   └── management_port.py
└── outbound/
    ├── __init__.py
    ├── orchestrator_port.py
    ├── storage_port.py
    ├── toolset_port.py
    ├── a2a_port.py
    ├── oauth_port.py
    └── usage_port.py
```

---

## Dependency Rule

```
┌─────────────────────────────────────────────┐
│               Adapters                       │
│  (FastAPI, ADK, SQLite, MCP Client)         │
└───────────────────┬─────────────────────────┘
                    │ implements
                    ↓
┌─────────────────────────────────────────────┐
│                 Ports                        │
│          (Abstract Interfaces)               │
└───────────────────┬─────────────────────────┘
                    │ uses
                    ↓
┌─────────────────────────────────────────────┐
│             Domain Core                      │
│         (Entities, Services)                 │
└─────────────────────────────────────────────┘
```

**규칙:** 안쪽 레이어는 바깥 레이어를 알지 못함

- Domain Core는 Ports만 알고 있음
- Ports는 Domain Core만 알고 있음
- Adapters는 Ports와 Domain Core를 알고 있음

---

*Last Updated: 2026-02-05*
