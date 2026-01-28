# AgentHub 구현 전 종합 검토 보고서

> 17가지 고민사항에 대한 분석, 권장사항, 선택 체크리스트

**작성일:** 2026-01-28
**목적:** 구현 착수 전 불확실성 해소 및 의사결정

---

## 요약 대시보드 (ADHD-Friendly)

| 카테고리 | 필수 결정 | 자동화 가능 | 보류 가능 |
|---------|:--------:|:----------:|:--------:|
| Plan 관리 | 2 | 1 | 0 |
| 테스트 전략 | 3 | 2 | 1 |
| 문서화 | 1 | 2 | 1 |
| 에이전트 | 2 | 1 | 0 |
| **총계** | **8** | **6** | **2** |

**우선 결정 필요:** #9 (전문가 에이전트), #11 (TDD skill), #15 (트레이드오프)

---

## Part 1: Plan 및 아키텍처 관리

### Q1. Plan 결함 시 대안 처리 자동화

**문제:** 구현 중 plan 자체가 틀렸음을 발견하면 로드맵/상세계획 수정 필요

**분석:**
- 완전 자동화는 불가능 (인간 판단 필요)
- 반자동화는 가능: 변경 감지 → 문서 업데이트 유도

**권장 솔루션:**
```
Plan 변경 발생 시 워크플로우:
1. [자동] 변경 사항 감지 (git diff)
2. [자동] 영향받는 문서 목록 제시
3. [수동] 변경 승인/거부
4. [자동] 승인 시 관련 문서에 변경 이력 추가
```

**구현 방법:**
- Stop Hook에서 `docs/` 파일 변경 감지 시 알림
- `CHANGELOG.md` 또는 `docs/decisions/` 폴더에 ADR(Architecture Decision Record) 자동 생성 유도

**[ ] 선택사항:**
- [x] **A. ADR 패턴 도입** - 중요 결정마다 `docs/decisions/NNNN-title.md` 생성 (권장)
- [ ] **B. 로드맵에 변경 이력 섹션 추가** - 간단하지만 추적 어려움
- [ ] **C. 현재 유지** - 수동 관리

---

### Q4. 아키텍처 영향 수정사항 관리

**문제:** 구현 중 발견한 문제가 다음 Phase에 영향을 줄 때

**분석:**
- 헥사고날 아키텍처의 장점: 변경 영향 범위가 Adapter로 제한됨
- Domain 변경 시만 전파 영향 발생

**권장 솔루션:**
```
영향도 분류:
- Adapter 변경: 해당 Phase만 수정
- Domain 변경: 전체 로드맵 검토 필요 → ADR 작성
```

**자동화 가능 범위:**
```bash
# code-reviewer 에이전트가 Domain 변경 감지 시 경고
grep -r "^[+-].*from domain\." | grep -v test
```

---

### Q5. 대안 구현 시 문서화

**문제:** 원래 계획과 다른 방식으로 구현했을 때 기록이 안 됨

**권장 솔루션:**
- ADR(Architecture Decision Record) 패턴 도입
- 템플릿 자동 생성

**ADR 템플릿:**
```markdown
# ADR-NNNN: [제목]

## 상태
제안됨 | 승인됨 | 폐기됨 | 대체됨

## 컨텍스트
왜 이 결정이 필요한가?

## 결정
무엇을 선택했는가?

## 대안
고려했던 다른 방법들

## 결과
이 결정의 영향
```

**[ ] 선택사항:**
- [x] **A. ADR 패턴 도입** (권장)
- [ ] **B. 로드맵 내 인라인 기록**
- [ ] **C. 커밋 메시지에만 기록**

---

## Part 2: 테스트 전략

### Q2. Plan 완료 전 테스트 미실행 문제

**문제:** 테스트가 필요함에도 plan 완료 전까지 테스트하지 않음

**분석:**
- TDD 원칙: 테스트 먼저 → 구현
- 현재 `tdd-agent`는 호출해야만 동작

**권장 솔루션:**
```
Phase 시작 시:
1. 해당 Phase의 테스트 파일 구조 먼저 생성 (빈 테스트)
2. 각 기능 구현 전 테스트 작성
3. 구현 후 테스트 통과 확인
```

**자동화:**
- PreToolUse Hook에 테스트 파일 존재 여부 체크 추가 가능
- 단, 과도한 Hook은 작업 방해 → **Stop Hook에서 테스트 실행 권장**

**[ ] 선택사항:**
- [x] **A. 매 구현 후 자동 pytest 실행 (Stop Hook 추가)** (권장)
- [ ] **B. 수동 테스트 실행**
- [ ] **C. PR 시에만 CI 테스트**

---

### Q10. TDD 테스트 파일 생성 시점

**현재 계획 (roadmap.md 기준):**
```
Phase 1 시작 시:
1. tests/ 폴더 구조 생성
2. 각 Entity/Service 구현 전 해당 테스트 파일 생성
3. Red (실패 테스트) → Green (구현) → Refactor
```

**구체적 타이밍:**
```
[Phase 1.1: Domain Entities]
├── tests/unit/domain/entities/ 폴더 생성
├── test_endpoint.py 작성 (Red)
├── endpoint.py 구현 (Green)
├── 리팩토링 (Refactor)
└── 다음 Entity로 이동
```

**[ ] 확인:**
- [x] 이 워크플로우에 동의함
- [ ] 테스트 파일은 구현 직전에 생성하는 것으로 이해함

---

### Q11. 기존 TDD Skill의 "etc" 분석

**현재 `.claude/skills/tdd/SKILL.md` 분석:**

| 포함된 내용 | 설명 | AgentHub 적합성 |
|------------|------|:---------------:|
| Red-Green-Refactor | TDD 핵심 | O |
| pytest 구조 | 테스트 프레임워크 | O |
| BDD 패턴 | Given-When-Then | O |
| 커버리지 가이드 | 80% 목표 | O |
| Auto-Detection | 자동 제안 | △ |

**"etc" 해석:**
- BDD 패턴 (pytest-bdd)
- Parametrized Tests
- Mocking 패턴

**`.claude/agents/tdd-agent.md` 분석:**
- AgentHub 특화: Fake Adapter 패턴, 헥사고날 테스트 구조
- 프로젝트 맞춤형으로 이미 작성됨

**비교:**
| 항목 | `/tdd` Skill | `tdd-agent` |
|------|:------------:|:-----------:|
| 범용성 | O | X |
| 프로젝트 특화 | X | O |
| Fake Adapter | X | O |
| 헥사고날 구조 | X | O |

**[ ] 선택사항:**
- [x] **A. 둘 다 유지** - Skill은 일반 TDD, Agent는 프로젝트 특화 (권장)
- [ ] **B. Skill에 프로젝트 내용 통합** - 단일 진입점
- [ ] **C. Agent만 사용** - Skill 제거

---

### Q12. 테스트 파일 일관성 유지

**문제:** 누적된 테스트가 다음 Phase, 개발 완료 후에도 유지되는가?

**보장 방법:**
1. **CI/CD 파이프라인:** 모든 PR에서 전체 테스트 실행
2. **Stop Hook:** 코드 변경 시 관련 테스트 실행
3. **커버리지 문턱값:** 80% 미만 시 경고/차단

**권장 설정 (`.github/workflows/ci.yml`):**
```yaml
- name: Run Tests
  run: pytest tests/ --cov=src --cov-fail-under=80
```

**[ ] 선택사항:**
- [x] **A. GitHub Actions CI 설정** (권장)
- [ ] **B. 로컬 pre-commit hook만**
- [ ] **C. 수동 확인**

---

### Q13. 테스트 활용 방법 및 담당 Agent/Skill

**테스트 종류 및 담당:**

| 테스트 유형 | 실행 명령 | 담당 |
|------------|----------|------|
| Unit | `pytest tests/unit/` | `tdd-agent` |
| Integration | `pytest tests/integration/` | `tdd-agent` |
| E2E | `pytest tests/e2e/` | `code-reviewer` (검토) |
| Coverage | `pytest --cov` | Stop Hook |

**현재 담당 에이전트 충분함:**
- `tdd-agent`: 테스트 작성 및 실행
- `code-reviewer`: 테스트 품질 검토

**추가 필요 여부:**
- [x] **불필요** - 현재 에이전트로 충분 (권장)
- [ ] **test-runner skill 추가** - 테스트 실행 전용

---

## Part 3: Context 및 세션 관리

### Q3. Context Window 문제로 중단

**문제:** 토큰 제한으로 작업 중단 시 대응

**분석:**
- Claude Code는 자동 요약 기능 보유
- 긴 세션에서도 컨텍스트 유지

**완화 전략:**
1. **Phase별 세션 분리:** 각 Phase를 별도 세션으로 진행
2. **체크포인트:** Phase 완료 시 상태 문서화
3. **TODO 활용:** `TodoWrite`로 진행 상황 추적

**[ ] 권장 워크플로우:**
```
1. Phase 시작 → TodoWrite로 작업 목록 작성
2. 작업 진행 → 완료 시 TODO 업데이트
3. 세션 종료 → 미완료 항목 다음 세션에서 계속
```

---

## Part 4: 문서화

### Q7. 프로그램 작동 방식 문서화

**문제:** 구현 후 실제 작동 방식을 모르겠음

**권장 솔루션:**

1. **Quick Start Guide** (`README.md` 보강)
```markdown
## 사용 방법

### 1. 서버 실행
uvicorn src.main:app --host localhost --port 8000

### 2. Extension 설치
cd extension && npm run build
Chrome → 확장프로그램 → 압축해제된 확장 로드

### 3. 사용
Chrome에서 Extension 아이콘 클릭 → MCP 서버 등록 → 채팅
```

2. **Architecture Overview** (이미 `docs/architecture.md` 존재)

3. **Demo/Screenshot** (Phase 2.5 완료 후)

**[ ] 선택사항:**
- [x] **A. README.md에 Quick Start 보강** (권장)
- [ ] **B. 별도 USAGE.md 생성**
- [ ] **C. 동영상 데모**

---

### Q8. 폴더별 README.md

**권장 구조:**
```
src/
├── README.md          # 전체 구조 설명
├── domain/
│   └── README.md      # Domain Layer 설명
├── adapters/
│   └── README.md      # Adapter Layer 설명
└── config/
    └── README.md      # 설정 방법

extension/
└── README.md          # Extension 개발 가이드
```

**생성 시점:**
- 해당 폴더 구현 완료 시 자동 생성 유도
- `code-reviewer`가 README 부재 시 경고

**[ ] 선택사항:**
- [x] **A. 각 주요 폴더에 README 생성** (권장)
- [ ] **B. 최상위 README만 상세화**
- [ ] **C. docs/만 활용**

---

## Part 5: 에이전트 전략

### Q6. 명시된 에이전트 활용 가능성

**현재 에이전트:**
| 에이전트 | 역할 | 호출 시점 |
|---------|------|----------|
| `tdd-agent` | TDD 사이클 강제 | 테스트 작성 요청 시 |
| `security-reviewer` | 보안 검토 | 보안 코드 작성 후 |
| `code-reviewer` | 코드 품질 검토 | PR 전 |

**활용도 분석:**
- 수동 호출 필요 → 잊기 쉬움
- Hook으로 자동 호출 불가 (현재)

**권장 워크플로우:**
```
기능 구현 시:
1. tdd-agent 호출 → 테스트 작성
2. 구현 진행
3. security-reviewer 호출 (보안 관련 시)
4. code-reviewer 호출 (기능 완료 시)
```

**개선 방안:**
- Phase 완료 시 `code-reviewer` 자동 호출 규칙화
- 보안 관련 파일 (security.py, auth.py) 수정 시 `security-reviewer` 호출

**[ ] 선택사항:**
- [x] **A. 현재 수동 호출 유지** (권장 - 초기 단계)
- [ ] **B. 워크플로우 문서에 호출 시점 명시**
- [ ] **C. Phase별 자동 에이전트 호출 규칙 정의**

---

### Q9. 프로젝트 맞춤형 전문가 에이전트 구성

**현재 AgentHub 기술 스택:**
- Python (FastAPI, ADK, aiosqlite)
- TypeScript (WXT, Chrome Extension)
- MCP/A2A 프로토콜
- 헥사고날 아키텍처

**권장 전문가 에이전트:**

| 에이전트 | 전문 분야 | 생성 시점 | 우선순위 |
|---------|----------|----------|:--------:|
| `adk-specialist` | Google ADK, LiteLLM, MCP | Phase 2 | 높음 |
| `extension-specialist` | WXT, Chrome Extension, Offscreen | Phase 2.5 | 높음 |
| `hexagonal-architect` | 헥사고날 아키텍처, Port/Adapter | Phase 1 | 중간 |
| `async-expert` | asyncio, 동시성, SQLite WAL | Phase 1 | 중간 |

**자동화 방안:**
```
각 Phase 완료 시:
1. 해당 Phase에서 배운 패턴/이슈를 에이전트 문서에 추가
2. skill.md 또는 references/ 폴더 업데이트
```

**[ ] 선택사항 (복수 선택 가능):**
- [x] **A. `adk-specialist` 생성** - ADK/MCP 전문
- [x] **B. `extension-specialist` 생성** - WXT/Chrome 전문
- [x] **C. `hexagonal-architect` 생성** - 아키텍처 전문
- [ ] **D. 현재 3개 에이전트 확장** - 기존 에이전트에 내용 추가
- [ ] **E. Phase 진행하며 필요시 생성** (권장)

---

### Q14. 범용성 vs 프로젝트 특화

**원칙:**
```
Skills (범용) → 여러 프로젝트에서 재사용
Agents (특화) → 프로젝트별 맞춤 지식
```

**현재 구조:**
- `/tdd` skill: 범용 TDD
- `tdd-agent`: AgentHub 특화 TDD (Fake Adapter 등)

**권장 전략:**
1. **범용 Skill 유지:** `/tdd`, `/commit` 등
2. **프로젝트 Agent 유지:** `tdd-agent`, `security-reviewer`, `code-reviewer`
3. **Phase별 Agent 업데이트:** 배운 패턴 추가

**[ ] 선택사항:**
- [x] **A. 현재 분리 유지 (Skill=범용, Agent=특화)** (권장)
- [ ] **B. Agent에 모든 것 통합**
- [ ] **C. Skill에 프로젝트 설정 추가**

---

## Part 6: 트레이드오프 및 최종 결정

### Q15. 트레이드오프 고려

**핵심 트레이드오프:**

| 항목 | 옵션 A | 옵션 B | 권장 |
|------|--------|--------|:----:|
| 테스트 강도 | 엄격 (모든 코드) | 유연 (핵심만) | A |
| 문서화 수준 | 상세 (모든 결정) | 간결 (주요만) | B |
| 에이전트 수 | 많음 (전문화) | 적음 (범용) | B |
| Hook 강도 | 강함 (자동 차단) | 약함 (알림만) | B |
| 자동화 범위 | 최대 | 필요시만 | B |

**ADHD 고려 사항:**
- 과도한 자동화 → 인터럽트 증가 → 집중력 저하
- 너무 적은 가이드 → 방향 상실

**권장 균형점:**
```
✓ Stop Hook만 활성화 (완료 시 1회)
✓ 주요 결정만 ADR 작성
✓ 에이전트 3-5개 유지
✓ Phase 단위로 집중
```

---

## Part 7: 자동화 vs 수동 명확화

### 완전 자동화 (시스템이 자동 실행)

| 항목 | 트리거 | 실행 내용 | 설정 위치 |
|------|--------|----------|----------|
| **ruff 포맷팅** | Claude 응답 완료 (Stop) | `ruff check --fix && ruff format` | `.claude/settings.json` |
| **pytest 실행** | Claude 응답 완료 (Stop) | `pytest tests/ -q` | `.claude/settings.json` |
| **main 브랜치 보호** | Edit/Write 시도 (PreToolUse) | main 브랜치면 차단 | `.claude/settings.json` |
| **GitHub Actions** | PR 생성/푸시 | 전체 테스트 + 커버리지 | `.github/workflows/ci.yml` |

### 수동 (사용자가 직접 요청)

| 항목 | 호출 방법 | 용도 |
|------|----------|------|
| **tdd-agent** | "tdd-agent로 테스트 작성해줘" | TDD 사이클 진행 |
| **security-reviewer** | "security-reviewer로 검토해줘" | 보안 취약점 검토 |
| **code-reviewer** | "code-reviewer로 리뷰해줘" | 코드 품질 검토 |
| **ADR 작성** | "ADR 작성해줘" | 아키텍처 결정 기록 |
| **README 작성** | "README 작성해줘" | 폴더/모듈 설명 |

### 반자동 (Claude가 제안, 사용자 승인)

| 항목 | 제안 시점 | 사용자 액션 |
|------|----------|------------|
| **테스트 작성** | 기능 구현 요청 시 | "네" 또는 "아니오" |
| **에이전트 호출** | 관련 작업 완료 시 | 호출 여부 결정 |
| **문서 업데이트** | 아키텍처 변경 시 | 변경 승인/거부 |

### 자동화 흐름도

```
┌─────────────────────────────────────────────────────────────┐
│                    개발 워크플로우                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [사용자 요청] ──→ [Claude 작업] ──→ [Stop Hook 자동 실행]   │
│       │                 │                   │               │
│       │                 │          ┌────────┴────────┐      │
│       │                 │          ▼                 ▼      │
│       │                 │    ruff 포맷팅      pytest 실행   │
│       │                 │                                   │
│       │                 ▼                                   │
│       │         [Edit/Write 시도]                           │
│       │                 │                                   │
│       │                 ▼                                   │
│       │         [PreToolUse Hook]                           │
│       │                 │                                   │
│       │         main 브랜치? ──Yes──→ 차단                  │
│       │                 │                                   │
│       │                No                                   │
│       │                 ▼                                   │
│       │            [작업 진행]                              │
│       │                                                     │
│       ▼                                                     │
│  [PR 생성] ──→ [GitHub Actions 자동 실행]                   │
│                        │                                    │
│               ┌────────┴────────┐                           │
│               ▼                 ▼                           │
│         테스트 실행      커버리지 검사                       │
│               │                 │                           │
│               └────────┬────────┘                           │
│                        ▼                                    │
│                 80% 미만? ──Yes──→ PR 차단                  │
│                        │                                    │
│                       No                                    │
│                        ▼                                    │
│                   [머지 가능]                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 8: ADHD 친화적 워크플로우

### 적용 원칙

1. **단일 작업 집중**
   - 한 번에 하나의 TODO만 `in_progress`
   - Phase 내 세부 작업 5개 이하로 분할

2. **시각적 진행 표시**
   - `TodoWrite`로 진행률 가시화
   - 완료 시 즉시 체크

3. **인터럽트 최소화**
   - PreToolUse Hook 최소화 (main 브랜치 보호만)
   - Stop Hook으로 일괄 처리

4. **명확한 다음 단계**
   - 각 작업 완료 시 다음 작업 명시
   - 세션 종료 시 재개 지점 기록

### 권장 세션 구조

```
🎯 시작: TodoWrite로 오늘 목표 설정 (3개 이하)
⏱️ 작업: 25분 집중 → 5분 휴식 (뽀모도로)
📝 종료: 미완료 항목 기록, 다음 시작점 명시
```

---

## 최종 체크리스트

### 필수 결정 사항 (구현 시작 전)

**Plan 관리:**
- [ ] ADR 패턴 도입 여부 결정
- [ ] 변경 이력 관리 방식 결정

**테스트:**
- [ ] Stop Hook에 pytest 추가 여부 결정
- [ ] TDD Skill vs Agent 관계 결정
- [ ] CI/CD 설정 여부 결정

**에이전트:**
- [ ] 추가 전문가 에이전트 생성 여부 결정
- [ ] 에이전트 호출 워크플로우 확정

**문서화:**
- [ ] 폴더별 README 생성 범위 결정
- [ ] Quick Start 보강 시점 결정

### 보류 가능 사항 (Phase 진행 중 결정)

- [ ] E2E 테스트 범위 (Phase 3)
- [ ] 동영상 데모 (Phase 2.5 이후)
- [ ] 추가 Skill 생성 (필요시)

---

## 권장 즉시 실행 항목

### 1. 테스트 폴더 구조 생성
```bash
mkdir -p tests/unit/domain/entities
mkdir -p tests/unit/domain/services
mkdir -p tests/unit/fakes
mkdir -p tests/integration
mkdir -p tests/e2e
touch tests/__init__.py
touch tests/conftest.py
```

### 2. ADR 폴더 생성 (선택 시)
```bash
mkdir -p docs/decisions
echo "# Architecture Decision Records" > docs/decisions/README.md
```

### 3. Stop Hook 업데이트 (테스트 추가 선택 시)
```json
{
  "hooks": {
    "Stop": [{
      "matcher": "",
      "hooks": [
        {
          "type": "command",
          "command": "ruff check src/ --fix --quiet 2>/dev/null; ruff format src/ --quiet 2>/dev/null; pytest tests/ -q --tb=no 2>/dev/null || true; exit 0"
        }
      ]
    }]
  }
}
```

---

## 부록: 용어 정리

| 용어 | 설명 |
|------|------|
| ADR | Architecture Decision Record - 아키텍처 결정 기록 |
| TDD | Test-Driven Development - 테스트 주도 개발 |
| BDD | Behavior-Driven Development - 행동 주도 개발 |
| Fake Adapter | 테스트용 가짜 어댑터 구현체 |
| Hook | Claude Code 이벤트 발생 시 실행되는 명령 |

---

*이 문서는 구현 시작 전 검토용이며, 선택 사항 결정 후 업데이트됩니다.*
