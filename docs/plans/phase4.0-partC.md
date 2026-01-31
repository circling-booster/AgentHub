# Phase 4 Part C: Dynamic Intelligence (Steps 8-9)

> **상태:** 📋 Planned
> **선행 조건:** Part A Complete (A2A wiring, StreamChunk)
> **목표:** 컨텍스트 인식 시스템 프롬프트, 도구 실행 재시도 로직
> **예상 테스트:** ~9 신규 (backend)

---

## 🎯 Progress Checklist

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **8** | Context-Aware System Prompt | ⬜ |
| **9** | Tool Execution Retry Logic | ⬜ |

**범례:** ✅ 완료 | 🚧 진행중 | ⬜ 미착수

---

## Part C Prerequisites

- [ ] Part A 완료 (Step 1: A2A wiring 필수)
- [ ] 기존 테스트 전체 통과

**⚡ 병렬화 옵션:** Part A 완료 후 Part B, D와 병렬 진행 가능

---

## Step 8: Context-Aware System Prompt

**문제:** `"You are a helpful assistant with access to various tools."` — 등록된 도구/에이전트 정보 미포함

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/outbound/adk/orchestrator_adapter.py` | MODIFY | `_rebuild_agent()`에서 동적 instruction 생성. DynamicToolset에서 등록된 도구 목록, `_sub_agents`에서 A2A 에이전트 정보 추출 |
| `src/adapters/outbound/adk/dynamic_toolset.py` | MODIFY | `get_registered_info()` 메서드 추가 (엔드포인트별 도구 이름 목록 반환) |
| `tests/integration/adapters/test_orchestrator_adapter.py` | MODIFY | 동적 instruction 검증 |
| `tests/unit/adapters/test_dynamic_toolset_info.py` | **NEW** | get_registered_info() 테스트 |

**Instruction 템플릿:**
```
You are AgentHub, an intelligent assistant with access to external tools and agents.

## Available MCP Tools:
{동적 생성: 서버별 도구 목록}
- Server "weather-api": get_weather, get_forecast
- Server "file-manager": read_file, write_file, list_files

## Available A2A Agents:
{동적 생성: 에이전트별 설명}
- Agent "translator": Translates text between languages
- Agent "summarizer": Summarizes long documents

## Usage Guidelines:
- Use MCP tools for specific actions (data queries, file operations, API calls)
- Delegate to A2A agents when the task matches their specialization
- You can use multiple tools in sequence to complete complex tasks
- Always report which tools/agents you used in your response
```

**TDD 순서:**
1. RED: `test_get_registered_info_returns_endpoint_tools`
2. RED: `test_dynamic_instruction_includes_mcp_tools`
3. RED: `test_dynamic_instruction_includes_a2a_agents`
4. RED: `test_instruction_updates_on_server_add_remove`
5. GREEN: `get_registered_info()` 구현, `_rebuild_agent()` instruction 수정

**DoD:**
- [ ] LLM instruction에 등록된 MCP 도구 이름 목록 포함
- [ ] LLM instruction에 A2A 에이전트 설명 포함
- [ ] 도구/에이전트 추가/제거 시 instruction 자동 갱신 (`_rebuild_agent()` 호출)
- [ ] 신규 테스트 4개 이상

**의존성:** Part A Step 1 (A2A agents in orchestrator)

---

## Step 9: Tool Execution Retry Logic

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/outbound/adk/dynamic_toolset.py` | MODIFY | `call_tool()`에 재시도 로직 추가 (exponential backoff). 일시적 에러(timeout, connection)만 재시도, 영구 에러(404, auth)는 즉시 실패 |
| `src/config/settings.py` | MODIFY | `mcp.max_retries`, `mcp.retry_backoff_seconds` 설정 추가 |
| `configs/default.yaml` | MODIFY | 재시도 기본값 (max_retries=2, backoff=1.0) |
| `tests/unit/adapters/test_tool_retry.py` | **NEW** | 재시도 로직 테스트 |

**핵심 설계:**
```python
# dynamic_toolset.py call_tool() 수정
TRANSIENT_ERRORS = (ConnectionError, TimeoutError, asyncio.TimeoutError)

async def call_tool(self, tool_name: str, arguments: dict) -> Any:
    max_retries = self._settings.mcp.max_retries  # default: 2
    backoff = self._settings.mcp.retry_backoff_seconds  # default: 1.0

    for attempt in range(max_retries + 1):
        try:
            return await self._execute_tool(tool_name, arguments)
        except TRANSIENT_ERRORS as e:
            if attempt == max_retries:
                raise
            wait = backoff * (2 ** attempt)
            logger.warning(f"Tool {tool_name} failed (attempt {attempt+1}), retrying in {wait}s: {e}")
            await asyncio.sleep(wait)
```

**TDD 순서:**
1. RED: `test_tool_retries_on_transient_error`
2. RED: `test_tool_no_retry_on_permanent_error`
3. RED: `test_exponential_backoff_timing`
4. RED: `test_max_retries_exceeded_raises`
5. RED: `test_retry_disabled_when_max_retries_zero`
6. GREEN: call_tool() 재시도 로직 구현

**DoD:**
- [ ] 일시적 도구 실행 실패 시 최대 N회 재시도
- [ ] Exponential backoff 적용 (1s, 2s, 4s...)
- [ ] 영구 에러(404, auth 실패)는 즉시 실패
- [ ] 설정으로 재시도 횟수 및 backoff 조정 가능
- [ ] 신규 테스트 5개 이상

**의존성:** 독립

---

## Skill/Agent 활용 계획

| 시점 | 호출 | 목적 |
|------|------|------|
| Step 8 시작 | `/tdd` | TDD Red-Green-Refactor |
| Step 9 시작 | `/tdd` | TDD Red-Green-Refactor |
| Part C 완료 | `code-reviewer` Agent | 코드 품질 검토 |

---

## 커밋 정책

```
feat(phase4): Step 8 - Context-aware dynamic system prompt
feat(phase4): Step 9 - Tool execution retry with exponential backoff
docs(phase4): Part C documentation updates
```

---

## Part C Definition of Done

### 기능

- [ ] 시스템 프롬프트에 도구/에이전트 목록 동적 포함
- [ ] 도구 추가/제거 시 프롬프트 자동 갱신
- [ ] 일시적 에러 시 재시도 (exponential backoff)
- [ ] 영구 에러 즉시 실패

### 품질

- [ ] 기존 테스트 전체 통과 (regression 0)
- [ ] Backend coverage >= 90%
- [ ] `ruff check` + `ruff format` clean

### 문서

- [ ] `docs/STATUS.md` — Phase 4 Part C 진행 상태 반영

---

## 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|--------|:------:|------|
| 동적 instruction이 너무 길어질 수 있음 | 🟡 중간 | 도구 수 > 30이면 요약 모드 |
| 재시도 중 이벤트 루프 블로킹 | 🟢 낮음 | `asyncio.sleep()` 사용 (non-blocking) |
| 일시적/영구 에러 분류 어려움 | 🟡 중간 | 보수적 접근: 명확한 영구 에러만 즉시 실패, 나머지 재시도 |

---

*Part C 계획 작성일: 2026-01-31*
*초안 Steps 7-8 기반*
