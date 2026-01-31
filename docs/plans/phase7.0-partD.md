# Phase 7 Part D: i18n (Steps 13-14)

> **상태:** 📋 Planned
> **선행 조건:** 없음 (독립 실행 가능)
> **목표:** Backend + Extension 다국어 지원 (Korean + English)
> **예상 테스트:** ~6 신규
> **실행 순서:** Step 13 → Step 14
> **병렬:** Part A, Part B와 병렬 가능

---

## 🎯 Progress Checklist

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **13** | Backend i18n | ⬜ |
| **14** | Extension i18n | ⬜ |

---

## Step 13: Backend i18n

**목표:** 에러 메시지, API 응답 메시지를 다국어로 제공

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/i18n/__init__.py` | NEW | get_message(code, lang) 함수 |
| `src/domain/i18n/messages.py` | NEW | 번역 리소스 (순수 Python dict) |
| `src/domain/exceptions.py` | MODIFY | get_localized_message() 메서드 추가 |
| `src/config/settings.py` | MODIFY | default_language 설정 |
| `tests/unit/domain/test_i18n.py` | NEW | i18n 테스트 |

**핵심 설계:**
```python
# src/domain/i18n/messages.py
MESSAGES = {
    "EndpointConnectionError": {
        "ko": "엔드포인트 연결에 실패했습니다: {detail}",
        "en": "Failed to connect to endpoint: {detail}",
    },
    "LlmRateLimitError": {
        "ko": "LLM API 호출 한도를 초과했습니다. 잠시 후 다시 시도해 주세요.",
        "en": "LLM API rate limit exceeded. Please try again later.",
    },
    # ...
}

# src/domain/i18n/__init__.py
def get_message(code: str, lang: str = "ko", **kwargs) -> str:
    msg = MESSAGES.get(code, {}).get(lang, code)
    return msg.format(**kwargs) if kwargs else msg
```

**지원 언어:** Korean (ko, 기본값) + English (en)
**적용 범위:** 에러 메시지, API 응답 상태 텍스트

**DoD:**
- [ ] 에러 메시지 한/영 제공
- [ ] default_language 설정 동작
- [ ] 3+ 테스트

---

## Step 14: Extension i18n

**목표:** Extension UI 전체 다국어 지원

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `extension/locales/ko.json` | NEW | 한국어 번역 |
| `extension/locales/en.json` | NEW | 영어 번역 |
| `extension/lib/i18n.ts` | NEW | i18next 초기화 |
| `extension/hooks/useLanguage.ts` | NEW | 언어 설정 관리 훅 |
| `extension/entrypoints/sidepanel/App.tsx` | MODIFY | 모든 문자열을 t() 함수로 교체 |
| `extension/components/*.tsx` | MODIFY | 하드코딩 문자열을 i18n key로 교체 |

**라이브러리:** `react-i18next` + `i18next`
**언어 저장:** `chrome.storage.local`

**번역 범위:**
- 탭 이름 (Chat, MCP Servers, A2A Agents, Plugins)
- 버튼 (Send, Register, Remove, Cancel, Export, Import)
- 상태 메시지 (Connected, Error, Loading)
- 에러 메시지 (타임아웃, 인증 실패 등)
- 플레이스홀더 (Type a message..., Enter URL...)

**핵심 설계:**
```typescript
// extension/lib/i18n.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

i18n.use(initReactI18next).init({
  resources: {
    ko: { translation: require('../locales/ko.json') },
    en: { translation: require('../locales/en.json') },
  },
  lng: 'ko',
  fallbackLng: 'en',
});

// 사용
const { t } = useTranslation();
<button>{t('chat.send')}</button>
```

**DoD:**
- [ ] 모든 UI 문자열 i18n key로 교체
- [ ] 한/영 전환 동작
- [ ] 언어 설정 `chrome.storage.local`에 저장
- [ ] Vitest 3+ 테스트

---

## Part D Definition of Done

### 기능
- [ ] Backend: 에러/상태 메시지 한/영 제공
- [ ] Extension: 전체 UI 한/영 전환

### 품질
- [ ] 6+ 테스트 추가
- [ ] 기존 테스트 regression 없음

---

## 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|--------|:------:|------|
| 번역 누락 | 🟢 | fallbackLng로 영어 기본 표시 |
| react-i18next 번들 크기 | 🟢 | lazy loading |
| 컴포넌트 수 많아 교체 범위 큼 | 🟡 | 점진적 적용 (핵심 UI → 나머지) |

---

*Part D 계획 작성일: 2026-01-31*
