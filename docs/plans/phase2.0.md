# Phase 2: MCP Integration - 구현 계획

> Backend API의 핵심 기능: MCP 서버 동적 연결, 도구 호출, 채팅 스트리밍

---

## 개요

Phase 1(Domain Core)과 Phase 1.5(Security Layer) 완료 상태에서, MCP 서버를 동적으로 연결하고 LLM을 통해 도구를 호출하는 핵심 기능을 구현합니다.

**산출물 요약:**
- Config Layer (settings.py 확장, container.py 확장)
- JsonEndpointStorage (엔드포인트 영속화)
- DynamicToolset + ToolsetAdapter (ADK BaseToolset ↔ ToolsetPort 브릿지)
- AdkOrchestratorAdapter (LlmAgent + LiteLLM)
- HTTP Routes: MCP CRUD + Chat SSE Streaming
- HTTP Exception Handler (Domain → HTTP 매핑)
- Integration Tests (커버리지 70%+)

---

## Phase 시작 전 체크리스트

### 선행 조건

- [ ] 브랜치 정리: `feature/phase-2-mcp` 신규 생성
- [ ] Git pre-commit hook 설치 확인 (main 직접 커밋 차단)
- [ ] 미반영 변경사항 커밋/정리 (`.claude/settings.json`, `pyproject.toml` 등)
- [x] `pyproject.toml` 의존성: `google-adk>=1.23.0` (이미 포함됨, 확인 완료)

### 필수 웹 검색 (Plan 단계 — 구현 전 1회)

- [ ] `google-adk pypi changelog 2026` — Breaking Changes 확인
- [ ] `BaseToolset get_tools signature google adk` — 시그니처 (`readonly_context` 매개변수 포함 여부)
- [ ] `MCPToolset StreamableHTTPConnectionParams import path` — import 경로
- [ ] `LlmAgent constructor 2026` — 생성자 파라미터
- [ ] `ADK Runner vs Agent run_async` — 실행 방식 결정 (**Step 4 아키텍처 좌우**)
- [ ] `pydantic-settings YamlConfigSettingsSource` — YAML 설정 패턴

### Step별 재검증 게이트

| Step | 검증 항목 | 방법 |
|:----:|----------|------|
| 2 시작 | TDD Red-Green-Refactor 사이클 | `/tdd` skill 호출 |
| 3 시작 | MCPToolset import 경로, BaseToolset 시그니처 | `/skill mcp-adk-standards` + 웹 검색 |
| 4 시작 | LiteLlm import, Runner/Agent 실행 방식 | `/skill mcp-adk-standards` + 웹 검색 |
| 5 시작 | TDD Red-Green-Refactor 사이클 | `/tdd` skill 호출 |
| 6 시작 | TDD Red-Green-Refactor 사이클 | `/tdd` skill 호출 |
| 6 완료 | API 보안 (토큰 검증, 입력 검증) | `/skill security-checklist` |
| 7 시작 | TDD Red-Green-Refactor 사이클 | `/tdd` skill 호출 |
| 8 완료 | 헥사고날 아키텍처 준수, Middleware 순서 | `/skill hexagonal-patterns` |

---

## 구현 순서 (10 Steps)

### Step 1: Config Layer 확장

**목표:** 설정 관리 + DI 컨테이너 기반 구축

**확장 파일 (이미 존재):**
- `src/config/settings.py` — 현재: `server_host`, `server_port`만 → Phase 2 설정 전체 추가
- `src/config/container.py` — 현재: `Settings` Singleton만 → Adapter providers 추가
- `tests/unit/config/test_settings.py` — 현재: 존재하지 않음 → 신규 생성
- `tests/unit/config/test_container.py` — 현재: 5개 테스트 → 기존 수정 + 신규 추가

**생성 파일 (신규):**
- `configs/default.yaml` — 기본 설정 파일 (이미 존재하면 수정 불필요)
- `.env.example` — Phase 2 필수 환경변수 명시 (ANTHROPIC_API_KEY 등)

**Breaking Change 주의:**

| 변경 사항 | 영향 | 대응 |
|----------|------|------|
| `env_prefix="AGENTHUB_"` 제거 또는 유지 결정 | 기존 환경변수 네이밍 변경 가능 | Step 1에서 결정 후 테스트 먼저 수정 |
| 플랫 필드 → 중첩 모델 (`server_host` → `server.host`) | `test_container.py` 5개 테스트 수정 필요 | TDD: 테스트 먼저 수정 → 구현 반영 |
| `env_nested_delimiter="__"` 추가 | 환경변수 `SERVER__HOST` 형태로 변경 | `.env.example`에 명시 |

**settings.py 확장 핵심:**
```python
class Settings(BaseSettings):
    server: ServerSettings      # host, port
    llm: LLMSettings           # default_model, timeout
    storage: StorageSettings    # data_dir, database
    health_check: HealthCheckSettings
    mcp: McpSettings           # max_active_tools(30), cache_ttl_seconds(300)
    # API keys from env only
    anthropic_api_key: str = ""
```
- `YamlConfigSettingsSource`로 `configs/default.yaml` 로드

**container.py 확장 핵심:**
- Singleton: Settings, SqliteConversationStorage, JsonEndpointStorage, DynamicToolset
- Singleton: AdkOrchestratorAdapter (Async Factory 패턴)
- Factory: ConversationService, OrchestratorService, RegistryService, HealthMonitorService

**영향받는 기존 테스트:**
- `tests/unit/config/test_container.py` (5건) — Settings 구조 변경으로 수정 필요
- `tests/integration/adapters/test_http_app.py` (13건) — create_app 시그니처 변경 시 확인
- `tests/integration/adapters/test_auth_routes.py` (8건) — CORS/Auth 미들웨어 순서 확인
- `tests/integration/adapters/test_health_routes.py` (5건) — lifespan 변경 시 확인

**의존성:** 없음 (기반 Step)

---

### Step 2: JsonEndpointStorage

**목표:** 엔드포인트 영속화 (JSON 파일)

**TDD 순서:** 테스트 파일 먼저 작성 (Red) → 구현 (Green) → 리팩토링

**생성 파일:**
- `tests/integration/adapters/test_json_endpoint_storage.py` ← 먼저 작성
- `src/adapters/outbound/storage/json_endpoint_storage.py`

**구현 핵심:**
- `EndpointStoragePort` 구현
- `{data_dir}/endpoints.json`에 저장
- `asyncio.to_thread`로 동기 파일 I/O 래핑 (추가 의존성 불필요)
- `asyncio.Lock`으로 쓰기 직렬화
- datetime → ISO format, enum → `.value` 직렬화
- 파일 없으면 자동 생성

**테스트:** `tmp_path` fixture로 CRUD 전체 검증, 파일 미존재 시 생성 확인

**의존성:** Step 1 (data_dir 설정)

---

### Step 3: DynamicToolset + ToolsetAdapter

**목표:** MCP 서버 연결 및 도구 관리

> **검증 게이트:** Step 시작 전 `/skill mcp-adk-standards` 호출, 아래 항목 웹 검색 완료 후 진행

**TDD 순서:** 테스트 파일 먼저 작성 (Red) → 구현 (Green) → 리팩토링

**생성 파일:**
- `tests/integration/adapters/test_dynamic_toolset.py` ← 먼저 작성
- `src/adapters/outbound/adk/__init__.py`
- `src/adapters/outbound/adk/dynamic_toolset.py` — ADK `BaseToolset` 상속
- `src/adapters/outbound/adk/toolset_adapter.py` — `ToolsetPort` 구현 (도메인 브릿지)

**아키텍처 결정 — Dual Interface 해결:**

`ToolsetPort.get_tools()` → `list[Tool]` (도메인)과 `BaseToolset.get_tools()` → `list[BaseTool]` (ADK)의 시그니처 충돌 해결:

```
DynamicToolset(BaseToolset)        ← ADK 세계 (BaseTool 반환)
    │
ToolsetAdapter(ToolsetPort)        ← 도메인 세계 (Tool 반환), DynamicToolset 래핑
```

- `DynamicToolset`: ADK `BaseToolset`만 상속. `get_tools()` → `list[BaseTool]`
- `ToolsetAdapter`: `ToolsetPort` 구현. 내부에서 DynamicToolset 호출 후 `BaseTool` → 도메인 `Tool` 변환

**DynamicToolset 핵심:**
- Streamable HTTP 우선 연결, SSE fallback
- TTL 기반 캐싱 (`asyncio.Lock` 보호)
- `MAX_ACTIVE_TOOLS = 30` 초과 시 `ToolLimitExceededError`
- `asyncio.to_thread`로 동기 블로킹 방지

**Standards Verification 필수 (웹 검색):**
- `google.adk.tools.BaseToolset` 인터페이스 확인 (`readonly_context` 매개변수 포함 여부)
- `MCPToolset`, `StreamableHTTPConnectionParams`, `SseServerParams` import 경로
- `MCPToolset` 생성자/`get_tools()` 시그니처

**ADR 생성 포인트:** MCP Transport 선택 (Streamable HTTP vs SSE fallback 전략) — `adr-specialist` Agent 호출

**테스트:**
- `@pytest.mark.local_mcp`로 로컬 MCP 서버 연결 테스트 (`http://127.0.0.1:9000/mcp`)
- 도구 수 제한, 캐시 동작 검증
- **FakeToolset 유지:** 기존 `tests/unit/fakes/fake_toolset.py`는 도메인 서비스 단위 테스트에 계속 사용. ToolsetAdapter는 Integration 테스트에서 별도 검증

**의존성:** Step 1 (MCP 설정값)

---

### Step 4: AdkOrchestratorAdapter

**목표:** LLM Agent + 도구 통합 오케스트레이션

> **검증 게이트:** Step 시작 전 LiteLlm import 경로, Runner/Agent 실행 방식 웹 검색 재확인

**TDD 순서:** 테스트 파일 먼저 작성 (Red) → 구현 (Green) → 리팩토링

**생성 파일:**
- `tests/integration/adapters/test_orchestrator_adapter.py` ← 먼저 작성
- `src/adapters/outbound/adk/orchestrator_adapter.py`

**구현 핵심:**
- `OrchestratorPort` 구현
- **Async Factory Pattern**: 생성자는 설정만, `initialize()`에서 `LlmAgent` 생성
- `LlmAgent(model=LiteLlm(model=model_name), tools=[dynamic_toolset])`
- `process_message()`: ADK Runner/Agent의 스트리밍 API 호출, 텍스트 chunk yield
- `close()`: DynamicToolset 정리

**Standards Verification 필수 (가장 중요):**
- `LlmAgent` 생성자 시그니처 (model, name, instruction, tools)
- ADK 실행 방식: `Runner.run_async()` vs `agent.run_async()` — ADK 1.23.0+ 확인
- Runner 사용 시 `InMemorySessionService` 등 추가 의존성 확인
- 스트리밍 이벤트 구조: `.text`, `.content`, 또는 다른 속성?
- `LiteLlm` import 경로: `google.adk.models.lite_llm.LiteLlm`

**ADR 생성 포인트:** ADK Runner vs Agent 실행 방식 — `adr-specialist` Agent 호출

**process_message() 변환 로직:** ADK 이벤트 → `AsyncIterator[str]` 변환이 핵심. 이벤트 구조에 따라 어댑터 내 변환 로직이 크게 달라지므로, Standards Verification에서 이벤트 구조를 반드시 확인

**LLM 통합 테스트 비용 방지:**
- 기본 테스트 모델: `openai/gpt-4o-mini` (가장 저렴: $0.15/M input, $0.60/M output)
- `@pytest.mark.llm` 마크 추가 — 기본 pytest 실행에서 제외 (`-m "not llm"`)
- 테스트 시 `max_tokens=50` 제한으로 응답 길이 최소화
- LLM 테스트는 최대 2~3건만 (연결 확인 + 스트리밍 응답 확인)
- CI에서는 기본 skip (API 키 없을 시 `@pytest.mark.skipif` 자동 skip)

**테스트:**
- API 키 필요 → `@pytest.mark.llm` + `@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"))`
- 기본 모델: `openai/gpt-4o-mini` (비용 최소화)
- 기존 `FakeOrchestrator`가 도메인 서비스 단위 테스트 커버

**의존성:** Step 3 (DynamicToolset)

---

### Step 5: HTTP Exception Handler

**목표:** 도메인 예외 → HTTP 상태 코드 자동 매핑

**TDD 순서:** 테스트 파일 먼저 작성 (Red) → 구현 (Green) → 리팩토링

**생성 파일:**
- `tests/unit/adapters/test_http_exceptions.py` ← 먼저 작성
- `src/adapters/inbound/http/exceptions.py`

**매핑 테이블:**

| Domain Exception | HTTP Status | 비고 |
|---|---|---|
| EndpointNotFoundError | 404 | |
| ToolNotFoundError | 404 | |
| ConversationNotFoundError | 404 | |
| LlmAuthenticationError | 401 | |
| LlmRateLimitError | 429 | |
| EndpointConnectionError | 502 | |
| EndpointTimeoutError | 504 | |
| ToolLimitExceededError | 409 또는 422 | 구현 시 재검토: 409 Conflict vs 422 Unprocessable Entity |
| InvalidUrlError | 422 | |
| ValidationError | 422 | |
| DomainException (기본) | 500 | |

- `ErrorResponse(error, code, message)` Pydantic 모델
- `register_exception_handlers(app)` 함수로 앱에 등록

**의존성:** 없음

---

### Step 6: MCP Management Routes

**목표:** MCP 서버 등록/조회/해제 REST API

> **검증 게이트:** Step 완료 후 `/skill security-checklist` 호출, API 보안 검토

**TDD 순서:** 테스트 파일 먼저 작성 (Red) → 구현 (Green) → 리팩토링

**생성 파일:**
- `tests/integration/adapters/test_mcp_routes.py` ← 먼저 작성
- `src/adapters/inbound/http/routes/mcp.py`
- `src/adapters/inbound/http/schemas/mcp.py`

**엔드포인트:**

| Method | Path | 설명 |
|---|---|---|
| POST | `/api/mcp/servers` | MCP 서버 등록 |
| GET | `/api/mcp/servers` | 서버 목록 조회 |
| GET | `/api/mcp/servers/{id}` | 서버 상세 조회 |
| GET | `/api/mcp/servers/{id}/tools` | 도구 목록 조회 |
| DELETE | `/api/mcp/servers/{id}` | 서버 해제 (204) |

**서비스 주입 패턴:**
- `app.state`에 서비스 인스턴스 저장 (lifespan에서 설정)
- Route에서 `request.app.state.registry_service`로 접근
- DI wiring 복잡성 회피, 테스트 시 `app.state` 오버라이드로 Fake 주입

**ADR 생성 포인트:** DI 패턴 (app.state vs dependency-injector wiring) — `adr-specialist` Agent 호출

**스키마:**
- `RegisterMcpServerRequest(url: str, name: str | None)`
- `McpServerResponse(id, name, url, type, enabled, status, registered_at, tools)`
- `ToolResponse(name, description, input_schema)`

**register_endpoint() 도구 중복 이슈:**
`RegistryService.register_endpoint()` L70-81에서 `toolset.add_mcp_server()`가 이미 `endpoint_id`가 설정된 `Tool` 리스트를 반환하는데, 다시 새 `Tool` 객체를 생성하여 `endpoint.tools`에 추가한다. **Step 6에서 ToolsetAdapter가 반환하는 Tool 객체를 그대로 사용할지, 변환이 필요한지 확인/수정 필요.**

**테스트:** TestClient + Fake 어댑터, 토큰 인증 포함. Fake 어댑터로 Step 3(ToolsetAdapter) 없이도 테스트 가능

**의존성:** Step 2 (JsonEndpointStorage), Step 3 (ToolsetAdapter — 테스트 시 Fake 대체 가능), Step 5 (Exception Handler)

---

### Step 7: Chat Streaming Route

**목표:** SSE 스트리밍 채팅 API

**TDD 순서:** 테스트 파일 먼저 작성 (Red) → 구현 (Green) → 리팩토링

**생성 파일:**
- `tests/integration/adapters/test_chat_routes.py` ← 먼저 작성
- `src/adapters/inbound/http/routes/chat.py`
- `src/adapters/inbound/http/schemas/chat.py`

**엔드포인트:**
- `POST /api/chat/stream` — SSE 스트리밍 응답

**SSE 이벤트 형식:**
```
data: {"type": "conversation_created", "conversation_id": "uuid..."}\n\n
data: {"type": "text", "content": "Hello"}\n\n
data: {"type": "tool_call", "name": "...", "arguments": {...}}\n\n
data: {"type": "done"}\n\n
data: {"type": "error", "message": "..."}\n\n
```

> **conversation_created 이벤트:** `ChatRequest.conversation_id`가 `None`일 때 새 대화가 생성되므로, 생성된 conversation_id를 클라이언트에 반환하는 메커니즘 필요. SSE 스트림 첫 이벤트로 전달.

**핵심 패턴:**
- `StreamingResponse(generate(), media_type="text/event-stream")`
- Headers: `Cache-Control: no-cache`, `X-Accel-Buffering: no`
- Zombie Task 방지: `await request.is_disconnected()` 매 chunk 확인
- `asyncio.CancelledError` 명시적 처리 후 re-raise
- `OrchestratorService.send_message(conversation_id, message)` 호출

**스키마:**
- `ChatRequest(conversation_id: str | None, message: str)`

**테스트:** FakeOrchestrator 주입, 스트리밍 이벤트 파싱 검증

**의존성:** Step 4 (AdkOrchestratorAdapter — 테스트 시 Fake 대체), Step 5

---

### Step 8: App Factory + Lifespan 확장

**목표:** 전체 연결 — startup/shutdown, 라우터 등록

> **검증 게이트:** Step 완료 후 `/skill hexagonal-patterns` 호출, 아키텍처 준수 검증

**수정 파일 (기존 확장):**
- `src/adapters/inbound/http/app.py` — 빈 lifespan 확장, 신규 라우터/예외핸들러 등록
- `src/main.py` — Container 연결

**기존 코드 영향 범위:**

| 변경 | 영향받는 파일 | 대응 |
|------|-------------|------|
| `create_app()` 시그니처 변경 (`container_override` 추가) | `src/main.py`, `tests/integration/conftest.py` | 하위 호환성 유지 (optional 파라미터) |
| 빈 lifespan 본체 확장 | 기존 테스트 `test_http_app.py` | lifespan 의존 테스트 확인 |
| 신규 라우터 등록 (`mcp.py`, `chat.py`) | Middleware 순서 | 회귀 테스트 포함 |

**Lifespan 확장 순서:**
```
Startup:
  1. Container 생성 → Settings 로드
  2. SqliteConversationStorage.initialize()
  3. JsonEndpointStorage (파일 로드)
  4. AdkOrchestratorAdapter.initialize() (Async Factory)
  5. HealthMonitorService.start()
  6. app.state에 서비스 저장

Shutdown:
  1. HealthMonitorService.stop()
  2. AdkOrchestratorAdapter.close()
  3. SqliteConversationStorage.close()
```

**Middleware 회귀 테스트 포함:**
- CORS preflight(OPTIONS) + 신규 라우터 경로 (`/api/mcp/*`, `/api/chat/*`)
- Auth 실패(403) 시 CORS 헤더 포함 확인
- 새 경로에서 토큰 검증 동작 확인

**테스트 지원:**
- `create_app(container_override=...)` 패턴으로 Fake 어댑터 주입 가능

**의존성:** Steps 1-7 전체

---

### Step 9: Integration Tests 보강

**목표:** 어댑터 레이어 통합 테스트 커버리지 70%+

**생성/수정 파일:**
- `tests/integration/conftest.py` — `fake_app`, `authenticated_client` fixture 추가
- `pyproject.toml` — 커스텀 pytest 마크 등록
- 각 Step에서 생성한 테스트 파일 보완

**테스트 인프라:**
- `fake_app` fixture: Fake 어댑터로 구성된 테스트용 앱
- `authenticated_client`: 유효한 X-Extension-Token 포함 TestClient
- 기존 `http_client` fixture와의 관계: `fake_app` 기반으로 **대체** (기존 fixture는 Phase 1.5 보안 테스트에서 계속 사용)
- `@pytest.mark.network`: 네트워크 의존 테스트 분리
- `@pytest.mark.skipif`: API 키 필요 테스트 분리

**pyproject.toml 추가:**
```toml
[tool.pytest.ini_options]
markers = [
    "local_mcp: tests requiring local MCP server (127.0.0.1:9000)",
    "llm: tests requiring LLM API key (excluded by default)",
]
addopts = "-v --tb=short -m 'not llm'"
```

**conftest.py 상수:**
```python
MCP_TEST_URL = "http://127.0.0.1:9000/mcp"
```

**FakeToolset 전략:**
- 기존 `tests/unit/fakes/fake_toolset.py`는 그대로 유지 — 도메인 서비스 단위 테스트용
- `ToolsetAdapter` Integration 테스트에서는 실제 `DynamicToolset` 또는 별도 Fake 사용

**의존성:** Steps 1-8

---

### Step 10: Documentation

**생성 파일:**
- `src/adapters/README.md` — Adapter Layer 구조, 구현체 목록

**수정 파일:**
- `src/README.md` — MCP 통합 아키텍처, API 엔드포인트 목록 추가
- `docs/roadmap.md` — Phase 2 DoD 체크박스 완료 표시
- 루트 `README.md` — Development Status 테이블: "MCP Integration" → "Complete" + Coverage
- `docs/plans/phase2.0.md` — DoD 체크박스 완료 표시

**의존성:** Steps 1-9

---

## Skill/Agent 활용 가이드

### 구현 중 자동 트리거 (Auto-invoked)

Skills는 auto-invoked 트리거를 가지므로, 해당 코드 작성 시 자동 로딩됩니다:
- ADK/MCP 코드 작성 → `mcp-adk-standards` 자동 로딩
- Adapter 구현 → `hexagonal-patterns` 자동 로딩
- 보안 관련 코드 → `security-checklist` 자동 로딩

### 명시적 호출 시점

| 시점 | 호출 | 목적 |
|------|------|------|
| Step 2, 5, 6, 7 시작 전 | `/tdd` skill | TDD Red-Green-Refactor 사이클 강제 |
| Step 3, 4 시작 전 | `/skill mcp-adk-standards` | ADK API 재검증 (웹 검색 강제) |
| Step 6 완료 후 | `security-reviewer` Agent | API 보안 감사 |
| Step 9 완료 후 | `code-reviewer` Agent | 코드 품질 리뷰 |
| Phase 완료 시 | `phase-orchestrator` Agent | DoD 검증 |
| 아키텍처 결정 시 | `adr-specialist` Agent | ADR 문서화 |

### ADR 생성 포인트

| Step | 결정 사항 | ADR |
|:----:|----------|-----|
| 3 | MCP Transport (Streamable HTTP vs SSE fallback) | `adr-specialist` |
| 4 | ADK Runner vs Agent 실행 방식 | `adr-specialist` |
| 6 | DI 패턴 (app.state vs dependency-injector wiring) | `adr-specialist` |

---

## 커밋 정책

**각 Step 완료 시 커밋** (테스트 통과 상태에서):
- 커밋 메시지 컨벤션: `feat(phase2): Step N - [설명]`
- Step 3-4에서 ADK API 불일치 발견 시 Step 2까지 롤백 가능
- ADK 관련 Step(3, 4)은 특히 **웹 검색 결과에 따라 설계가 변경될 수 있으므로**, 이전 Step까지 커밋 완료 후 진행

---

## Standards Verification Checklist

구현 전 웹 검색으로 반드시 확인할 항목:

| 항목 | 확인 내용 | Step |
|---|---|:---:|
| ADK `BaseToolset` | 인터페이스, `get_tools()` 시그니처, `readonly_context` 포함 여부 | 3 |
| ADK `MCPToolset` | 생성자 파라미터, `StreamableHTTPConnectionParams` | 3 |
| ADK `LlmAgent` | 생성자 (model, name, instruction, tools) | 4 |
| ADK Runner/실행 | `Runner.run_async()` vs `agent.run_async()`, `InMemorySessionService` 필요 여부 | 4 |
| ADK 스트리밍 이벤트 | 이벤트 속성 (`.text`? `.content`?) — process_message 변환 로직 좌우 | 4 |
| `LiteLlm` import | `google.adk.models.lite_llm.LiteLlm` 경로 확인 | 4 |
| `pydantic-settings` YAML | `YamlConfigSettingsSource` 사용법 | 1 |
| `dependency-injector` | DeclarativeContainer + FastAPI 통합 패턴 | 1 |

---

## 병렬 작업 가능 구간

```
Step 1 (Config 확장)
  ├─→ Step 2 (JsonEndpointStorage)    ─┐
  ├─→ Step 3 (DynamicToolset)         ─┤
  │     └─→ Step 4 (Orchestrator)      │
  └─→ Step 5 (Exception Handler)      ─┤
        ├─→ Step 6 (MCP Routes)  ←── Step 2 + Step 3
        └─→ Step 7 (Chat Route)  ←── Step 4
                                       ↓
                              Step 8 (App Factory 확장)
                                       ↓
                              Step 9 (Integration Tests)
                                       ↓
                              Step 10 (Documentation)
```

> **주의:** Step 6은 Step 2(JsonEndpointStorage) + Step 3(ToolsetAdapter)에 의존합니다. 테스트에서 Fake 어댑터를 사용하면 Step 3 없이도 진행 가능하지만, 실제 연결 테스트에는 Step 3이 필요합니다.

---

## Definition of Done

- [ ] 로컬 MCP 서버 연결 성공 (`http://127.0.0.1:9000/mcp`)
- [ ] `POST /api/mcp/servers` → 서버 등록 + 도구 목록 반환
- [ ] `GET /api/mcp/servers` → 등록된 서버 목록
- [ ] `DELETE /api/mcp/servers/{id}` → 서버 해제
- [ ] 도구 30개 초과 시 에러 (ToolLimitExceededError)
- [ ] `POST /api/chat/stream` → SSE 스트리밍 (conversation_created → text → done)
- [ ] 모든 `/api/*` 엔드포인트 토큰 검증 (403)
- [ ] 도메인 예외 → 올바른 HTTP 상태 코드
- [ ] Settings: YAML + 환경변수 로드
- [ ] DI Container 올바른 인스턴스 제공
- [ ] Middleware 순서 회귀 테스트 포함
- [ ] 통합 테스트 커버리지 70%+
- [ ] 기존 테스트 전체 통과 (regression 없음)
- [ ] `ruff check` + `ruff format` clean
- [ ] `src/adapters/README.md` 생성
- [ ] `src/README.md` MCP 아키텍처 섹션 추가
- [ ] `docs/roadmap.md` Phase 2 DoD 완료 표시
- [ ] 루트 `README.md` Development Status 업데이트

---

## 리스크 및 대응

| 리스크 | 영향 | 대응 |
|---|---|---|
| ADK API 변경 (docs 작성 이후) | 높음 | Plan + 구현 양 단계에서 웹 검색 교차 검증 |
| BaseToolset/ToolsetPort 시그니처 충돌 | 중간 | ToolsetAdapter 래퍼 패턴으로 해결 |
| 로컬 MCP 서버 미실행 | 중간 | `@pytest.mark.local_mcp`로 분리, 테스트 전 서버 실행 확인 |
| LLM 통합 테스트 비용 폭탄 | 높음 | `@pytest.mark.llm` 기본 제외 + `max_tokens=50` + `openai/gpt-4o-mini` 사용 |
| LLM 통합 테스트에 API 키 필요 | 중간 | `pytest.mark.skipif`로 분리, Fake 어댑터 중심 테스트 |
| dependency-injector FastAPI 통합 복잡도 | 중간 | `app.state` 패턴으로 단순화 |
| **Settings env_prefix Breaking Change** | 중간 | Step 1에서 기존 테스트 먼저 수정 (TDD) |
| **create_app() 시그니처 변경** | 중간 | conftest.py, main.py 동시 수정 (Step 8) |
| **Middleware 순서 회귀** | 높음 | Step 8에서 CORS/Auth 순서 회귀 테스트 포함 |
| **ADK Runner vs Agent 실행 방식 미결** | 높음 | Step 3 이전에 웹 검색으로 결정, ADR 생성 |

---

## 핵심 수정 대상 파일

| 파일 | 작업 |
|---|---|
| `src/config/settings.py` | Phase 2 설정 전체 추가 (확장) |
| `src/config/container.py` | Adapter providers 추가 (확장) |
| `src/adapters/inbound/http/app.py` | lifespan 확장, 라우터/예외핸들러 등록 |
| `src/main.py` | Container 연결 |
| `tests/unit/config/test_container.py` | 기존 5개 테스트 수정 + 신규 추가 |
| `tests/integration/conftest.py` | fake_app, authenticated_client fixture |
| `pyproject.toml` | 의존성 추가, pytest 마크 등록 |
| `.env.example` | Phase 2 필수 환경변수 명시 |

---

## 테스트 서버 정책

> **프로젝트 전역 정책:** MCP 및 A2A 서버는 **외부 서버가 아닌 로컬 서버만으로 테스트**합니다.

| 서버 | URL | 실행 방법 | Phase |
|------|-----|----------|:-----:|
| **MCP (Synapse)** | `http://127.0.0.1:9000/mcp` | `SYNAPSE_PORT=9000 python -m synapse` | 2 |
| **A2A Agents** | 로컬 A2A Agent Server (구현 중) | TBD | 3 |

**로컬 MCP 서버 (Synapse) 정보:**
- 프로젝트: `C:\Users\sungb\Documents\GitHub\MCP_SERVER\MCP_Streamable_HTTP`
- Transport: Streamable HTTP (2025년 권장 표준)
- 제공 도구 11개: echo, read_file, write_file, list_directory, web_search 등
- 포트: 9000 (AgentHub 기본 포트 8000과 충돌 방지)

**주의:**
- AgentHub(포트 8000)과 MCP 서버(포트 9000)는 별도 프로세스로 동시 실행
- 통합 테스트 실행 전 로컬 MCP 서버가 실행 중인지 확인 필요
- CI 환경에서는 `@pytest.mark.local_mcp` 테스트가 자동 skip됨
