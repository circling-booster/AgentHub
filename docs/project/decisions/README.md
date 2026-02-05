# Architecture Decision Records (ADR)

프로젝트의 주요 아키텍처 결정을 기록합니다.

---

## ADR Index

| ID | Title | Status | Date |
|----|-------|--------|------|
| [ADR-0001](0001-adopt-adr-pattern.md) | ADR 패턴 도입 | Accepted | 2026-01 |
| [ADR-0009](0009-langgraph-a2a-not-plugin.md) | LangGraph A2A: Plugin이 아닌 Native | Accepted | 2026-01 |
| [ADR-0010](0010-adk-workflow-agents.md) | ADK Workflow Agents 채택 | Accepted | 2026-01 |
| [ADR-0011](ADR-011-workflow-agents-spike-results.md) | Workflow Agents Spike 결과 | Accepted | 2026-01 |

---

## Creating New ADRs

### Naming Convention

```
XXXX-<short-descriptive-title>.md
```

- `XXXX`: 4자리 순번 (0001, 0002, ...)
- `<short-descriptive-title>`: 하이픈으로 연결된 제목

예시: `0012-adopt-litellm-for-multi-llm.md`

### Template

```markdown
# ADR-XXXX: <Title>

## Status

Proposed | Accepted | Deprecated | Superseded by ADR-XXXX

## Context

결정이 필요한 배경과 문제 상황

## Decision

내린 결정과 그 이유

## Consequences

### Positive
- 장점 1
- 장점 2

### Negative
- 단점 1
- 단점 2

### Neutral
- 중립적 영향

## Alternatives Considered

검토했으나 채택하지 않은 대안들

## References

- 관련 문서, 링크
```

---

## ADR Status Lifecycle

```
Proposed → Accepted → [Deprecated | Superseded]
```

| Status | Description |
|--------|-------------|
| **Proposed** | 검토 중인 결정 |
| **Accepted** | 채택되어 적용 중 |
| **Deprecated** | 더 이상 유효하지 않음 |
| **Superseded** | 새로운 ADR로 대체됨 |

---

## When to Write an ADR

다음 상황에서 ADR을 작성합니다:

1. **아키텍처 변경**: 시스템 구조에 영향을 주는 결정
2. **기술 스택 선택**: 프레임워크, 라이브러리 도입
3. **패턴 채택**: 코딩 패턴, 테스트 전략 변경
4. **트레이드오프**: 명확한 장단점이 있는 선택

ADR을 작성하지 않아도 되는 경우:
- 사소한 리팩토링
- 버그 수정
- 문서 업데이트

---

## Related

- [Project Hub](../) - 프로젝트 관리 허브
- [Planning](../planning/) - 로드맵 및 계획

---

*Last Updated: 2026-02-05*
