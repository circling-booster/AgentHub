# Phase 3: Stability, A2A Integration, UI Polish, E2E Tests

> **상태:** 📋 Planned
> **선행 조건:** Phase 2.5 Complete (수동검증 완료)
> **목표:** Backend 안정성 강화, A2A 네이티브 통합, Extension UI 완성, Full Playwright E2E
> **아키텍처 결정:** ADK Native A2A (RemoteA2aAgent + to_a2a())
> **분할:** Part A (Backend: Steps 1-7) → Part B (UI+E2E: Steps 8-10)

---

## 🎯 Phase 3 진행 상황 체크리스트

### Part A: Backend (Steps 1-7)

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **1** | Backend Stability Hardening (Zombie Task + Thread Isolation) | ⬜ |
| **2** | A2A Test Agent Fixtures (Echo Agent) | ⬜ |
| **3** | A2A Client Adapter (RemoteA2aAgent) | ⬜ |
| **4** | RegistryService A2A 지원 | ⬜ |
| **5** | A2A HTTP Routes | ⬜ |
| **6** | A2A Server Exposure (to_a2a) | ⬜ |
| **7** | Orchestrator A2A Integration + DI Container | ⬜ |

### Part B: Frontend & E2E (Steps 8-10)

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **8.1** | MCP Tools 목록 표시 | ⬜ |
| **8.2** | 대화 히스토리 유지 | ⬜ |
| **8.3** | 코드 블록 하이라이팅 + 도구 실행 UI | ⬜ |
| **8.4** | A2A 에이전트 표시 | ⬜ |
| **9** | Full Playwright E2E Tests | ⬜ |
| **10** | Documentation Updates | ⬜ |

### 전체 DoD 요약

| 영역 | 진행률 | 상태 |
|------|:------:|:----:|
| Part A 기능 (11개 항목) | 0/11 | ⬜ |
| Part A 품질 (5개 항목) | 0/5 | ⬜ |
| Part A 문서 (2개 항목) | 0/2 | ⬜ |
| Part B 기능 (5개 항목) | 0/5 | ⬜ |
| Part B 품질 (3개 항목) | 0/3 | ⬜ |
| Part B 문서 (5개 항목) | 0/5 | ⬜ |

**범례:** ✅ 완료 | 🚧 진행중 | ⬜ 미착수

---

## 분할 전략

Phase 3은 범위가 넓어 두 개의 독립적인 파트로 분리합니다:

| 파트 | 범위 | 초점 | Steps |
|------|------|------|:-----:|
| **Part A** | A2A Core + Stability | Backend Python | 1-7 |
| **Part B** | UI Polish + E2E | Extension TypeScript + Playwright | 8-10 |

- Part A 완료 후 Part B 시작 (순차 실행)
- 각 파트는 독립 DoD + 커밋 정책을 가짐
- Part A 완료 시 중간 문서 업데이트 포함

---

# Part A: A2A Core + Backend Stability (Steps 1-7)

> **목표:** Backend A2A 통합 완료 + 안정성 테스트 강화
> **산출물:** A2A 에이전트 등록/조회/삭제 API, Orchestrator A2A sub_agent 통합, AgentHub A2A 노출

## Part A 산출물 요약

| 영역 | 새 파일 | 수정 파일 | 예상 테스트 |
|------|:------:|:--------:|:---------:|
| Stability Tests + Logging | 2 | 1 | ~8 |
| A2A Test Fixtures | 4 | 1 | ~3 |
| A2A Client Adapter | 4 | 0 | ~10 |
| RegistryService A2A | 0 | 4 | ~6 |
| A2A HTTP Routes | 3 | 1 | ~12 |
| A2A Server Exposure | 3 | 1 | ~4 |
| Orchestrator Integration | 0 | 4 | ~4 |

---

## Phase 시작 전 체크리스트

### 선행 조건

- [x] 기존 테스트 전체 통과: `pytest tests/ -v` (262 selected)
- [x] Coverage >= 80%: `pytest --cov=src --cov-fail-under=80` (현재 89.66%)
- [x] 브랜치 확인: `feature/phase-3` 생성

### 필수 웹 검색 (Plan 단계) ✅

- [x] `google adk RemoteA2aAgent constructor 2026` — ✅ `name`, `description`, `agent_card` (URL)
- [x] `google adk to_a2a utility return type 2026` — ✅ ASGI application (FastAPI 마운트 가능)
- [x] `A2A protocol agent card schema 2026` — ✅ 필수: `name`, `description`, `version`, `api`, `auth`
- [x] `google adk agent without LLM callback 2026` — ✅ Callback으로 LLM 우회 가능 (테스트용)

### Step별 재검증 게이트

| Step | 검증 항목 | 방법 |
|:----:|----------|------|
| 1 시작 | TDD Red-Green-Refactor | `/tdd` skill 호출 |
| 2 시작 | ADK A2A import 경로, to_a2a() 시그니처 | Web search + `/skill mcp-adk-standards` |
| 3 시작 | RemoteA2aAgent 생성자, 호출 패턴 | Web search 재검증 |
| 4 시작 | TDD (도메인 서비스 확장) | `/tdd` skill 호출 |
| 5 시작 | TDD + API 설계 | `/tdd` skill 호출 |
| 5 완료 | API 보안 감사 | `/skill security-checklist` |
| 6 시작 | to_a2a() 마운트 방식 | Web search 재검증 |
| 7 완료 | 헥사고날 아키텍처 검증 | `/skill hexagonal-patterns` |

---

## Step 1: Backend Stability Hardening (3.1 + 3.2)

**목표:** 기존 구현에 대한 전용 integration test 추가 + 구조화된 로깅 개선

**현재 상태 (이미 구현됨):**
- `src/adapters/inbound/http/routes/chat.py:66` — `request.is_disconnected()` SSE 루프 체크
- `src/adapters/outbound/adk/dynamic_toolset.py:282` — `asyncio.to_thread()` 도구 실행
- `src/domain/services/health_monitor_service.py` — `CancelledError` 처리

**TDD 순서:**
1. `/tdd` skill 호출
2. Red: `test_zombie_task_cancelled_on_disconnect` — SSE 스트림 중 클라이언트 연결 해제 시 태스크 정리 확인
3. Red: `test_thread_isolation_health_during_tool_execution` — 무거운 도구 실행 중 `/health` 즉시 응답 확인
4. Red: `test_cancelled_error_not_swallowed` — `CancelledError` 전파 검증
5. Green: `chat.py` 구조화된 로깅 추가 (conversation_id, task lifecycle: created/streaming/cancelled/completed)
6. Refactor: 로그 포맷 정리

**생성/수정 파일:**

| 파일 | 작업 | 설명 |
|------|:----:|------|
| `tests/integration/adapters/test_zombie_task.py` | NEW | Zombie task 취소 테스트 |
| `tests/integration/adapters/test_thread_isolation.py` | NEW | Thread isolation 테스트 |
| `src/adapters/inbound/http/routes/chat.py` | MODIFY | 구조화된 로깅 추가 |

**Phase 4 이관 항목 (명시적 문서화):**
- **LLM 호출 중 취소 gap**: `runner.run_async()` 실행 중에는 SSE 루프가 차단되어 `is_disconnected()` 체크에 도달하지 않음. ADK Runner 취소 API 부재로 `asyncio.Task` 래핑 + 캐스케이딩 취소 필요
- **동시 SSE 스트림 Connection Pooling**
- **Backpressure 메커니즘**

**의존성:** 없음 (기반 Step)

---

## Step 2: A2A Test Agent Fixtures

**목표:** ADK 표준 A2A 테스트 에이전트를 프로젝트 내에 생성, conftest에서 subprocess 자동 관리

> **검증 게이트:** Web search + `/skill mcp-adk-standards` — `to_a2a()` import 경로 및 시그니처 확인

**TDD 순서:**
1. `/skill mcp-adk-standards` + 웹 검색: `to_a2a()` 시그니처, non-LLM agent 가능 여부
2. Echo agent 스크립트 생성 (ADK `to_a2a()` 패턴)
3. conftest fixture: subprocess 시작/종료 + health check 대기
4. Smoke test: Agent Card fetch 검증

**생성/수정 파일:**

| 파일 | 작업 | 설명 |
|------|:----:|------|
| `tests/fixtures/__init__.py` | NEW | Package init |
| `tests/fixtures/a2a_agents/__init__.py` | NEW | Package init |
| `tests/fixtures/a2a_agents/echo_agent.py` | NEW | ADK to_a2a() 기반 echo agent |
| `tests/conftest.py` | MODIFY | A2A fixture import + `a2a_echo_agent` session fixture |
| `pyproject.toml` | MODIFY | `local_a2a` pytest marker 추가 |

**⚠️ conftest 스코프 주의:**
A2A fixture는 `tests/conftest.py` (root)에 정의하여 모든 테스트 디렉토리에서 접근 가능하게 함. `tests/fixtures/a2a_agents/conftest.py`가 아님.

**Echo Agent 구현 방향:**
```python
# tests/fixtures/a2a_agents/echo_agent.py
# NOTE: to_a2a()에 LlmAgent가 필수인지 웹 검색 확인 필요
# 대안 1: ADK callback/function agent (LLM 불필요)
# 대안 2: 단순 FastAPI + Agent Card JSON 직접 서빙
# 대안 3: LlmAgent + FakeLLM (ADK 제공 시)
```

**conftest fixture 패턴:**
```python
# tests/conftest.py (root level)
@pytest.fixture(scope="session")
def a2a_echo_agent():
    """A2A echo agent subprocess (port 9001)"""
    proc = subprocess.Popen(
        [sys.executable, "tests/fixtures/a2a_agents/echo_agent.py", "9001"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _wait_for_health("http://127.0.0.1:9001", timeout=10)
    yield "http://127.0.0.1:9001"
    proc.terminate()
    proc.wait(timeout=5)
```

**의존성:** 없음 (독립 fixture)

---

## Step 3: A2A Client Adapter (A2A 에이전트 소비)

**목표:** `A2aPort` 인터페이스를 ADK `RemoteA2aAgent` 기반으로 구현

> **검증 게이트:** Web search — `RemoteA2aAgent` 생성자, **직접 호출 가능 여부** 확인

**TDD 순서:**
1. `/tdd` skill 호출
2. Red: `FakeA2aClient` 생성 (unit test용)
3. Red: `test_register_a2a_agent_fetches_card` — Agent Card 교환 성공
4. Red: `test_health_check_a2a_agent` — 상태 확인
5. Red: `test_unregister_a2a_agent` — 등록 해제
6. Green: `A2aClientAdapter` 구현
7. Integration test: Step 2 fixture agent 대상 실행

**생성 파일:**

| 파일 | 작업 | 설명 |
|------|:----:|------|
| `tests/unit/fakes/fake_a2a_client.py` | NEW | Fake A2aPort (unit test용) |
| `src/adapters/outbound/a2a/__init__.py` | NEW | Package init |
| `src/adapters/outbound/a2a/a2a_client_adapter.py` | NEW | A2aPort 구현 |
| `tests/integration/adapters/test_a2a_client_adapter.py` | NEW | Integration test |

**⚠️ 핵심 리스크 — RemoteA2aAgent 호출 패턴:**

ADK의 `RemoteA2aAgent`는 `sub_agent`로만 동작할 가능성이 있음 (직접 `call_agent()` 불가). Step 3 시작 시 웹 검색으로 확정하고, 불가 시:

- **대안 A (권장):** `A2aClientAdapter`에서 `httpx`로 A2A JSON-RPC 2.0 직접 호출. `register_agent()`에서 Agent Card fetch, `call_agent()`에서 `tasks/send` 호출
- **대안 B:** `call_agent()`는 `NotImplementedError` (Orchestrator sub_agent 경유로만 호출 가능)
- 대안 선택 시 ADR 생성: `adr-specialist` Agent 호출

**의존성:** Step 2 (A2A test fixture)

---

## Step 4: RegistryService A2A 지원

**목표:** `register_endpoint()`에 A2A 타입 지원 추가. 도메인 순수성 유지.

**TDD 순서:**
1. `/tdd` skill 호출
2. Red: `test_register_a2a_endpoint` — A2A 타입 등록 흐름
3. Red: `test_list_endpoints_a2a_filter` — type_filter="a2a" 조회
4. Red: `test_unregister_a2a_endpoint` — A2A 엔드포인트 해제
5. Red: `test_endpoint_agent_card_field` — Endpoint에 agent_card 필드 존재
6. Green: Endpoint 엔티티 + RegistryService + JsonEndpointStorage 수정
7. Refactor

**수정 파일:**

| 파일 | 작업 | 설명 |
|------|:----:|------|
| `src/domain/entities/endpoint.py` | MODIFY | `agent_card: dict \| None = None` 필드 추가 |
| `src/domain/services/registry_service.py` | MODIFY | `endpoint_type` 파라미터, A2A 분기, `a2a_client` 의존성 |
| `src/adapters/outbound/storage/json_endpoint_storage.py` | MODIFY | `agent_card` 직렬화/역직렬화 추가 |
| `tests/unit/domain/services/test_registry_service.py` | MODIFY | A2A 테스트 케이스 추가 |
| `tests/unit/domain/entities/test_endpoint.py` | MODIFY | agent_card 필드 테스트 |
| `tests/integration/adapters/test_json_endpoint_storage.py` | MODIFY | A2A endpoint 직렬화 테스트 |

**⚠️ JsonEndpointStorage 직렬화 변경 (Gap 수정):**
```python
# _serialize_endpoint() 추가:
"agent_card": endpoint.agent_card,  # dict | None → JSON 호환

# _deserialize_endpoint() 추가:
agent_card=data.get("agent_card"),  # 기존 데이터 하위 호환 (None default)
```

**RegistryService 변경 핵심:**
```python
class RegistryService:
    def __init__(self, storage, toolset, a2a_client: A2aPort | None = None):
        self._a2a_client = a2a_client  # NEW (None이면 A2A 미지원)

    async def register_endpoint(
        self, url, name=None,
        endpoint_type: EndpointType = EndpointType.MCP,  # 하위 호환
    ) -> Endpoint:
        endpoint = Endpoint(url=url, type=endpoint_type, name=name or "")

        if endpoint_type == EndpointType.MCP:
            tools = await self._toolset.add_mcp_server(endpoint)
            for tool in tools:
                endpoint.tools.append(Tool(...))
        elif endpoint_type == EndpointType.A2A:
            if self._a2a_client is None:
                raise ValueError("A2A client not configured")
            agent_card = await self._a2a_client.register_agent(endpoint)
            endpoint.agent_card = agent_card

        await self._storage.save_endpoint(endpoint)
        return endpoint

    async def unregister_endpoint(self, endpoint_id):
        endpoint = await self._storage.get_endpoint(endpoint_id)
        if not endpoint:
            return False
        if endpoint.type == EndpointType.A2A and self._a2a_client:
            await self._a2a_client.unregister_agent(endpoint_id)
        elif endpoint.type == EndpointType.MCP:
            await self._toolset.remove_mcp_server(endpoint_id)
        return await self._storage.delete_endpoint(endpoint_id)
```

**도메인 순수성:** `A2aPort`는 순수 Python ABC. ADK import 없음. ✅

**의존성:** Step 3 (FakeA2aClient for unit tests)

---

## Step 5: A2A HTTP Routes

**목표:** A2A 에이전트 관리 REST API (MCP routes 패턴 미러링)

> **검증 게이트:** Step 완료 후 `/skill security-checklist` 호출

**TDD 순서:**
1. `/tdd` skill 호출
2. Red: `test_register_a2a_agent_route` — POST /api/a2a/agents
3. Red: `test_list_a2a_agents_route` — GET /api/a2a/agents
4. Red: `test_get_a2a_agent_card_route` — GET /api/a2a/agents/{id}/card
5. Red: `test_delete_a2a_agent_route` — DELETE /api/a2a/agents/{id}
6. Red: `test_a2a_routes_require_token` — 토큰 없이 403
7. Green: 스키마 + 라우트 구현
8. Security review: `/skill security-checklist`

**생성/수정 파일:**

| 파일 | 작업 | 설명 |
|------|:----:|------|
| `tests/integration/adapters/test_a2a_routes.py` | NEW | A2A route 테스트 |
| `src/adapters/inbound/http/schemas/a2a.py` | NEW | Request/Response 스키마 |
| `src/adapters/inbound/http/routes/a2a.py` | NEW | A2A CRUD 라우트 |
| `src/adapters/inbound/http/app.py` | MODIFY | A2A 라우터 등록 |

**엔드포인트:**

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/a2a/agents` | A2A 에이전트 등록 |
| GET | `/api/a2a/agents` | 에이전트 목록 |
| GET | `/api/a2a/agents/{id}` | 에이전트 상세 |
| GET | `/api/a2a/agents/{id}/card` | Agent Card 조회 |
| DELETE | `/api/a2a/agents/{id}` | 에이전트 해제 (204) |

**보안:** 모든 `/api/a2a/*` 경로는 기존 `ExtensionAuthMiddleware`에 의해 자동 보호됨 (`path.startswith("/api/")`). 추가: URL 입력 검증 (SSRF 방지).

**의존성:** Step 4 (RegistryService A2A 지원)

---

## Step 6: A2A Server Exposure (AgentHub 노출)

**목표:** AgentHub의 LlmAgent를 A2A 프로토콜로 노출 (다른 에이전트가 호출 가능)

> **검증 게이트:** Web search — `to_a2a()` 반환 타입, FastAPI 마운트 가능 여부

**TDD 순서:**
1. `/skill mcp-adk-standards` + 웹 검색
2. Red: `test_agent_card_served_at_well_known_path` — `GET /.well-known/agent.json` 200
3. Red: `test_agent_card_has_required_fields` — agentId, name, skills 등
4. Green: 구현 (방안 A 또는 B)
5. Refactor

**생성/수정 파일:**

| 파일 | 작업 | 설명 |
|------|:----:|------|
| `tests/integration/adapters/test_a2a_server.py` | NEW | A2A server 노출 테스트 |
| `src/adapters/inbound/a2a/__init__.py` | NEW | Package init |
| `src/adapters/inbound/a2a/a2a_server.py` | NEW | A2A server wrapper |
| `src/adapters/inbound/http/app.py` | MODIFY | Agent Card 라우트 또는 sub-app 마운트 |

**구현 방향 (웹 검색으로 확정):**
- **방안 A (우선):** `to_a2a()` 반환값이 ASGI app이면 FastAPI에 마운트
- **방안 B (대안):** blocking이면 `/.well-known/agent.json` 수동 엔드포인트 + JSON-RPC 핸들러
- ADR 생성: 마운트 방식 결정 — `adr-specialist` Agent

**의존성:** Step 7에서 참조 (Orchestrator의 Agent를 노출)

---

## Step 7: Orchestrator A2A Integration + DI Container

**목표:** A2A 에이전트를 LlmAgent의 `sub_agents`로 동적 추가/제거 + DI 연결

> **검증 게이트:** Step 완료 후 `/skill hexagonal-patterns` 호출

**TDD 순서:**
1. `/tdd` skill 호출
2. Red: `test_add_a2a_sub_agent` — RemoteA2aAgent가 sub_agent로 추가됨
3. Red: `test_remove_a2a_sub_agent` — sub_agent 제거 후 Agent 재구성
4. Red: `test_orchestrator_with_mixed_tools_and_agents` — MCP + A2A 동시 동작
5. Green: AdkOrchestratorAdapter 수정
6. Green: Container 업데이트 + Lifespan 업데이트
7. Hexagonal architecture review: `/skill hexagonal-patterns`

**수정 파일:**

| 파일 | 작업 | 설명 |
|------|:----:|------|
| `src/adapters/outbound/adk/orchestrator_adapter.py` | MODIFY | `_sub_agents` dict, `add/remove_a2a_agent()`, `_rebuild_agent()` |
| `src/config/container.py` | MODIFY | `a2a_client_adapter` Singleton, registry_service에 주입 |
| `src/adapters/inbound/http/app.py` | MODIFY | lifespan에 A2A 초기화 추가 |
| `tests/integration/adapters/test_orchestrator_adapter.py` | MODIFY | A2A sub_agent 테스트 |

**OrchestratorAdapter 변경 핵심:**
```python
class AdkOrchestratorAdapter(OrchestratorPort):
    def __init__(self, model, dynamic_toolset, instruction="..."):
        # ... 기존 ...
        self._sub_agents: dict[str, RemoteA2aAgent] = {}  # NEW

    async def add_a2a_agent(self, endpoint_id: str, agent_card_url: str):
        remote = RemoteA2aAgent(
            name=f"a2a_{endpoint_id}",
            description="...",  # Agent Card에서 추출
            agent_card=agent_card_url,
        )
        self._sub_agents[endpoint_id] = remote
        await self._rebuild_agent()

    async def _rebuild_agent(self):
        """Agent + Runner 재구성 (세션 서비스 유지)"""
        self._agent = LlmAgent(
            model=LiteLlm(model=self._model_name),
            name="agenthub_agent",
            instruction=self._instruction,
            tools=[self._dynamic_toolset],
            sub_agents=list(self._sub_agents.values()),  # NEW
        )
        # Runner 재생성, 기존 session_service 유지 (대화 컨텍스트 보존)
        self._runner = Runner(
            agent=self._agent,
            app_name=APP_NAME,
            session_service=self._session_service,
        )
```

**DI Container 업데이트:**
```python
# container.py 추가:
a2a_client_adapter = providers.Singleton(A2aClientAdapter)

registry_service = providers.Factory(
    RegistryService,
    toolset=dynamic_toolset,
    storage=endpoint_storage,
    a2a_client=a2a_client_adapter,  # NEW
)
```

**의존성:** Steps 3, 4, 5, 6

---

## Part A 병렬 작업 구간

```
Step 1 (Stability) ─────────────────────────────┐
                                                  │
Step 2 (A2A Fixture) ──────────────┐              │
  └──→ Step 3 (A2A Client)        │              │
         └──→ Step 4 (Registry)    │              │
                └──→ Step 5 (Routes) ──→ Step 6  │
                                          └──→ Step 7
```

**병렬 가능:** Step 1 ∥ Step 2 (독립적)

---

## Part A Skill/Agent 활용

| 시점 | 호출 | 목적 |
|------|------|------|
| Steps 1, 4, 5 시작 | `/tdd` | TDD Red-Green-Refactor |
| Steps 2, 3, 6 시작 | `/skill mcp-adk-standards` + web search | ADK A2A API 검증 |
| Step 5 완료 | `security-reviewer` Agent | API 보안 감사 |
| Step 7 완료 | `hexagonal-architect` Agent | 아키텍처 검증 |
| Part A 완료 | `phase-orchestrator` Agent | Part A DoD 검증 |

---

## Part A 커밋 정책

```
feat(phase3): Step 1 - Backend stability tests and structured logging
feat(phase3): Step 2 - A2A echo agent test fixture
feat(phase3): Step 3 - A2aClientAdapter with RemoteA2aAgent
feat(phase3): Step 4 - RegistryService A2A endpoint support
feat(phase3): Step 5 - A2A HTTP management routes
feat(phase3): Step 6 - A2A server exposure via to_a2a()
feat(phase3): Step 7 - Orchestrator A2A sub-agent integration and DI wiring
```

---

## Part A Definition of Done

### 기능

- [ ] Zombie Task: Integration test — 클라이언트 연결 해제 시 태스크 정리 검증
- [ ] Thread Isolation: Integration test — 무거운 도구 실행 중 `/health` 즉시 응답
- [ ] 구조화된 로깅: task lifecycle 로그 (conversation_id 포함)
- [ ] A2A 테스트 fixture: Echo agent conftest 자동 시작/종료
- [ ] A2aClientAdapter: fixture agent 대상 integration test 통과
- [ ] RegistryService: MCP + A2A 모두 등록/해제/조회 가능
- [ ] A2A Routes: CRUD + 토큰 인증 동작
- [ ] A2A Server: AgentHub Agent Card `/.well-known/agent.json` 서빙
- [ ] Orchestrator: A2A agents를 sub_agents로 동적 추가/제거
- [ ] DI Container: A2A adapter 올바르게 wiring
- [ ] JsonEndpointStorage: A2A endpoint + agent_card 직렬화/역직렬화

### 품질

- [ ] 기존 테스트 전체 통과 (regression 0)
- [ ] Backend 커버리지 >= 80%
- [ ] `ruff check` + `ruff format` clean
- [ ] 보안 리뷰 완료 (A2A routes)
- [ ] 헥사고날 아키텍처 검증 완료

### 중간 문서

- [ ] `CLAUDE.md` — Test Resources 테이블에 A2A 테스트 서버 추가
- [ ] `docs/STATUS.md` — Phase 3 Part A 진행 상태 반영

---

# Part B: UI Polish + E2E Tests (Steps 8-10)

> **선행 조건:** Part A 완료
> **목표:** Extension UI 완성 + Full Playwright E2E + 전체 문서 업데이트

---

## Step 8: Extension UI Polish (3.3.1 ~ 3.3.4)

**목표:** Phase 2.5에서 이관된 UI 항목 + A2A 에이전트 표시

### 8.1 MCP Tools 목록 표시

**현재 상태:** Backend API `GET /api/mcp/servers/{id}/tools` 존재. Extension에서 미호출.

**수정 파일:**
- `extension/lib/api.ts` — MODIFY: `getServerTools(serverId)` 추가
- `extension/hooks/useMcpServers.ts` — MODIFY: tools 상태 관리, 등록 후 자동 조회
- `extension/components/McpServerManager.tsx` — MODIFY: expandable tools list

### 8.2 대화 히스토리 유지

**현재 상태:** `useChat.ts`가 `useState`만 사용. 탭 전환 시 대화 소멸.

**구현:** `chrome.storage.session`에 현재 대화 상태 저장 (탭 전환 시 복원, 브라우저 종료 시 삭제)

**수정 파일:**
- `extension/hooks/useChat.ts` — MODIFY: `chrome.storage.session` 연동
- `extension/entrypoints/sidepanel/App.tsx` — MODIFY: conversation ID App 레벨 lift

### 8.3 코드 블록 하이라이팅 + 도구 실행 UI

**구현:** `highlight.js` 또는 `prism-react-renderer` 사용

**생성/수정 파일:**
- `extension/components/CodeBlock.tsx` — NEW
- `extension/components/ToolCallDisplay.tsx` — NEW
- `extension/components/MessageBubble.tsx` — MODIFY
- `extension/package.json` — MODIFY (의존성 추가)

### 8.4 A2A 에이전트 표시

**생성/수정 파일:**
- `extension/lib/api.ts` — MODIFY (A2A API 함수)
- `extension/lib/types.ts` — MODIFY (A2A 타입)
- `extension/hooks/useA2aAgents.ts` — NEW
- `extension/components/A2aAgentManager.tsx` — NEW
- `extension/entrypoints/sidepanel/App.tsx` — MODIFY (A2A 탭 추가)

**Vitest 테스트:** 각 hook, API 함수, 컴포넌트 테스트. 목표: 129 → 150+ tests.

**의존성:** Part A 완료 (A2A routes 필요)

---

## Step 9: Full Playwright E2E Tests

**목표:** Chrome Extension을 실제 브라우저에 로드하여 전체 흐름 자동 테스트

**Prerequisites:**
- `pip install playwright && playwright install chromium`
- Extension 빌드: `cd extension && npm run build`
- 서버 + MCP/A2A 테스트 서버 실행

**테스트 시나리오:**
1. `test_extension_loads_and_connects` — Sidepanel 열기, "Connected"
2. `test_token_exchange_on_startup` — Background 토큰 교환
3. `test_chat_sends_and_receives` — 채팅 입력 → 응답 수신
4. `test_mcp_server_registration_and_tools` — MCP 등록, 도구 목록 (MCP 서버 필요)
5. `test_a2a_agent_registration` — A2A 등록 (A2A fixture 필요)
6. `test_conversation_persists_across_tabs` — 탭 전환 대화 유지
7. `test_code_block_rendering` — 코드 블록 하이라이팅

**⚠️ auth.py 토큰 상태:** 서버를 subprocess로 새로 시작하므로 `_token_issued` 전역 상태가 자동 리셋됨. 별도 처리 불필요.

**생성/수정 파일:**

| 파일 | 작업 | 설명 |
|------|:----:|------|
| `tests/e2e/conftest.py` | MODIFY | Playwright fixtures (server subprocess, browser context) |
| `tests/e2e/test_playwright_extension.py` | NEW | Full browser E2E |
| `pyproject.toml` | MODIFY | playwright 의존성, e2e_playwright marker |

**Playwright conftest:**
```python
@pytest.fixture(scope="session")
def server_process():
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "src.main:app", ...])
    _wait_for_health("http://localhost:8000/health", timeout=10)
    yield proc
    proc.terminate()

@pytest.fixture
def browser_context(extension_path, server_process):
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            "", channel="chromium", headless=False,
            args=[f"--disable-extensions-except={extension_path}",
                  f"--load-extension={extension_path}"],
        )
        sw = context.wait_for_event("serviceworker") if not context.service_workers else context.service_workers[0]
        extension_id = sw.url.split("/")[2]
        yield context, extension_id
        context.close()
```

**실행:**
- 로컬: `pytest tests/e2e/test_playwright_extension.py -m e2e_playwright --headed`
- CI: 기본 skip (`addopts = "-m 'not llm and not e2e_playwright'"`)

**의존성:** Steps 1-8

---

## Step 10: Documentation Updates

**수정 파일:**

| 파일 | 작업 | 주요 변경 |
|------|:----:|----------|
| `docs/plans/phase3.0.md` | MODIFY | 초안 → 상세 계획 + DoD 완료 표시 |
| `docs/STATUS.md` | MODIFY | Phase 3 Complete, 커버리지 업데이트 |
| `docs/roadmap.md` | MODIFY | Phase 3 DoD 체크, Phase 4 deferred items 명시 |
| `README.md` | MODIFY | A2A 사용법, Development Status |
| `CLAUDE.md` | MODIFY | A2A 테스트 서버, 업데이트된 Quick Reference |
| `src/adapters/README.md` | MODIFY | A2A Client/Server 어댑터 섹션 |
| `tests/README.md` | NEW | 테스트 전략, E2E 섹션, Fake Adapter 패턴 |

**의존성:** Steps 1-9

---

## Part B 커밋 정책

```
feat(phase3): Step 8.1 - Extension MCP tools list UI
feat(phase3): Step 8.2 - Conversation history persistence
feat(phase3): Step 8.3 - Code block highlighting
feat(phase3): Step 8.4 - A2A agents display in Extension
feat(phase3): Step 9 - Playwright E2E tests
docs(phase3): Step 10 - Documentation updates
```

---

## Part B Definition of Done

### 기능

- [ ] Extension: MCP 서버별 도구 목록 표시
- [ ] Extension: Chat ↔ MCP Servers 탭 전환 시 대화 유지
- [ ] Extension: 코드 블록 신택스 하이라이팅
- [ ] Extension: A2A 에이전트 관리 UI
- [ ] Playwright E2E: 토큰 교환 → 채팅 → MCP/A2A 전체 흐름 통과

### 품질

- [ ] Extension Vitest >= 150 tests (현재 129)
- [ ] Backend regression 0
- [ ] 전체 코드 리뷰 완료

### 문서

- [ ] `docs/STATUS.md` Phase 3 Complete
- [ ] `docs/roadmap.md` Phase 3 DoD + Phase 4 항목
- [ ] `README.md` A2A 사용법 + 상태
- [ ] `CLAUDE.md` A2A 테스트 서버
- [ ] `tests/README.md` 생성

---

# 공통 섹션

## 리스크 및 대응

| 리스크 | 심각도 | 파트 | 대응 |
|--------|:------:|:----:|------|
| ADK A2A API 변경 | 🔴 높음 | A | Steps 2, 3, 6에서 웹 검색. 각 Step 후 커밋. |
| RemoteA2aAgent 직접 호출 불가 | 🔴 높음 | A | Step 3에서 웹 검색. 대안: httpx JSON-RPC 직접 호출 |
| to_a2a() blocking 서버 | 🟡 중간 | A | Step 6에서 웹 검색. 대안: 수동 Agent Card 엔드포인트 |
| Echo agent에 실제 LLM 필요 | 🟡 중간 | A | ADK FakeLLM 확인. 대안: 단순 HTTP echo + Agent Card |
| Playwright headed 모드 필수 | 🟡 중간 | B | `@pytest.mark.e2e_playwright` 기본 skip |
| highlight.js 번들 크기 | 🟢 낮음 | B | 필수 언어팩만 포함 |
| RegistryService 변경 시 MCP 테스트 깨짐 | 🟡 중간 | A | `endpoint_type` 기본값 MCP. TDD 먼저. |
| Endpoint agent_card 직렬화 | 🟢 낮음 | A | dict → JSON 자동 호환. 하위 호환 `data.get()` |

---

## 테스트 서버 정책

> **프로젝트 전역 정책:** **로컬 서버만 사용**. 외부 서버 금지.

| 서버 | URL | 실행 | 관리 | Marker |
|------|-----|------|:----:|--------|
| **MCP (Synapse)** | `http://127.0.0.1:9000/mcp` | `SYNAPSE_PORT=9000 python -m synapse` | 수동 | `@pytest.mark.local_mcp` |
| **A2A (Echo)** | `http://127.0.0.1:9001` | conftest subprocess | 자동 | `@pytest.mark.local_a2a` |

**MCP Server:** `C:\Users\sungb\Documents\GitHub\MCP_SERVER\MCP_Streamable_HTTP`
**A2A Agent:** `tests/fixtures/a2a_agents/echo_agent.py`

---

## Phase 4 이관 항목 (전체)

| 항목 | 이유 | Phase 3 대안 |
|------|------|-------------|
| LLM 호출 중 취소 gap | ADK Runner 취소 API 부재 | SSE 루프 break + 로그 경고 |
| SSE Connection Pooling | 단일 Extension 클라이언트 | 1 stream/client |
| Defer Loading (tools > 50) | MAX_ACTIVE_TOOLS=30 충분 | 기존 제한 유지 |
| Vector Search (도구 라우팅) | 임베딩 인프라 필요 | LLM 자체 선택 |
| Multi-user 지원 | localhost 단일 사용자 | DEFAULT_USER_ID |
| MCP 테스트 서버 내장화 | Synapse 잘 동작 | 외부 유지 |

---

## 검증 방법 (End-to-End)

### Part A 검증
```bash
# Backend 테스트 (A2A fixture 자동 시작)
pytest tests/ --cov=src --cov-fail-under=80 -v

# A2A integration 테스트만
pytest tests/integration/adapters/test_a2a_*.py -v

# 수동: curl로 A2A 엔드포인트 확인
curl -H "X-Extension-Token: <token>" http://localhost:8000/api/a2a/agents
curl http://localhost:8000/.well-known/agent.json
```

### Part B 검증
```bash
# Extension 테스트
cd extension && npm test

# E2E (수동 - 서버 + MCP + 빌드 필요)
cd extension && npm run build
pytest tests/e2e/test_playwright_extension.py -m e2e_playwright --headed
```

---

## 핵심 파일 요약

| 파일 | Steps | 작업 |
|------|:-----:|------|
| `src/domain/entities/endpoint.py` | 4 | `agent_card` 필드 추가 |
| `src/domain/services/registry_service.py` | 4 | A2A type, a2a_client 의존성 |
| `src/adapters/outbound/a2a/a2a_client_adapter.py` | 3 | NEW — A2aPort 구현 |
| `src/adapters/outbound/storage/json_endpoint_storage.py` | 4 | agent_card 직렬화 |
| `src/adapters/inbound/http/routes/a2a.py` | 5 | NEW — A2A CRUD routes |
| `src/adapters/inbound/a2a/a2a_server.py` | 6 | NEW — to_a2a() wrapper |
| `src/adapters/outbound/adk/orchestrator_adapter.py` | 7 | sub_agents 관리 |
| `src/config/container.py` | 7 | A2A adapter wiring |
| `src/adapters/inbound/http/app.py` | 5, 6, 7 | 라우터, lifespan |
| `src/adapters/inbound/http/routes/chat.py` | 1 | 구조화된 로깅 |
| `tests/fixtures/a2a_agents/echo_agent.py` | 2 | NEW — 테스트 에이전트 |
| `tests/e2e/test_playwright_extension.py` | 9 | NEW — Full E2E |

---

*Phase 3 계획 작성일: 2026-01-30*
*Phase 2.5 수동검증 결과 기반*
*분할: Part A (Steps 1-7, Backend) → Part B (Steps 8-10, UI+E2E)*
