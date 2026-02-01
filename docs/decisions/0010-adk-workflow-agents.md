# ADR-0010: ADK Workflow Agents (SequentialAgent / ParallelAgent) 도입

## 상태

승인됨

## 날짜

2026-02-01

## 컨텍스트

Phase 5 Part A에서 A2A 단일 에이전트 위임이 검증 완료되었으나, **Multi-step A2A Delegation**(여러 에이전트에 순차/병렬 위임)은 미구현 상태였다.

현재 제약:
- ADK Runner의 `run_async()`는 `transfer_to_agent` 후 자동 체인 실행을 하지 않음
- LlmAgent → 1개 RemoteA2aAgent 위임 후 결과 반환으로 종료
- 복합 과업(Echo → Math → Echo)을 분해하여 순차 실행 불가

AgentHub의 1차 목표는 ADK를 네이티브로 지원하는 것이므로, ADK 표준 방식으로 Multi-step Delegation을 해결해야 한다.

## 결정

**ADK 네이티브 Workflow Agents (SequentialAgent, ParallelAgent)를 도입한다.**

```python
from google.adk.agents import SequentialAgent, ParallelAgent

# 순차 실행: deterministic pipeline
workflow = SequentialAgent(
    name="echo_math_workflow",
    sub_agents=[echo_agent, math_agent, echo_agent],
)

# 병렬 실행: concurrent execution
parallel = ParallelAgent(
    name="parallel_query",
    sub_agents=[echo_agent, math_agent],
)
```

**배치:** Phase 5 Part E (Steps 13-16)

**핵심 API:**
- Import: `from google.adk.agents import SequentialAgent, ParallelAgent, LoopAgent`
- State 공유: `output_key` → `session.state[key]` → 다음 agent 접근
- 모든 sub_agents가 동일한 `InvocationContext` 공유

## 대안

### 대안 1: LLM 기반 사전 분석 (Option A)
- 사전 LLM 호출로 agent sequence를 미리 분석/계획
- 장점: 유연함, 자연어 이해
- 단점: 추가 LLM 호출 비용, 비결정적, ADK 비표준

### 대안 2: 수동 오케스트레이션 루프 (Option C)
- 여러 번의 `run_async()` 호출로 수동 체인 구성
- 장점: LLM이 동적으로 sequence 결정, 유연함
- 단점: ADK 비표준 workaround, 복잡도 높음, 토큰 비용 증가
- ADK 공식 가이드: "Start simple: Do not build a nested loop system on day one"

### 대안 3: 현재 상태 유지 (기능 추가 없음)
- 단일 위임만 지원, Multi-step은 Phase 6+ 연기
- 장점: 구현 비용 없음
- 단점: 핵심 기능 부재, ADK의 Workflow Agent 활용 못함

## 근거

1. **ADK 네이티브 우선**: AgentHub의 1차 목표가 ADK 네이티브 지원이므로, ADK 공식 패턴인 SequentialAgent/ParallelAgent 사용이 자연스러움
2. **결정적 실행**: Workflow Agent는 LLM 없이 deterministic하게 실행되어 예측 가능하고 비용 효율적
3. **공식 문서 지원**: [ADK Sequential Agents](https://google.github.io/adk-docs/agents/workflow-agents/sequential-agents/) 공식 문서에서 권장
4. **복잡도 최소화**: 수동 오케스트레이션(Option C) 대비 구현/유지보수 복잡도가 낮음

## 결과

### 긍정적 영향
- ADK 네이티브 Workflow Agents로 Multi-step A2A Delegation 지원
- SequentialAgent: 고정 순서 파이프라인 (Echo → Math → Echo)
- ParallelAgent: 병렬 실행 (Echo + Math 동시)
- State 공유(`output_key`)로 agent 간 데이터 전달

### 부정적 영향 / 트레이드오프
- SequentialAgent는 **고정 순서** (LLM이 동적으로 순서 결정 불가)
- RemoteA2aAgent와의 호환성이 공식 문서에 미언급 (Spike Test 필요)
- Workflow 정의 API 추가로 API surface 증가

### 후속 조치
- [ ] Phase 5 Part E Step 13: Spike Test로 SequentialAgent + RemoteA2aAgent 호환성 검증
- [ ] 비호환 시 대안 설계 (LlmAgent wrapper)
- [ ] Phase 5 Part E Steps 14-16: 도메인 엔티티, API, Extension UI, E2E 구현

## 관련 문서

- [Phase 5 Part E 계획](../plans/phase5/partE.md)
- [ADK Sequential Agents](https://google.github.io/adk-docs/agents/workflow-agents/sequential-agents/)
- [ADK Multi-Agent Systems](https://google.github.io/adk-docs/agents/multi-agents/)
- [ADR-9: LangGraph=A2A, Plugin=개별 도구만](0009-langgraph-a2a-not-plugin.md)
