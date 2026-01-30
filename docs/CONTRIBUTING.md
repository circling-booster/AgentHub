# Contributing to AgentHub Documentation

> Phase 완료 시 문서 업데이트 가이드

---

## 📋 Phase 완료 시 체크리스트

Phase를 완료할 때마다 다음 파일들을 업데이트해야 합니다.

### 1단계: Phase DoD 확인 ✅

**파일:** `docs/STATUS.md` (현재 Phase 섹션)

**업데이트 내용:**
```markdown
### Completed ✅
- [x] 모든 DoD 항목 체크 확인

### In Progress 🚧
- (비우기)

### Pending 📋
- (비우기)
```

**예시:**
```diff
## 🎯 Current Phase: Phase 2.5 (Chrome Extension)

**Target Completion:** 2026-01-30
- **DoD Progress:** 4/8 completed (50%)
+ **DoD Progress:** 8/8 completed (100%)

### Completed ✅
- [x] Extension 구조 설계 (WXT + Offscreen Document)
- [x] Token Handshake 클라이언트 구현
- [x] SSE 스트리밍 처리 (Offscreen)
- [x] Vitest 전체 통과 (129 tests)
+ [x] 서버 연동 수동 검증
+ [x] Sidepanel UI 실사용 테스트
+ [x] extension/README.md 최종 검토
+ [x] E2E 테스트 자동화 완료
```

---

### 2단계: Overall Progress 업데이트 📊

**파일:** `docs/STATUS.md` (Phase Progress 테이블)

**업데이트 내용:**

```diff
| Phase | Status | Progress | Key Deliverables |
|-------|:------:|:--------:|------------------|
...
- | **Phase 2.5** | **🚧 In Progress** | **95%** | **Chrome Extension (129 tests)** |
+ | Phase 2.5 | ✅ Complete | 100% | Chrome Extension (E2E 통과) |
+ | **Phase 3** | **🚧 In Progress** | **10%** | **A2A Integration** |
```

**Quick Overview 섹션도 업데이트:**

```diff
| Metric | Status |
|--------|--------|
- | **Overall Progress** | 65% (Phase 2.5/4 진행 중) |
+ | **Overall Progress** | 75% (Phase 3/4 진행 중) |
```

---

### 3단계: Current Phase 전환 🔄

**파일:** `docs/STATUS.md`

**업데이트 내용:**

1. **헤더 변경:**
```diff
> **Last Updated:** 2026-01-30
- > **Current Phase:** Phase 2.5 (Chrome Extension)
+ > **Current Phase:** Phase 3.0 (A2A Integration)
```

2. **Current Phase 섹션 교체:**
```markdown
## 🎯 Current Phase: Phase 3.0 (A2A Integration)

**Target Completion:** TBD
**DoD Progress:** 0/7 completed (0%)

### Completed ✅
(없음)

### In Progress 🚧
- [ ] A2A 스펙 최신 검증

### Pending 📋
- [ ] Agent Card 구현
- [ ] JSON-RPC 2.0 통신

**📋 Detailed Plan:** [phase3.0.md](plans/phase3.0.md)
```

3. **완료된 Phase를 Recent Milestones에 추가:**
```diff
## 📅 Recent Milestones

+ - **2026-01-30**: Phase 2.5 Complete - Chrome Extension (E2E 통과)
- **2026-01-29**: Phase 2 Complete - MCP Integration (88% coverage)
```

---

### 4단계: Next Actions 업데이트 ⚡

**파일:** `docs/STATUS.md` (Next Actions 섹션)

**업데이트 내용:**

```diff
### Phase 2.5 완료 작업
- | 🔴 High | Extension 수동 검증 (서버 연동) | 👤 수동 | Pending |

+ ### Phase 3 시작 작업
+ | Priority | Task | Type | Status |
+ |:--------:|------|:----:|:------:|
+ | 🔴 High | A2A 스펙 최신 검증 (웹 검색) | 🤖 구현 | In Progress |
+ | 🟡 Medium | Agent Card 스키마 설계 | 🤖 구현 | Pending |
```

---

### 5단계: Test Coverage 업데이트 🧪

**파일:** `docs/STATUS.md` (Test Coverage Summary 테이블)

**업데이트 내용:**

```diff
| Component | Coverage | Target | Status |
|-----------|:--------:|:------:|:------:|
| Domain Core | 90.84% | 80% | ✅ |
| Security Layer | 96% | - | ✅ |
| MCP Integration | 88% | 70% | ✅ |
| Extension (Vitest) | 129 tests | - | ✅ |
- | E2E Tests | 10 passed, 2 skipped | - | ⚠️ 수동 검증 필요 |
+ | E2E Tests | 12 passed | - | ✅ |

- **Overall Backend Coverage:** 89.55% (Target: 80%)
+ **Overall Backend Coverage:** 90.12% (Target: 80%)
```

---

### 6단계: README.md 업데이트 (루트)

**파일:** `README.md` (Development Status 섹션)

**업데이트 내용:**

```diff
## Development Status

- **Current Phase:** Phase 2.5 (Chrome Extension) - 95% Complete
+ **Current Phase:** Phase 3.0 (A2A Integration) - 10% Complete

**Quick Status:**
- ✅ Phase 0-2: Complete (Domain Core, Security, MCP Integration)
- - 🚧 Phase 2.5: In Progress (Extension 수동 검증 대기)
+ - ✅ Phase 2.5: Complete (Chrome Extension E2E 통과)
+ - 🚧 Phase 3: In Progress (A2A 스펙 검증)
- 📋 Phase 3-4: Planned (A2A Integration, Advanced Features)
+ - 📋 Phase 4: Planned (Advanced Features)
```

---

### 7단계: 폴더별 README 생성 (해당 Phase에서 요구 시)

**roadmap.md의 "Documentation Update" 섹션 참조**

예시 (Phase 1 완료 시):
- `src/README.md` 생성 (백엔드 전체 구조)
- `src/domain/README.md` 생성 (Domain Layer 설계)
- `tests/README.md` 생성 (테스트 전략)

예시 (Phase 2.5 완료 시):
- `extension/README.md` 생성 (Extension 개발 가이드)

---

## 📊 업데이트 우선순위

| 우선순위 | 파일 | 변경 빈도 | Phase 완료 시 필수 |
|:-------:|------|:--------:|:-----------------:|
| 🔴 High | `docs/STATUS.md` | 매우 높음 | ✅ 필수 |
| 🟡 Medium | `README.md` | 중간 | ✅ 필수 |
| 🟢 Low | `docs/roadmap.md` | 낮음 | ❌ 선택적 |
| 🟢 Low | Phase 플랜 문서 | 낮음 | ❌ 선택적 |

**roadmap.md는 Phase 완료 시 업데이트 불필요:**
- Phase별 DoD 목록은 Phase 시작 시 1회 작성 후 고정
- STATUS.md의 체크박스 상태만 추적

---

## 🔄 자동화 고려사항 (선택적)

### GitHub Actions로 자동 업데이트

```yaml
# .github/workflows/update-status.yml
name: Update STATUS.md

on:
  push:
    branches: [main]
    paths:
      - 'pytest.xml'
      - 'coverage.xml'

jobs:
  update-status:
    runs-on: ubuntu-latest
    steps:
      - name: Extract coverage percentage
        run: |
          # pytest-cov XML 파싱
          coverage=$(grep -oP 'line-rate="\K[0-9.]+' coverage.xml | head -1)
          echo "COVERAGE=$(echo "$coverage * 100" | bc)%" >> $GITHUB_ENV

      - name: Update STATUS.md
        run: |
          sed -i "s/Overall Backend Coverage: [0-9.]*%/Overall Backend Coverage: $COVERAGE/" docs/STATUS.md
```

---

## 🎯 Quick Reference

### Phase 완료 시 5분 체크리스트

```bash
# 1. STATUS.md 업데이트
[ ] Current Phase 진행률 100%로 변경
[ ] Phase Progress 테이블에서 상태를 ✅ Complete로 변경
[ ] Current Phase 섹션을 다음 Phase로 교체
[ ] Next Actions 업데이트
[ ] Test Coverage 수치 업데이트
[ ] Recent Milestones에 완료 기록 추가

# 2. README.md 업데이트
[ ] Development Status 섹션 업데이트

# 3. 폴더 README 생성 (해당 Phase 요구사항에 따라)
[ ] src/README.md, tests/README.md, extension/README.md 등

# 4. Git Commit
git add docs/STATUS.md README.md
git commit -m "docs: Phase X.Y complete - update STATUS.md"
```

---

## 📝 문서 작성 규칙

### STATUS.md 작성 규칙

1. **Last Updated 필수:** 매 업데이트 시 날짜 변경
2. **DoD Progress 정확히:** `X/Y completed (Z%)`
3. **Status 이모지 일관성:**
   - ✅ Complete
   - 🚧 In Progress
   - 📋 Planned
   - ⏸️ Paused
   - ❌ Blocked

### README.md 작성 규칙

1. **간결성:** Development Status는 3-5줄 이내
2. **STATUS.md 링크:** 항상 상세 링크 제공

---

*문서 생성일: 2026-01-30*
