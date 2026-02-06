# Plan NN: {Descriptive Name}

## Overview

**목표:** {Plan의 핵심 목표를 1-2문장으로 설명}

**핵심 원칙:**
- **TDD Required**: 모든 구현은 테스트 먼저 작성 (Red → Green → Refactor)
- **헥사고날 아키텍처**: {레이어별 구현 순서 명시}
- **테스트 격리**: 단위/통합/E2E 테스트 명확히 구분

**현재 상태:**
- Branch: `feature/plan-NN-{descriptive-name}`
- Test Coverage: {현재 커버리지}%
- Phase Progress: See [Implementation Phases](#implementation-phases) below

---

## User Decisions

(필요 시) 구현 방향에 대한 사용자 결정 사항 기록

| 항목 | 선택 |
|------|------|
| **Tech Stack** | {선택한 기술 스택} |
| **Approach** | {선택한 접근 방식} |

---

## Implementation Phases

각 Phase는 **헥사고날 아키텍처 레이어**에 정렬되며, **TDD 사이클(Red-Green-Refactor)**을 따릅니다.

| Phase | Layer | Status | 문서 |
|-------|-------|--------|------|
| **Phase 1** | {Layer Name} | ⏸️ Pending | [01_{phase_name}.md](01_{phase_name}.md) |
| **Phase 2** | {Layer Name} | ⏸️ Pending | [02_{phase_name}.md](02_{phase_name}.md) |
| **Phase 3** | {Layer Name} | ⏸️ Pending | [03_{phase_name}.md](03_{phase_name}.md) |
| **Phase 4** | {Layer Name} | ⏸️ Pending | [04_{phase_name}.md](04_{phase_name}.md) |
| **Phase 5** | {Layer Name} | ⏸️ Pending | [05_{phase_name}.md](05_{phase_name}.md) |

**Status Icons:**
- ⏸️ **Pending** - 대기 중
- 🔄 **In Progress** - 진행 중 (항상 1개만)
- ✅ **Done** - 완료

**Phase Update Workflow:**
1. **Phase 시작**: Status를 ⏸️ → 🔄로 변경
2. **Phase 완료**: Status를 🔄 → ✅로 변경, Git 커밋: `docs: complete phase N - {phase_name}`

---

## Architecture Diagram

```
{시스템 아키텍처 다이어그램 ASCII art}
```

---

## Features

### 필수 (Core Features)
- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3

### 고급 (Advanced)
- [ ] Advanced Feature 1

### 제외
- Reason for exclusion

---

## Test Strategy

### 1. Unit Tests (Phase N)
**위치:** `tests/unit/{module}/`
**대상:** {테스트 대상 모듈}
**도구:** pytest
**TDD 필수:** Red → Green → Refactor

### 2. Integration Tests (Phase N)
**위치:** `tests/integration/{module}/`
**대상:** {통합 테스트 대상}
**도구:** pytest
**TDD 필수:** Red → Green → Refactor

### 3. E2E Tests (Phase N)
**위치:** `tests/e2e/test_{feature}.py`
**대상:** {E2E 테스트 시나리오}
**도구:** pytest / Playwright
**TDD 필수:** Red → Green → Refactor

---

## File Structure

```
{예상 파일 구조}
src/
├── domain/
│   └── {entities, services, ports}
├── adapters/
│   ├── inbound/
│   └── outbound/

tests/
├── unit/
├── integration/
└── e2e/

docs/
└── {관련 문서}
```

---

## Verification

### 로컬 테스트
```bash
# 단위/통합 테스트
pytest tests/unit tests/integration -q

# E2E 테스트
pytest tests/e2e/ -v

# Coverage 검증
pytest --cov=src --cov-fail-under=80 -q
```

### 수동 테스트
```bash
{수동 테스트 명령어}
```

---

## Critical Files Summary

| 구분 | 파일 | Phase |
|------|------|-------|
| **{Category}** | `{file_path}` | N |

---

## Design Decisions

### Decision 1
- **이유**: {결정 근거}
- **트레이드오프**: {장단점}

### Decision 2
- **이유**: {결정 근거}
- **트레이드오프**: {장단점}

---

## Risk Mitigation

| 위험 | 대응 |
|------|------|
| {Risk 1} | {Mitigation 1} |
| {Risk 2} | {Mitigation 2} |

---

## TDD 원칙 (CRITICAL)

**모든 Phase는 반드시 다음 순서를 따릅니다:**

1. **Red**: 테스트 작성 → 실행 → 실패 확인
2. **Green**: 최소 구현 → 테스트 통과
3. **Refactor**: 코드 개선 → 테스트 여전히 통과

**TDD 적용:**
- **Phase 1-N**: {어떤 Phase에 어떤 TDD 전략을 적용할지 명시}

---

## Review Checklist

### 구현 전 검증
- [ ] Phase가 헥사고날 레이어에 정렬되었는가?
- [ ] 각 Phase에 TDD 사이클이 명시되었는가?
- [ ] 테스트 전략이 단위/통합/E2E로 구분되었는가?

### 구현 중 검증
- [ ] 테스트를 먼저 작성했는가? (Red)
- [ ] 최소 구현으로 통과했는가? (Green)
- [ ] 리팩토링 후에도 테스트가 통과하는가? (Refactor)

### 구현 후 검증
- [ ] 모든 단위/통합 테스트 통과 (`pytest tests/unit tests/integration -q`)
- [ ] E2E 테스트 통과 (`pytest tests/e2e/ -v`)
- [ ] Coverage 80% 이상 (`pytest --cov=src --cov-fail-under=80`)

---

*Last Updated: {YYYY-MM-DD}*
*Structure: Phase-based (Plan > Phase > Step)*
*TDD: Red-Green-Refactor Enforced*
