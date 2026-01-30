# AgentHub Documentation

> 📚 프로젝트 문서 네비게이션 허브

**⚡ Quick Start:** [STATUS.md](STATUS.md) → [roadmap.md](roadmap.md) → [guides/](guides/)

---

## 📊 현황 & 계획

| 문서 | 설명 | 업데이트 빈도 |
|------|------|--------------|
| **[STATUS.md](STATUS.md)** | 📊 프로젝트 현황 대시보드 (Phase 진행률, 테스트 커버리지, Next Actions) | 높음 (매 Phase) |
| **[roadmap.md](roadmap.md)** | 🗺️ 전체 Phase 로드맵 및 개요 | 중간 (Phase 추가 시) |

---

## 📖 개발 가이드 (자주 참조)

| 가이드 | 설명 | 대상 |
|--------|------|------|
| [guides/architecture.md](guides/architecture.md) | 헥사고날 아키텍처 설계 | 모든 개발자 |
| [guides/implementation-guide.md](guides/implementation-guide.md) | 구현 패턴 및 코드 예시 | Backend 개발자 |
| [guides/extension-guide.md](guides/extension-guide.md) | Chrome Extension 개발 가이드 | Frontend 개발자 |
| [guides/skill-agent-guide.md](guides/skill-agent-guide.md) | Phase별 Skill/Agent 활용 전략 | Claude Code 사용자 |
| [guides/standards-verification.md](guides/standards-verification.md) | MCP/A2A/ADK 표준 검증 프로토콜 | 모든 개발자 |

**→ [View all guides](guides/)**

---

## 📋 Phase별 상세 계획

| Phase | 문서 | 상태 |
|-------|------|:----:|
| Phase 1.0 | [plans/phase1.0.md](plans/phase1.0.md) | ✅ Complete |
| Phase 1.5 | [plans/phase1.5.md](plans/phase1.5.md) | ✅ Complete |
| Phase 2.0 | [plans/phase2.0.md](plans/phase2.0.md) | ✅ Complete |
| Phase 2.5 | [plans/phase2.5.md](plans/phase2.5.md) | 🚧 In Progress |
| Phase 3.0 | [plans/phase3.0.md](plans/phase3.0.md) | 📋 Planned |

**→ [View all plans](plans/)**

---

## 📝 Architecture Decision Records (ADR)

| 문서 | 설명 |
|------|------|
| [decisions/0001-adopt-adr-pattern.md](decisions/0001-adopt-adr-pattern.md) | ADR 패턴 채택 결정 |
| [decisions/2026-01-28-claude-md-automation-workflow.md](decisions/2026-01-28-claude-md-automation-workflow.md) | CLAUDE.md 자동화 워크플로우 |

**→ [View all ADRs](decisions/)**

---

## 📦 Archive (완료된 문서)

| 문서 | 설명 |
|------|------|
| [archive/feasibility-analysis-2026-01.md](archive/feasibility-analysis-2026-01.md) | 초기 기술 스택 분석 |
| [archive/pre-implementation-review.md](archive/pre-implementation-review.md) | 구현 전 리뷰 |
| [archive/risk-assessment.md](archive/risk-assessment.md) | 리스크 평가 및 완화 전략 |

**→ [View archive](archive/)**

---

## 🧭 상황별 네비게이션

### 신규 개발자 온보딩

1. **[STATUS.md](STATUS.md)** - 현재 프로젝트 상태 파악
2. **[guides/architecture.md](guides/architecture.md)** - 아키텍처 이해
3. **[guides/implementation-guide.md](guides/implementation-guide.md)** - 구현 패턴 학습
4. **현재 Phase 플랜** - [plans/phase2.5.md](plans/phase2.5.md)

### Phase 완료 후

1. **[STATUS.md](STATUS.md)** - 현재 Phase DoD 체크
2. **다음 Phase 플랜** 확인
3. **[roadmap.md](roadmap.md)** - 다음 Phase 목표 파악

### 기술 검증 필요 시

1. **[guides/standards-verification.md](guides/standards-verification.md)** - MCP/A2A/ADK 최신 스펙 확인
2. **[guides/skill-agent-guide.md](guides/skill-agent-guide.md)** - Skill/Agent 활용 전략

---

## 📌 문서 작성 및 업데이트 규칙

### Phase 완료 시 업데이트

**→ [CONTRIBUTING.md](CONTRIBUTING.md) - Phase 완료 시 문서 업데이트 체크리스트**

**필수 업데이트 파일:**
1. `STATUS.md` - Current Phase, DoD Progress, Next Actions
2. `README.md` - Development Status 섹션

### 문서 작성 규칙

- **현황 정보**: STATUS.md에 집중
- **Phase 계획**: plans/ 폴더에 phase*.md 형식
- **아키텍처 결정**: decisions/ 폴더에 ADR 형식
- **개발 가이드**: guides/ 폴더에 주제별 분류

---

*문서 구조 업데이트: 2026-01-30*
