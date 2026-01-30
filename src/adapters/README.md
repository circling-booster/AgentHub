# Adapters Layer

> 외부 시스템과의 연동 인터페이스 구현 (헥사고날 아키텍처)

## 개요

Adapters Layer는 도메인 로직(Domain Layer)과 외부 시스템(MCP, ADK, FastAPI, SQLite 등) 사이의 **번역기** 역할을 수행합니다.

**핵심 원칙:**
- Domain이 외부를 모름 (의존성 역전)
- Port 인터페이스를 구현하여 도메인과 연결
- 외부 기술 스택 변경 시 Adapter만 교체

---

## 구조

```
adapters/
├── inbound/         # Primary Adapters (외부 → 도메인)
│   ├── http/        # FastAPI HTTP API + SSE
│   └── a2a/         # A2A Server (AgentHub를 A2A 프로토콜로 노출)
│
└── outbound/        # Secondary Adapters (도메인 → 외부)
    ├── adk/         # Google ADK (LlmAgent, DynamicToolset)
    ├── a2a/         # A2A Client (원격 A2A 에이전트 호출)
    └── storage/     # 저장소 (JSON, SQLite)
```

---

## Inbound Adapters (Primary)

### HTTP API ([src/adapters/inbound/http](inbound/http/))

**역할:** FastAPI 기반 REST API + SSE 스트리밍

**주요 구성:**
- `app.py`: FastAPI 앱 팩토리, Lifespan 관리
- `routes/`: API 라우트 (chat, mcp, auth, health)
- `schemas/`: Pydantic 요청/응답 스키마
- `security.py`: Token Handshake 미들웨어
- `exceptions.py`: Domain Exception → HTTP 응답 변환

**API 엔드포인트:**

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/health` | GET | 헬스체크 |
| `/auth/token` | POST | Extension 토큰 교환 |
| `/api/chat/stream` | POST | SSE 스트리밍 채팅 |
| `/api/mcp/servers` | GET/POST/DELETE | MCP 서버 관리 |
| `/api/mcp/servers/{id}/tools` | GET | MCP 서버 도구 조회 |
| `/api/a2a/agents` | GET/POST/DELETE | A2A 에이전트 관리 |
| `/api/a2a/agents/{id}/card` | GET | Agent Card 조회 |
| `/.well-known/agent.json` | GET | AgentHub Agent Card |

### A2A Server ([src/adapters/inbound/a2a](inbound/a2a/))

**역할:** AgentHub의 LlmAgent를 A2A 프로토콜로 노출 (다른 에이전트가 호출 가능)

**구현:** ADK `to_a2a()` 유틸리티 사용

**주요 파일:**
- `a2a_server.py`: to_a2a() 래퍼, Agent Card 생성

**Agent Card 예시:**
```json
{
  "agentId": "agenthub-agent",
  "name": "AgentHub",
  "description": "Local agent gateway with MCP tools",
  "version": "0.1.0",
  "skills": [],
  "api": {
    "protocol": "a2a",
    "endpoint": "http://localhost:8000"
  }
}
```

**참조:**
- [Google ADK A2A Utils](https://google.github.io/adk-docs/a2a/utils/)
- [A2A Protocol Specification](https://a2a-protocol.org/)

---

## Outbound Adapters (Secondary)

### ADK Adapters ([src/adapters/outbound/adk](outbound/adk/))

**역할:** Google ADK를 사용한 LLM 오케스트레이션 및 MCP 도구 통합

#### DynamicToolset ([dynamic_toolset.py](outbound/adk/dynamic_toolset.py))

**구현:** `BaseToolset` (ADK) + `ToolsetPort` (Domain)

**특징:**
- MCP 서버 동적 등록/해제
- Streamable HTTP 우선, SSE fallback
- TTL 기반 캐싱 (기본 5분)
- Context Explosion 방지 (MAX_ACTIVE_TOOLS=30)

**주요 메서드:**
- `get_tools(readonly_context) -> list[BaseTool]` — ADK Agent가 매 turn마다 호출
- `add_mcp_server(endpoint) -> list[Tool]` — MCP 서버 등록
- `remove_mcp_server(endpoint_id) -> bool` — MCP 서버 해제
- `call_tool(tool_name, arguments) -> Any` — 도구 직접 실행

#### AdkOrchestratorAdapter ([orchestrator_adapter.py](outbound/adk/orchestrator_adapter.py))

**구현:** `OrchestratorPort` (Domain)

**특징:**
- Async Factory Pattern (FastAPI lifespan에서 초기화)
- LlmAgent + DynamicToolset 통합
- 텍스트 스트리밍 응답 (AsyncIterator[str])
- Lazy initialization 지원

**주요 메서드:**
- `initialize() -> None` — Async Factory 초기화
- `process_message(message, conversation_id) -> AsyncIterator[str]` — 메시지 처리
- `add_a2a_agent(endpoint_id, agent_card_url) -> None` — A2A sub-agent 추가 (Phase 3)
- `remove_a2a_agent(endpoint_id) -> None` — A2A sub-agent 제거
- `close() -> None` — 리소스 정리

### A2A Client Adapter ([src/adapters/outbound/a2a](outbound/a2a/))

**역할:** 원격 A2A 에이전트와 통신 (ADK `RemoteA2aAgent` 기반)

**구현:** `A2aPort` (Domain)

**주요 파일:**
- `a2a_client_adapter.py`: A2aPort 구현

**특징:**
- ADK `RemoteA2aAgent` 사용
- Agent Card 교환 및 검증
- LlmAgent의 `sub_agents`로만 추가 가능 (직접 호출 불가)

**주요 메서드:**
- `register_agent(endpoint) -> dict` — Agent Card 교환
- `unregister_agent(endpoint_id) -> None` — 에이전트 등록 해제
- `health_check(endpoint_id) -> bool` — 상태 확인

**제약:**
- `RemoteA2aAgent`는 `LlmAgent.sub_agents`로만 동작
- 직접 `call_agent()` 불가, Orchestrator에 추가 후 LLM이 자동 호출

**참조:**
- [Google ADK RemoteA2aAgent](https://google.github.io/adk-docs/a2a/remote-a2a-agent/)

### Storage Adapters ([src/adapters/outbound/storage](outbound/storage/))

**역할:** 엔드포인트 및 대화 이력 영속화

#### JsonEndpointStorage ([json_endpoint_storage.py](outbound/storage/json_endpoint_storage.py))

**구현:** `EndpointStoragePort` (Domain)

**특징:**
- JSON 파일 기반 엔드포인트 저장 (MCP + A2A)
- 비동기 파일 I/O (aiofiles)
- 읽기/쓰기 Lock (asyncio.Lock)
- `agent_card` 필드 지원 (Phase 3)

#### SqliteConversationStorage ([sqlite_conversation_storage.py](outbound/storage/sqlite_conversation_storage.py))

**구현:** `ConversationStoragePort` (Domain)

**특징:**
- SQLite WAL 모드 (동시 읽기/쓰기)
- 비동기 쿼리 (aiosqlite)
- 쓰기 직렬화 (asyncio.Lock)
- 자동 테이블 생성 (lifespan에서 initialize())

**스키마:**
- `conversations`: id, title, created_at, updated_at
- `messages`: id, conversation_id, role, content, created_at
- `tool_calls`: id, message_id, tool_name, input, output, duration_ms

---

## 의존성 주입

Adapters는 `dependency-injector` 컨테이너를 통해 주입됩니다.

**Container 구성:** ([src/config/container.py](../config/container.py))
- **Singleton**: Settings, Storage Adapters, DynamicToolset, AdkOrchestratorAdapter, A2aClientAdapter
- **Factory**: Domain Services (ConversationService, OrchestratorService, RegistryService)

**FastAPI 통합:**
```python
from dependency_injector.wiring import inject, Provide

@router.post("/api/chat/stream")
@inject
async def chat_stream(
    orchestrator: OrchestratorService = Depends(Provide[Container.orchestrator_service]),
):
    ...
```

---

## 보안

### Token Handshake (Drive-by RCE 방지)

**문제:** localhost API가 악성 웹사이트의 JavaScript 호출에 노출될 위험

**해결:**
1. 서버 시작 시 난수 토큰 생성 (`ExtensionAuthMiddleware`)
2. Extension 초기화 시 `/auth/token`으로 토큰 교환
3. 모든 `/api/*` 요청에 `X-Extension-Token` 헤더 필수

**참조:** [docs/implementation-guide.md#9-보안-패턴](../docs/implementation-guide.md#9-보안-패턴)

---

## 테스트 전략

| 테스트 유형 | 범위 | Fake Adapter |
|-----------|------|--------------|
| **Unit** | Domain Services | Fake Adapter 사용 |
| **Integration** | Adapters + External | 실제 구현 (TestClient, 로컬 MCP 서버) |

**Integration Test Fixtures:**
- `authenticated_client`: 인증된 TestClient (공통 fixture)
- `temp_data_dir`: 임시 데이터 디렉토리
- `a2a_echo_agent`: A2A 테스트 에이전트 (`http://127.0.0.1:9001`, session scope)

**참조:**
- [tests/integration/adapters/conftest.py](../../tests/integration/adapters/conftest.py)
- [tests/conftest.py](../../tests/conftest.py) (A2A fixture)

---

## 참고 문서

- [docs/architecture.md](../docs/architecture.md) — 헥사고날 아키텍처 설계
- [docs/implementation-guide.md](../docs/implementation-guide.md) — 구현 패턴 및 코드 예시
- [src/domain/README.md](../domain/README.md) — Domain Layer 설계 철학

---

*문서 생성일: 2026-01-29*
*A2A 섹션 추가: 2026-01-30*
