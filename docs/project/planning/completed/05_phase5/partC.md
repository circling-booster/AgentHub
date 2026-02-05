# Phase 5 Part C: Content Script (Steps 9-10)

> **상태:** 📋 Planned
> **선행 조건:** Phase 5 Part A Complete
> **목표:** 현재 페이지 컨텍스트를 LLM 대화에 포함시키는 Content Script + Toggle UI
> **예상 테스트:** ~8 신규 (3 Vitest + 5 pytest)
> **실행 순서:** Step 9 → Step 10
> **병렬:** Part B, Part D와 병렬 가능

---

## 🎯 Progress Checklist

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **9** | Content Script Implementation | ⬜ |
| **10** | Sidepanel Toggle + Context Injection | ⬜ |

---

## Step 9: Content Script Implementation

**목표:** 웹 페이지에서 URL, 제목, 선택 텍스트 등을 추출하는 Content Script 추가

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `extension/entrypoints/content.ts` | NEW | Content Script 엔트리포인트 (WXT) |
| `extension/lib/content-extract.ts` | NEW | 페이지 데이터 추출 로직 |
| `extension/lib/content-messaging.ts` | NEW | Content ↔ Background 메시지 프로토콜 |
| `extension/wxt.config.ts` | MODIFY | content_scripts 설정 추가 |
| `extension/entrypoints/background.ts` | MODIFY | Content Script 메시지 핸들러 추가 |
| `extension/lib/types.ts` | MODIFY | PageContext 타입 정의 |

**핵심 설계:**
```typescript
// extension/lib/types.ts
export interface PageContext {
  url: string;
  title: string;
  selectedText: string;
  metaDescription: string;
  mainContent: string;  // 간략화된 본문 (최대 2000자)
}

// extension/entrypoints/content.ts
export default defineContentScript({
  matches: ['<all_urls>'],
  runAt: 'document_idle',
  main() {
    browser.runtime.onMessage.addListener((message) => {
      if (message.type === 'GET_PAGE_CONTEXT') {
        return Promise.resolve(extractPageContext());
      }
    });
  },
});

// extension/lib/content-extract.ts
export function extractPageContext(): PageContext {
  return {
    url: window.location.href,
    title: document.title,
    selectedText: window.getSelection()?.toString() || '',
    metaDescription: document.querySelector('meta[name="description"]')?.getAttribute('content') || '',
    mainContent: extractMainContent(),  // 본문 추출 (최대 2000자)
  };
}
```

**TDD 순서:**
1. RED: `test_extract_page_context_returns_url_and_title` (Vitest)
2. RED: `test_extract_selected_text` (Vitest)
3. RED: `test_content_messaging_roundtrip` (Vitest)
4. GREEN: content.ts, content-extract.ts, content-messaging.ts 구현
5. REFACTOR

**DoD:**
- [ ] Content Script가 페이지 URL, 제목, 선택 텍스트 추출
- [ ] Background와 메시지 통신 동작
- [ ] WXT config에 content_scripts 등록

---

## Step 10: Sidepanel Toggle + Context Injection

**목표:** Sidepanel에 페이지 컨텍스트 포함 토글 추가, 활성 시 LLM 메시지에 컨텍스트 주입

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `extension/entrypoints/sidepanel/App.tsx` | MODIFY | 토글 버튼 추가 (Include page context) |
| `extension/hooks/usePageContext.ts` | NEW | 페이지 컨텍스트 상태 관리 훅 |
| `extension/lib/api.ts` | MODIFY | ChatRequest에 page_context 포함 |
| `src/adapters/inbound/http/schemas/chat.py` | MODIFY | `page_context: PageContextSchema \| None` 필드 추가 |
| `src/adapters/outbound/adk/orchestrator_adapter.py` | MODIFY | 페이지 컨텍스트를 메시지에 주입 |
| `tests/unit/adapters/test_page_context.py` | NEW | 컨텍스트 주입 테스트 |

**핵심 설계:**
```typescript
// 토글 UI
const [includePageContext, setIncludePageContext] = useState(false);

// 메시지 전송 시
async function sendMessage(text: string) {
  let pageContext = null;
  if (includePageContext) {
    pageContext = await requestPageContext();  // Content Script에서 가져오기
  }
  await api.chatStream({
    message: text,
    conversation_id: currentConversationId,
    page_context: pageContext,
  });
}
```

```python
# orchestrator_adapter.py 메시지 주입
async def process_message(self, message: str, conversation_id: str,
                          page_context: dict | None = None) -> AsyncIterator[StreamChunk]:
    if page_context:
        context_block = (
            f"[Page Context]\n"
            f"URL: {page_context['url']}\n"
            f"Title: {page_context['title']}\n"
        )
        if page_context.get('selectedText'):
            context_block += f"Selected Text: {page_context['selectedText']}\n"
        if page_context.get('mainContent'):
            context_block += f"Content: {page_context['mainContent'][:1000]}\n"
        message = f"{context_block}\n{message}"
    # ... 기존 처리 ...
```

**TDD 순서:**

0. TDD SKILL 호출 : '/tdd'
1. RED: `test_message_with_page_context_includes_url` (pytest)
2. RED: `test_message_without_page_context_unchanged` (pytest)
3. RED: `test_page_context_truncated_at_limit` (pytest)
4. RED: `test_toggle_state_persists` (Vitest)
5. RED: `test_toggle_off_excludes_context` (Vitest)
6. RED: 그외 모든 구현 내용에 대한 테스트 작성
6. GREEN: 모든 파일 수정
7. REFACTOR: 컨텍스트 포맷팅 함수 분리 포함 리펙토링

**DoD:**
- [ ] 토글 ON: 메시지에 페이지 컨텍스트 포함
- [ ] 토글 OFF: 기존과 동일하게 동작
- [ ] 컨텍스트 길이 제한 (1000자)
- [ ] Backend API에서 page_context 필드 수용
- [ ] REFACTOR 완료
---

## 커밋 정책

```
# 중간 커밋
feat(phase5): Step 9-10 - Content script implementation

# 마지막 커밋
feat(phase5): Step 10 - Page context toggle and injection
docs(phase5): Part C complete - Content Script
```

---

## Part C Definition of Done

### 기능
- [ ] Content Script: 페이지 URL, 제목, 선택 텍스트 추출
- [ ] 토글 ON 시 페이지 컨텍스트가 LLM 메시지에 포함
- [ ] 토글 OFF 시 기존과 동일

### 품질
- [ ] Vitest 3+ 테스트 추가
- [ ] pytest 5+ 테스트 추가
- [ ] 기존 테스트 regression 없음

---

## 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|--------|:------:|------|
| CSP 제약으로 Content Script 제한 | 🟡 | Background 경유 메시지 패싱 (직접 fetch 안 함) |
| 특정 사이트에서 Content Script 차단 | 🟢 | graceful fallback (컨텍스트 없이 진행) |
| 본문 추출 품질 | 🟢 | 간단한 DOM 파싱, 추후 개선 가능 |

---

*Part C 계획 작성일: 2026-01-31*
