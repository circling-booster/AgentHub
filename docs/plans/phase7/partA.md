# Phase 7 Part A: Extension UX Polish (Steps 1-4)

> **상태:** 📋 Planned
> **선행 조건:** Phase 6 Complete (Phase 6A Step 3 for Cost UI)
> **목표:** Markdown 렌더링 개선, 설정 Export/Import, 대화 관리 UI, Cost Dashboard
> **예상 테스트:** ~13 신규
> **실행 순서:** Step 1 + Step 2 + Step 3 (병렬) → Step 4
> **병렬:** Part B, Part D와 병렬 가능

---

## 🎯 Progress Checklist

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **1** | Markdown Preview Enhancement | ⬜ |
| **2** | Export/Import Configuration | ⬜ |
| **3** | Conversation Management UI | ⬜ |
| **4** | Cost/Budget Dashboard UI | ⬜ |

---

## Step 1: Markdown Preview Enhancement

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `extension/components/MarkdownRenderer.tsx` | NEW | 통합 Markdown 렌더러 |
| `extension/components/MarkdownRenderer.test.tsx` | NEW | 렌더러 테스트 |
| `extension/entrypoints/sidepanel/App.tsx` | MODIFY | 기존 렌더링을 MarkdownRenderer로 교체 |

**라이브러리:** `react-markdown` + `remark-gfm` + `rehype-highlight`


**TDD(SKILLS 호출) 순서(순수 UI 를 제외):** 
1.  **Immutable Tests**: Never modify a failing test to make it pass. You must fix the implementation. Updating tests is allowed ONLY when requirements explicitly change.
2.  **Strict Red-Green-Refactor**: Follow the cycle rigorously. During the 'Refactor' phase, improve structure only—never alter behavior.
3.  **Boundary Mocking Only**: Mock only external boundaries (DB, HTTP, Time, Random). NEVER mock core domain logic or algorithms.


**지원 범위:**
- GFM 테이블, 체크리스트
- 코드 블록 신택스 하이라이팅 (기존 개선)
- 이미지 렌더링
- 링크 (새 탭 열기)
- LaTeX/수식 (선택적)

**DoD:**
- [ ] 테이블, 코드 블록, 이미지 정상 렌더링
- [ ] Vitest 3+ 테스트

---

## Step 2: Export/Import Configuration

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/inbound/http/routes/config.py` | NEW | Config Export/Import API |
| `extension/components/ConfigExport.tsx` | NEW | Export/Import UI |
| `tests/integration/adapters/test_config_export.py` | NEW | Config API 테스트 |

**API:**
- `GET /api/config/export` - 모든 엔드포인트 + 설정 JSON 내보내기
- `POST /api/config/import` - JSON 설정 가져오기

**Export 내용:**
```json
{
  "version": "1.0",
  "endpoints": [...],
  "plugins": [...],
  "settings": { "llm": {...}, "gateway": {...} }
}
```
**TDD(SKILLS 호출) 순서(순수 UI 를 제외):**
1.  **Immutable Tests**: Never modify a failing test to make it pass. You must fix the implementation. Updating tests is allowed ONLY when requirements explicitly change.
2.  **Strict Red-Green-Refactor**: Follow the cycle rigorously. During the 'Refactor' phase, improve structure only—never alter behavior.
3.  **Boundary Mocking Only**: Mock only external boundaries (DB, HTTP, Time, Random). NEVER mock core domain logic or algorithms.


**DoD:**
- [ ] Export: 현재 설정을 JSON으로 다운로드
- [ ] Import: JSON 업로드로 설정 복원
- [ ] 4+ 테스트

---

## Step 3: Conversation Management UI

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `extension/components/ConversationList.tsx` | NEW | 대화 목록 |
| `extension/components/ConversationItem.tsx` | NEW | 대화 항목 |
| `extension/hooks/useConversations.ts` | NEW | Conversations API 훅 |

**기능:** New Chat, 이전 대화 로딩, 대화 삭제
**기존 API 활용:** `GET /api/conversations`, `POST /api/conversations`

**DoD:**
- [ ] 대화 목록 표시, 새 대화 생성, 기존 대화 로딩, 삭제
- [ ] Vitest 3+ 테스트

---

## Step 4: Cost/Budget Dashboard UI

**의존성:** Phase 6 Part A Step 3 (Cost Tracking API)

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `extension/components/UsageDashboard.tsx` | NEW | 사용량 차트 |
| `extension/components/BudgetAlert.tsx` | NEW | 예산 알림 |
| `extension/hooks/useUsage.ts` | NEW | Usage API 훅 |

**기능:** 모델별 비용 차트, 월별 추이, 예산 설정 & 잔여 표시

**TDD(SKILLS 호출) 순서(순수 UI 를 제외):**
1.  **Immutable Tests**: Never modify a failing test to make it pass. You must fix the implementation. Updating tests is allowed ONLY when requirements explicitly change.
2.  **Strict Red-Green-Refactor**: Follow the cycle rigorously. During the 'Refactor' phase, improve structure only—never alter behavior.
3.  **Boundary Mocking Only**: Mock only external boundaries (DB, HTTP, Time, Random). NEVER mock core domain logic or algorithms.


**DoD:**
- [ ] 모델별/기간별 사용량 차트
- [ ] 예산 알림 표시
- [ ] Vitest 3+ 테스트

---

## Part A Definition of Done

### 기능
- [ ] Markdown 테이블/이미지/코드 정상 렌더링
- [ ] 설정 Export/Import JSON
- [ ] 대화 목록/히스토리 관리
- [ ] Cost Dashboard 차트

### 품질
- [ ] 13+ 테스트 추가
- [ ] Extension tests 통과

---

*Part A 계획 작성일: 2026-01-31*
