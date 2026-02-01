# AgentHub Backend (src/)

> 헥사고날 아키텍처 기반 Python 백엔드

## Purpose

AgentHub API 서버의 핵심 비즈니스 로직과 외부 시스템 연동을 담당합니다.

## Structure

```
src/
├── domain/           # 핵심 비즈니스 로직 (순수 Python)
│   ├── entities/     # 도메인 엔티티 (Agent, Tool, Endpoint, Conversation)
│   ├── services/     # 도메인 서비스 (Orchestrator, Registry, Conversation)
│   ├── ports/        # 포트 인터페이스 (Inbound/Outbound)
│   └── exceptions.py # 도메인 예외
│
├── adapters/         # 외부 시스템 연동
│   ├── inbound/      # Driving Adapters (FastAPI HTTP, A2A Server)
│   └── outbound/     # Driven Adapters (ADK, Storage, A2A Client)
│
└── config/           # 설정 및 의존성 주입
    ├── settings.py   # pydantic-settings 기반 설정
    └── container.py  # DI 컨테이너
```

## Hexagonal Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Adapters (외부)                         │
│   ┌─────────────────┐           ┌─────────────────────┐     │
│   │ Inbound Adapters│           │  Outbound Adapters  │     │
│   │ - FastAPI HTTP  │           │  - ADK Orchestrator │     │
│   │ - A2A Server    │           │  - SQLite Storage   │     │
│   └────────┬────────┘           └──────────▲──────────┘     │
│            │                               │                 │
│   ┌────────▼───────────────────────────────┴────────┐       │
│   │                    Ports                         │       │
│   │   Inbound: ChatPort, ManagementPort             │       │
│   │   Outbound: OrchestratorPort, StoragePort, ...  │       │
│   └────────┬───────────────────────────────▲────────┘       │
│            │                               │                 │
│   ┌────────▼───────────────────────────────┴────────┐       │
│   │              Domain (순수 Python)                │       │
│   │   - Entities: Agent, Tool, Endpoint, ...        │       │
│   │   - Services: ConversationService, ...          │       │
│   │   - 외부 라이브러리 import 금지                   │       │
│   └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## Key Principles

| 원칙 | 설명 |
|------|------|
| **의존성 역전** | Domain이 외부를 모름. Adapter가 Domain에 의존 |
| **Port 추상화** | ABC 인터페이스로 외부 시스템과 통신 |
| **Domain 순수성** | 외부 라이브러리(ADK, FastAPI 등) import 금지 |

## Security (Phase 1.5)

**Zero-Trust localhost API 보안**으로 Drive-by RCE 공격 차단.

### 위협 모델

| 위협 | 설명 | 완화 |
|------|------|------|
| **Drive-by RCE** | 악성 웹사이트가 `fetch('http://localhost:8000/api/...')` 호출 | Token Handshake |
| **CORS Bypass** | 웹 페이지에서 localhost API 접근 | Origin 제한 |
| **Token Spoofing** | 토큰 없이 API 우회 | Middleware 검증 |

### 보안 컴포넌트

```
┌─────────────────────────────────────────────────────────────┐
│  Chrome Extension                                            │
│    1. 서버에 /auth/token 요청 (Origin: chrome-extension://) │
│    2. 토큰 수신 후 chrome.storage.session에 저장             │
│    3. 모든 /api/* 요청에 X-Extension-Token 헤더 포함         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  AgentHub API Server                                         │
│                                                              │
│  1. CORSMiddleware                                           │
│     - allow_origin_regex: ^chrome-extension://[a-zA-Z0-9_-]+$│
│     - 웹 Origin (https://evil.com) 차단                      │
│                                                              │
│  2. ExtensionAuthMiddleware                                  │
│     - /api/* 요청에 X-Extension-Token 검증                   │
│     - 토큰 불일치 시 403 Forbidden                           │
│                                                              │
│  3. TokenProvider                                            │
│     - secrets.token_urlsafe(32)로 암호학적 토큰 생성         │
│     - 서버 세션당 1개 토큰 유지                              │
└─────────────────────────────────────────────────────────────┘
```

### 주요 파일

| 파일 | 역할 |
|------|------|
| `adapters/inbound/http/security.py` | TokenProvider, ExtensionAuthMiddleware |
| `adapters/inbound/http/routes/auth.py` | POST /auth/token (Origin 검증) |
| `adapters/inbound/http/app.py` | CORS 설정, Middleware 순서 |

### 공개 엔드포인트 (토큰 불필요)

- `/health` - 서버 상태 확인
- `/auth/token` - 토큰 교환 (Origin 검증)
- `/docs`, `/redoc`, `/openapi.json` - API 문서

참조: [docs/implementation-guide.md#9-보안-패턴](../docs/implementation-guide.md#9-보안-패턴)

## MCP Integration (Phase 2)

**Model Context Protocol (MCP)** 서버를 동적으로 연결하여 100+ 외부 도구를 LLM에 통합합니다.

### Architecture

```
┌─────────────────────────────────────────────────┐
│         LlmAgent (Google ADK)                    │
│   - model: LiteLlm                              │
│   - tools: [DynamicToolset]                     │
└──────────────────┬──────────────────────────────┘
                   │ get_tools() (매 turn)
      ┌────────────▼────────────┐
      │    DynamicToolset       │
      │  (BaseToolset 상속)      │
      │  - TTL 캐싱 (5분)        │
      │  - MAX_ACTIVE_TOOLS=30  │
      └────────────┬────────────┘
                   │
    ┌──────────────┴──────────────┐
    │         MCPToolset           │
    │  - Streamable HTTP (우선)    │
    │  - SSE (fallback)           │
    └──────────────┬──────────────┘
                   │
    ┌──────────────▼──────────────┐
    │      MCP Servers             │
    │  (외부 도구 제공)             │
    └──────────────────────────────┘
```

### API Endpoints

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/mcp/servers` | GET | 등록된 MCP 서버 목록 |
| `/api/mcp/servers` | POST | MCP 서버 등록 |
| `/api/mcp/servers/{id}` | DELETE | MCP 서버 해제 |
| `/api/mcp/servers/{id}/tools` | GET | 서버 도구 조회 |
| `/api/chat/stream` | POST | SSE 스트리밍 채팅 |

### Context Explosion 방지

| 제약 | 값 | 이유 |
|------|-----|------|
| `MAX_ACTIVE_TOOLS` | 30 | 컨텍스트 윈도우 초과 방지 |
| `TOOL_TOKEN_WARNING_THRESHOLD` | 10000 | 토큰 비용 폭탄 방지 |
| `cache_ttl_seconds` | 300 | MCP 서버 조회 최소화 |

### 주요 파일

| 파일 | 역할 |
|------|------|
| `adapters/outbound/adk/dynamic_toolset.py` | BaseToolset + MCP 동적 관리 |
| `adapters/outbound/adk/orchestrator_adapter.py` | LlmAgent + Streaming |
| `adapters/inbound/http/routes/mcp.py` | MCP 서버 CRUD API |
| `adapters/inbound/http/routes/chat.py` | SSE 채팅 스트리밍 |

참조: [src/adapters/README.md](adapters/README.md#adk-adapters), [docs/implementation-guide.md#2-dynamictoolset-구현](../docs/implementation-guide.md#2-dynamictoolset-구현)

## Phase 4 Part A-D: Advanced Features (2026-01-31)

### StreamChunk SSE 이벤트 확장 (Part A)

**역할:** SSE 스트리밍 이벤트 타입 확장으로 도구 호출 및 에이전트 전환 가시성 확보

**핵심 이벤트:**
- `text`: 일반 텍스트 스트리밍
- `tool_call`: 도구 호출 시작 (name, arguments)
- `tool_result`: 도구 실행 결과
- `agent_transfer`: A2A 에이전트 전환

**주요 파일:**
- `src/domain/entities/stream_chunk.py`: StreamChunk 엔티티 (frozen dataclass)
- `src/adapters/inbound/http/routes/chat.py`: SSE 이벤트 변환

**Extension 통합:**
- `extension/lib/sse.ts`: StreamChunk 타입 정의
- `extension/components/ToolCallIndicator.tsx`: 도구 호출 UI

### Observability (Part B)

**목표:** LLM 호출, 도구 호출, 에러 추적 가시성 확보

#### ErrorCode 상수화 (Step 0)
```
Backend: src/domain/constants.py (ErrorCode 클래스)
Extension: extension/lib/constants.ts (ErrorCode enum)

타입 안전성 보장:
- LlmRateLimitError
- EndpointConnectionError
- ToolNotFoundError
- ...
```

#### LiteLLM CustomLogger (Step 5)
```
파일: src/adapters/outbound/adk/litellm_callbacks.py

로깅 내용:
- 모델명 (openai/gpt-4o-mini, anthropic/claude-sonnet-4-5 등)
- 토큰 수 (prompt_tokens, completion_tokens)
- 지연시간 (response_ms)

설정: observability.log_llm_requests = true
```

#### Tool Call Tracing (Step 6)
```
SQLite 테이블: tool_calls
- id, message_id, tool_name, arguments, result, error, duration_ms

API: GET /api/conversations/{id}/tool-calls

파일: src/adapters/outbound/storage/sqlite_conversation_storage.py
```

#### Structured Logging (Step 7)
```
파일: src/config/logging_config.py

포맷 옵션:
- "text" (기본): 일반 텍스트 로그
- "json": JSON 포맷 (timestamp, level, logger, message, extra)

설정: observability.log_format = "json"
```

### Dynamic Intelligence (Part C)

**목표:** 컨텍스트 인식 시스템 프롬프트 및 도구 재시도 로직

#### Context-Aware System Prompt (Step 8)
```
파일: src/adapters/outbound/adk/orchestrator_adapter.py

동적 instruction 생성:
- 등록된 MCP 도구 목록 자동 포함
- 등록된 A2A 에이전트 정보 자동 포함

메서드: _build_dynamic_instruction()
```

#### Tool Execution Retry (Step 9)
```
파일: src/adapters/outbound/adk/dynamic_toolset.py

재시도 로직:
- TRANSIENT_ERRORS: ConnectionError, TimeoutError
- Exponential Backoff: 1s, 2s, 4s, ...
- 설정: mcp.max_retries = 2, mcp.retry_backoff_seconds = 1.0
```

### Reliability & Scale (Part D)

**목표:** A2A Health 모니터링 및 대규모 도구 지원

#### A2A Health Monitoring (Step 10)
```
파일: src/domain/services/health_monitor_service.py

타입별 health check:
- endpoint.type == MCP → toolset.health_check()
- endpoint.type == A2A → a2a_client.health_check()
```

#### Defer Loading (Step 11)
```
파일: src/adapters/outbound/adk/dynamic_toolset.py

확장성:
- MAX_ACTIVE_TOOLS: 30 → 100
- DeferredToolProxy: 메타데이터만 로드, 실행 시 Lazy Loading
- 설정: mcp.defer_loading_threshold = 30
```

참조: [docs/plans/phase4/phase4.0.md](../docs/plans/phase4/phase4.0.md)

## Key Files

| 파일 | 역할 |
|------|------|
| `domain/services/conversation_service.py` | 대화 처리 핵심 로직 |
| `domain/services/registry_service.py` | 엔드포인트 등록/관리 |
| `domain/ports/outbound/orchestrator_port.py` | LLM 오케스트레이터 인터페이스 |
| `adapters/outbound/storage/sqlite_conversation_storage.py` | SQLite WAL 저장소 |

## Usage

```bash
# 서버 실행
uvicorn src.main:app --host localhost --port 8000

# 테스트
pytest tests/ --cov=src
```

## References

- [docs/architecture.md](../docs/architecture.md) - 헥사고날 아키텍처 상세
- [docs/implementation-guide.md](../docs/implementation-guide.md) - 구현 패턴
- [src/domain/README.md](domain/README.md) - Domain Layer 상세
- [src/config/README.md](config/README.md) - 설정 가이드
