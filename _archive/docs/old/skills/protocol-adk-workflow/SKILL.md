---
name: adk-workflow
description: Google ADK 멀티에이전트 워크플로우를 생성합니다. 에이전트 체인, 병렬 처리 구현 시 사용하세요.
argument-hint: <pattern: sequential|parallel|loop>
---

# ADK 워크플로우 생성

패턴: `$ARGUMENTS`

## 지원 패턴

### Sequential (순차)
```python
from google.adk.agents import SequentialAgent

workflow = SequentialAgent(
    name="pipeline",
    sub_agents=[agent1, agent2, agent3]
)
```

### Parallel (병렬)
```python
from google.adk.agents import ParallelAgent

workflow = ParallelAgent(
    name="parallel-tasks",
    sub_agents=[agent1, agent2, agent3]
)
```

### Loop (반복)
```python
from google.adk.agents import LoopAgent

workflow = LoopAgent(
    name="iterative",
    sub_agent=processor,
    max_iterations=10
)
```

### Custom Router (조건부)
```python
from google.adk.agents import Agent

def route_request(context):
    if context.needs_code:
        return code_agent
    return general_agent

orchestrator = Agent(
    name="router",
    sub_agents=[code_agent, general_agent],
    router=route_request
)
```

## 작업 절차

1. 워크플로우 목적 파악
2. 적절한 패턴 선택
3. 서브에이전트 정의
4. 연결 및 설정

## 참고

- [ADK Multi-Agent](https://google.github.io/adk-docs/agents/multi-agents/)
