# Planning

프로젝트 계획 및 로드맵 문서입니다.

---

## 📁 Directory Structure

```
planning/
├─ active/                      # 진행 중인 Plan
│  └─ NN_descriptive_name/      # Plan 폴더 (예: 07_hybrid_dual)
│     ├─ README.md              # Plan 개요 + Phase 목록
│     ├─ 01_phase_name.md       # Phase 1 (Steps 1.1, 1.2, ...)
│     ├─ 02_phase_name.md       # Phase 2
│     └─ ...
│
├─ completed/                   # 완료된 Plan
│  └─ NN_descriptive_name/
│     └─ (active와 동일한 구조)
│
└─ planned/                     # 예정된 Plan
   └─ (미래 계획)
```

---

## 📐 Planning Structure (표준)

### 계층 구조

```
Plan > Phase > Step
```

**예시:**
```
07_hybrid_dual (Plan)
├─ Phase 1: Domain Entities
│  ├─ Step 1.1: 새 엔티티 생성
│  ├─ Step 1.2: Enums 추가
│  └─ Step 1.3: Exceptions 추가
├─ Phase 2: Port Interface
│  ├─ Step 2.1: McpClientPort 생성
│  └─ Step 2.2: FakeMcpClient 구현
└─ ...
```

### 네이밍 규칙

| 레벨 | 형식 | 예시 |
|------|------|------|
| **Plan 폴더** | `NN_descriptive_name` | `07_hybrid_dual`, `08_oauth_integration` |
| **Phase 파일** | `NN_phase_name.md` | `01_domain_entities.md`, `02_port_interface.md` |
| **Step 번호** | `N.1`, `N.2`, ... | Step 1.1, Step 1.2, Step 2.1, ... |

---

## 🎯 Planning Principles

### 1. Phase는 아키텍처 레이어와 정렬

헥사고날 아키텍처를 따라 Phase를 구성합니다:

```
Phase 1: Domain Entities      (순수 Python)
Phase 2: Port Interface        (추상화 계층)
Phase 3: Domain Services       (비즈니스 로직)
Phase 4: Adapter               (외부 시스템)
Phase 5: Integration           (DI + 통합)
Phase 6: HTTP Routes           (Inbound Adapter)
Phase 7: UI                    (Extension)
```

### 2. Phase별 독립 파일

- **1 Phase = 1 File** (파일 크기 최적화)
- 각 Phase는 독립적인 TDD 사이클
- Git Diff 명확성 확보

### 3. Step은 구현 단위

- Phase 내부의 세부 작업
- TDD Red-Green-Refactor 단위
- 번호: `N.1`, `N.2`, `N.3` (Phase별로 독립)

---

## 📊 Plan Status

| Status | Description |
|--------|-------------|
| **active** | 현재 진행 중인 Plan (1개만) |
| **completed** | 완료된 Plan (보관) |
| **planned** | 예정된 Plan (백로그) |

---

## 🔄 Phase Lifecycle

```
planned/ → active/ → completed/
```

**Phase 완료 시:**
1. `active/NN_plan/` → `completed/NN_plan/` 이동
2. `completed/README.md` 테이블에 완료 Plan 추가
3. `active/README.md` 다음 Plan 정보로 업데이트
4. Git 커밋: `docs: complete plan NN`

---

## 📚 Historical Note

### 기존 구조 (Phase 1-6)

Phase 1-6는 **Part 기반 구조**로 작성되었습니다:
```
NN_phaseN/
├─ phaseN.0.md          # Phase 개요
├─ partA.md             # Part A (Steps 1-4)
├─ partB.md             # Part B (Steps 5-7)
└─ ...

계층: Phase > Part > Step
```

### 현재 구조 (Phase 7+)

Phase 7부터는 **Phase 기반 구조**로 전환했습니다:
```
NN_descriptive_name/
├─ README.md                    # Plan 개요
├─ 01_phase_name.md            # Phase 1 (Steps 1.1, 1.2, ...)
├─ 02_phase_name.md            # Phase 2
└─ ...

계층: Plan > Phase > Step
```

**전환 이유:**
- 헥사고날 아키텍처 레이어와 명확한 정렬
- TDD 사이클 명확화
- 파일 크기 최적화 (Part: 580줄 → Phase: 277줄)
- AI 토큰 효율성 (필요한 Phase만 읽기)
- 확장성 및 유지보수성 향상

---

## 🔗 Related Documents

- [Project Management](../README.md) - 프로젝트 거버넌스
- [Architecture Decisions](../decisions/) - ADR 기록
- [Documentation Map](../../MAP.md) - 전체 문서 구조

---

*Last Updated: 2026-02-05*
*Structure Version: 2.0 (Phase-based)*
