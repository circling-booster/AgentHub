# Archive

완료된 Phase 문서, 폐기된 접근법, 과거 분석 보고서를 보관하는 아카이브입니다.

---

## Archived Documents

### Completed Phases

| Document | Description | Archived Date |
|----------|-------------|---------------|
| phase1.0.md | 핵심 도메인 모델 설계 | 2026-01 |
| phase1.5.md | 기초 인프라 구현 | 2026-01 |
| phase2.0.md | MCP 통합 | 2026-01 |
| phase2.5.md | Chrome Extension | 2026-01 |
| phase3.0.md | A2A 통합 | 2026-01 |
| phase4.0.md | Production Features | 2026-02 |
| phase5.0.md | Security & Reliability | 2026-02 |

### Deprecated Approaches

| Document | Why Deprecated |
|----------|----------------|
| feasibility-analysis-2026-01.md | 초기 접근법, 현재 ADK 기반으로 변경 |
| LLM TestFailuresFixPlan.md | 일회성 수정 계획, 완료됨 |

### Reports

| Document | Description |
|----------|-------------|
| comprehensive-evaluation-2026-01-29.md | 프로젝트 종합 평가 |
| claude-code-optimization.md | Claude Code 최적화 분석 |
| security-report-2026-01-29.md | 보안 점검 보고서 |

---

## Why Archive?

### 아카이브 대상

1. **완료된 Phase 계획**: 구현이 끝나고 다음 Phase로 넘어간 문서
2. **폐기된 접근법**: 채택되지 않았거나 대체된 설계
3. **일회성 보고서**: 특정 시점 분석/평가 문서
4. **레거시 가이드**: 현재 구조와 맞지 않는 과거 문서

### 아카이브 기준

- **6개월 이상** 업데이트 없음
- **현재 코드베이스**와 불일치
- **후속 Phase**에서 대체됨

### 아카이브 방법

```bash
# 1. 문서를 archive/ 폴더로 이동
mv docs/plans/phase1.0.md docs/project/archive/

# 2. 이 README의 테이블에 추가

# 3. 원본 위치에서 링크 제거 또는 아카이브 링크로 변경
```

---

## Browsing Tips

- Git history를 통해 아카이브 시점 확인 가능
- 특정 시점의 문서가 필요하면 `git show` 사용

```bash
# 특정 커밋 시점의 문서 보기
git show <commit-hash>:docs/plans/phase1.0.md
```

---

*Last Updated: 2026-02-05*
