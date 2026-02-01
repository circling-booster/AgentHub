# Phase 4: Critical Fixes, Observability, Dynamic Intelligence, Reliability

> **상태:** 📋 Planned
> **선행 조건:** Phase 3 Complete (90.63% coverage, 315 backend tests, 180 extension tests)
> **목표:** A2A Wiring 버그 수정, 관찰성 확보, 동적 인텔리전스, 안정성 강화
> **분할:** Part A-D (개별 파일)
> **E2E:** Playwright 별도 작업 불필요 (기존 7개 시나리오 재활용, pytest + Vitest 완결)

---

## 확정된 의사결정 (ADR)

### ADR-1: A2A Wiring → Option B (RegistryService에 OrchestratorPort 주입)

**문제:** `POST /api/a2a/agents` → Agent Card만 저장, `orchestrator.add_a2a_agent()` 미호출
**결정:** RegistryService에 `orchestrator: OrchestratorPort | None = None` 주입
**이유:** MCP 패턴과 일관성, 인터페이스 무관 동작, 단위 테스트 가능

### ADR-2: SSE Events → 도메인 StreamChunk 엔티티

**문제:** `OrchestratorPort.process_message()` → `AsyncIterator[str]` (텍스트만)
**결정:** `StreamChunk` 순수 Python dataclass 도입, `AsyncIterator[StreamChunk]` 반환
**이유:** 도메인 표현력 향상, 타입 안전성, 확장성. 헥사고날 위반 아님 (순수 Python)

### ADR-3: MCP 고급 기능 → Phase 5로 연기

**문제:** ADK MCPToolset이 Resources, Prompts, Sampling 미지원 (2026-01 기준)
**결정:** Phase 5로 연기. Port 인터페이스만 예약
**이유:** ADK 미지원 상태에서 자체 구현은 충돌 위험

### ADR-4: LLM 로깅 → LiteLLM CustomLogger

**결정:** `litellm.callbacks = [AgentHubLogger()]` 패턴
**이유:** 로컬 앱에 적합, 프라이버시 보장, 구현 복잡도 낮음

---

## Phase 구조

| Part | 파일 | Steps | 초점 |
|:----:|------|:-----:|------|
| A | [partA.md](partA.md) | 1-4 | Critical Fixes |
| B | [partB.md](partB.md) | 5-7 | Observability |
| C | [partC.md](partC.md) | 8-9 | Dynamic Intelligence |
| D | [partD.md](partD.md) | 10-11 | Reliability & Scale |
| E | [phase4.0-partE.md](phase4.0-partE.md) | 12-16 | Production Hardening (초안) |

---

## Step 번호 매핑 (초안 → 최종)

| 최종 Step | 초안 Step | Title | Part |
|:---------:|:---------:|-------|:----:|
| 1 | 1 | A2A Agent LLM Wiring Fix | A |
| 2 | 2 | SSE Event Streaming (StreamChunk) | A |
| 3 | 3 | Typed Error Propagation | A |
| **4** | **11** | **Endpoint Auto-Restore on Startup** | **A** |
| 5 | 4 | LiteLLM Callback Logging | B |
| 6 | 5 | Tool Call Tracing (DB) | B |
| 7 | 6 | Structured Logging Improvements | B |
| 8 | 7 | Context-Aware System Prompt | C |
| 9 | 8 | Tool Execution Retry Logic | C |
| 10 | 9 | A2A Agent Health Monitoring | D |
| 11 | 10 | Defer Loading (Large-Scale Tools) | D |
| **12** | - | **MCP Gateway Pattern** | **E** |
| **13** | - | **Cost Tracking & Budgeting** | **E** |
| **14** | - | **Semantic Tool Routing** | **E** |
| **15** | - | **Chaos Engineering Tests** | **E** |
| **16** | - | **Plugin System (Mock)** | **E** |

---

## Phase 시작 전 체크리스트

### 선행 조건

- [ ] 기존 테스트 전체 통과: `pytest tests/ -q --tb=line -x`
- [ ] Coverage >= 80%: `pytest --cov=src --cov-fail-under=80 -q` (현재 90.63%)
- [ ] 브랜치: `feature/phase-4` 생성

### 필수 웹 검색 (Plan 단계)

- [ ] ADK Event API: `get_function_calls()`, `get_function_responses()`, `is_final_response()` 시그니처
- [ ] LiteLLM CustomLogger API: `log_success_event()`, `log_failure_event()` 시그니처
- [ ] ADK RemoteA2aAgent health check 패턴

---

## 전체 실행 순서 및 의존성

**권장 실행 방식: 순차 진행 (Claude Code 단일 세션 최적화)**

```
Part A (Critical Fixes) — 순차 실행 (권장: Step 1 → 4 → 2 → 3)
  Step 1: A2A Wiring Fix           ← 기반 (Steps 2, 4 선행)
  Step 4: Endpoint Auto-Restore    ← Step 1 필요 (orchestrator 주입)
  Step 2: SSE StreamChunk          ← 가장 큰 변경, Step 1 필요
  Step 3: Error Typing             ← Step 2 이후 (병렬 가능)

Part B (Observability) — Part A 이후 (⚡ Part C, D와 병렬 가능)
  Step 5: LiteLLM Callbacks        ← 독립
  Step 6: Tool Call Tracing        ← Step 2 이후 (StreamChunk 이벤트 필요)
  Step 7: Structured Logging       ← 독립

Part C (Dynamic Intelligence) — Part A 이후 (⚡ Part B, D와 병렬 가능)
  Step 8: Dynamic System Prompt    ← Step 1 이후 (A2A 연결 필요)
  Step 9: Tool Retry Logic         ← 독립

Part D (Reliability) — Part A 이후 (⚡ Part B, C와 병렬 가능)
  Step 10: A2A Health Monitoring   ← Step 1 이후
  Step 11: Defer Loading           ← 독립
```

### 병렬화 옵션 (팀 환경 또는 속도 우선 시)

Part A 완료 후 다음 그룹을 병렬 실행 가능:

```
Group 1 (Part A 완료 즉시 시작 가능):
  ├─ Part B: Step 5, 7
  ├─ Part C: Step 8, 9
  ├─ Part D: Step 10, 11
  └─ Part E: Step 12, 16

Group 2 (Part A Step 2 완료 후):
  └─ Part B: Step 6

Group 3 (Part D Step 11 완료 후):
  └─ Part E: Step 14

Group 4 (모든 기능 완료 후):
  └─ Part E: Step 15
```

**권장:** 단일 개발자 환경에서는 순차 진행 (명확한 DoD, 컨텍스트 스위칭 최소화)

---

## 테스트 전략

| 테스트 유형 | 대상 | 커버리지 목표 |
|-----------|------|:----------:|
| Unit | Domain Layer (StreamChunk, RegistryService 확장) | 90%+ |
| Integration | Adapters (LiteLLM callbacks, Tool Tracing, Health Monitor) | 80%+ |
| Extension (Vitest) | hooks, components (ToolCallIndicator, ErrorDisplay) | 190+ tests |
| E2E (Playwright) | 기존 7개 시나리오 재활용 | Critical Path |

### 예상 테스트 추가

| Part | 신규 Backend | 수정 Backend | 신규 Vitest | 누적 Backend | 누적 Vitest |
|:----:|:-----------:|:----------:|:----------:|:-----------:|:----------:|
| A | ~19 | ~30 | ~10 | ~336 | ~190 |
| B | ~12 | ~3 | 0 | ~348 | ~190 |
| C | ~9 | ~2 | 0 | ~357 | ~190 |
| D | ~7 | ~2 | 0 | ~364 | ~190 |
| **합계** | **~47** | **~37** | **~10** | **~364** | **~190** |

커버리지 목표: >= 90% (현재 90.63% 유지)

---

## 검증 방법

### 자동 검증
```bash
# 전체 테스트 + 커버리지
pytest tests/ --cov=src --cov-fail-under=80 -q --tb=line -x

# Part A 검증
pytest tests/unit/domain/services/test_registry_service.py -q
pytest tests/unit/domain/entities/test_stream_event.py -q
pytest tests/integration/adapters/test_endpoint_restore.py -q

# Part B 검증
pytest tests/unit/adapters/test_litellm_callbacks.py -q
pytest tests/integration/adapters/test_tool_call_tracing.py -q

# Extension 검증
cd extension && npm test
```

### 수동 검증
1. MCP 서버 등록 → 채팅에서 도구 사용 → SSE에 tool_call/tool_result 이벤트 확인
2. A2A 에이전트 등록 → LLM이 sub_agent 호출 → SSE에 agent_transfer 이벤트 확인
3. 서버 로그에서 LLM 토큰 수, 도구 호출 이력 확인
4. 서버 재시작 후 엔드포인트 자동 복원 확인

---

## Phase 5 Scope (연기 항목)

Phase 4 이후 + 외부 의존성(ADK 기능) 충족 시 진행:

| 항목 | 의존성 | 설명 |
|------|--------|------|
| MCP Advanced Features | ADK MCPResourceSet (#1779) | Resources, Prompts, Sampling |
| Vector Search | Phase 4 Step 11 (Defer Loading) | 도구 시맨틱 라우팅, 임베딩 기반 |
| Multi-user 지원 | 인증 인프라 결정 | 사용자별 대화/엔드포인트 격리 |
| SSE Connection Pooling | Phase 4 완료 | Backpressure 메커니즘 |
| LLM 호출 중 취소 | ADK Runner 취소 API | asyncio.Task 래핑 + 캐스케이딩 |
| **Event-Driven Architecture** | **Multi-User 또는 장시간 작업 요구** | **Job Queue (Redis, Celery) - 현재 Offscreen Document로 충분** |

### 보류: Event-Driven Architecture (Job Queue)

**보류 이유:**
- AgentHub는 단일 사용자 로컬 앱 (Multi-Tenancy 미지원)
- 대부분 작업이 30초 이내 완료 (Offscreen Document로 충분, 최대 5분 지원)
- Job Queue 도입 시 복잡도 증가 (Redis, Celery, Worker 프로세스 관리)

**재검토 시점:**
- Multi-User Support 구현 시 (Phase 5+)
- 장시간 작업 (1분 이상) 비율이 20% 초과 시
- 백그라운드 작업 요구사항 발생 시 (예: 일괄 데이터 처리)

**장단점:**
- ✅ 장점: 비동기 작업 처리, 확장성, 재시도 메커니즘
- ❌ 단점: 복잡도 증가, 디버깅 어려움, 인프라 비용

**현재 대안:** Offscreen Document (5분 제한) + 폴링 API (`GET /api/jobs/{id}/status`)

상세: [phase4.0-partE.md](phase4.0-partE.md#보류-항목-event-driven-architecture-job-queue)

---

## 핵심 진단 결과 (초안에서 계승)

### Bug #1: A2A 에이전트가 LLM에 연결되지 않음 (CRITICAL)
- **파일:** `src/adapters/inbound/http/routes/a2a.py:54`
- **원인:** `POST /api/a2a/agents` → Agent Card만 저장, `orchestrator.add_a2a_agent()` 미호출
- **수정:** Part A Step 1

### Bug #2: 관찰성 부재 (HIGH)
- SSE 이벤트가 "text" 타입만 전송, 도구 호출 이벤트 필터링됨
- LLM API request/response 로깅 없음
- **수정:** Part A Step 2 + Part B Steps 5-7

### Bug #3: 시스템 프롬프트가 너무 일반적
- `"You are a helpful assistant with access to various tools."` — 도구/에이전트 목록 미포함
- **수정:** Part C Step 8

### 확인된 정상 동작
- ADK `tools=[BaseToolset]` 패턴 정상
- DI Container Singleton: RegistryService와 OrchestratorAdapter가 동일 DynamicToolset 공유
- MCP 등록 흐름: `add_mcp_server()` → `_mcp_toolsets` → `get_tools()` 반환

---

## 참고 자료

- [ADK Events](https://google.github.io/adk-docs/events/)
- [ADK Runtime](https://google.github.io/adk-docs/runtime/)
- [ADK MCP Tools](https://google.github.io/adk-docs/tools-custom/mcp-tools/)
- [ADK Multi-Agent Patterns](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
- [LiteLLM Callbacks](https://docs.litellm.ai/docs/observability/callbacks)
- [LiteLLM Custom Callbacks](https://docs.litellm.ai/docs/observability/custom_callback)
- [MCP Specification (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25)
- [A2A Protocol](https://a2a-protocol.org/latest/)
- [ADK MCP Resources Issue #1779](https://github.com/google/adk-python/issues/1779)

---

*Phase 4 계획 확정일: 2026-01-31*
*초안 기반: phase4.0(초안).md → docs/archive/ 이동*
