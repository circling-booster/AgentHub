# 플랜 검증 보고서: Phase 6 Part B - MCP Resources, Prompts, Apps

**검증 대상:** `docs/plans/phase6/partB.md`
**플랜 타입:** Part Plan (Part B)
**검증 일시:** 2026-02-02
**검증 기준:** AgentHub CLAUDE.md, roadmap.md, STATUS.md, 기존 플랜 문서
**보고서 저장 위치:** `docs/validations/phase6-partB-validation-20260202.md`

---

## 1. 요약 (Executive Summary)

**검증 결과:** PASS WITH CONCERNS

Phase 6 Part B 플랜은 MCP Resources, Prompts, Apps 기능을 구현하기 위한 명확한 계획을 제시하고 있으며, 헥사고날 아키텍처 원칙을 준수하고 있습니다. 그러나 다음 우려사항이 존재합니다:

1. **MCP Apps 표준 검증 미비**: Step 8의 웹 검색 요구사항이 있으나, 외부 엔드포인트가 실제로 MCP Apps를 지원하는지 사전 검증이 필요합니다.
2. **하이브리드 아키텍처 복잡도**: ADK MCPToolset + MCP Python SDK 동시 사용으로 인한 관리 복잡도가 증가할 수 있습니다.
3. **테스트 전략 미흡**: TDD 순서가 일부 Step에만 명시되어 있으며, Extension UI 테스트 전략이 누락되었습니다.
4. **DoD 구체성 부족**: "Extension UI" 관련 DoD가 추상적이며, 구체적인 검증 기준이 필요합니다.

## 2. 아키텍처 정합성

| 항목 | 상태 | 비고 |
|------|:----:|------|
| Domain Layer 순수성 | ✅ | Resource, PromptTemplate 엔티티가 순수 Python으로 설계됨 |
| Port 인터페이스 정의 | ✅ | McpClientPort 인터페이스가 명확히 정의됨 |
| Adapter 격리 | ✅ | MCP Python SDK 구현체가 McpClientAdapter로 격리됨 |
| DI Container 반영 | ⚠️ | DI Container 통합 계획이 명시되지 않음 |
| 헥사고날 의존성 방향 | ✅ | Domain → Adapter 방향 유지 |

**상세 분석:**

**긍정적 요소:**
- Resource, PromptTemplate 엔티티가 순수 Python으로 설계되어 Domain Layer 순수성 유지
- McpClientPort 인터페이스로 MCP Python SDK 추상화
- Fake Adapter 계획으로 테스트 가능성 확보

**우려사항:**
- **DI Container 통합**: `src/config/container.py`에 McpClientPort 및 McpClientAdapter 주입 계획이 누락됨
- **하이브리드 아키텍처 복잡도**: ADK MCPToolset(Tools) + MCP Python SDK(Resources/Prompts) 동시 사용으로 인한 복잡도 증가 가능성

**권장사항:**
- Step 5에서 DI Container 통합 계획 추가 필요 (`container.py` 수정 파일 목록에 포함)
- 하이브리드 아키텍처 설계 결정에 대한 ADR 작성 고려 (ADR-011 또는 ADR-012)

---

## 3. 기존 플랜 양식 비교

### 3.1 Master Plan 정합성 (Part Plan인 경우만 해당)

| 검증 항목 | 상태 | 비고 |
|-----------|:----:|------|
| Master Plan에 명시된 목표와 일치 | ✅ | "MCP Resources, Prompts, Apps" 목표 일치 |
| Master Plan의 Part 설명과 일치 | ✅ | Steps 5-8이 Master Plan과 일치 |
| Master Plan의 우선순위 반영 | ✅ | Priority P3 (낮음) 반영 |
| Steps 범위가 Master Plan과 일치 | ✅ | Steps 5-8 범위 일치 |

**Master Plan과의 불일치:**
- 발견되지 않음. Master Plan (`phase6.0.md`)의 Part B 설명과 정확히 일치합니다.

### 3.2 기존 Part Plan 양식 비교

**비교 대상:** Phase 5 Part A, Phase 6 Part A

| 비교 항목 | 기존 플랜 (Phase 5 Part A) | 현재 플랜 (Phase 6 Part B) | 차이점 |
|-----------|---------------------------|--------------------------|--------|
| Progress Checklist | ✅ 포함 | ✅ 포함 | 동일 |
| Prerequisites | ✅ 포함 (선행 조건, Step별 검증 게이트) | ⬜ **누락** | **불일치** |
| Step별 DoD | ✅ 포함 | ✅ 포함 | 동일 |
| TDD 순서 명시 | ✅ 포함 (모든 Step) | ⚠️ **부분 포함** (Step 5만) | **불일치** |
| Skill/Agent 활용 계획 | ✅ 포함 | ⬜ **누락** | **불일치** |
| 커밋 정책 | ✅ 포함 | ⬜ **누락** | **불일치** |
| Deferred Features | ✅ 포함 | ⬜ 누락 | 일부 플랜에만 존재 |
| 리스크 및 대응 | ✅ 포함 | ✅ 포함 | 동일 |
| Part Definition of Done | ✅ 포함 | ✅ 포함 | 동일 |

**누락된 섹션 상세:**

1. **Prerequisites 섹션 누락**: Phase 5 Part A에는 "선행 조건" 및 "Step별 검증 게이트"가 명시되어 있으나, Part B에는 없음
2. **TDD 순서 미흡**: Step 5에만 TDD 순서가 명시되어 있고, Steps 6-8은 누락됨
3. **Skill/Agent 활용 계획 누락**: Phase 5 Part A에는 시점별 Skill/Agent 호출 계획이 표 형식으로 제시되어 있으나, Part B에는 없음
4. **커밋 정책 누락**: Part A에는 커밋 메시지 형식 및 예시가 제공되나, Part B에는 없음

**양식 일관성을 위한 개선 필요:**
- Prerequisites 섹션 추가 (선행 조건, Step별 검증 게이트)
- Steps 6-8에도 TDD 순서 명시
- Skill/Agent 활용 계획 표 추가
- 커밋 정책 섹션 추가

---

## 4. 완전성 검증

### 충족된 항목 ✅

- **도메인 엔티티 정의**: Resource, PromptTemplate 엔티티 명시
- **Port 인터페이스**: McpClientPort 인터페이스 정의
- **Adapter 구현**: McpClientAdapter (MCP Python SDK 기반)
- **Fake Adapter**: `tests/unit/fakes/fake_mcp_client.py` 계획
- **API 엔드포인트**: Resources, Prompts API 명시
- **Extension UI**: ResourceList, PromptSelector 컴포넌트 계획
- **웹 검색 요구사항**: Step 8에 MCP Apps 스펙 검증 명시
- **리스크 분석**: 하이브리드 아키텍처, MCP Apps 스펙 미표준화 리스크 인식

### 누락/부족한 항목 ⚠️

1. **TDD 테스트 전략 미흡**:
   - Step 5에만 TDD 순서 명시, Steps 6-8 누락
   - Extension UI 컴포넌트 테스트 전략 부재 (ResourceList, PromptSelector)
   - Integration 테스트 시나리오 구체성 부족

2. **DI Container 통합 계획 누락**:
   - McpClientPort, McpClientAdapter를 `container.py`에 주입하는 계획 미명시
   - OrchestratorService 또는 RegistryService에서 McpClientPort 사용 방법 미정의

3. **Extension UI 검증 기준 모호**:
   - "Extension에서 MCP 서버별 리소스 표시" (Step 6 DoD)가 추상적
   - "Extension에서 프롬프트 선택 및 실행 UI" (Step 7 DoD)가 구체적 검증 기준 부족

4. **MCP Apps 외부 엔드포인트 사전 검증 부재**:
   - Step 8에서 웹 검색 요구사항이 있으나, 구현 전 사전 검증이 필요
   - 외부 엔드포인트 `remote-mcp-server-authless.idosalomon.workers.dev`가 실제로 MCP Apps를 지원하는지 확인 필요

5. **Prerequisites 섹션 누락**:
   - Phase 5 Part A와 달리 선행 조건, Step별 검증 게이트 부재

6. **Skill/Agent 활용 계획 누락**:
   - 웹 검색, TDD Skill 호출 시점이 명시되지 않음

7. **커밋 정책 누락**:
   - 브랜치 전략, 커밋 메시지 형식 부재

---

## 5. 모호성 및 위험 요소

| # | 위험 요소 | 심각도 | 설명 | 권장 조치 |
|---|----------|:------:|------|----------|
| 1 | **MCP Apps 스펙 비표준화** | 🔴 높음 | Step 8에서 MCP Apps 메타데이터 표시를 계획하고 있으나, 공식 MCP 스펙에 포함되었는지 불명확. `_meta.ui.resourceUri` 필드가 표준인지 검증 필요. | **구현 전 필수 웹 검색**: MCP Specification 최신 버전 확인, MCP Apps 스펙 표준화 여부 검증. Step 8 DoD에 "웹 검색으로 MCP Apps 스펙 검증 완료" 체크박스 추가 필요. |
| 2 | **외부 테스트 엔드포인트 미지원 가능성** | 🟡 중간 | `remote-mcp-server-authless.idosalomon.workers.dev` 서버가 MCP Apps를 실제로 지원하는지 사전 검증 필요. 지원하지 않을 경우 Step 8 구현 불가. | **구현 전 필수 웹 검색**: 외부 엔드포인트의 MCP Apps 지원 여부 확인. 대체 테스트 엔드포인트 탐색 필요. |
| 3 | **하이브리드 아키텍처 복잡도** | 🟡 중간 | ADK MCPToolset(Tools) + MCP Python SDK(Resources/Prompts) 동시 사용으로 관리 복잡도 증가. 두 구현체의 연결 관리, 에러 처리, 버전 관리가 복잡해질 수 있음. | Port 인터페이스로 명확히 분리하고, 통합 테스트로 상호작용 검증. ADR 작성으로 설계 결정 문서화 권장. |
| 4 | **MCP Python SDK API 변경** | 🟡 중간 | MCP Python SDK (`mcp` 패키지)가 빠르게 진화 중. `ClientSession`, `list_resources()`, `get_prompt()` 등의 API가 변경될 수 있음. | **구현 전 필수 웹 검색**: MCP Python SDK 최신 API 확인. 버전 고정 (`requirements.txt`에 명시). |
| 5 | **Extension UI 테스트 전략 부재** | 🟠 중상 | ResourceList, PromptSelector 컴포넌트의 Vitest 테스트 전략이 명시되지 않음. UI 동작 검증 기준이 모호함. | Steps 6-7에 Extension UI 테스트 시나리오 추가 (예: "리소스 목록 렌더링 테스트", "프롬프트 변수 바인딩 UI 테스트"). |
| 6 | **DI Container 통합 미정의** | 🟠 중상 | McpClientPort를 어떤 Service에서 사용할지, DI Container에 어떻게 주입할지 불명확. | Step 5에 `container.py` 수정 계획 추가. RegistryService 또는 별도 McpService 생성 고려. |
| 7 | **DoD 구체성 부족** | 🟡 중간 | "Extension에서 리소스 표시", "프롬프트 실행 UI" 등의 DoD가 추상적. 구체적인 검증 기준(예: "리소스 URI 클릭 시 내용 표시", "프롬프트 변수 입력 폼 렌더링") 필요. | DoD를 구체화하여 검증 가능한 기준 명시. |

---

## 6. 프로젝트 방향성 일치도

| 문서 | 일치 여부 | 비고 |
|------|:--------:|------|
| **roadmap.md** | ✅ 일치 | Phase 6 Part B 목표와 일치 |
| **STATUS.md** | ✅ 일치 | Phase 5 Complete → Phase 6 시작 순서 준수 |
| **CLAUDE.md** | ✅ 일치 | 헥사고날 아키텍처, TDD 원칙 반영 |
| **ADR** | ⚠️ 부분 일치 | 하이브리드 아키텍처에 대한 ADR 부재 |

**상세:**

**✅ roadmap.md 일치:**
- Phase 6 Part B는 "MCP Resources, Prompts, Apps" 목표와 정확히 일치
- Priority P3 (낮음) 순서 준수

**✅ STATUS.md 일치:**
- Phase 5 Part E 완료 (2026-02-01) 후 Phase 6 시작 순서 준수
- Backend Coverage 91% 유지 목표 반영

**✅ CLAUDE.md 일치:**
- Domain Layer 순수성 준수 (Resource, PromptTemplate 순수 Python)
- TDD 원칙 반영 (Step 5에 TDD 순서 명시)
- Standards Verification Protocol 부분 준수 (Step 8에 웹 검색 요구사항)

**⚠️ ADR 부족:**
- 하이브리드 아키텍처 (ADK MCPToolset + MCP Python SDK) 설계 결정에 대한 ADR 부재
- 권장: ADR-011 "MCP Resources/Prompts 구현 전략 - Hybrid Approach" 작성 고려

---

## 7. 개선 필요 사항 (Action Items)

### 필수 (Must Fix Before Implementation)

1. **MCP Apps 표준 검증 사전 수행** (Step 8 구현 전 필수):
   - 웹 검색으로 MCP Specification 최신 버전 확인
   - MCP Apps (`_meta.ui.resourceUri`)가 공식 스펙에 포함되었는지 검증
   - 외부 테스트 엔드포인트 `remote-mcp-server-authless.idosalomon.workers.dev`의 MCP Apps 지원 여부 확인
   - 검증 결과를 플랜에 반영 또는 Step 8 조정

2. **Prerequisites 섹션 추가**:
   - 선행 조건 (Phase 5 완료, Coverage >= 90%, 브랜치 전략 등)
   - Step별 검증 게이트 표 추가 (웹 검색 시점 명시)

3. **DI Container 통합 계획 명시** (Step 5):
   - `src/config/container.py` 수정 파일 목록에 추가
   - McpClientPort, McpClientAdapter 주입 방법 명시
   - McpClientPort를 사용할 Service 정의 (RegistryService 또는 별도 McpService)

4. **TDD 순서 전체 Step 명시**:
   - Steps 6-8에도 TDD Red-Green-Refactor 순서 추가
   - Extension UI 컴포넌트 테스트 전략 포함

### 권장 (Should Fix)

5. **Skill/Agent 활용 계획 추가**:
   - 웹 검색, TDD Skill, Code Reviewer 호출 시점을 표 형식으로 추가
   - 예시: Phase 5 Part A의 "Skill/Agent 활용 계획" 섹션 참조

6. **커밋 정책 섹션 추가**:
   - 브랜치 전략 (`feature/phase-6`)
   - 커밋 메시지 형식 및 예시

7. **DoD 구체화**:
   - "Extension에서 리소스 표시" → "리소스 목록 렌더링 + URI 클릭 시 내용 표시"
   - "프롬프트 실행 UI" → "변수 입력 폼 + 렌더링 결과 표시"

8. **Extension UI 테스트 시나리오 추가**:
   - Steps 6-7 DoD에 Vitest 테스트 개수 및 시나리오 명시
   - 예: "ResourceList 렌더링 테스트 3개, PromptSelector 바인딩 테스트 4개"

### 제안 (Nice to Have)

9. **ADR 작성 고려**:
   - ADR-011: "MCP Resources/Prompts 구현 전략 - Hybrid Approach (ADK MCPToolset + MCP Python SDK)"
   - 하이브리드 아키텍처 채택 이유, 대안, 장단점 문서화

10. **예상 테스트 개수 구체화**:
    - 현재 "~17 신규"로만 명시
    - Step별 테스트 개수 분해 (예: Step 5: 6 tests, Step 6: 5 tests, Step 7: 4 tests, Step 8: 2 tests)

11. **MCP Apps 렌더링 연기 근거 명시**:
    - Step 8에서 "실제 HTML 렌더링은 포함하지 않음"이라고 명시했으나, Phase 7 이후 구현 계획 부재
    - Deferred Features 섹션에 "MCP Apps HTML Rendering" 추가 고려

---

## 8. 기타 제안

### 1. 외부 의존성 버전 고정
MCP Python SDK가 빠르게 진화 중이므로, `requirements.txt` 또는 `pyproject.toml`에 버전 고정 필요:
```toml
[tool.poetry.dependencies]
mcp = "^1.26.0"  # 버전 명시
```

### 2. Hybrid Architecture 문서화
ADK MCPToolset + MCP Python SDK 동시 사용에 대한 설계 결정을 문서화하면 향후 유지보수에 도움:
- 왜 ADK MCPToolset으로 Resources/Prompts를 구현하지 않았는지
- MCP Python SDK 채택의 장단점
- 두 구현체 간 상호작용 방법

### 3. Extension UI Mockup/Wireframe 고려
ResourceList, PromptSelector 컴포넌트의 UI/UX를 사전에 설계하면 구현 시 명확성 향상. 필수는 아니지만, 복잡한 UI일 경우 도움이 될 수 있음.

### 4. MCP Apps 표준화 진행 상황 모니터링
MCP Apps가 아직 공식 스펙에 포함되지 않았을 가능성이 있으므로, 구현 후에도 지속적으로 표준 변경 사항 모니터링 필요.

### 5. 테스트 Resources 관리
Phase 5에서 로컬 MCP 서버(Synapse)를 사용했던 것처럼, MCP Resources/Prompts 테스트를 위한 로컬 MCP 서버 업데이트 필요 여부 검토.

---

## 검증 결과: PASS WITH CONDITIONS

**조건:**
1. **Step 8 구현 전 필수 웹 검색 수행**: MCP Apps 스펙 표준화 여부 + 외부 테스트 엔드포인트 지원 확인
2. **Prerequisites 섹션 추가**: 선행 조건 및 Step별 검증 게이트 명시
3. **DI Container 통합 계획 추가**: `container.py` 수정 및 McpClientPort 주입 방법 명시
4. **TDD 순서 전체 Step 명시**: Steps 6-8에도 Red-Green-Refactor 순서 추가
5. **필수 개선사항 (1-4) 반영 후 재검토 권장**

**플랜 품질 평가:**
- **아키텍처 설계**: 우수 (헥사고날 원칙 준수, Port 인터페이스 명확)
- **TDD 전략**: 보통 (일부 Step만 명시)
- **완전성**: 보통 (DI Container, Extension 테스트 전략 미흡)
- **리스크 인식**: 우수 (주요 리스크 파악 및 대응 계획)
- **양식 일관성**: 미흡 (Prerequisites, Skill/Agent 활용, 커밋 정책 누락)

---

*검증 완료: 2026-02-02*
*검증자: Claude Sonnet 4.5 (Plan Validation Agent)*
