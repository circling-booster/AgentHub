# AgentHub Project Status

> **Last Updated:** 2026-02-01 (Part A-D Complete)
> **Current Phase:** Phase 4 Part A-D Complete → Part E 예정
> **Active Branch:** `feature/phase-4`

---

## 📊 Quick Overview

| Metric | Status |
|--------|--------|
| **Overall Progress** | 95% (Phase 4 Part A-D Complete) |
| **Backend Coverage** | 91% (Target: 90%) |
| **Backend Tests** | 389 passed / 391 collected (pytest) |
| **Extension Tests** | 197 tests (Vitest) |
| **E2E Tests** | 7 scenarios (Playwright) |
| **Last Milestone** | Phase 4 Part C Complete (2026-01-31) |

---

## 🚀 Phase Progress

| Phase | Status | Progress | Key Deliverables |
|-------|:------:|:--------:|------------------|
| Phase 0 | ✅ Complete | 100% | Workflow Validation |
| Phase 1 | ✅ Complete | 100% | Domain Core (90.84% coverage) |
| Phase 1.5 | ✅ Complete | 100% | Security Layer (96% coverage) |
| Phase 2 | ✅ Complete | 100% | MCP Integration (88% coverage) |
| Phase 2.5 | ✅ Complete | 100% | Chrome Extension (129 tests + 수동검증) |
| Phase 3 | ✅ Complete | 100% | A2A Integration + UI Polish + E2E |
| **Phase 4 Part A** | **✅ Complete** | **100%** | **Critical Fixes (StreamChunk, A2A Wiring, Error Typing, Auto-Restore)** |
| **Phase 4 Part B** | **✅ Complete** | **100%** | **Observability (ErrorCode, LLM Logging, Tool Tracing, Structured Logging)** |
| **Phase 4 Part C** | **✅ Complete** | **100%** | **Dynamic Intelligence (Context-Aware Prompts, Tool Retry)** |
| **Phase 4 Part D** | **✅ Complete** | **100%** | **Reliability & Scale (A2A Health, Defer Loading)** |
| Phase 4 Part E | 📋 Planned | 0% | Production Hardening |
| Phase 5 | 📋 Planned | 0% | MCP Advanced, Vector Search, Multi-user |

**범례:**
✅ Complete | 🚧 In Progress | 📋 Planned | ⏸️ Paused | ❌ Blocked

---

## 🎯 Phase 2.5 완료 요약

**수동검증 일자:** 2026-01-30
**결과:** 핵심 기능 모두 동작 확인, 6건 버그 발견 및 수정

### 검증 완료 항목 ✅

- [x] Extension 설치 시 서버와 자동 토큰 교환 성공
- [x] Sidepanel에서 채팅 응답 수신 (OpenAI gpt-4o-mini)
- [x] MCP 서버 등록/해제 동작
- [x] 브라우저 재시작 후 토큰 재교환 및 정상 동작
- [x] 20초+ 응답 처리 (Offscreen Document)
- [x] Vitest 129 tests 전체 통과
- [x] `extension/README.md` 생성 완료

### 수동검증 중 발견된 버그 (모두 수정 완료)

| Bug | 원인 | 수정 |
|-----|------|------|
| Offscreen 문서 경로 불일치 | WXT 빌드 경로와 코드 불일치 | `constants.ts` |
| SSE 인증 토큰 누락 | `X-Extension-Token` 헤더 미포함 | `sse.ts` |
| Offscreen 로딩 레이스 컨디션 | 메시지 전송 시 문서 미준비 | `background-handlers.ts` |
| Offscreen `storage.session` 미지원 | 컨텍스트 제한 (Background→파라미터 전달로 변경) | `sse.ts`, `offscreen-handlers.ts`, `background.ts` |
| LLM 모델 설정 오류 | `anthropic` → `openai/gpt-4o-mini` | `settings.py`, `default.yaml` |
| API 키 환경변수 미반영 | pydantic-settings가 os.environ 미설정 | `app.py` |

### Phase 3으로 이관된 항목

- MCP Tools 목록 UI 표시 (Backend API 존재, Extension UI 미구현)
- 대화 히스토리 탭 전환 시 유지 (React state만 사용, 영속화 미구현)
- 코드 블록 하이라이팅 및 도구 실행 UI

---

## 🎯 Phase 3 Part A 완료 요약

**완료 일자:** 2026-01-30
**결과:** A2A 전체 스택 구현 완료, DoD 18/18 항목 (100%) 통과

### 완료된 Steps (2-7)

| Step | 내용 | 테스트 | 상태 |
|:----:|------|:------:|:----:|
| **1** | Backend Stability Hardening | 5개 테스트 | ⚠️ 기존 구현 활용 |
| **2** | A2A Echo Agent Fixture | 3개 테스트 | ✅ |
| **3** | A2aClientAdapter | 18개 테스트 (unit 11 + integration 7) | ✅ |
| **4** | RegistryService A2A 지원 | 6개 테스트 | ✅ |
| **5** | A2A HTTP Routes | 10개 테스트 | ✅ |
| **6** | A2A Server Exposure | 3개 테스트 | ✅ |
| **7** | Orchestrator A2A Integration | 4개 테스트 | ✅ |

### 핵심 성과

- ✅ **A2A 전체 스택**: Client Adapter, Server Exposure, Orchestrator sub_agents, HTTP CRUD API
- ✅ **안정성 강화**: Zombie Task 취소, Thread Isolation, 구조화된 로깅
- ✅ **테스트 품질**: 47개 A2A 테스트 (315 tests total, 99.7% 통과율)
- ✅ **커버리지 향상**: 89.55% → 90.63% (+1.08%p, 목표 80% 대비 +10.63%p)
- ✅ **아키텍처 원칙**: Domain Layer 순수성 유지, Hexagonal Architecture 준수

### Part B 완료 요약

**완료 일자:** 2026-01-30
**결과:** Extension UI 완성 + Playwright E2E 테스트 7개 시나리오

| Step | 내용 | 테스트 | 상태 |
|:----:|------|:------:|:----:|
| **8.1** | MCP Tools 목록 UI | 14 tests (McpServerManager) | ✅ |
| **8.2** | 대화 히스토리 유지 | 13 tests (useChat) | ✅ |
| **8.3** | 코드 블록 하이라이팅 | 5 tests (CodeBlock) | ✅ |
| **8.4** | A2A 에이전트 표시 | 12 tests (A2aAgentManager) | ✅ |
| **9** | Playwright E2E Tests | 7 scenarios | ✅ |

### 핵심 성과

- ✅ **Extension 기능 완성**: MCP Tools 목록, 대화 유지, 코드 하이라이팅, A2A 관리 UI
- ✅ **테스트 품질**: Vitest 180 tests (129→180), Playwright 7 E2E 시나리오
- ✅ **E2E 자동화**: Extension → Server → MCP/A2A 전체 흐름 검증
- ✅ **문서화 완료**: tests/README.md, src/adapters/README.md 생성

---

## 🎯 Phase 4 Part A 완료 요약

**완료 일자:** 2026-01-31
**결과:** Critical Fixes 완료 (A2A Wiring, StreamChunk, Typed Error, Auto-Restore)

### 완료된 Steps (1-4)

| Step | 내용 | 테스트 | 상태 |
|:----:|------|:------:|:----:|
| **1** | A2A Agent LLM Wiring Fix | 4개 unit tests | ✅ |
| **2** | SSE Event Streaming (StreamChunk) | 11개 entity tests + 6개 Vitest | ✅ |
| **3** | Typed Error Propagation | 4개 unit tests | ✅ |
| **4** | Endpoint Auto-Restore on Startup | 4개 unit tests | ✅ |

### 핵심 성과

- ✅ **A2A Wiring 수정**: RegistryService에 OrchestratorPort 주입, A2A 등록 시 LLM 자동 연결
- ✅ **StreamChunk 도메인 엔티티**: 순수 Python, SSE 이벤트 타입 확장 (tool_call, tool_result, agent_transfer)
- ✅ **Typed Error 전파**: 에러 코드별 사용자 친화 메시지 (LlmRateLimitError, EndpointConnectionError 등)
- ✅ **엔드포인트 자동 복원**: 서버 재시작 시 저장된 MCP/A2A 엔드포인트 자동 재연결
- ✅ **Extension UI 완성**: ToolCallIndicator 컴포넌트, MessageBubble에 toolCalls/agentTransfer 표시
- ✅ **테스트 품질**: Backend 342 passed (90.18% coverage), Extension 197 tests
- ✅ **TDD 준수**: Red-Green-Refactor 사이클 엄격히 따름

---

## 🎯 Phase 4 Part C 완료 요약

**완료 일자:** 2026-01-31
**결과:** Dynamic Intelligence 구현 완료 (Context-Aware System Prompt + Tool Retry Logic)

### 완료된 Steps (8-9)

| Step | 내용 | 테스트 | 상태 |
|:----:|------|:------:|:----:|
| **8** | Context-Aware System Prompt | 4개 unit + 1개 integration | ✅ |
| **9** | Tool Execution Retry Logic | 6개 unit tests | ✅ |

### 핵심 성과

- ✅ **동적 시스템 프롬프트**: 등록된 MCP 도구 목록 및 A2A 에이전트 정보를 instruction에 자동 포함
  - `DynamicToolset.get_registered_info()` 메서드로 엔드포인트별 도구 정보 제공
  - `_rebuild_agent()`에서 동적 instruction 생성 (MCP Tools + A2A Agents 섹션)
  - 도구/에이전트 추가/제거 시 instruction 자동 갱신
- ✅ **도구 실행 재시도 로직**: Exponential backoff로 일시적 에러 자동 재시도
  - 일시적 에러 (ConnectionError, TimeoutError) 최대 N회 재시도
  - 재시도 간격: 1s, 2s, 4s (exponential backoff)
  - 영구 에러 (ValueError, RuntimeError) 즉시 실패
  - 설정 가능: `mcp.max_retries`, `mcp.retry_backoff_seconds` (default.yaml)
- ✅ **테스트 품질**: 229 unit/integration tests passed (Unit: 219, Integration: 10)
  - 신규 테스트 10개 (test_dynamic_toolset_info.py: 4, test_tool_retry.py: 6)
  - Regression 0 (기존 테스트 전체 통과)
- ✅ **TDD 준수**: Red-Green-Refactor 사이클 엄격히 따름

### 구현 파일

- `src/adapters/outbound/adk/dynamic_toolset.py`: `get_registered_info()`, 재시도 로직
- `src/adapters/outbound/adk/orchestrator_adapter.py`: `_build_dynamic_instruction()`
- `src/config/settings.py`: `McpSettings` (max_retries, retry_backoff_seconds)
- `configs/default.yaml`: 재시도 기본값 (max_retries=2, backoff=1.0)

### 테스트 파일

- `tests/unit/adapters/test_dynamic_toolset_info.py`: 도구 정보 조회 테스트
- `tests/unit/adapters/test_tool_retry.py`: 재시도 로직 테스트
- `tests/integration/adapters/test_orchestrator_adapter.py`: 동적 instruction 통합 테스트
- `tests/integration/adapters/test_dynamic_toolset.py`: 캐싱 테스트 수정

---

## 🎯 Phase 4 Part B 완료 요약

**완료 일자:** 2026-01-31
**결과:** Observability 구현 완료 (ErrorCode Constants + LLM Logging + Tool Tracing + Structured Logging)

### 완료된 Steps (0, 5-7)

| Step | 내용 | 테스트 | 상태 |
|:----:|------|:------:|:----:|
| **0** | ErrorCode 상수화 (Backend + Extension) | - | ✅ |
| **5** | LiteLLM CustomLogger 콜백 로깅 | 4개 unit tests | ✅ |
| **6** | Tool Call Tracing (SQLite 저장 + API) | 5개 tests (3 unit + 2 API) | ✅ |
| **7** | Structured Logging (JSON 포맷 옵션) | 4개 unit tests | ✅ |

### 핵심 성과

- ✅ **ErrorCode 타입 안전성**: Backend (constants.py) + Extension (constants.ts) 일치
- ✅ **LLM 호출 가시성**: 모델명, 토큰 수, 지연시간 로깅
- ✅ **Tool Call 추적**: SQLite `tool_calls` 테이블 + API 조회 (`GET /api/conversations/{id}/tool-calls`)
- ✅ **구조화된 로깅**: JSON 포맷 옵션 (settings.observability.log_format = "json")
- ✅ **테스트 품질**: 13 tests (4 LiteLLM + 5 Tracing + 4 Logging)
- ✅ **TDD 준수**: Red-Green-Refactor 사이클 엄격히 따름

### 구현 파일

- `src/domain/constants.py`: ErrorCode 클래스
- `src/adapters/outbound/adk/litellm_callbacks.py`: CustomLogger
- `src/adapters/outbound/storage/sqlite_conversation_storage.py`: tool_calls 테이블
- `src/config/logging_config.py`: JsonFormatter
- `extension/lib/constants.ts`: ErrorCode enum

### 테스트 파일

- `tests/unit/adapters/test_litellm_callbacks.py`: 4 tests
- `tests/integration/adapters/test_tool_call_tracing.py`: 3 tests
- `tests/integration/adapters/test_tool_call_api.py`: 2 tests
- `tests/unit/config/test_logging_config.py`: 4 tests

---

## 🎯 Phase 4 Part D 완료 요약

**완료 일자:** 2026-01-31
**결과:** Reliability & Scale 구현 완료 (A2A Health Monitoring + Defer Loading)

### 완료된 Steps (10-11)

| Step | 내용 | 테스트 | 상태 |
|:----:|------|:------:|:----:|
| **10** | A2A Agent Health Monitoring | 3개 unit tests | ✅ |
| **11** | Defer Loading (MAX_ACTIVE_TOOLS 100) | 4개 tests | ✅ |

### 핵심 성과

- ✅ **A2A Health Check**: HealthMonitorService 타입별 health check 분기 (MCP/A2A)
- ✅ **Defer Loading**: DeferredToolProxy로 메타데이터만 로드, 실행 시 Lazy Loading
- ✅ **확장성 향상**: MAX_ACTIVE_TOOLS 30 → **100** (3배 증가)
- ✅ **테스트 품질**: 7 tests (3 Health + 4 Defer)
- ✅ **TDD 준수**: Red-Green-Refactor 사이클 엄격히 따름

### 구현 파일

- `src/domain/services/health_monitor_service.py`: A2A 타입 분기
- `src/adapters/outbound/adk/dynamic_toolset.py`: DeferredToolProxy, MAX_ACTIVE_TOOLS 100
- `src/config/settings.py`: McpSettings (max_active_tools, defer_loading_threshold)
- `configs/default.yaml`: 설정 기본값

### 테스트 파일

- `tests/unit/domain/services/test_health_monitor_service.py`: 3+ tests
- `tests/integration/adapters/test_dynamic_toolset.py`: 4+ tests

---

## 🧪 Test Coverage Summary

| Component | Coverage | Target | Status |
|-----------|:--------:|:------:|:------:|
| Domain Core | 90.84% | 80% | ✅ |
| Security Layer | 96% | - | ✅ |
| MCP Integration | 88% | 70% | ✅ |
| A2A Integration | 90.18% | 80% | ✅ |
| Phase 4 Part A | 90.18% | 90% | ✅ |
| Extension (Vitest) | 197 tests | - | ✅ |
| Backend (pytest) | 342 passed / 355 total | - | ✅ |
| E2E Tests (Playwright) | 7 scenarios | - | ✅ |
| E2E Tests (Manual) | 10 passed, 2 skipped | - | ✅ 수동검증 완료 |

**Overall Backend Coverage:** 91% (Target: 90%)

---

## 📅 Recent Milestones

- **2026-02-01**: Phase 4 Part A-D Complete - Critical Fixes + Observability + Dynamic Intelligence + Reliability (91% coverage, 389 tests)
- **2026-01-31**: Phase 4 Part D Complete - Reliability & Scale (A2A Health, Defer Loading)
- **2026-01-31**: Phase 4 Part C Complete - Dynamic Intelligence (Context-Aware Prompts, Tool Retry)
- **2026-01-31**: Phase 4 Part B Complete - Observability (ErrorCode, LLM Logging, Tool Tracing, Structured Logging)
- **2026-01-31**: Phase 4 Part A Complete - Critical Fixes (StreamChunk, A2A Wiring, Error Typing, Auto-Restore)
- **2026-01-30**: Phase 3 Complete - A2A Integration + UI Polish + E2E (180 Extension tests, 7 E2E scenarios)
- **2026-01-30**: Phase 3 Part A Complete - A2A Core Integration (90.63% coverage, 315 tests)
- **2026-01-30**: Phase 2.5 Complete - 수동검증 완료 (6건 버그 수정)
- **2026-01-29**: Phase 2 Complete - MCP Integration (88% coverage)
- **2026-01-28**: Phase 1.5 Complete - Security Layer (96% coverage)

---

## ⚡ Next Actions (Phase 4)

### Phase 4 구조 (Part A-E)

| Part | Steps | 초점 | 상태 |
|:----:|:-----:|------|:----:|
| **A** | **1-4** | **Critical Fixes (A2A Wiring, StreamChunk, Error Typing, Auto-Restore)** | **✅ 완료** |
| **B** | **0, 5-7** | **Observability (Error Code Constants, LLM Logging, Tool Tracing, Structured Logging)** | **✅ 완료** |
| **C** | **8-9** | **Dynamic Intelligence (System Prompt, Tool Retry)** | **✅ 완료** |
| **D** | **10-11** | **Reliability & Scale (A2A Health, Defer Loading)** | **✅ 완료** |
| E | 12-16 | Production Hardening (Gateway, Cost Tracking, Semantic Routing, Chaos Tests, Plugin) | 💡 초안 |

### Part A 완료 (2026-01-31) ✅

| 구현 항목 | 상태 |
|----------|:----:|
| A2A Wiring 수정 (RegistryService → OrchestratorPort) | ✅ |
| StreamChunk 도메인 엔티티 (tool_call, tool_result, agent_transfer) | ✅ |
| Typed Error 전파 (LlmRateLimitError, EndpointConnectionError 등) | ✅ |
| 엔드포인트 자동 복원 (서버 재시작 시 MCP/A2A 재연결) | ✅ |
| Extension ToolCallIndicator 컴포넌트 | ✅ |
| Backend 91% coverage, Extension 197 tests | ✅ |

**📋 Detailed Plans:**
- [phase4.0.md](plans/phase4.0.md) (Master Plan)
- [phase4.0-partA.md](plans/phase4.0-partA.md) ✅ | [partB](plans/phase4.0-partB.md) ✅ | [partC](plans/phase4.0-partC.md) ✅ | [partD](plans/phase4.0-partD.md) ✅ | [partE](plans/phase4.0-partE.md) 💡

---

## 🚧 Known Issues & Blockers

**현재 알려진 이슈 없음** ✅

---

## ⏸️ Deferred Features

### Event-Driven Architecture (Job Queue) — 보류 중

**보류 사유:**
- AgentHub는 **단일 사용자** 로컬 앱 (Multi-Tenancy 미지원)
- 대부분 작업이 **30초 이내** 완료 (Offscreen Document로 충분, 최대 5분 지원)
- Job Queue 도입 시 **복잡도 증가** (Redis, Celery, Worker 프로세스 관리)

**재검토 시점:**
- Multi-User Support 구현 시 (Phase 5+)
- 장시간 작업 (1분 이상) 비율이 20% 초과 시
- 백그라운드 작업 요구사항 발생 시

**현재 대안:**
- Offscreen Document (최대 5분 작업 지원)
- 5분 초과 시: Job ID 반환 + 폴링 API (`GET /api/jobs/{id}/status`)

**장단점:**
- ✅ 장점: 비동기 작업 처리, 확장성, 재시도 메커니즘
- ❌ 단점: 복잡도 증가, 디버깅 어려움, 인프라 비용

**상세:** [phase4.0-partE.md](plans/phase4.0-partE.md#보류-항목-event-driven-architecture-job-queue)

---

## 📚 Documentation Status

| Document | Status | Last Updated |
|----------|:------:|:------------:|
| README.md | ✅ Up-to-date | 2026-01-28 |
| CLAUDE.md | ✅ Up-to-date | 2026-01-31 |
| docs/roadmap.md | ✅ Up-to-date | 2026-01-31 |
| docs/architecture.md | ✅ Up-to-date | 2026-01-28 |
| docs/plans/phase3.0.md | ✅ Complete | 2026-01-30 |
| docs/plans/phase4.0.md | ✅ Updated | 2026-01-31 |
| docs/plans/phase4.0-partE.md | 💡 Draft | 2026-01-31 |
| src/README.md | ⚠️ Pending | - |
| src/adapters/README.md | ✅ Created | 2026-01-30 |
| tests/README.md | ✅ Created | 2026-01-30 |
| extension/README.md | ✅ Created | 2026-01-29 |

---

## 🔗 Quick Links

- [Overall Roadmap](roadmap.md)
- [Phase 3 Plan](plans/phase3.0.md)
- [Phase 4 Plan](plans/phase4.0.md)
- [Architecture Overview](guides/architecture.md)
- [Implementation Guide](guides/implementation-guide.md)
- [All Guides](guides/)
- [Test Reports](../tests/)

---

*This document serves as the single source of truth for project status.*
*Update this file on each Phase milestone completion.*
