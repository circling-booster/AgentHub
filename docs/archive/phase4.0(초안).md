# Phase 4(초안): MCP/A2A 완전 통합 + 관찰성 + 고급 기능

> **상태:** 최종 확정 계획 전
> **기반:** Phase 3 완료 (90.63% coverage, 315 backend tests)
> **확정된 결정:**
> - ADR-1: A2A Wiring → **Option B (RegistryService에 OrchestratorPort 주입)**
> - ADR-2: SSE Events → **도메인 StreamChunk 엔티티** (헥사고날 위반 아님: 순수 Python dataclass)
> - ADR-3: MCP 고급 기능 → **Phase 5로 연기** (ADK 미지원)
> - ADR-4: LLM 로깅 → **LiteLLM CustomLogger**
> - E2E: Playwright 별도 작업 불필요 (pytest + Vitest로 완결, 기존 7개 시나리오 재활용)

---

## 1. 핵심 진단 결과

### Bug #1: A2A 에이전트가 LLM에 연결되지 않음 (CRITICAL)
- **파일:** `src/adapters/inbound/http/routes/a2a.py:54`
- **원인:** `POST /api/a2a/agents` → `registry.register_endpoint()` → Agent Card만 저장소에 저장
- **누락:** `orchestrator_adapter.add_a2a_agent()`가 어디서도 호출되지 않음
- `AdkOrchestratorAdapter.add_a2a_agent()` 메서드는 존재하지만 unreachable

### Bug #2: 관찰성 부재 (HIGH)
- `DynamicToolset.get_tools()`에 로깅 없음
- LLM API request/response 로깅 없음 (LiteLLM callbacks 미설정)
- SSE 이벤트가 "text" 타입만 전송 - 도구 호출 이벤트 필터링됨
- `event.is_final_response()`만 처리하여 중간 이벤트 무시

### Bug #3: 시스템 프롬프트가 너무 일반적
- **파일:** `src/adapters/outbound/adk/orchestrator_adapter.py:45`
- `"You are a helpful assistant with access to various tools."` - 도구/에이전트 목록 미포함

### 확인된 정상 동작:
- ADK `tools=[BaseToolset]` 패턴 정상 (ADK가 매 turn마다 `get_tools(readonly_context)` 호출)
- DI Container Singleton: RegistryService와 OrchestratorAdapter가 동일한 DynamicToolset 공유
- MCP 등록 흐름: `add_mcp_server()` → `_mcp_toolsets` 추가 → `get_tools()`에서 반환

---

## 2. 의사결정 분석 (ADR)

### ADR-1: A2A 에이전트 LLM 연결 위치

#### 현재 MCP와의 비교

**MCP 패턴 (현재 동작):**
```
POST /api/mcp/servers
  → registry.register_endpoint(url, type=MCP)
    → RegistryService._toolset.add_mcp_server(endpoint)  ← DynamicToolset에 직접 연결
      → MCPToolset 생성, 도구 캐시
```
- RegistryService가 ToolsetPort(=DynamicToolset)를 직접 호출
- **도메인 서비스가 인프라 포트를 통해 연결** (헥사고날 패턴 정상)

**A2A 패턴 (현재 - 버그):**
```
POST /api/a2a/agents
  → registry.register_endpoint(url, type=A2A)
    → A2aPort.register_agent(endpoint)  ← Agent Card만 조회/저장
    → ❌ OrchestratorPort.add_a2a_agent() 호출 안 됨
```

#### 옵션 비교

| 기준 | Option A: HTTP Route 레벨 | Option B: RegistryService에 OrchestratorPort 주입 | Option C: 새 Application Service |
|------|--------------------------|--------------------------------------------------|--------------------------------|
| **MCP와의 일관성** | ❌ 낮음 (MCP는 도메인에서 연결) | ✅ 높음 (MCP와 동일 패턴) | ⚠️ 중간 (새 레이어 추가) |
| **도메인 순수성** | ✅ 도메인 무변경 | ⚠️ RegistryService가 2개 포트 의존 | ✅ 도메인 무변경 |
| **구현 복잡도** | ✅ 낮음 (route에 2줄 추가) | ⚠️ 중간 (DI 변경 필요) | ❌ 높음 (새 서비스+테스트) |
| **응집도** | ❌ 등록 로직이 route에 분산 | ✅ 등록 로직이 서비스에 집중 | ✅ 조율 로직이 별도 서비스에 |
| **테스트 용이성** | ⚠️ route 레벨 통합 테스트 필요 | ✅ 단위 테스트로 검증 가능 | ✅ 단위 테스트 가능 |
| **추후 제약** | route 추가 시마다 wiring 반복 | OrchestratorPort 변경 시 RegistryService 영향 | 서비스 간 의존 관리 복잡 |
| **삭제 시 일관성** | route에서 delete도 처리 필요 | unregister_endpoint에서 자동 처리 | 서비스에서 자동 처리 |
| **Future-proof** | ❌ WebSocket/CLI 등 새 인터페이스 추가 시 중복 | ✅ 인터페이스 무관하게 동작 | ✅ 인터페이스 무관 |

#### MCP와의 차이점 분석

MCP에서 `ToolsetPort.add_mcp_server()`는 **도구 등록 = 도구셋에 추가**라는 자연스러운 관계입니다.
A2A에서 **에이전트 등록 = Orchestrator에 sub_agent 추가**인데, 이는 Orchestrator가 RegistryService의 관심사가 아닌 것처럼 보입니다.

**그러나**: MCP 패턴을 자세히 보면, ToolsetPort는 사실 "도구를 관리하는 인프라 포트"이고 RegistryService가 이를 사용합니다. 마찬가지로 OrchestratorPort를 "에이전트를 관리하는 인프라 포트"로 보면 동일한 패턴입니다.

#### 추천: **Option B - RegistryService에 OrchestratorPort 주입**

**이유:**
1. MCP 패턴과 일관성 유지 (가장 중요)
2. 인터페이스(HTTP, WebSocket, CLI) 추가 시 중복 없음
3. 등록/해제 로직이 한 곳에 집중
4. 단위 테스트로 검증 가능

**제약:**
- RegistryService 생성자에 optional 파라미터 추가 (`orchestrator: OrchestratorPort | None = None`)
- container.py에서 orchestrator_adapter를 registry_service에 주입

---

### ADR-2: SSE 이벤트 확장 모델

#### 배경

현재 `OrchestratorPort.process_message()` → `AsyncIterator[str]` (텍스트만)
ADK `Runner.run_async()`는 다양한 이벤트를 발생시킴:
- `event.get_function_calls()` → 도구 호출 요청
- `event.get_function_responses()` → 도구 실행 결과
- `event.is_final_response()` → 최종 텍스트 응답
- `event.actions.transfer_to_agent` → sub-agent 위임

#### 옵션 비교

| 기준 | Option A: 도메인 StreamChunk 엔티티 | Option B: 어댑터 레벨에서만 변환 |
|------|-----------------------------------|-------------------------------|
| **변경 범위** | ❌ 넓음: Port 인터페이스, 서비스, Fake, 테스트 | ✅ 좁음: orchestrator_adapter + chat route만 |
| **타입 안전성** | ✅ 컴파일 타임 검증 | ⚠️ dict 기반으로 런타임 오류 가능 |
| **도메인 표현력** | ✅ "도구 호출" 개념이 도메인에 존재 | ❌ 도메인은 텍스트만 인지 |
| **테스트 변경** | ❌ 기존 315개 중 ~30개 수정 필요 | ✅ 기존 테스트 거의 무변경 |
| **확장성** | ✅ 새 이벤트 타입 추가 용이 | ⚠️ 이벤트 구조 변경 시 산발적 수정 |
| **ConversationService 영향** | ❌ send_message() 전면 수정 | ✅ 텍스트 축적 로직 유지 |

**상세 설명:**

**Option A (StreamChunk):**
```python
# src/domain/entities/stream_event.py (새 파일)
@dataclass
class StreamChunk:
    type: str  # "text", "tool_call", "tool_result", "agent_transfer"
    content: str = ""
    tool_name: str = ""
    tool_arguments: dict = field(default_factory=dict)
    tool_result: str = ""
    agent_name: str = ""

# src/domain/ports/outbound/orchestrator_port.py (변경)
class OrchestratorPort(ABC):
    @abstractmethod
    async def process_message(self, message, conversation_id) -> AsyncIterator[StreamChunk]:
        ...

# 영향받는 파일: conversation_service.py, fake_orchestrator.py,
# test_conversation_service.py, test_orchestrator_service.py 등 ~15개 파일
```

**Option B (어댑터 레벨):**
```python
# orchestrator_adapter.py (변경) - 새 메서드 추가
async def process_message_with_events(self, message, conversation_id) -> AsyncIterator[dict]:
    """도구 호출 이벤트 포함 스트리밍"""
    async for event in runner.run_async(...):
        if event.get_function_calls():
            for fc in event.get_function_calls():
                yield {"type": "tool_call", "name": fc.name, "args": fc.args}
        if event.get_function_responses():
            for fr in event.get_function_responses():
                yield {"type": "tool_result", "name": fr.name, "result": str(fr.response)}
        if event.is_final_response():
            for part in event.content.parts:
                if part.text:
                    yield {"type": "text", "content": part.text}

# chat.py에서 이 메서드를 직접 호출
# OrchestratorPort 인터페이스는 유지 (str 스트리밍)
# ConversationService는 기존 process_message() 사용하여 텍스트만 저장
```

#### 확정: **Option A - 도메인 StreamChunk 엔티티**

**헥사고날 아키텍처 적합성 검증:**
- StreamChunk는 `@dataclass(frozen=True, slots=True)` - 순수 Python, 외부 import 없음
- "도구 호출", "에이전트 위임"은 도메인 비즈니스 개념 → 도메인에 속함
- 기존 Message, Tool, Conversation 엔티티와 동일 패턴
- **결론: 헥사고날 위반 아님**

**변경 사항:**
1. `OrchestratorPort.process_message()` → `AsyncIterator[StreamChunk]`로 변경
2. `StreamChunk` 도메인 엔티티 신규 생성
3. `ConversationService.send_message()` → StreamChunk 처리, 텍스트 축적
4. 기존 FakeOrchestrator → StreamChunk yield로 업데이트
5. 기존 테스트 ~30개 수정 필요 (타입 변경 반영)

**테스트 전략:**
- pytest로 백엔드 완결 검증 (unit + integration)
- Vitest로 Extension 단위 테스트
- Playwright 별도 작업 불필요 (기존 7개 E2E 시나리오 재활용)

---

### ADR-3: MCP 고급 기능 (Resources, Prompts, Sampling)

#### 조사 결과

**ADK MCPToolset 현황 (2026-01 기준):**
- ✅ Tools: `MCPToolset.get_tools()` → 완전 지원
- ❌ Resources: 미지원 ([GitHub Issue #1779](https://github.com/google/adk-python/issues/1779))
- ❌ Prompts: 미지원 ([GitHub Discussion #3097](https://github.com/google/adk-python/discussions/3097))
- ❌ Sampling: 미지원
- ❌ Roots/Elicitation: 미지원

ADK 팀이 향후 `MCPPromptSet`, `MCPResourceSet` 등을 추가할 계획이 있으나 아직 미구현.

#### 결정: **Phase 4에서 제외, Phase 5로 연기**

**이유:** ADK가 공식 지원하지 않는 상태에서 자체 구현하면:
1. ADK 업데이트 시 충돌 위험
2. 자체 MCP 클라이언트 구현 필요 (ADK 우회)
3. 투자 대비 효과 낮음

**대안:** ADK가 지원할 때 즉시 통합할 수 있도록 Port 인터페이스만 예약

---

### ADR-4: LLM API 로깅 방식

| 기준 | LiteLLM Custom Callback | Python logging 직접 | 외부 관찰성 도구 (Langfuse 등) |
|------|------------------------|--------------------|-----------------------------|
| **구현 복잡도** | ✅ 낮음 | ⚠️ 중간 | ❌ 높음 (외부 서비스 필요) |
| **정보 품질** | ✅ 토큰 수, 지연시간, 모델 등 | ⚠️ 수동 추출 필요 | ✅ 풍부한 분석 |
| **프라이버시** | ✅ 로컬 로그만 | ✅ 로컬 | ⚠️ 외부 전송 |
| **AgentHub 적합** | ✅ 로컬 앱에 적합 | ✅ 적합 | ❌ 과도함 |

**결정:** LiteLLM Custom Callback (`CustomLogger` 상속)

---

## 3. 실행 계획

### Phase 4 구조

```
Phase 4.0: Critical Fixes          (Part A - Steps 1-3)
Phase 4.1: Observability            (Part B - Steps 4-6)
Phase 4.2: Dynamic Intelligence     (Part C - Steps 7-8)
Phase 4.3: Reliability & Scale      (Part D - Steps 9-11)
```

---

### Part A: Critical Fixes (Steps 1-3)

#### Step 1: A2A 에이전트 LLM 연결 수정

**수정 파일:**

| 파일 | 변경 내용 |
|------|----------|
| `src/domain/services/registry_service.py` | `__init__`에 `orchestrator: OrchestratorPort \| None = None` 추가. `register_endpoint(A2A)` 시 `orchestrator.add_a2a_agent()` 호출. `unregister_endpoint(A2A)` 시 `orchestrator.remove_a2a_agent()` 호출 |
| `src/domain/ports/outbound/orchestrator_port.py` | `add_a2a_agent()`, `remove_a2a_agent()` 메서드를 Port 인터페이스에 추가 |
| `src/config/container.py` | `registry_service`에 `orchestrator=orchestrator_adapter` 주입 추가 |
| `tests/unit/services/test_registry_service.py` | A2A 등록 시 orchestrator.add_a2a_agent 호출 검증 테스트 추가 |
| `tests/unit/fakes/fake_orchestrator.py` | add_a2a_agent, remove_a2a_agent 메서드 추가 |

**TDD:**
1. RED: A2A 등록 시 `orchestrator.add_a2a_agent()` 호출 검증 테스트
2. RED: A2A 삭제 시 `orchestrator.remove_a2a_agent()` 호출 검증 테스트
3. GREEN: RegistryService 수정
4. REFACTOR: 기존 테스트 업데이트

**DoD:**
- [ ] A2A 에이전트 등록 시 LlmAgent의 sub_agents에 추가됨
- [ ] A2A 에이전트 삭제 시 sub_agents에서 제거됨
- [ ] 기존 MCP 등록 테스트 regression 없음
- [ ] 신규 테스트 4개 이상

---

#### Step 2: SSE 이벤트 스트리밍 확장

**수정 파일:**

| 파일 | 변경 내용 |
|------|----------|
| `src/domain/entities/stream_event.py` | **신규** - StreamChunk 도메인 엔티티 (`@dataclass`, 순수 Python) |
| `src/domain/ports/outbound/orchestrator_port.py` | `process_message()` 반환 타입 `AsyncIterator[str]` → `AsyncIterator[StreamChunk]` 변경 |
| `src/adapters/outbound/adk/orchestrator_adapter.py` | `process_message()` 수정: ADK 이벤트에서 `get_function_calls()`, `get_function_responses()`, `is_final_response()` 분기하여 StreamChunk yield |
| `src/domain/services/conversation_service.py` | `send_message()` 수정: StreamChunk 처리, text 타입만 축적하여 저장 |
| `src/adapters/inbound/http/routes/chat.py` | SSE generator에서 StreamChunk 타입별 이벤트 전송 (tool_call, tool_result, agent_transfer, text) |
| `src/adapters/inbound/http/schemas/chat.py` | 이벤트 타입 스키마 추가/업데이트 |
| `tests/unit/fakes/fake_orchestrator.py` | StreamChunk yield로 업데이트 |
| `tests/unit/services/test_conversation_service.py` | StreamChunk 처리 테스트로 업데이트 |
| `tests/unit/services/test_orchestrator_service.py` | StreamChunk 처리 테스트로 업데이트 |
| `extension/lib/types.ts` | `StreamEventToolCall`, `StreamEventToolResult` 타입 추가 |
| `extension/hooks/useChat.ts` | 새 이벤트 타입 처리 |
| `extension/components/ToolCallIndicator.tsx` | **신규** - 도구 호출 표시 컴포넌트 |

**ADK Event API (구현 시 반드시 웹 검색으로 재확인):**
```python
async for event in runner.run_async(...):
    # 도구 호출 요청
    if event.get_function_calls():
        for fc in event.get_function_calls():
            yield {"type": "tool_call", "tool_name": fc.name, "arguments": dict(fc.args)}

    # 도구 실행 결과
    if event.get_function_responses():
        for fr in event.get_function_responses():
            yield {"type": "tool_result", "tool_name": fr.name, "result": str(fr.response)}

    # sub-agent 위임
    if hasattr(event, 'actions') and event.actions and event.actions.transfer_to_agent:
        yield {"type": "agent_transfer", "agent_name": event.actions.transfer_to_agent}

    # 최종 텍스트 응답
    if event.is_final_response() and event.content and event.content.parts:
        for part in event.content.parts:
            if part.text:
                yield {"type": "text", "content": part.text}
```

**DoD:**
- [ ] SSE에서 tool_call 이벤트가 도구 이름, 인자와 함께 전송됨
- [ ] SSE에서 tool_result 이벤트가 도구 이름, 결과와 함께 전송됨
- [ ] 기존 text/done/error 이벤트 정상 동작
- [ ] Extension UI에 도구 호출 표시 (최소한 텍스트로)
- [ ] 신규 테스트 8개 이상

---

#### Step 3: 타입별 에러 전파

**수정 파일:**

| 파일 | 변경 내용 |
|------|----------|
| `src/adapters/inbound/http/routes/chat.py` | except 블록에서 도메인 예외 타입별 분기, error 이벤트에 `code` 필드 추가 |
| `extension/lib/types.ts` | error 이벤트에 `code` 필드 추가 |
| `extension/hooks/useChat.ts` | error code별 사용자 친화 메시지 매핑 |

**DoD:**
- [ ] Rate limit 에러 시 `{"type": "error", "code": "LlmRateLimitError", ...}` 전송
- [ ] 인증 에러, 연결 에러 등 구분
- [ ] 신규 테스트 3개 이상

---

### Part B: Observability (Steps 4-6)

#### Step 4: LiteLLM Callback 로깅

**신규/수정 파일:**

| 파일 | 변경 내용 |
|------|----------|
| `src/adapters/outbound/adk/litellm_callbacks.py` | **신규** - `CustomLogger` 상속, `log_success_event()`, `log_failure_event()` 구현. 모델명, 토큰 수, 지연시간 로깅 |
| `src/adapters/outbound/adk/orchestrator_adapter.py` | `initialize()`에서 `litellm.callbacks = [AgentHubLogger()]` 설정 |
| `src/config/settings.py` | `observability` 섹션 추가 (log_llm_requests: bool, max_log_chars: int) |
| `configs/default.yaml` | observability 기본값 추가 |

**DoD:**
- [ ] LLM 호출 성공 시 모델, 토큰 수, 지연시간 로깅
- [ ] LLM 호출 실패 시 에러 상세 로깅
- [ ] 설정으로 비활성화 가능
- [ ] 신규 테스트 3개 이상

---

#### Step 5: Tool Call Tracing (DB 저장)

**신규/수정 파일:**

| 파일 | 변경 내용 |
|------|----------|
| `src/domain/entities/tool_call.py` | **신규** - ToolCallRecord 엔티티 (id, message_id, tool_name, input_json, output_json, duration_ms) |
| `src/domain/ports/outbound/storage_port.py` | `save_tool_call()`, `get_tool_calls(conversation_id)` 메서드 추가 |
| `src/adapters/outbound/storage/sqlite_conversation_storage.py` | `tool_calls` 테이블 구현 (스키마는 이미 문서화됨) |
| `src/adapters/inbound/http/routes/chat.py` | tool_call/tool_result 이벤트 발생 시 DB에 저장 |
| `src/adapters/inbound/http/routes/conversations.py` | `GET /api/conversations/{id}/tool-calls` 엔드포인트 추가 |
| `tests/unit/fakes/fake_storage.py` | save_tool_call 메서드 추가 |

**DoD:**
- [ ] 도구 호출이 SQLite에 저장됨 (이름, 입력, 출력, 소요시간)
- [ ] API로 대화별 도구 호출 이력 조회 가능
- [ ] 신규 테스트 6개 이상

---

#### Step 6: 구조화된 로깅 개선

**수정 파일:**

| 파일 | 변경 내용 |
|------|----------|
| `src/adapters/outbound/adk/dynamic_toolset.py` | `get_tools()`에 캐시 hit/miss, 도구 수 로깅 추가. `add_mcp_server()`, `remove_mcp_server()`에 상세 로깅 |
| `src/adapters/outbound/adk/orchestrator_adapter.py` | `process_message()`에 세션 ID, 이벤트 수 로깅. `_rebuild_agent()`에 도구/에이전트 수 로깅 |
| `src/config/logging_config.py` | **신규** - JSON 포맷 옵션, 일관된 필드명 |
| `src/adapters/inbound/http/app.py` | 로깅 설정 초기화 |

**DoD:**
- [ ] DynamicToolset.get_tools() 호출 시 캐시 hit/miss와 반환 도구 수 로깅
- [ ] Runner.run_async() 호출 시 세션 ID와 이벤트 카운트 로깅
- [ ] JSON 로깅 포맷 옵션 제공
- [ ] 신규 테스트 3개 이상

---

### Part C: Dynamic Intelligence (Steps 7-8)

#### Step 7: 컨텍스트 인식 시스템 프롬프트

**수정 파일:**

| 파일 | 변경 내용 |
|------|----------|
| `src/adapters/outbound/adk/orchestrator_adapter.py` | `_rebuild_agent()`에서 동적 instruction 생성. DynamicToolset에서 등록된 도구 목록, _sub_agents에서 A2A 에이전트 정보 추출하여 instruction에 포함 |
| `src/adapters/outbound/adk/dynamic_toolset.py` | `get_registered_info()` 메서드 추가 (엔드포인트별 도구 이름 목록 반환) |

**Instruction 템플릿:**
```
You are AgentHub, an intelligent assistant with access to external tools and agents.

## Available MCP Tools:
{동적 생성: 서버별 도구 목록}

## Available A2A Agents:
{동적 생성: 에이전트별 설명}

## Usage Guidelines:
- Use MCP tools for specific actions (data queries, file operations, API calls)
- Delegate to A2A agents when the task matches their specialization
- You can use multiple tools in sequence to complete complex tasks
- Always report which tools/agents you used in your response
```

**DoD:**
- [ ] LLM instruction에 등록된 MCP 도구 이름 목록 포함
- [ ] LLM instruction에 A2A 에이전트 설명 포함
- [ ] 도구/에이전트 추가/제거 시 instruction 자동 갱신
- [ ] 신규 테스트 4개 이상

---

#### Step 8: 도구 실행 재시도 로직

**수정 파일:**

| 파일 | 변경 내용 |
|------|----------|
| `src/adapters/outbound/adk/dynamic_toolset.py` | `call_tool()`에 재시도 로직 추가 (exponential backoff). 일시적 에러(timeout, connection)만 재시도, 영구 에러(404, auth)는 즉시 실패 |
| `src/config/settings.py` | `mcp.max_retries`, `mcp.retry_backoff_seconds` 설정 추가 |
| `configs/default.yaml` | 재시도 기본값 (max_retries=2, backoff=1.0) |

**DoD:**
- [ ] 일시적 도구 실행 실패 시 최대 N회 재시도
- [ ] Exponential backoff 적용
- [ ] 영구 에러는 재시도하지 않음
- [ ] 신규 테스트 5개 이상

---

### Part D: Reliability & Scale (Steps 9-11)

#### Step 9: A2A 에이전트 Health 모니터링

**수정 파일:**

| 파일 | 변경 내용 |
|------|----------|
| `src/domain/services/health_monitor_service.py` | A2A 타입 엔드포인트 health check 추가 (Agent Card URL GET) |
| `src/domain/services/registry_service.py` | `check_endpoint_health()`에서 타입별 분기 (MCP: toolset.health_check, A2A: a2a_client.health_check) |
| `src/domain/ports/outbound/a2a_port.py` | `health_check(endpoint_id)` 메서드 추가 |
| `src/adapters/outbound/a2a/a2a_client_adapter.py` | Agent Card URL GET으로 health check 구현 |

**DoD:**
- [ ] A2A 에이전트 주기적 health check
- [ ] 비정상 A2A 에이전트 로깅
- [ ] MCP/A2A 모두 health check API 동작
- [ ] 신규 테스트 3개 이상

---

#### Step 10: Defer Loading (대규모 도구 지원)

**수정 파일:**

| 파일 | 변경 내용 |
|------|----------|
| `src/adapters/outbound/adk/dynamic_toolset.py` | `MAX_ACTIVE_TOOLS` 100으로 증가. threshold 초과 시 메타데이터만 로드하는 `DeferredToolProxy` 래퍼 구현 |
| `src/config/settings.py` | `mcp.defer_loading_threshold` 설정 추가 (기본 30) |

**DoD:**
- [ ] 도구 30개 초과 시 메타데이터만 로드
- [ ] 도구 실행 시 풀 스키마 lazy load
- [ ] MAX_ACTIVE_TOOLS 100으로 증가
- [ ] 신규 테스트 4개 이상

---

#### Step 11: 앱 시작 시 저장된 엔드포인트 자동 복원

**문제:** 서버 재시작 시 JSON에 저장된 MCP/A2A 엔드포인트가 로드되지만, DynamicToolset과 Orchestrator에는 재연결되지 않음.

**수정 파일:**

| 파일 | 변경 내용 |
|------|----------|
| `src/adapters/inbound/http/app.py` | lifespan에서 저장된 엔드포인트 목록을 읽어 DynamicToolset 재연결 + A2A sub_agent 재등록 |
| `src/domain/services/registry_service.py` | `restore_endpoints()` 메서드 추가 |

**DoD:**
- [ ] 서버 재시작 시 저장된 MCP 서버 자동 재연결
- [ ] 서버 재시작 시 저장된 A2A 에이전트 자동 재등록
- [ ] 연결 실패 시 graceful 에러 처리 (비정상 엔드포인트 건너뛰기)
- [ ] 신규 테스트 4개 이상

---

## 4. 실행 순서 및 의존성

```
Part A (Critical)
  Step 1: A2A Wiring Fix         ← 최우선
  Step 2: SSE Event Streaming    ← Step 1 이후
  Step 3: Error Typing           ← Step 2 이후 (병렬 가능)

Part B (Observability)
  Step 4: LiteLLM Callbacks      ← Part A 이후 (독립)
  Step 5: Tool Call Tracing      ← Step 2 이후 (이벤트 스트림 필요)
  Step 6: Structured Logging     ← 독립 (아무 때나)

Part C (Dynamic Intelligence)
  Step 7: Dynamic Instruction    ← Step 1 이후 (A2A 연결 필요)
  Step 8: Tool Retry Logic       ← 독립

Part D (Reliability)
  Step 9: A2A Health Monitoring  ← Step 1 이후
  Step 10: Defer Loading         ← 독립
  Step 11: Endpoint Auto-Restore ← Step 1 이후
```

---

## 5. 예상 테스트 추가

| Part | Steps | 신규 테스트 | 누적 |
|------|:-----:|:----------:|:----:|
| Part A | 1-3 | ~15 | 330 |
| Part B | 4-6 | ~12 | 342 |
| Part C | 7-8 | ~9 | 351 |
| Part D | 9-11 | ~11 | 362 |
| **합계** | | **~47** | **~362** |

커버리지 목표: >= 90% (현재 90.63% 유지)

---

## 6. 검증 방법

### 자동 검증
```bash
# 전체 테스트 + 커버리지
pytest tests/ --cov=src --cov-fail-under=80 -q --tb=line -x

# Part A 검증: A2A 연결 + SSE 이벤트
pytest tests/unit/services/test_registry_service.py -q
pytest tests/integration/adapters/test_a2a_wiring.py -q

# Part B 검증: 로깅 + DB 저장
pytest tests/unit/adapters/test_litellm_callbacks.py -q
pytest tests/integration/adapters/test_tool_call_tracing.py -q
```

### 수동 검증
1. MCP 서버 등록 → 채팅에서 도구 사용 확인 → SSE에 tool_call/tool_result 이벤트 확인
2. A2A 에이전트 등록 → 채팅에서 에이전트 위임 확인 → SSE에 agent_transfer 이벤트 확인
3. 서버 로그에서 LLM 토큰 수, 도구 호출 이력 확인
4. 서버 재시작 후 엔드포인트 자동 복원 확인

---

## 7. 참고 자료

- [ADK Events](https://google.github.io/adk-docs/events/)
- [ADK Runtime](https://google.github.io/adk-docs/runtime/)
- [ADK MCP Tools](https://google.github.io/adk-docs/tools-custom/mcp-tools/)
- [ADK Multi-Agent Patterns](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
- [LiteLLM Callbacks](https://docs.litellm.ai/docs/observability/callbacks)
- [LiteLLM Custom Callbacks](https://docs.litellm.ai/docs/observability/custom_callback)
- [MCP Specification (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25)
- [A2A Protocol](https://a2a-protocol.org/latest/)
- [ADK MCP Resources Issue #1779](https://github.com/google/adk-python/issues/1779)
- [ADK MCP Prompts Discussion #3097](https://github.com/google/adk-python/discussions/3097)
