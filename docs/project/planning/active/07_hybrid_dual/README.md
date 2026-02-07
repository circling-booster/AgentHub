# Plan 07: Hybrid-Dual Architecture (Revised)

## Overview

**목표:** ADK Track(MCP Tools + A2A)과 SDK Track(Resources/Prompts/Sampling/Elicitation)을 병행하는 Hybrid-Dual 아키텍처 구현

**현재 상태:**
- ADK Track: 작동 중 (DynamicToolset, GatewayToolset, RemoteA2aAgent)
- SDK Track: 없음 (McpClientAdapter, SamplingService 등 도입 필요)

**핵심 원칙:**
- TDD (테스트 먼저 작성 - Red → Green → Refactor)
- 헥사고날 아키텍처 (Domain 레이어는 순수 Python)
- MCP SDK v1.25+ 사용 (`mcp>=1.25,<2`)
- **Method C (Callback-Centric)**: LLM 호출은 Route의 approve 핸들러에서 수행, 결과를 Event 시그널로 콜백에 전달
- **Playground-First Testing** (Phase 6+: HTTP API와 Playground UI를 함께 구현)

---

## Method C: Callback-Centric Architecture

**핵심 변경사항:**
- LLM 호출: Route의 `/api/sampling/requests/{id}/approve` 핸들러에서 OrchestratorPort.generate_response() 호출
- 결과 전달: SamplingService.approve(request_id, llm_result) → asyncio.Event 시그널
- 콜백 대기: RegistryService._create_sampling_callback() 클로저 내부에서 wait_for_response() → MCP 서버에 결과 반환
- Domain 순수성 유지: SamplingService는 순수 HITL 큐 역할만 수행

**장점:**
- 헥사고날 아키텍처 준수 (Route는 OrchestratorPort를 통해 LLM 호출)
- 미래 대비 (ADK가 sampling을 native 지원하면 콜백만 변경)
- 단순성 (콜백은 대기+반환만)

---

## Playground-First Testing

**원칙:** Phase 6-7에서 구현되는 HTTP API와 SSE 이벤트는 Playground로 즉시 테스트합니다.

**Phase 6 (HTTP Routes + Playground):**
- Backend Routes + Playground UI Tabs (Resources, Prompts, Sampling, Elicitation)
- Playwright E2E Tests (즉시 회귀 방지)

**Phase 7 (SSE Events + Playground):**
- StreamChunk 확장 (Backend) + Playground SSE Verification
- Extension UI는 제외 (Production Phase로 연기)

**Verification:**
```bash
# Playground E2E Tests
pytest tests/e2e/test_playground.py -v -k "resources or prompts or sampling or elicitation"

# JavaScript Unit Tests
cd tests/manual/playground && npm test
```

**장점:**
- 즉각적인 피드백 (Extension 빌드 불필요)
- 빠른 회귀 테스트 (< 10초)
- API 계약 조기 검증

---

## Implementation Phases

각 Phase의 상세 내용은 아래 링크를 참조하세요:

| Phase | 설명 | Playground | Status | 문서 |
|-------|------|------------|--------|------|
| **Phase 1** | Domain Entities | - | ✅ | [01_domain_entities.md](01_domain_entities.md) |
| **Phase 2** | Port Interface + Fake | - | ✅ | [02_port_interface.md](02_port_interface.md) |
| **Phase 3** | Domain Services (Method C) | - | ✅ | [03_domain_services.md](03_domain_services.md) |
| **Phase 4** | Adapter Implementation + Synapse Tests | - | ✅ | [04_adapter_implementation.md](04_adapter_implementation.md) |
| **Phase 5** | Integration (Method C Callback) | - | ✅ | [05_integration.md](05_integration.md) |
| **Phase 6** | HTTP Routes + Playground UI | ✅ | 🔄 | [06_http_routes.md](06_http_routes.md) |
| **Phase 7** | SSE Events + Playground | ✅ | ⏸️ | [07_sse_events_playground.md](07_sse_events_playground.md) |

**Playground Column:**
- ✅ - Playground UI/테스트를 백엔드와 함께 구현
- - (dash) - 해당 없음 (Domain layer)

**Status Icons:**
- ⏸️ **Pending** - 대기 중
- 🔄 **In Progress** - 진행 중 (항상 1개만)
- ✅ **Done** - 완료

**Phase Update Workflow:**
1. Phase 시작: Status를 ⏸️ → 🔄로 변경
2. Phase 완료: Status를 🔄 → ✅로 변경, Git 커밋: `docs: complete phase N - {phase_name}`

**제외 (Extension → Production Preparation Phase):**
- extension/lib/types.ts, api.ts (Sampling/Elicitation 타입/API)
- HitlModal 컴포넌트, SSE 이벤트 핸들러

**순서대로 구현 가능:** Phase 2에서 Fake를 함께 작성하여 Phase 3 테스트에서 사용

---

## Verification

### Unit Tests
```bash
pytest tests/unit/ -q --tb=line -x
```

### Integration Tests
```bash
# Synapse 통합 (로컬 MCP 서버 필요)
pytest tests/integration/test_mcp_client_adapter.py -m local_mcp -v

# LLM 통합 (API 키 필요)
pytest tests/integration/test_orchestrator_generate.py -m llm -v

# Dual-Track (Synapse + LLM)
pytest tests/integration/test_dual_track.py -m "local_mcp and llm" -v

# 모든 Integration 테스트
pytest tests/integration/ -q --tb=line
```

### Coverage
```bash
pytest --cov=src --cov-fail-under=80 -q
```

### Playground Tests (Phase 6-7)
```bash
# Playground E2E Tests
pytest tests/e2e/test_playground.py -v

# Specific feature tests
pytest tests/e2e/test_playground.py -v -k "resources or prompts or sampling or elicitation"

# JavaScript Unit Tests
cd tests/manual/playground && npm test
```

### Local MCP Server Test (Synapse)
```bash
# MCP 서버 시작 (별도 터미널)
cd C:\Users\sungb\Documents\GitHub\MCP_SERVER\MCP_Streamable_HTTP
python -m synapse

# 서버 시작 및 테스트
uvicorn src.main:app --port 8000
```

### Manual Playground Test
```bash
# Terminal 1: Backend (DEV_MODE)
DEV_MODE=true uvicorn src.main:app --reload

# Terminal 2: Playground
python -m http.server 3000 --directory tests/manual/playground

# Browser: http://localhost:3000
```

---

## Critical Files Summary

| 구분 | 신규/수정 | 파일 |
|------|----------|------|
| Entity (신규) | 신규 | `src/domain/entities/prompt_template.py`, `elicitation_request.py` |
| Entity (수정) | 수정 | `src/domain/entities/stream_chunk.py`, `sampling_request.py` (rejection_reason 추가) |
| Port (신규) | 신규 | `src/domain/ports/outbound/event_broadcast_port.py` (SSE 추상화) |
| Entity (기존) | 기존 | `src/domain/entities/resource.py`, `sampling_request.py` |
| Port (신규) | 신규 | `src/domain/ports/outbound/mcp_client_port.py`, `hitl_notification_port.py` |
| Port (수정) | 수정 | `src/domain/ports/outbound/orchestrator_port.py` (+generate_response) |
| Service (신규) | 신규 | `src/domain/services/resource_service.py`, `prompt_service.py`, `sampling_service.py`, `elicitation_service.py` |
| Service (수정) | 수정 | `src/domain/services/registry_service.py` (Method C callback) |
| Adapter (신규) | 신규 | `src/adapters/outbound/mcp/mcp_client_adapter.py`, `src/adapters/outbound/sse/hitl_notification_adapter.py`, `src/adapters/outbound/sse/broker.py` (SseBroker) |
| Adapter (수정) | 수정 | `src/adapters/outbound/adk/orchestrator_adapter.py` (+generate_response) |
| Schema (신규) | 신규 | `src/adapters/inbound/http/schemas/resources.py`, `prompts.py`, `sampling.py`, `elicitation.py` (Pydantic Response Models) |
| Integration (수정) | 수정 | `src/config/container.py` |
| Route (신규) | 신규 | `src/adapters/inbound/http/routes/resources.py`, `prompts.py`, `sampling.py`, `elicitation.py` |
| Fake (신규) | 신규 | `tests/unit/fakes/fake_mcp_client.py`, `fake_hitl_notification.py`, `fake_sse_broker.py` |
| Fake (수정) | 수정 | `tests/unit/fakes/fake_orchestrator.py` (+generate_response) |
| Route (신규) | 신규 | `src/adapters/inbound/http/routes/hitl_events.py` (HITL SSE 엔드포인트) |
| Playground | 수정 | `tests/manual/playground/index.html`, `js/main.js`, `js/sse-handler.js` |

---

## Design Decisions

### Method C: Callback-Centric LLM Placement

**LLM 호출 위치:**
- Route `/api/sampling/requests/{id}/approve` 핸들러
- `orchestrator.generate_response()` 호출 (OrchestratorPort 인터페이스)
- 결과를 `sampling_service.approve(request_id, llm_result)` 전달

**콜백 구조:**
```python
# RegistryService._create_sampling_callback()
async def callback(...):
    request = SamplingRequest(...)
    await sampling_service.create_request(request)

    # 30초 대기 (MCP SDK callback은 blocking await)
    result = await sampling_service.wait_for_response(request_id, timeout=30.0)

    if result is None:
        # Timeout → SSE 알림
        await hitl_notification.notify_sampling_request(request)
        # 더 긴 대기 (Extension 응답)
        result = await sampling_service.wait_for_response(request_id, timeout=270.0)

    if result is None or result.status == REJECTED:
        raise HitlTimeoutError(...)

    return result.llm_result  # MCP 서버에 반환
```

### HITL Flow: Hybrid Timeout

- **Short timeout (30s)**: 요청 수신 후 30초간 대기
- **Timeout 초과 시**: SSE로 Extension에 알림 + 270초 추가 대기
- **장점**: 빠른 응답(30s 이내)과 비동기 처리(30s 초과) 모두 지원

### Extension UI: Production Phase로 연기

- **전체 화면 모달** (Extension UI)
- Sampling: 메시지 내용 + 승인/거부 버튼
- Elicitation: 동적 폼 (requested_schema 기반) + accept/decline/cancel
- **연기 이유**: Playground로 충분히 검증 가능, Extension UI는 Production 단계에서 더 나은 UX 설계 가능

### Domain 콜백 추상화

- MCP SDK 타입 대신 Domain 전용 Protocol 사용
- Adapter에서 MCP SDK 타입으로 변환 (Phase 4)
- Domain 레이어 순수 Python 유지

### Architecture Decision Records

주요 아키텍처 결정은 ADR로 문서화되어 있습니다:

- **[ADR-A05: Method C — Callback-Centric LLM Placement](../../decisions/architecture/ADR-A05-method-c-callback-centric.md)**
  - LLM 호출 위치 결정 (Route에서 OrchestratorPort 사용)
  - Method A/B와의 비교
  - 헥사고날 아키텍처 준수

- **[ADR-A06: Hybrid Timeout Strategy](../../decisions/architecture/ADR-A06-hybrid-timeout-strategy.md)**
  - 30초 Short + 270초 Long timeout 전략
  - SSE 알림을 통한 비동기 승인 지원
  - 시스템 안정성과 UX 균형

- **[ADR-A07: Dual-Track Architecture (ADK + SDK)](../../decisions/architecture/ADR-A07-dual-track-architecture.md)**
  - 동일 MCP 서버에 ADK + SDK 이중 연결
  - Tools(ADK) vs Resources/Prompts/Sampling/Elicitation(SDK) 역할 분리
  - 리소스 오버헤드 모니터링 계획

- **[ADR-T07: Playground-First Testing](../../decisions/technical/ADR-T07-playground-first-testing.md)**
  - Phase 6+ HTTP API와 Playground UI 동시 구현
  - 즉각적 피드백 및 빠른 회귀 테스트
  - Extension UI는 Production Phase로 연기

---

## Test Strategy Matrix

| Phase | 테스트 유형 | 파일 | 마커 |
|-------|------------|------|------|
| 1 | Unit | `tests/unit/domain/entities/test_*.py` | (default) |
| 2 | Unit | `tests/unit/fakes/test_fake_*.py` | (default) |
| 3 | Unit | `tests/unit/domain/services/test_*.py` | (default) |
| 4 | Integration | `tests/integration/test_mcp_client_adapter.py` | `local_mcp` |
| 4 | Integration | `tests/integration/test_orchestrator_generate.py` | `llm` |
| 5 | Unit | `tests/unit/domain/services/test_registry_service.py` | (default) |
| 5 | Integration | `tests/integration/test_dual_track.py` | `local_mcp`, `llm` |
| 6 | Integration | `tests/integration/test_*_routes.py` | (default) |
| 6 | E2E | `tests/e2e/test_playground.py` | `e2e_playwright` |
| 7 | Unit | `tests/unit/domain/entities/test_stream_chunk.py` | (default) |
| 7 | E2E | `tests/e2e/test_playground.py::TestPlaygroundSSEEvents` | `e2e_playwright` |

**Synapse 필수 테스트 (local_mcp)**:
- Resources: list + read
- Prompts: list + get(render)
- Sampling callback: ADK tool call → Synapse sampling request → AgentHub callback
- Elicitation callback: trigger → verify
- **주의**: Synapse Streamable HTTP에서 sampling hang 가능 → timeout 설정 필수

---

## Risk Mitigation

| 위험 | 대응 |
|------|------|
| MCP SDK v2 Breaking Changes | `mcp>=1.25,<2`로 버전 고정 |
| 이중 세션 오버헤드 | 로깅 모니터링, 리소스 영향 낮을 것으로 예상 |
| 콜백 시그니처 변경 | Domain 추상화로 격리, Adapter에서 변환 |
| HITL 타임아웃 | Hybrid 방식 (30s + 270s, SSE 알림) |
| 세션 누수 | 서버 종료 시 `disconnect_all()` 호출 (Phase 5) |
| Synapse Streamable HTTP hang | timeout 설정, E2E 테스트로 조기 발견 |

---

## Review Notes (2026-02-06 - Method C Revision)

### 검토 완료 항목
- [x] Method C 적용 (Callback-Centric)
- [x] OrchestratorPort.generate_response() 추가
- [x] HitlNotificationPort 신규 정의
- [x] PromptTemplate, ElicitationRequest 엔티티 추가
- [x] SamplingService.get_request() 메서드 추가
- [x] Synapse 통합 테스트 포함
- [x] Dual-Track 상호작용 테스트 포함
- [x] MCP Apps raw 응답 지원
- [x] Playground-First Testing 원칙 적용
- [x] DI Container Provide[] 패턴 사용
- [x] datetime.now(timezone.utc) 사용 (utcnow 폐기)
- [x] TDD 원칙 강조 (각 Phase에 테스트 먼저 명시)

### 주요 변경사항
1. **헥사고날 위반 해결**: LLM 호출은 Route에서 하되 OrchestratorPort 인터페이스 사용
2. **누락 엔티티/메서드 추가**: PromptTemplate, ElicitationRequest, generate_response(), get_request()
3. **HITL timeout→SSE 메커니즘 정의**: HitlNotificationPort + 30s/270s hybrid timeout
4. **테스트 갭 해소**: Synapse 통합, Dual-Track 상호작용 테스트

### 주의사항
1. **Phase 순서대로 구현 가능**: Phase 2에서 Fake를 함께 작성하여 Phase 3 테스트에서 사용
2. **Phase 4 테스트는 Integration**: McpClientAdapter는 외부 SDK 사용하므로 `tests/integration/`에 위치
3. **콜백 변환 로직**: Adapter에서 Domain → MCP SDK 타입 변환 필수
4. **Synapse 테스트 주의**: Sampling hang 가능성, timeout 설정 필수

---

*Last Updated: 2026-02-06*
*Revision: Method C (Callback-Centric), Synapse Integration, Playground-First Testing*
*Reviewed: TDD, Hexagonal Architecture, MCP SDK Spec Compliance*
