# Phase 4 Part A: Critical Fixes (Steps 1-4)

> **상태:** 📋 Planned
> **선행 조건:** Phase 3 Complete
> **목표:** A2A Wiring 버그 수정, SSE 이벤트 확장, 타입별 에러 전파, 엔드포인트 자동 복원
> **예상 테스트:** ~19 신규 (backend) + ~10 신규 (Vitest) + ~30 수정 (backend)
> **권장 실행 순서:** Step 1 → Step 4 → Step 2 → Step 3

---

## 🎯 Progress Checklist

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **1** | A2A Agent LLM Wiring Fix | ⬜ |
| **2** | SSE Event Streaming (StreamChunk) | ⬜ |
| **3** | Typed Error Propagation | ⬜ |
| **4** | Endpoint Auto-Restore on Startup | ⬜ |

**범례:** ✅ 완료 | 🚧 진행중 | ⬜ 미착수

---

## Part A Prerequisites

### 선행 조건

- [ ] 기존 테스트 전체 통과: `pytest tests/ -q --tb=line -x`
- [ ] Coverage >= 80%: 현재 90.63%
- [ ] 브랜치: `feature/phase-4`

### Step별 검증 게이트

| Step | 검증 항목 | 방법 |
|:----:|----------|------|
| 1 시작 | OrchestratorPort에 add/remove_a2a_agent 추가 패턴 | `/tdd` skill |
| 2 시작 | ADK Event API 시그니처 확인 | Web search |
| 2 시작 | `event.get_function_calls()` 반환 타입 | Web search 재검증 |
| 3 완료 | 도메인 예외 → SSE error 매핑 | Code review |
| 4 완료 | lifespan restore 패턴 | `/tdd` skill |

---

## Step 1: A2A Agent LLM Wiring Fix (CRITICAL)

**문제:** `POST /api/a2a/agents` → `registry.register_endpoint()` → Agent Card만 저장, `orchestrator.add_a2a_agent()` 미호출.

**결정:** ADR-1 Option B — RegistryService에 OrchestratorPort 주입.

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/ports/outbound/orchestrator_port.py` | MODIFY | `add_a2a_agent()`, `remove_a2a_agent()` abstract method 추가 |
| `src/domain/services/registry_service.py` | MODIFY | `__init__`에 `orchestrator: OrchestratorPort \| None = None` 추가. `register_endpoint(A2A)` 시 `orchestrator.add_a2a_agent()` 호출. `unregister_endpoint(A2A)` 시 `orchestrator.remove_a2a_agent()` 호출 |
| `src/config/container.py` | MODIFY | `registry_service`에 `orchestrator=orchestrator_adapter` 주입 |
| `tests/unit/fakes/fake_orchestrator.py` | MODIFY | `add_a2a_agent()`, `remove_a2a_agent()` 메서드 + 호출 추적 |
| `tests/unit/domain/services/test_registry_service.py` | MODIFY | A2A wiring 검증 테스트 4개 추가 |

**TDD 순서:**
1. RED: `test_register_a2a_calls_orchestrator_add_agent`
2. RED: `test_unregister_a2a_calls_orchestrator_remove_agent`
3. RED: `test_register_a2a_without_orchestrator_graceful` (orchestrator=None 시 스킵)
4. RED: `test_register_mcp_ignores_orchestrator` (regression)
5. GREEN: OrchestratorPort, RegistryService, FakeOrchestrator 수정
6. GREEN: container.py 업데이트

**핵심 설계:**
```python
# registry_service.py 변경
class RegistryService:
    def __init__(self, storage, toolset, a2a_client=None, orchestrator=None):
        self._orchestrator = orchestrator  # NEW

    async def register_endpoint(self, url, name=None, endpoint_type=EndpointType.MCP):
        # ... 기존 ...
        elif endpoint_type == EndpointType.A2A:
            if self._a2a_client is None:
                raise ValueError("A2A client not configured")
            agent_card = await self._a2a_client.register_agent(endpoint)
            endpoint.agent_card = agent_card
            # NEW: Wire to LLM
            if self._orchestrator:
                await self._orchestrator.add_a2a_agent(
                    endpoint.id, endpoint.url
                )
        # ...

    async def unregister_endpoint(self, endpoint_id):
        # ... 기존 ...
        if endpoint.type == EndpointType.A2A:
            if self._a2a_client:
                await self._a2a_client.unregister_agent(endpoint_id)
            # NEW: Unwire from LLM
            if self._orchestrator:
                await self._orchestrator.remove_a2a_agent(endpoint_id)
        # ...
```

**DoD:**
- [ ] A2A 등록 시 `orchestrator.add_a2a_agent()` 호출됨
- [ ] A2A 삭제 시 `orchestrator.remove_a2a_agent()` 호출됨
- [ ] orchestrator=None 시 graceful skip (에러 없음)
- [ ] 기존 MCP 등록 테스트 regression 없음
- [ ] 신규 테스트 4개 이상

**의존성:** 없음 (기반 Step)

---

## Step 2: SSE Event Streaming (StreamChunk)

**⚠️ Phase 4 최대 변경. ~30개 기존 테스트 수정 필요.**

> **검증 게이트:** Web search — ADK Event API (`get_function_calls()`, `get_function_responses()`, `is_final_response()`) 시그니처 확인

### 영향 분석

**Backend 파일 (13개):**

| 파일 | 작업 | 영향 |
|------|:----:|------|
| `src/domain/entities/stream_event.py` | **NEW** | StreamChunk 도메인 엔티티 |
| `src/domain/entities/__init__.py` | MODIFY | StreamChunk export 추가 |
| `src/domain/ports/outbound/orchestrator_port.py` | MODIFY | `AsyncIterator[str]` → `AsyncIterator[StreamChunk]` |
| `src/domain/ports/inbound/chat_port.py` | MODIFY | `AsyncIterator[str]` → `AsyncIterator[StreamChunk]` |
| `src/domain/services/conversation_service.py` | MODIFY | StreamChunk 처리, text 타입만 축적 |
| `src/domain/services/orchestrator_service.py` | MODIFY | StreamChunk yield |
| `src/adapters/outbound/adk/orchestrator_adapter.py` | MODIFY | ADK event → StreamChunk 매핑 |
| `src/adapters/inbound/http/routes/chat.py` | MODIFY | 타입별 SSE 이벤트 전송 |
| `src/adapters/inbound/http/schemas/chat.py` | MODIFY | 이벤트 타입 스키마 업데이트 |
| `tests/unit/fakes/fake_orchestrator.py` | MODIFY | StreamChunk yield |
| `tests/unit/domain/services/test_conversation_service.py` | MODIFY | ~10개 테스트 수정 |
| `tests/unit/domain/services/test_orchestrator_service.py` | MODIFY | ~5개 테스트 수정 |
| `tests/integration/adapters/test_orchestrator_adapter.py` | MODIFY | StreamChunk 처리 |

**Extension 파일 (4개):**

| 파일 | 작업 | 변경 |
|------|:----:|------|
| `extension/lib/types.ts` | MODIFY | `StreamEventToolCall`, `StreamEventToolResult`, `StreamEventAgentTransfer` 타입 추가 |
| `extension/hooks/useChat.ts` | MODIFY | 새 이벤트 타입 처리 로직 |
| `extension/components/ToolCallIndicator.tsx` | **NEW** | 도구 호출 표시 컴포넌트 |
| Vitest tests | NEW/MODIFY | ~8개 테스트 |

### Migration 순서 (원자적 커밋)

```
1. StreamChunk 엔티티 생성 + 테스트
2. FakeOrchestrator → StreamChunk yield 수정
3. Domain Services 수정 + 테스트 업데이트
4. Port 인터페이스 반환 타입 변경
5. Adapter 수정 (ADK event → StreamChunk)
6. HTTP Route 수정 (타입별 SSE)
7. Extension 타입/Hook 수정
8. Extension ToolCallIndicator 컴포넌트 생성
```

### StreamChunk 엔티티 설계

```python
# src/domain/entities/stream_event.py
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True, slots=True)
class StreamChunk:
    """SSE 스트리밍 이벤트 단위 (순수 Python, 외부 import 없음)"""
    type: str  # "text", "tool_call", "tool_result", "agent_transfer", "error", "done"
    content: str = ""
    tool_name: str = ""
    tool_arguments: dict[str, Any] = field(default_factory=dict)
    tool_result: str = ""
    agent_name: str = ""
    error_code: str = ""

    @staticmethod
    def text(content: str) -> "StreamChunk":
        return StreamChunk(type="text", content=content)

    @staticmethod
    def tool_call(name: str, arguments: dict[str, Any]) -> "StreamChunk":
        return StreamChunk(type="tool_call", tool_name=name, tool_arguments=arguments)

    @staticmethod
    def tool_result(name: str, result: str) -> "StreamChunk":
        return StreamChunk(type="tool_result", tool_name=name, tool_result=result)

    @staticmethod
    def agent_transfer(agent_name: str) -> "StreamChunk":
        return StreamChunk(type="agent_transfer", agent_name=agent_name)

    @staticmethod
    def done() -> "StreamChunk":
        return StreamChunk(type="done")

    @staticmethod
    def error(message: str, code: str = "") -> "StreamChunk":
        return StreamChunk(type="error", content=message, error_code=code)
```

### ADK Event → StreamChunk 매핑 (구현 시 웹 검색 필수)

```python
# orchestrator_adapter.py process_message() 수정
async for event in runner.run_async(...):
    if event.get_function_calls():
        for fc in event.get_function_calls():
            yield StreamChunk.tool_call(fc.name, dict(fc.args))

    if event.get_function_responses():
        for fr in event.get_function_responses():
            yield StreamChunk.tool_result(fr.name, str(fr.response))

    if hasattr(event, 'actions') and event.actions and event.actions.transfer_to_agent:
        yield StreamChunk.agent_transfer(event.actions.transfer_to_agent)

    if event.is_final_response() and event.content and event.content.parts:
        for part in event.content.parts:
            if part.text:
                yield StreamChunk.text(part.text)
```

**TDD 순서:**
1. RED: `test_stream_chunk_text_factory`, `test_stream_chunk_tool_call_factory`
2. RED: `test_stream_chunk_frozen_immutable`
3. GREEN: StreamChunk 엔티티 생성
4. FakeOrchestrator 수정 (StreamChunk yield)
5. RED: `test_conversation_service_accumulates_text_chunks`
6. RED: `test_conversation_service_ignores_non_text_chunks`
7. GREEN: ConversationService 수정
8. Adapter + Route 수정
9. Extension 타입/Hook 수정

**DoD:**
- [ ] StreamChunk 도메인 엔티티 (pure Python, `@dataclass(frozen=True, slots=True)`)
- [ ] SSE에서 tool_call 이벤트 (도구 이름 + 인자)
- [ ] SSE에서 tool_result 이벤트 (도구 이름 + 결과)
- [ ] SSE에서 agent_transfer 이벤트
- [ ] 기존 text/done/error 이벤트 정상 동작
- [ ] ConversationService: text 타입만 축적하여 메시지 저장
- [ ] Extension ToolCallIndicator 컴포넌트
- [ ] 신규 backend 테스트 8개 이상
- [ ] 신규 Vitest 테스트 ~8개
- [ ] 기존 ~30개 테스트 수정 완료 (regression 0)

**의존성:** Step 1 (OrchestratorPort 수정됨)

---

## Step 3: Typed Error Propagation

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/inbound/http/routes/chat.py` | MODIFY | except 블록에서 도메인 예외 타입별 분기, StreamChunk.error()에 code 포함 |
| `extension/lib/types.ts` | MODIFY | error 이벤트에 `code` 필드 추가 |
| `extension/hooks/useChat.ts` | MODIFY | error code별 사용자 친화 메시지 매핑 |
| `extension/components/ErrorDisplay.tsx` | **NEW** | 에러 코드별 표시 컴포넌트 |

**에러 코드 매핑:**
```python
# chat.py except 블록
except LlmRateLimitError as e:
    yield StreamChunk.error(str(e), code="LlmRateLimitError")
except LlmAuthenticationError as e:
    yield StreamChunk.error(str(e), code="LlmAuthenticationError")
except EndpointConnectionError as e:
    yield StreamChunk.error(str(e), code="EndpointConnectionError")
except Exception as e:
    yield StreamChunk.error(str(e), code="UnknownError")
```

**DoD:**
- [ ] Rate limit 에러 시 `{"type": "error", "code": "LlmRateLimitError", ...}` 전송
- [ ] 인증 에러, 연결 에러 등 코드 구분
- [ ] Extension에서 코드별 사용자 친화 메시지 표시
- [ ] 신규 backend 테스트 3개 이상
- [ ] 신규 Vitest 테스트 ~2개

**의존성:** Step 2 (StreamChunk.error() 사용)

---

## Step 4: Endpoint Auto-Restore on Startup

**문제:** 서버 재시작 시 JSON에 저장된 MCP/A2A 엔드포인트가 로드되지만, DynamicToolset과 Orchestrator에 재연결되지 않음.

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/services/registry_service.py` | MODIFY | `restore_endpoints()` 메서드 추가 |
| `src/adapters/inbound/http/app.py` | MODIFY | lifespan에서 `restore_endpoints()` 호출 |
| `tests/unit/domain/services/test_registry_service.py` | MODIFY | 복원 테스트 4개 추가 |

**핵심 설계:**
```python
# registry_service.py
async def restore_endpoints(self) -> dict[str, list[str]]:
    """서버 시작 시 저장된 엔드포인트 복원. 실패 시 건너뜀."""
    endpoints = await self._storage.list_endpoints()
    restored, failed = [], []
    for ep in endpoints:
        try:
            if ep.type == EndpointType.MCP:
                await self._toolset.add_mcp_server(ep)
            elif ep.type == EndpointType.A2A:
                if self._a2a_client and self._orchestrator:
                    agent_card = await self._a2a_client.register_agent(ep)
                    ep.agent_card = agent_card
                    await self._orchestrator.add_a2a_agent(ep.id, ep.url)
            restored.append(ep.url)
        except Exception as e:
            logger.warning(f"Failed to restore endpoint {ep.url}: {e}")
            failed.append(ep.url)
    return {"restored": restored, "failed": failed}

# app.py lifespan 수정
async def lifespan(app):
    # ... 기존 초기화 ...
    await orchestrator.initialize()
    # NEW: 저장된 엔드포인트 복원
    result = await registry_service.restore_endpoints()
    logger.info(f"Endpoints restored: {len(result['restored'])}, failed: {len(result['failed'])}")
    yield
    # ... 정리 ...
```

**TDD 순서:**
1. RED: `test_restore_mcp_endpoints_reconnects`
2. RED: `test_restore_a2a_endpoints_rewires`
3. RED: `test_restore_failed_endpoint_skipped`
4. RED: `test_restore_empty_storage`
5. GREEN: RegistryService.restore_endpoints() 구현
6. GREEN: app.py lifespan 수정

**DoD:**
- [ ] 서버 재시작 시 저장된 MCP 서버 자동 재연결
- [ ] 서버 재시작 시 저장된 A2A 에이전트 자동 재등록
- [ ] 연결 실패 시 graceful 에러 처리 (건너뛰기 + 로깅)
- [ ] 신규 테스트 4개 이상

**의존성:** Step 1 (orchestrator 주입 필요)

---

## Skill/Agent 활용 계획

| 시점 | 호출 | 목적 |
|------|------|------|
| Step 1 시작 | `/tdd` | TDD Red-Green-Refactor |
| Step 2 시작 | Web search + `/skill mcp-adk-standards` | ADK Event API 시그니처 검증 |
| Step 2 완료 | `hexagonal-architect` Agent | StreamChunk 도메인 순수성 검증 |
| Step 3 완료 | `code-reviewer` Agent | 에러 전파 패턴 검토 |
| Part A 완료 | `phase-orchestrator` Agent | Part A DoD 검증 |

---

## 커밋 정책

```
fix(phase4): Step 1 - Wire A2A agents to LLM via RegistryService-OrchestratorPort
feat(phase4): Step 4 - Auto-restore saved endpoints on server startup
feat(phase4): Step 2 - SSE StreamChunk events (tool_call, tool_result, agent_transfer)
feat(phase4): Step 3 - Typed error propagation with domain exception codes
docs(phase4): Part A documentation updates
```

---

## Part A Definition of Done

### 기능

- [ ] A2A 에이전트 등록 시 LlmAgent sub_agents에 추가됨
- [ ] A2A 에이전트 삭제 시 sub_agents에서 제거됨
- [ ] SSE 스트리밍: tool_call, tool_result, agent_transfer 이벤트 전송
- [ ] StreamChunk 도메인 엔티티 (순수 Python)
- [ ] 에러 이벤트에 typed code 포함
- [ ] 서버 재시작 시 엔드포인트 자동 복원
- [ ] Extension ToolCallIndicator 컴포넌트
- [ ] Extension error code별 사용자 메시지

### 품질

- [ ] 기존 테스트 전체 통과 (regression 0)
- [ ] Backend coverage >= 90%
- [ ] Vitest >= 190 tests
- [ ] `ruff check` + `ruff format` clean

### 문서

- [ ] `docs/STATUS.md` — Phase 4 Part A 진행 상태 반영
- [ ] `CLAUDE.md` — StreamChunk 엔티티 관련 업데이트 (필요 시)

---

## 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|--------|:------:|------|
| Step 2 StreamChunk ~30 테스트 수정 | 🔴 높음 | Migration 순서 엄수. 원자적 커밋 |
| ADK Event API 변경 가능 | 🔴 높음 | Step 2 시작 시 웹 검색 게이트 |
| RegistryService 4개 포트 의존 | 🟡 중간 | orchestrator는 Optional(None이면 스킵) |
| Extension 기존 SSE 처리 변경 | 🟡 중간 | 기존 text/done/error는 유지, 새 타입만 추가 |
| OrchestratorPort 시그니처 변경 | 🟡 중간 | FakeOrchestrator 먼저 수정 → 모든 테스트 컴파일 |

---

## 핵심 파일 요약

| 파일 | Steps | 중요도 |
|------|:-----:|:------:|
| `src/domain/services/registry_service.py` | 1, 4 | ⭐⭐⭐ |
| `src/domain/ports/outbound/orchestrator_port.py` | 1, 2 | ⭐⭐⭐ |
| `src/domain/entities/stream_event.py` | 2 | ⭐⭐⭐ |
| `src/domain/services/conversation_service.py` | 2 | ⭐⭐⭐ |
| `src/adapters/outbound/adk/orchestrator_adapter.py` | 2 | ⭐⭐⭐ |
| `src/adapters/inbound/http/routes/chat.py` | 2, 3 | ⭐⭐ |
| `src/config/container.py` | 1 | ⭐⭐ |
| `tests/unit/fakes/fake_orchestrator.py` | 1, 2 | ⭐⭐ |

---

*Part A 계획 작성일: 2026-01-31*
*초안 Steps 1-3, 11 기반*
