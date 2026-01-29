# Phase 2: MCP Integration - 구현 계획

> Backend API의 핵심 기능: MCP 서버 동적 연결, 도구 호출, 채팅 스트리밍

---

## 개요

Phase 1(Domain Core)과 Phase 1.5(Security Layer) 완료 상태에서, MCP 서버를 동적으로 연결하고 LLM을 통해 도구를 호출하는 핵심 기능을 구현합니다.

**산출물 요약:**
- Config Layer (settings.py, container.py)
- JsonEndpointStorage (엔드포인트 영속화)
- DynamicToolset + ToolsetAdapter (ADK BaseToolset ↔ ToolsetPort 브릿지)
- AdkOrchestratorAdapter (LlmAgent + LiteLLM)
- HTTP Routes: MCP CRUD + Chat SSE Streaming
- HTTP Exception Handler (Domain → HTTP 매핑)
- Integration Tests (커버리지 70%+)

---

## 구현 순서 (10 Steps)

### Step 1: Config Layer

**목표:** 설정 관리 + DI 컨테이너 기반 구축

**생성 파일:**
- `src/config/settings.py` — pydantic-settings (환경변수 > .env > YAML > 기본값)
- `src/config/container.py` — dependency-injector DeclarativeContainer
- `configs/default.yaml` — 이미 존재 (수정 불필요)
- `tests/unit/config/test_settings.py`
- `tests/unit/config/test_container.py`

**settings.py 핵심:**
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

**container.py 핵심:**
- Singleton: Settings, SqliteConversationStorage, JsonEndpointStorage, DynamicToolset
- Singleton: AdkOrchestratorAdapter (Async Factory 패턴)
- Factory: ConversationService, OrchestratorService, RegistryService, HealthMonitorService

**의존성:** 없음 (기반 Step)

---

### Step 2: JsonEndpointStorage

**목표:** 엔드포인트 영속화 (JSON 파일)

**생성 파일:**
- `src/adapters/outbound/storage/json_endpoint_storage.py`
- `tests/integration/adapters/test_json_endpoint_storage.py`

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

**생성 파일:**
- `src/adapters/outbound/adk/__init__.py`
- `src/adapters/outbound/adk/dynamic_toolset.py` — ADK `BaseToolset` 상속
- `src/adapters/outbound/adk/toolset_adapter.py` — `ToolsetPort` 구현 (도메인 브릿지)
- `tests/integration/adapters/test_dynamic_toolset.py`

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

**Standards Verification 필수:**
- `google.adk.tools.BaseToolset` 인터페이스 확인
- `MCPToolset`, `StreamableHTTPConnectionParams`, `SseServerParams` import 경로
- `MCPToolset` 생성자/`get_tools()` 시그니처

**테스트:**
- `@pytest.mark.network`로 MCP 테스트 서버 연결 테스트
- 도구 수 제한, 캐시 동작 검증

**의존성:** Step 1 (MCP 설정값)

---

### Step 4: AdkOrchestratorAdapter

**목표:** LLM Agent + 도구 통합 오케스트레이션

**생성 파일:**
- `src/adapters/outbound/adk/orchestrator_adapter.py`
- `tests/integration/adapters/test_orchestrator_adapter.py`

**구현 핵심:**
- `OrchestratorPort` 구현
- **Async Factory Pattern**: 생성자는 설정만, `initialize()`에서 `LlmAgent` 생성
- `LlmAgent(model=LiteLlm(model=model_name), tools=[dynamic_toolset])`
- `process_message()`: ADK Runner/Agent의 스트리밍 API 호출, 텍스트 chunk yield
- `close()`: DynamicToolset 정리

**Standards Verification 필수 (가장 중요):**
- `LlmAgent` 생성자 시그니처 (model, name, instruction, tools)
- ADK 실행 방식: `Runner.run_async()` vs `agent.run_async()` — ADK 1.23.0+ 확인
- 스트리밍 이벤트 구조: `.text`, `.content`, 또는 다른 속성?
- `LiteLlm` import 경로: `google.adk.models.lite_llm.LiteLlm`

**테스트:**
- API 키 필요 → `@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"))`
- 기존 `FakeOrchestrator`가 도메인 서비스 단위 테스트 커버

**의존성:** Step 3 (DynamicToolset)

---

### Step 5: HTTP Exception Handler

**목표:** 도메인 예외 → HTTP 상태 코드 자동 매핑

**생성 파일:**
- `src/adapters/inbound/http/exceptions.py`
- `tests/unit/adapters/test_http_exceptions.py`

**매핑 테이블:**

| Domain Exception | HTTP Status |
|---|---|
| EndpointNotFoundError | 404 |
| ToolNotFoundError | 404 |
| ConversationNotFoundError | 404 |
| LlmAuthenticationError | 401 |
| LlmRateLimitError | 429 |
| EndpointConnectionError | 502 |
| EndpointTimeoutError | 504 |
| ToolLimitExceededError | 409 |
| InvalidUrlError | 422 |
| ValidationError | 422 |
| DomainException (기본) | 500 |

- `ErrorResponse(error, code, message)` Pydantic 모델
- `register_exception_handlers(app)` 함수로 앱에 등록

**의존성:** 없음

---

### Step 6: MCP Management Routes

**목표:** MCP 서버 등록/조회/해제 REST API

**생성 파일:**
- `src/adapters/inbound/http/routes/mcp.py`
- `src/adapters/inbound/http/schemas/mcp.py`
- `tests/integration/adapters/test_mcp_routes.py`

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

**스키마:**
- `RegisterMcpServerRequest(url: str, name: str | None)`
- `McpServerResponse(id, name, url, type, enabled, status, registered_at, tools)`
- `ToolResponse(name, description, input_schema)`

**테스트:** TestClient + Fake 어댑터, 토큰 인증 포함

**의존성:** Step 2, Step 5

---

### Step 7: Chat Streaming Route

**목표:** SSE 스트리밍 채팅 API

**생성 파일:**
- `src/adapters/inbound/http/routes/chat.py`
- `src/adapters/inbound/http/schemas/chat.py`
- `tests/integration/adapters/test_chat_routes.py`

**엔드포인트:**
- `POST /api/chat/stream` — SSE 스트리밍 응답

**SSE 이벤트 형식:**
```
data: {"type": "text", "content": "Hello"}\n\n
data: {"type": "done"}\n\n
data: {"type": "error", "message": "..."}\n\n
```

**핵심 패턴:**
- `StreamingResponse(generate(), media_type="text/event-stream")`
- Headers: `Cache-Control: no-cache`, `X-Accel-Buffering: no`
- Zombie Task 방지: `await request.is_disconnected()` 매 chunk 확인
- `asyncio.CancelledError` 명시적 처리 후 re-raise
- `OrchestratorService.send_message(conversation_id, message)` 호출

**스키마:**
- `ChatRequest(conversation_id: str | None, message: str)`

**테스트:** FakeOrchestrator 주입, 스트리밍 이벤트 파싱 검증

**의존성:** Step 5

---

### Step 8: App Factory + Lifespan 통합

**목표:** 전체 연결 — startup/shutdown, 라우터 등록

**수정 파일:**
- `src/adapters/inbound/http/app.py` — lifespan 추가, 라우터/예외핸들러 등록
- `src/main.py` — Container 연결

**Lifespan 순서:**
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

**테스트 지원:**
- `create_app(container_override=...)` 패턴으로 Fake 어댑터 주입 가능

**의존성:** Steps 1-7 전체

---

### Step 9: Integration Tests 보강

**목표:** 어댑터 레이어 통합 테스트 커버리지 70%+

**생성/수정 파일:**
- `tests/integration/conftest.py` — `fake_app`, `authenticated_client` fixture 추가
- 각 Step에서 생성한 테스트 파일 보완

**테스트 인프라:**
- `fake_app` fixture: Fake 어댑터로 구성된 테스트용 앱
- `authenticated_client`: 유효한 X-Extension-Token 포함 TestClient
- `@pytest.mark.network`: 네트워크 의존 테스트 분리
- `@pytest.mark.skipif`: API 키 필요 테스트 분리

**의존성:** Steps 1-8

---

### Step 10: Documentation

**생성 파일:**
- `src/adapters/README.md` — Adapter Layer 구조, 구현체 목록
- `docs/plans/phase2.0.md` — 이 계획의 공식 버전

**수정 파일:**
- `src/README.md` — MCP 통합 아키텍처, API 엔드포인트 목록 추가

**의존성:** Steps 1-9

---

## Standards Verification Checklist

구현 전 웹 검색으로 반드시 확인할 항목:

| 항목 | 확인 내용 |
|---|---|
| ADK `BaseToolset` | 인터페이스, `get_tools()` 시그니처 |
| ADK `MCPToolset` | 생성자 파라미터, `StreamableHTTPConnectionParams` |
| ADK `LlmAgent` | 생성자 (model, name, instruction, tools) |
| ADK Runner/실행 | `Runner.run_async()` vs `agent.run_async()` |
| ADK 스트리밍 이벤트 | 이벤트 속성 (`.text`? `.content`?) |
| `LiteLlm` import | `google.adk.models.lite_llm.LiteLlm` 경로 확인 |
| `pydantic-settings` YAML | `YamlConfigSettingsSource` 사용법 |
| `dependency-injector` | DeclarativeContainer + FastAPI 통합 패턴 |

---

## 병렬 작업 가능 구간

```
Step 1 (Config)
  ├─→ Step 2 (JsonEndpointStorage)    ─┐
  ├─→ Step 3 (DynamicToolset)         ─┤
  │     └─→ Step 4 (Orchestrator)      │
  └─→ Step 5 (Exception Handler)      ─┤
        ├─→ Step 6 (MCP Routes)        │
        └─→ Step 7 (Chat Route)        │
                                        ↓
                               Step 8 (App Factory)
                                        ↓
                               Step 9 (Integration Tests)
                                        ↓
                               Step 10 (Documentation)
```

---

## Definition of Done

- [ ] MCP 테스트 서버 연결 성공 (`https://example-server.modelcontextprotocol.io/mcp`)
- [ ] `POST /api/mcp/servers` → 서버 등록 + 도구 목록 반환
- [ ] `GET /api/mcp/servers` → 등록된 서버 목록
- [ ] `DELETE /api/mcp/servers/{id}` → 서버 해제
- [ ] 도구 30개 초과 시 409 에러 (ToolLimitExceededError)
- [ ] `POST /api/chat/stream` → SSE 스트리밍 (text → done 이벤트)
- [ ] 모든 `/api/*` 엔드포인트 토큰 검증 (403)
- [ ] 도메인 예외 → 올바른 HTTP 상태 코드
- [ ] Settings: YAML + 환경변수 로드
- [ ] DI Container 올바른 인스턴스 제공
- [ ] 통합 테스트 커버리지 70%+
- [ ] 기존 테스트 전체 통과 (regression 없음)
- [ ] `ruff check` + `ruff format` clean
- [ ] `src/adapters/README.md` 생성
- [ ] `src/README.md` MCP 아키텍처 섹션 추가

---

## 리스크 및 대응

| 리스크 | 영향 | 대응 |
|---|---|---|
| ADK API 변경 (docs 작성 이후) | 높음 | Plan + 구현 양 단계에서 웹 검색 교차 검증 |
| BaseToolset/ToolsetPort 시그니처 충돌 | 중간 | ToolsetAdapter 래퍼 패턴으로 해결 |
| MCP 테스트 서버 불가용 | 중간 | `@pytest.mark.network`로 분리, CI에서 skip |
| LLM 통합 테스트에 API 키 필요 | 중간 | `pytest.mark.skipif`로 분리, Fake 어댑터 중심 테스트 |
| dependency-injector FastAPI 통합 복잡도 | 중간 | `app.state` 패턴으로 단순화 |

---

## 핵심 수정 대상 파일

| 파일 | 작업 |
|---|---|
| [app.py](src/adapters/inbound/http/app.py) | lifespan 추가, 라우터/예외핸들러 등록 |
| [main.py](src/main.py) | Container 연결 |
| [config/__init__.py](src/config/__init__.py) | settings, container 모듈화 |
| [conftest.py](tests/integration/conftest.py) | fake_app, authenticated_client fixture |
