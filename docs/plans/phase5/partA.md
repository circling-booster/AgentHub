# Phase 5 Part A: A2A Verification & Test Agents (Steps 1-4)

> **상태:** 📋 Planned
> **선행 조건:** Phase 4 Part A-D Complete
> **목표:** A2A 에이전트가 LLM에 의해 실제로 인식/위임되는지 검증, 향상된 테스트 에이전트 생성
> **예상 테스트:** ~14 신규 (backend)
> **실행 순서:** Step 1 → Step 2 → Step 3 → Step 4

---

## 🎯 Progress Checklist

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **1** | A2A Wiring Diagnostic | ✅ |
| **2** | Enhanced Echo Agent | ✅ |
| **3** | Math Agent (ADK LlmAgent, ADR-9) | ✅ |
| **4** | A2A Full Flow Integration Test | ✅ |

**범례:** ✅ 완료 | 🚧 진행중 | ⬜ 미착수

**완료 일자:** 2026-02-01
**테스트:** 11 신규 (Step 1: 4, Step 3: 4, Step 4: 3)
**커버리지:** 91% (목표 90% 초과)

---

## Part A Prerequisites

### 선행 조건

- [ ] 기존 테스트 전체 통과: `pytest tests/ -q --tb=line -x`
- [ ] Coverage >= 90%: 현재 91%
- [ ] 브랜치: `feature/phase-5`

### Step별 검증 게이트

| Step | 검증 항목 | 방법 |
|:----:|----------|------|
| 1 시작 | ADK LlmAgent sub_agents 전달 방식 확인 | Web search |
| 1 시작 | RemoteA2aAgent 생성 시 필수 파라미터 확인 | 코드 리뷰 |
| 3 시작 | LangGraph 최신 API 확인 | Web search |
| 4 완료 | A2A 전체 흐름 검증 | Integration test |

---

## 핵심 문제

**현상:** LLM에 프롬프트를 보내면 MCP Tool은 인식하지만, A2A Agent에 대한 인식이 없는 듯 함.

**가능한 원인:**
1. **Echo Agent 문제:** 테스트 Echo Agent가 유용한 기능을 제공하지 않아 LLM이 위임할 이유를 못 찾음
2. **Wiring 문제:** `sub_agents` 리스트가 LlmAgent에 제대로 전달되지 않음
3. **Instruction 문제:** 동적 시스템 프롬프트에 A2A 에이전트 정보가 부족함
4. **ADK 제한:** ADK의 RemoteA2aAgent가 특정 조건에서만 작동

**접근:** Step 1에서 진단 후, Step 2-3에서 테스트 에이전트 개선, Step 4에서 전체 흐름 검증

---

## Step 1: A2A Wiring Diagnostic

**문제:** A2A 에이전트 등록 후 LLM이 실제로 인식하는지 확인 필요

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/outbound/adk/orchestrator_adapter.py` | MODIFY | `_rebuild_agent()` 에 sub_agents 상태 디버그 로깅 추가 |
| `tests/integration/adapters/test_a2a_wiring_diagnostic.py` | NEW | A2A wiring 진단 테스트 |

**핵심 검증 항목:**
```python
# 검증 1: sub_agents 딕셔너리 채워지는지
assert len(orchestrator._sub_agents) > 0

# 검증 2: _rebuild_agent() 후 LlmAgent.sub_agents에 포함되는지
assert orchestrator._agent.sub_agents is not None
assert len(orchestrator._agent.sub_agents) > 0

# 검증 3: 동적 instruction에 A2A 섹션이 포함되는지
instruction = orchestrator._build_dynamic_instruction()
assert "A2A" in instruction or "agent" in instruction.lower()

# 검증 4: LLM이 실제로 agent_transfer 이벤트를 생성하는지 (integration)
```

**TDD 순서:**
1. RED: `test_sub_agents_populated_after_registration`
2. RED: `test_rebuild_agent_includes_sub_agents`
3. RED: `test_dynamic_instruction_contains_a2a_section`
4. RED: `test_llm_delegates_to_a2a_agent` (integration, real LLM 호출)
5. GREEN: 디버그 로깅 추가, 필요 시 wiring 수정
6. REFACTOR: 불필요한 디버그 로그 제거

**DoD:**
- [ ] 4개 진단 테스트 전체 통과
- [ ] A2A 미인식 원인 파악 완료
- [ ] 원인이 Echo Agent 문제인지, Wiring 문제인지 결론

**의존성:** 없음 (Part A 첫 번째 Step)

---

## Step 2: Enhanced Echo Agent

**문제:** 현재 Echo Agent의 Agent Card description이 너무 단순하여 LLM이 위임할 이유를 찾지 못할 수 있음

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `tests/fixtures/a2a_agents/echo_agent.py` | MODIFY | Agent Card 설명 강화, capabilities 추가 |

**핵심 설계:**
```python
# 기존 (불충분)
AGENT_CARD = {
    "name": "echo_agent",
    "description": "A simple echo agent for testing",
    ...
}

# 개선 (LLM이 위임할 수 있도록)
AGENT_CARD = {
    "name": "echo_agent",
    "description": "Echo agent that repeats and transforms user input. "
                   "Use this agent when the user explicitly asks to echo, "
                   "repeat, mirror, or transform their message. "
                   "Supports: echo, repeat, reverse text.",
    "capabilities": {
        "echo": "Repeat the exact input text",
        "reverse": "Reverse the input text",
    },
    ...
}
```

**DoD:**
- [ ] Agent Card description이 LLM에게 명확한 위임 기준 제공
- [ ] 기존 Echo Agent 테스트 regression 없음

**의존성:** Step 1 결과에 따라 방향 조정

---

## Step 3: LangGraph Chat Agent

**목표:** 실제 LLM을 사용하는 A2A 테스트 에이전트 생성. 수학/계산 전문 도메인.

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `tests/fixtures/a2a_agents/chat_agent.py` | NEW | LangGraph 기반 Chat Agent (수학 전문) |
| `tests/fixtures/a2a_agents/requirements.txt` | NEW | langgraph, langchain-openai 의존성 |
| `tests/conftest.py` | MODIFY | chat_agent fixture 추가 (동적 포트) |

**핵심 설계:**
```python
# tests/fixtures/a2a_agents/chat_agent.py
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI

class State(TypedDict):
    messages: Annotated[list, add_messages]

llm = ChatOpenAI(model="gpt-4o-mini")

def math_chatbot(state: State):
    """수학/계산 전문 챗봇"""
    system_msg = ("You are a math specialist. You can solve arithmetic, "
                  "algebra, and basic calculus problems.")
    return {"messages": [llm.invoke([{"role": "system", "content": system_msg}] + state["messages"])]}

graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", math_chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
agent = graph_builder.compile()

# A2A Server로 노출
AGENT_CARD = {
    "name": "math_agent",
    "description": "Mathematics specialist agent. Delegates to this agent "
                   "when the user asks math questions, calculations, "
                   "arithmetic, algebra, or calculus problems.",
    ...
}
```

**동적 포트 할당:**
```python
# tests/conftest.py
import socket

def get_free_port():
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1]
```

**TDD 순서:**
1. RED: `test_chat_agent_responds_standalone` - Agent 단독 실행 확인
2. RED: `test_chat_agent_a2a_server_starts` - A2A 서버 시작 확인
3. RED: `test_orchestrator_delegates_math_to_chat_agent` - LLM 위임 확인
4. GREEN: chat_agent.py 구현, conftest.py fixture 추가
5. REFACTOR: 공통 부분 추출

**DoD:**
- [ ] LangGraph Chat Agent가 수학 질문에 올바르게 응답
- [ ] A2A 서버로 노출 시 Agent Card 교환 성공
- [ ] 동적 포트 할당으로 테스트 격리

**의존성:** Step 1 (진단 결과), Step 2 (Echo Agent 개선)

---

## Step 4: A2A Full Flow Integration Test

**목표:** Echo + Chat Agent 모두 등록 후, 메시지별 적절한 에이전트에 위임하는 전체 흐름 검증

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `tests/integration/test_a2a_full_flow.py` | NEW | A2A 전체 흐름 통합 테스트 |

**테스트 시나리오:**
```python
# 시나리오 1: "Echo this: hello world" → echo_agent에 위임
# 시나리오 2: "What is 2 + 3 * 4?" → math_agent에 위임
# 시나리오 3: "What's the weather?" → 위임 없이 직접 응답 (매칭 에이전트 없음)
```

**검증 포인트:**
- SSE 스트림에 `agent_transfer` 이벤트 포함 여부
- 응답 내용이 해당 에이전트에서 온 것인지 확인
- 매칭 에이전트 없는 경우 graceful fallback

**TDD 순서:**
1. RED: `test_echo_delegation_full_flow`
2. RED: `test_math_delegation_full_flow`
3. RED: `test_no_matching_agent_fallback`
4. GREEN: 필요 시 orchestrator_adapter.py 수정
5. REFACTOR: 테스트 헬퍼 함수 추출

**DoD:**
- [ ] 3개 시나리오 모두 통과
- [ ] SSE stream에 agent_transfer 이벤트 확인
- [ ] 기존 테스트 regression 없음

**의존성:** Step 1 + Step 2 + Step 3 모두 완료

---

## Skill/Agent 활용 계획

| 시점 | 호출 | 목적 |
|------|------|------|
| Step 1 시작 | Web search (ADK RemoteA2aAgent) | ADK sub_agents 작동 방식 확인 |
| Step 3 시작 | Web search (LangGraph + A2A) | LangGraph 최신 API 확인 |
| Step 1-3 구현 | `/tdd` | TDD Red-Green-Refactor |
| Step 4 완료 | code-reviewer | 전체 A2A 코드 검토 |

---

## 커밋 정책

```
feat(phase5): Step 1 - A2A wiring diagnostic tests
feat(phase5): Step 2 - Enhanced echo agent description
feat(phase5): Step 3 - LangGraph math chat agent
feat(phase5): Step 4 - A2A full flow integration tests
docs(phase5): Part A complete - A2A Verification
```

---

## Part A Definition of Done

### 기능
- [ ] A2A wiring 진단 완료 (근본 원인 파악)
- [ ] Echo Agent: 명확한 위임 기준 제공
- [ ] Chat Agent: 수학 전문 LLM 에이전트 동작
- [ ] 전체 흐름: 메시지별 적절한 에이전트 위임

### 품질
- [ ] Backend 14+ 테스트 추가
- [ ] Coverage >= 90% 유지
- [ ] 기존 테스트 regression 없음

### 문서
- [ ] Part A progress checklist 업데이트

---

## 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|--------|:------:|------|
| ADK RemoteA2aAgent가 LLM 위임 미지원 | 🔴 | ADK GitHub Issues 확인, workaround (커스텀 sub-agent) |
| LangGraph 의존성 충돌 | 🟡 | test fixture에만 한정, 별도 requirements.txt |
| 수학 질문 위임 불안정 (LLM 판단) | 🟡 | 더 명확한 프롬프트 + 여러 번 실행 검증 |
| A2A echo agent 포트 충돌 | 🟢 | 동적 포트 할당으로 해결 |

---

## Deferred Features (Phase 6+)

### Multi-step A2A Delegation Test (Advanced Orchestration)

**목표:** LLM이 복합 과업을 분해하여 여러 A2A 에이전트에 순차/병렬 위임

**시나리오 예시:**
```python
async def test_llm_multi_agent_task_decomposition():
    """
    Given: 항공사 에이전트 + 환율 에이전트 등록
    When: "최저가 비행기를 찾아서 현재 환율로 조회해줘"
    Then:
      - 항공사 에이전트 호출 (agent_transfer 이벤트)
      - 환율 에이전트 호출 (agent_transfer 이벤트)
      - 2개 이상 agent_transfer 이벤트 발생
      - 최종 응답에 항공편 + 환율 정보 모두 포함
    """
```

**연기 이유:**
- Phase 5 Part A는 "단일 에이전트 위임" 검증에 집중
- Multi-step delegation은 더 복잡한 orchestration 패턴 필요
- 적절한 테스트 에이전트 (항공사, 환율 등) 구현 필요

**구현 시점:** Phase 6 이후 (A2A Advanced 기능으로 분류)

**참고:**
- ADK는 LLM-Driven Orchestration 지원 (LlmAgent + sub_agents)
- Sequential/Parallel Agent 패턴 활용 가능
- 웹 검색: [Multi-Agent Systems in ADK](https://google.github.io/adk-docs/agents/multi-agents/)

---

*Part A 계획 작성일: 2026-01-31*
*Part A 완료일: 2026-02-01*
