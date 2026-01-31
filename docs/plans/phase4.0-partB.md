# Phase 4 Part B: Observability (Steps 5-7)

> **상태:** 📋 Planned
> **선행 조건:** Part A Complete
> **목표:** LLM 호출 로깅, 도구 호출 추적(DB), 구조화된 로깅
> **예상 테스트:** ~12 신규 (backend)

---

## 🎯 Progress Checklist

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **5** | LiteLLM Callback Logging | ⬜ |
| **6** | Tool Call Tracing (DB) | ⬜ |
| **7** | Structured Logging Improvements | ⬜ |

**범례:** ✅ 완료 | 🚧 진행중 | ⬜ 미착수

---

## Part B Prerequisites

- [ ] Part A 완료
- [ ] 기존 테스트 전체 통과

**⚡ 병렬화 옵션:** Part A 완료 후 Part C, D와 병렬 진행 가능 (단, Step 6은 Part A Step 2 완료 필요)

### Step별 검증 게이트

| Step | 검증 항목 | 방법 |
|:----:|----------|------|
| 5 시작 | LiteLLM CustomLogger API 시그니처 | Web search |
| 6 시작 | tool_calls 테이블 스키마 확인 | implementation-guide.md 참조 |
| 7 완료 | 로깅 출력 포맷 확인 | Manual inspection |

---

## Step 5: LiteLLM Callback Logging

**신규/수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/outbound/adk/litellm_callbacks.py` | **NEW** | `CustomLogger` 상속. `log_success_event()`: 모델명, 토큰 수, 지연시간. `log_failure_event()`: 에러 상세 |
| `src/adapters/outbound/adk/orchestrator_adapter.py` | MODIFY | `initialize()`에서 `litellm.callbacks = [AgentHubLogger()]` 설정 |
| `src/config/settings.py` | MODIFY | `observability` 섹션 추가 (`log_llm_requests: bool`, `max_log_chars: int`) |
| `configs/default.yaml` | MODIFY | observability 기본값 추가 |
| `tests/unit/adapters/test_litellm_callbacks.py` | **NEW** | Callback 로깅 검증 |

**핵심 설계:**
```python
# src/adapters/outbound/adk/litellm_callbacks.py
import litellm
from litellm.integrations.custom_logger import CustomLogger
import logging

logger = logging.getLogger(__name__)

class AgentHubLogger(CustomLogger):
    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        model = kwargs.get("model", "unknown")
        usage = getattr(response_obj, "usage", None)
        tokens = usage.total_tokens if usage else "N/A"
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        logger.info(
            f"LLM call success: model={model} tokens={tokens} duration={duration_ms}ms"
        )

    def log_failure_event(self, kwargs, response_obj, start_time, end_time):
        model = kwargs.get("model", "unknown")
        error = kwargs.get("exception", "unknown")
        logger.error(f"LLM call failed: model={model} error={error}")
```

**TDD 순서:**
1. RED: `test_log_success_event_logs_model_and_tokens`
2. RED: `test_log_failure_event_logs_error`
3. RED: `test_callback_disabled_by_config`
4. GREEN: AgentHubLogger 구현

**DoD:**
- [ ] LLM 호출 성공 시 모델, 토큰 수, 지연시간 로깅
- [ ] LLM 호출 실패 시 에러 상세 로깅
- [ ] 설정으로 비활성화 가능 (`observability.log_llm_requests: false`)
- [ ] 신규 테스트 3개 이상

**의존성:** 독립

---

## Step 6: Tool Call Tracing (DB 저장)

**주의:** `src/domain/entities/tool_call.py`는 이미 존재 (Phase 1에서 생성). `tool_calls` 테이블 스키마도 implementation-guide.md에 문서화됨. StoragePort 확장 + SQLite 구현만 필요.

**신규/수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/ports/outbound/storage_port.py` | MODIFY | `save_tool_call()`, `get_tool_calls(conversation_id)` 메서드 추가 |
| `src/adapters/outbound/storage/sqlite_conversation_storage.py` | MODIFY | `tool_calls` 테이블 CRUD 구현 |
| `src/domain/services/conversation_service.py` | MODIFY | StreamChunk tool_call/tool_result 이벤트 발생 시 ToolCall 저장 |
| `src/adapters/inbound/http/routes/conversations.py` | MODIFY | `GET /api/conversations/{id}/tool-calls` 엔드포인트 추가 |
| `tests/unit/fakes/fake_storage.py` | MODIFY | `save_tool_call()`, `get_tool_calls()` 구현 |
| `tests/unit/domain/services/test_conversation_service.py` | MODIFY | tool call 저장 테스트 |
| `tests/integration/adapters/test_tool_call_tracing.py` | **NEW** | SQLite tool_calls CRUD 테스트 |

**핵심 설계:**
```python
# storage_port.py 추가
class ConversationStoragePort(ABC):
    # ... 기존 ...

    @abstractmethod
    async def save_tool_call(self, tool_call: ToolCall) -> None: ...

    @abstractmethod
    async def get_tool_calls(self, conversation_id: str) -> list[ToolCall]: ...
```

**TDD 순서:**
1. RED: `test_save_and_retrieve_tool_call`
2. RED: `test_tool_calls_linked_to_conversation`
3. RED: `test_tool_call_api_endpoint`
4. GREEN: StoragePort 확장, SQLite 구현, API 엔드포인트
5. RED: `test_conversation_service_saves_tool_calls`
6. GREEN: ConversationService에서 tool_call 이벤트 → ToolCall 저장

**DoD:**
- [ ] 도구 호출이 SQLite에 저장됨 (이름, 입력, 출력, 소요시간)
- [ ] API로 대화별 도구 호출 이력 조회 가능 (`GET /api/conversations/{id}/tool-calls`)
- [ ] ConversationService가 StreamChunk tool_call/tool_result 쌍을 매칭하여 저장
- [ ] 신규 테스트 6개 이상

**의존성:** Part A Step 2 (StreamChunk tool_call 이벤트 필요)

---

## Step 7: Structured Logging Improvements

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/config/logging_config.py` | **NEW** | JSON 포맷 옵션, 일관된 필드명 (timestamp, level, logger, message, extra) |
| `src/adapters/outbound/adk/dynamic_toolset.py` | MODIFY | `get_tools()`: 캐시 hit/miss, 반환 도구 수. `add_mcp_server()`, `remove_mcp_server()`: endpoint URL, 도구 수 |
| `src/adapters/outbound/adk/orchestrator_adapter.py` | MODIFY | `process_message()`: 세션 ID, 이벤트 수. `_rebuild_agent()`: 도구/에이전트 수 |
| `src/adapters/inbound/http/app.py` | MODIFY | 로깅 설정 초기화 |
| `src/config/settings.py` | MODIFY | `observability.log_format` 설정 (text/json) |
| `configs/default.yaml` | MODIFY | log_format 기본값 |
| `tests/unit/config/test_logging_config.py` | **NEW** | 로깅 포맷 테스트 |

**DoD:**
- [ ] DynamicToolset.get_tools() 호출 시 캐시 hit/miss와 반환 도구 수 로깅
- [ ] Runner.run_async() 호출 시 세션 ID와 이벤트 카운트 로깅
- [ ] JSON 로깅 포맷 옵션 제공 (`observability.log_format: json`)
- [ ] 신규 테스트 3개 이상

**의존성:** 독립

---

## Skill/Agent 활용 계획

| 시점 | 호출 | 목적 |
|------|------|------|
| Step 5 시작 | Web search | LiteLLM CustomLogger API 검증 |
| Step 6 시작 | `/tdd` | TDD Red-Green-Refactor |
| Part B 완료 | `code-reviewer` Agent | 관찰성 코드 품질 검토 |

---

## 커밋 정책

```
feat(phase4): Step 5 - LiteLLM callback logging (model, tokens, latency)
feat(phase4): Step 6 - Tool call tracing with SQLite storage
feat(phase4): Step 7 - Structured logging with JSON format option
docs(phase4): Part B documentation updates
```

---

## Part B Definition of Done

### 기능

- [ ] LLM 호출 성공/실패 시 상세 로깅
- [ ] 도구 호출 SQLite 저장 및 API 조회
- [ ] 구조화된 로깅 (JSON 포맷 옵션)
- [ ] 설정으로 관찰성 기능 on/off

### 품질

- [ ] 기존 테스트 전체 통과 (regression 0)
- [ ] Backend coverage >= 90%
- [ ] `ruff check` + `ruff format` clean

### 문서

- [ ] `docs/STATUS.md` — Phase 4 Part B 진행 상태 반영
- [ ] `src/adapters/README.md` — Observability 섹션 추가

---

## 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|--------|:------:|------|
| LiteLLM CustomLogger API 변경 | 🟡 중간 | Step 5 시작 시 웹 검색 |
| tool_calls 테이블 이미 문서화됨 | 🟢 낮음 | implementation-guide.md 스키마 그대로 사용 |
| JSON 로깅 성능 오버헤드 | 🟢 낮음 | 설정으로 비활성화 가능 |

---

*Part B 계획 작성일: 2026-01-31*
*초안 Steps 4-6 기반*
