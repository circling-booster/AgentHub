# Phase 5 Part E: ADK Workflow Agents (Steps 13-16)

> **상태:** 📋 Planned
> **선행 조건:** Phase 5 Part A Complete (A2A 단일 위임 검증 완료)
> **목표:** ADK 네이티브 Workflow Agents (SequentialAgent, ParallelAgent) 도입으로 Multi-step A2A Delegation 지원
> **예상 테스트:** ~32 신규 (12 unit + 14 integration + 2 E2E + 4 Vitest)
> **실행 순서:** Step 13 → Step 14 → Step 15 → Step 16

---

## 🎯 Progress Checklist

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **13** | ADK Workflow Agent API 검증 (Spike Test) | ⬜ |
| **14** | WorkflowAgent 도메인 엔티티 + OrchestratorAdapter 확장 | ⬜ |
| **15** | Workflow API Endpoint + Extension UI | ⬜ |
| **16** | ParallelAgent 지원 + E2E 시나리오 | ⬜ |

**범례:** ✅ 완료 | 🚧 진행중 | ⬜ 미착수

---

## Part E Prerequisites

- [ ] Part A Complete (A2A 단일 위임 검증 완료)
- [ ] 기존 테스트 전체 통과
- [ ] Echo Agent + Math Agent fixture 동작 확인

### Step별 검증 게이트

| Step | 검증 항목 | 방법 |
|:----:|----------|------|
| 13 시작 | ADK SequentialAgent import 경로 확인 | Web search |
| 13 시작 | SequentialAgent + RemoteA2aAgent 호환성 | Spike test |
| 14 시작 | Step 13 Spike 결과 반영 | 코드 리뷰 |
| 15 시작 | ADK Runner + SequentialAgent 이벤트 구조 | Web search |

---

## 배경: 현재 제약과 ADK 해법

### 현재 상태 (Phase 5 Part A)
```
User Message → LlmAgent (sub_agents) → 1개 Agent 위임 → 결과 반환
❌ 순차 실행 불가 (Agent A → Agent B → Agent C)
❌ 병렬 실행 불가 (Agent A + Agent B 동시)
```

### ADK 표준 Workflow Agents
```python
from google.adk.agents import SequentialAgent, ParallelAgent, LoopAgent

# 순차 실행: Agent A → Agent B → Agent C (자동 체인)
sequential = SequentialAgent(name="seq", sub_agents=[agent_a, agent_b, agent_c])

# 병렬 실행: Agent A + Agent B 동시
parallel = ParallelAgent(name="par", sub_agents=[agent_a, agent_b])
```

### State 공유 메커니즘
- `output_key`: Agent의 결과를 `session.state[key]`에 자동 저장
- 다음 Agent가 `{key}`로 참조하여 파이프라인 구성
- 모든 sub_agents가 동일한 `InvocationContext`를 공유

---

## Step 13: ADK Workflow Agent API 검증 (Spike Test)

**목표:** SequentialAgent + RemoteA2aAgent 조합이 실제 동작하는지 먼저 검증

**핵심 질문 (웹 검색 + 코드 실험으로 확인):**
1. `SequentialAgent(sub_agents=[RemoteA2aAgent(...)])` — 실행 가능?
2. RemoteA2aAgent에 `output_key` 설정 가능?
3. State 공유가 A2A 에이전트 간 동작?

**수정/생성 파일:**

| 파일 | 작업 | 내용 |
|------|:----:|------|
| `tests/integration/adapters/test_workflow_agent_spike.py` | NEW | Spike test: SequentialAgent + Echo/Math agents |

**TDD 순서:**
1. RED: `test_sequential_agent_with_two_remote_agents` — Echo → Math 순차 실행
2. RED: `test_sequential_agent_state_sharing` — output_key로 결과 전달
3. RED: `test_sequential_agent_with_local_llm_agent` — LlmAgent + RemoteA2aAgent 혼합
4. RED: `test_parallel_agent_with_remote_agents` — 병렬 실행

**리스크 대응:**
- RemoteA2aAgent가 SequentialAgent 내부에서 비호환 시:
  - **대안 A**: LlmAgent wrapper (RemoteA2aAgent를 감싸는 LlmAgent 사용)
  - **대안 B**: Custom SequentialRunner (직접 순차 실행 로직 구현)
  - 대안 결정은 Spike 결과에 따라 Step 14에 반영

**DoD:**
- [ ] SequentialAgent + RemoteA2aAgent 조합 동작 확인 (또는 제약 사항 문서화)
- [ ] State 공유 메커니즘 확인
- [ ] 동작하지 않는 경우 대안 설계 (Step 14에 반영)

---

## Step 14: WorkflowAgent 도메인 엔티티 + Orchestrator 확장

**목표:** 도메인 엔티티와 Adapter에 Workflow Agent 지원 추가

### 14-1. 도메인 엔티티

**수정/생성 파일:**

| 파일 | 작업 | 내용 |
|------|:----:|------|
| `src/domain/entities/workflow.py` | NEW | Workflow, WorkflowStep 엔티티 (순수 Python) |
| `tests/unit/domain/entities/test_workflow.py` | NEW | 엔티티 단위 테스트 |

**핵심 설계:**
```python
# src/domain/entities/workflow.py (순수 Python, 외부 의존성 없음)
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class WorkflowStep:
    """Workflow 내 단일 실행 단계"""
    agent_endpoint_id: str   # 등록된 A2A agent의 endpoint_id
    output_key: str          # session.state에 저장할 키
    instruction: str = ""    # 이 step에 특화된 instruction (선택)

@dataclass
class Workflow:
    """Multi-step Agent Workflow 정의"""
    id: str
    name: str
    workflow_type: str       # "sequential" | "parallel"
    steps: list[WorkflowStep]
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
```

### 14-2. StreamChunk 이벤트 확장

**수정 파일:**

| 파일 | 작업 | 내용 |
|------|:----:|------|
| `src/domain/entities/stream_chunk.py` | MODIFY | Workflow 이벤트 타입 추가 |

```python
# stream_chunk.py 추가 메서드
@staticmethod
def workflow_start(workflow_id: str, workflow_type: str, total_steps: int) -> "StreamChunk": ...

@staticmethod
def workflow_step_start(workflow_id: str, step_number: int, agent_name: str) -> "StreamChunk": ...

@staticmethod
def workflow_step_complete(workflow_id: str, step_number: int, agent_name: str) -> "StreamChunk": ...

@staticmethod
def workflow_complete(workflow_id: str, status: str, total_steps: int) -> "StreamChunk": ...
```

### 14-3. OrchestratorAdapter 확장

**수정 파일:**

| 파일 | 작업 | 내용 |
|------|:----:|------|
| `src/domain/ports/outbound/orchestrator_port.py` | MODIFY | Workflow 메서드 추가 |
| `src/adapters/outbound/adk/orchestrator_adapter.py` | MODIFY | `create_workflow_agent()`, `execute_workflow()` |
| `tests/unit/adapters/test_workflow_orchestrator.py` | NEW | Workflow 실행 단위 테스트 |
| `tests/integration/adapters/test_workflow_integration.py` | NEW | Echo→Math 통합 테스트 |
| `src/config/container.py` | MODIFY | DI 업데이트 (필요시) |

**핵심 설계:**
```python
# orchestrator_adapter.py 추가 메서드 (개요)
async def create_workflow_agent(self, workflow: Workflow) -> None:
    """Workflow 정의 → ADK SequentialAgent/ParallelAgent 생성"""
    if workflow.workflow_type == "sequential":
        sub_agents = [self._sub_agents[step.agent_endpoint_id] for step in workflow.steps]
        self._workflow_agents[workflow.id] = SequentialAgent(
            name=f"workflow_{workflow.id}",
            sub_agents=sub_agents,
        )
    # ...

async def execute_workflow(
    self, workflow_id: str, message: str, conversation_id: str,
) -> AsyncIterator[StreamChunk]:
    """Workflow Agent 실행 + StreamChunk 이벤트 스트리밍"""
    workflow_agent = self._workflow_agents[workflow_id]
    # Runner로 실행, 이벤트 스트리밍
    ...
```

**TDD(SKILLS 호출) 순서(기재되지 않아도 구현 전 테스트 작성 필수):**
1. RED: `test_workflow_entity_creation` (4 tests)
2. RED: `test_workflow_step_validation` (4 tests)
3. GREEN: Workflow 엔티티 구현
4. RED: `test_create_sequential_workflow_agent` (2 tests)
5. RED: `test_execute_sequential_workflow_streams_events` (2 tests)
6. GREEN: OrchestratorAdapter workflow 메서드 구현
7. REFACTOR

**DoD:**
- [ ] Workflow 도메인 엔티티 순수 Python (ADK 의존성 없음)
- [ ] OrchestratorAdapter에 workflow 생성/실행 메서드 추가
- [ ] Echo → Math 순차 실행 통합 테스트 통과
- [ ] Coverage >= 90% 유지

---

## Step 15: Workflow API Endpoint + Extension UI

**목표:** REST API + Extension UI로 Workflow 생성/실행

### 15-1. Backend API

**수정/생성 파일:**

| 파일 | 작업 | 내용 |
|------|:----:|------|
| `src/adapters/inbound/http/routes/workflow.py` | NEW | Workflow CRUD + Execute API |
| `src/adapters/inbound/http/schemas/workflow.py` | NEW | Pydantic 스키마 |
| `tests/integration/adapters/test_workflow_api.py` | NEW | API 통합 테스트 |

**API 설계:**
```
POST   /api/workflows                   # Workflow 생성
GET    /api/workflows                   # 목록 조회
GET    /api/workflows/{id}              # 상세 조회
DELETE /api/workflows/{id}              # 삭제
POST   /api/workflows/{id}/execute      # Workflow 실행 (SSE 스트리밍)
```

### 15-2. Extension UI

**수정/생성 파일:**

| 파일 | 작업 | 내용 |
|------|:----:|------|
| `extension/entrypoints/sidepanel/components/WorkflowManager.tsx` | NEW | Workflow 관리 UI |
| `extension/lib/types.ts` | MODIFY | Workflow TypeScript 타입 추가 |
| `extension/lib/sse.ts` | MODIFY | Workflow 이벤트 핸들링 추가 |
| `extension/components/__tests__/WorkflowManager.test.tsx` | NEW | Vitest 테스트 |

**TDD(SKILLS 호출) 순서(기재되지 않아도 구현 전 테스트 작성 필수):**
1. RED: `test_create_workflow_api` (2 tests)
2. RED: `test_execute_workflow_api_streams_sse` (2 tests)
3. RED: `test_list_delete_workflow_api` (2 tests)
4. GREEN: API 구현
5. RED: WorkflowManager Vitest (4 tests)
6. GREEN: Extension UI 구현
7. REFACTOR

**DoD:**
- [ ] Workflow CRUD API 동작
- [ ] Workflow 실행 시 SSE 스트리밍 (workflow_start → step_start → step_complete → workflow_complete)
- [ ] Extension Sidepanel에 Workflow 관리 탭 추가
- [ ] 기존 테스트 regression 없음

---

## Step 16: ParallelAgent 지원 + E2E 시나리오

**목표:** 병렬 실행 지원 + 전체 흐름 E2E 검증

**수정/생성 파일:**

| 파일 | 작업 | 내용 |
|------|:----:|------|
| `src/adapters/outbound/adk/orchestrator_adapter.py` | MODIFY | ParallelAgent 지원 |
| `tests/integration/adapters/test_parallel_workflow.py` | NEW | 병렬 실행 테스트 |
| `tests/e2e/test_workflow_e2e.py` | NEW | E2E 시나리오 |

**테스트 시나리오:**
1. **Sequential E2E**: Extension → Workflow 생성 → Echo→Math 순차 실행 → UI에 결과 표시
2. **Parallel E2E**: Echo + Math 병렬 실행 → 결과 병합 → UI에 표시
3. **Workflow SSE Execution** (Step 15에서 deferred): 실제 A2A 에이전트와 함께 Workflow 실행 SSE 스트리밍 검증

**TDD(SKILLS 호출) 순서(기재되지 않아도 구현 전 테스트 작성 필수):**
1. RED: `test_parallel_workflow_execution` (2 tests)
2. RED: `test_parallel_state_isolation` (2 tests)
3. GREEN: ParallelAgent 지원 구현
4. RED: E2E scenarios (2 tests)
5. GREEN: E2E 통과
6. REFACTOR

**DoD:**
- [ ] ParallelAgent로 2개 에이전트 병렬 실행
- [ ] State isolation 확인 (각 agent 별도 output_key)
- [ ] E2E: Extension → Workflow API → Agent 실행 → 결과 표시
- [ ] Step 15 deferred test: Workflow SSE 실행 스트리밍 검증 (실제 A2A 에이전트 사용)
- [ ] Coverage >= 90% 유지

---

## Skill/Agent 활용 계획

| 시점 | 호출 | 목적 |
|------|------|------|
| Step 13 시작 | Web search (ADK SequentialAgent API) | 최신 API 확인 |
| Step 13 시작 | Web search (ADK + RemoteA2aAgent) | 호환성 확인 |
| Step 13-16 구현 | `/tdd` | TDD Red-Green-Refactor |
| Step 14 완료 | hexagonal-architect | 도메인 순수성 검증 |
| Step 16 완료 | code-reviewer | 전체 코드 품질 리뷰 |

---

## 커밋 정책

```
# Step 13 완료 후
test(phase5): Step 13 - ADK Workflow Agent spike test (SequentialAgent + RemoteA2aAgent)

# Step 14 완료 후
feat(phase5): Step 14 - Workflow entity + OrchestratorAdapter workflow support

# Step 15 완료 후
feat(phase5): Step 15 - Workflow REST API + Extension UI

# Step 16 완료 후
feat(phase5): Step 16 - ParallelAgent support + E2E tests
docs(phase5): Part E complete - ADK Workflow Agents
```

---

## Part E Definition of Done

### 기능
- [ ] SequentialAgent로 2+ 에이전트 순차 실행
- [ ] ParallelAgent로 2+ 에이전트 병렬 실행
- [ ] Workflow CRUD API 동작
- [ ] Extension UI에서 Workflow 생성/실행
- [ ] 기존 단일 위임 (Phase 5A) 동작 유지

### 품질
- [ ] ~32 신규 테스트 (12 unit + 14 integration + 2 E2E + 4 Vitest)
- [ ] Backend coverage >= 90%
- [ ] TDD Red-Green-Refactor 사이클 준수
- [ ] 기존 테스트 전체 통과

### 문서
- [ ] ADR-10: ADK Workflow Agents 도입 결정 기록
- [ ] `docs/STATUS.md` Phase 5 Part E 추가
- [ ] `docs/roadmap.md` Part E 반영

---

## 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|--------|:------:|------|
| SequentialAgent + RemoteA2aAgent 비호환 | 🔴 | Step 13 Spike로 조기 발견. 대안: LlmAgent wrapper |
| RemoteA2aAgent output_key 미지원 | 🟡 | 수동 state 관리 또는 wrapper agent 사용 |
| ParallelAgent state race condition | 🟡 | 고유 output_key 강제 (prefix 규칙) |
| ADK API 변경 (breaking changes) | 🟡 | 구현 전 웹 검색으로 최신 API 확인 |
| 기존 단일 위임 regression | 🟢 | 기존 테스트 전체 실행으로 확인 |

---

*Part E 계획 작성일: 2026-02-01*
