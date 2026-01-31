# Phase 5: Advanced Features (Future)

> **상태:** 💡 초안 (Phase 4 완료 후 확정)
> **선행 조건:** Phase 4 Part A-E 완료
> **목표:** ADK 공식 지원 대기 기능 + 확장성 강화 + Multi-User Support
> **예상 기간:** Phase 4 완료 후 재평가

---

## 🎯 Progress Checklist

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **1** | MCP Advanced Features (Resources, Prompts, Sampling) | 💡 |
| **2** | Vector Search (Semantic Tool Routing) | 💡 |
| **3** | Multi-User Support + i18n | 💡 |
| **4** | Advanced Reliability | 💡 |

**범례:** ✅ 완료 | 🚧 진행중 | 📋 Planned | 💡 초안

---

## Phase 5 Prerequisites

- [ ] Phase 4 Part A-E 완료
- [ ] ADK 공식 지원 상태 확인 (Resources, Prompts, Sampling)
- [ ] Multi-User 요구사항 정의
- [ ] i18n 라이브러리 선정

**⚠️ 주의:** Phase 5는 외부 의존성(ADK 공식 지원)에 따라 변동 가능. 각 Step별 착수 전 ADK 릴리스 노트 확인 필수.

---

## Step 1: MCP Advanced Features

**전제 조건:** ADK 공식 지원 대기

### 1.1 Resources (ADK MCPResourceSet 지원 시)

**참고:** [ADK Issue #1779](https://github.com/google/adk/issues/1779) - MCP Resources 지원 요청

**목표:** MCP 서버의 리소스(파일, 문서, 컨텍스트 데이터) 읽기 및 구독 기능 제공

**신규/수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/outbound/adk/mcp_resource_adapter.py` | **NEW** | MCPResourceSet 기반 리소스 읽기 어댑터 |
| `src/domain/entities/resource.py` | **NEW** | Resource 엔티티 (uri, name, mimeType, content) |
| `src/domain/ports/outbound/resource_port.py` | **NEW** | ResourcePort 인터페이스 |
| `src/adapters/inbound/http/routes/resources.py` | **NEW** | `GET /api/resources`, `GET /api/resources/{uri}` |

**핵심 기능:**
- MCP 리소스 목록 조회
- URI 기반 리소스 읽기
- 리소스 변경 구독 (WebSocket)

**DoD:**
- [ ] MCP 서버 리소스 목록 조회 API
- [ ] 특정 리소스 읽기 API
- [ ] Extension에서 리소스 선택 UI

**의존성:** ADK MCPResourceSet API 출시 대기

---

### 1.2 Prompts (ADK MCPPromptSet 지원 시)

**참고:** [ADK Discussion #3097](https://github.com/google/adk/discussions/3097) - MCP Prompts 지원 논의

**목표:** MCP 서버 제공 프롬프트 템플릿 활용

**신규/수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/outbound/adk/mcp_prompt_adapter.py` | **NEW** | MCPPromptSet 기반 프롬프트 어댑터 |
| `src/domain/entities/prompt_template.py` | **NEW** | PromptTemplate 엔티티 |
| `src/adapters/inbound/http/routes/prompts.py` | **NEW** | `GET /api/prompts`, `POST /api/prompts/{name}/render` |

**핵심 기능:**
- MCP 프롬프트 템플릿 목록 조회
- 변수 바인딩 후 프롬프트 렌더링
- Extension에서 프롬프트 선택 및 적용

**DoD:**
- [ ] 프롬프트 템플릿 조회 API
- [ ] 프롬프트 렌더링 API
- [ ] Extension 프롬프트 선택 UI

**의존성:** ADK MCPPromptSet API 출시 대기

---

### 1.3 Sampling (ADK 지원 시)

**목표:** MCP 서버 주도 LLM 호출 (Server → Client → LLM → Server)

**신규/수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/outbound/adk/mcp_sampling_adapter.py` | **NEW** | MCP Sampling 프록시 어댑터 |
| `src/domain/services/sampling_service.py` | **NEW** | Sampling 요청 처리 서비스 |

**핵심 기능:**
- MCP 서버가 LLM 호출 요청
- AgentHub가 LLM 호출 후 결과 반환
- Sampling 권한 제어 (사용자 승인)

**DoD:**
- [ ] MCP Sampling 프록시 구현
- [ ] Extension 사용자 승인 UI

**의존성:** ADK MCP Sampling API 출시 대기

---

## Step 2: Vector Search (Semantic Tool Routing)

**전제 조건:** Phase 4 Step 11 (Defer Loading) 완료

**목표:** 도구가 50개 이상일 때 시맨틱 검색으로 최적 도구 추천

**신규/수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/outbound/embedding/openai_embedding_adapter.py` | **NEW** | OpenAI Embeddings API 호출 |
| `src/domain/services/semantic_router.py` | **NEW** | 시맨틱 도구 라우팅 서비스 |
| `src/adapters/outbound/storage/vector_storage.py` | **NEW** | 벡터 DB (ChromaDB 또는 Qdrant) |
| `src/config/settings.py` | MODIFY | `semantic_routing` 섹션 추가 (enabled, top_k, threshold) |

**핵심 설계:**
```python
# 도구 설명 임베딩 생성 및 저장
tools = await dynamic_toolset.get_tools()
for tool in tools:
    embedding = await embedding_adapter.embed(tool.description)
    await vector_storage.save(tool.name, embedding)

# 사용자 쿼리 기반 시맨틱 검색
query_embedding = await embedding_adapter.embed(user_message)
relevant_tools = await vector_storage.search(query_embedding, top_k=10)

# LLM에게 관련 도구만 제공
agent = LlmAgent(tools=relevant_tools)
```

**DoD:**
- [ ] 도구 설명 임베딩 생성 및 벡터 DB 저장
- [ ] 사용자 쿼리 기반 top-k 도구 추천
- [ ] 설정으로 시맨틱 라우팅 활성화/비활성화
- [ ] 도구 50개 이상 시 성능 벤치마크

**의존성:** 독립

**예상 작업시간:** 1주

---

## Step 3: Multi-User Support + i18n

**목표:** 단일 사용자 로컬 앱 → 다중 사용자 지원 + 다국어 UI

### 3.1 Multi-User Backend

**신규/수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/entities/user.py` | **NEW** | User 엔티티 (user_id, username, language, created_at) |
| `src/adapters/outbound/storage/sqlite_user_storage.py` | **NEW** | 사용자 프로필 CRUD |
| `src/domain/services/auth_service.py` | **NEW** | 간단한 인증 서비스 (로컬 사용자 관리) |
| `src/adapters/inbound/http/routes/users.py` | **NEW** | `GET/POST /api/users`, `GET/PUT /api/users/{id}/preferences` |
| `src/domain/entities/conversation.py` | MODIFY | `user_id` 필드 추가 |
| `src/adapters/outbound/storage/sqlite_conversation_storage.py` | MODIFY | 사용자별 대화 격리 쿼리 |

**핵심 설계:**
```python
# 사용자 프로필
class User:
    user_id: str
    username: str
    language: str = "ko"  # 기본값: 한국어
    created_at: datetime

# 대화 격리
async def get_conversations(self, user_id: str) -> list[Conversation]:
    async with conn.execute(
        "SELECT * FROM conversations WHERE user_id = ?",
        (user_id,)
    ) as cursor:
        ...
```

**DoD:**
- [ ] User 엔티티 및 SQLite 저장소
- [ ] 사용자 프로필 CRUD API
- [ ] 대화 및 엔드포인트 사용자별 격리
- [ ] Extension 로그인 UI (간단한 사용자 선택)

---

### 3.2 i18n Infrastructure

**목표:** Backend 에러 메시지 + Extension UI 다국어 지원 (한국어/영어)

**신규/수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/i18n/messages.py` | **NEW** | 에러 메시지 다국어 딕셔너리 |
| `src/domain/exceptions.py` | MODIFY | `get_localized_message(lang)` 메서드 추가 |
| `extension/locales/ko.json` | **NEW** | 한국어 리소스 파일 |
| `extension/locales/en.json` | **NEW** | 영어 리소스 파일 |
| `extension/lib/i18n.ts` | **NEW** | react-i18next 설정 |
| `extension/hooks/useChat.ts` | MODIFY | `mapErrorCodeToMessage()` → `t('errors.{code}')` 사용 |

**핵심 설계:**

**Backend:**
```python
# src/domain/i18n/messages.py
ERROR_MESSAGES = {
    "ko": {
        "LlmRateLimitError": "요청이 너무 많습니다. 잠시 후 다시 시도해주세요.",
        "LlmAuthenticationError": "API 인증 오류가 발생했습니다. 설정을 확인해주세요.",
        # ...
    },
    "en": {
        "LlmRateLimitError": "Too many requests. Please try again later.",
        "LlmAuthenticationError": "API authentication error. Please check settings.",
        # ...
    }
}

# src/domain/exceptions.py
class DomainException(Exception):
    def get_localized_message(self, lang: str = "ko") -> str:
        return ERROR_MESSAGES.get(lang, {}).get(self.code, self.message)
```

**Extension (react-i18next):**
```typescript
// extension/lib/i18n.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import ko from '../locales/ko.json';
import en from '../locales/en.json';

i18n.use(initReactI18next).init({
  resources: { ko: { translation: ko }, en: { translation: en } },
  lng: 'ko',  // 기본값
  fallbackLng: 'en',
});

// extension/hooks/useChat.ts
import { useTranslation } from 'react-i18next';

const { t } = useTranslation();
const errorMessage = t(`errors.${error_code}`, { defaultValue: content });
```

**리소스 파일 예시:**
```json
// extension/locales/ko.json
{
  "errors": {
    "LlmRateLimitError": "요청이 너무 많습니다. 잠시 후 다시 시도해주세요.",
    "LlmAuthenticationError": "API 인증 오류가 발생했습니다."
  },
  "ui": {
    "send_message": "메시지 보내기",
    "mcp_servers": "MCP 서버",
    "add_server": "서버 추가"
  }
}

// extension/locales/en.json
{
  "errors": {
    "LlmRateLimitError": "Too many requests. Please try again later.",
    "LlmAuthenticationError": "API authentication error."
  },
  "ui": {
    "send_message": "Send message",
    "mcp_servers": "MCP Servers",
    "add_server": "Add server"
  }
}
```

**DoD:**
- [ ] Backend 에러 메시지 다국어 딕셔너리 (`ko`, `en`)
- [ ] Extension react-i18next 설정
- [ ] 한국어/영어 리소스 파일 생성
- [ ] Extension UI 전체 다국어 변환
- [ ] 사용자 프로필 API를 통한 언어 설정 저장/조회
- [ ] Extension 설정 UI에서 언어 선택 가능

**예상 작업시간:** 1-2주

---

## Step 4: Advanced Reliability

**목표:** SSE 연결 풀링, LLM 호출 취소 (ADK API 대기)

### 4.1 SSE Connection Pooling

**신규/수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/inbound/http/sse_pool.py` | **NEW** | SSE 연결 풀 관리 (최대 동시 연결 수 제한) |
| `src/adapters/inbound/http/routes/chat.py` | MODIFY | SSE Pool 통합 |

**DoD:**
- [ ] 동시 SSE 연결 수 제한 (기본값: 100)
- [ ] Backpressure 처리 (연결 초과 시 429 반환)

---

### 4.2 LLM 호출 취소 (ADK Runner 취소 API 대기)

**신규/수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/outbound/adk/orchestrator_adapter.py` | MODIFY | `cancel_current_operation()` 구현 |

**DoD:**
- [ ] 진행 중인 LLM 호출 취소 가능
- [ ] Extension UI에서 "Stop" 버튼 클릭 시 즉시 취소

**의존성:** ADK Runner 취소 API 출시 대기

---

## Phase 5 Definition of Done

### 기능

- [ ] MCP Resources/Prompts/Sampling 지원 (ADK 지원 시)
- [ ] Semantic Tool Routing (도구 50개 이상 시)
- [ ] Multi-User Support (사용자별 대화 격리)
- [ ] i18n 인프라 (한국어/영어)
- [ ] SSE Connection Pooling
- [ ] LLM 호출 취소 (ADK 지원 시)

### 품질

- [ ] 기존 테스트 전체 통과
- [ ] Backend coverage >= 90%
- [ ] Extension 다국어 리소스 커버리지 100%

### 문서

- [ ] `docs/STATUS.md` — Phase 5 진행 상태 반영
- [ ] `docs/guides/i18n-guide.md` — i18n 개발 가이드 생성
- [ ] `README.md` — Multi-User 사용법 추가

---

## 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|--------|:------:|------|
| ADK MCP Advanced 지원 지연 | 🔴 높음 | Step 1 보류, Step 2-3 우선 진행 |
| i18n 리소스 번역 누락 | 🟡 중간 | 자동화 스크립트 (미번역 키 검출) |
| Multi-User 인증 복잡도 | 🟡 중간 | 로컬 사용자 선택 UI로 단순화 (OAuth 제외) |

---

## Skill/Agent 활용 계획

| 시점 | 호출 | 목적 |
|------|------|------|
| Step 1 시작 | Web search | ADK MCP Advanced API 출시 여부 확인 |
| Step 2 시작 | Web search | 벡터 DB 라이브러리 선정 (ChromaDB, Qdrant) |
| Step 3 시작 | Web search | react-i18next 최신 버전 확인 |
| Phase 5 완료 | `code-reviewer` Agent | 전체 코드 품질 검토 |

---

## 커밋 정책

```
feat(phase5): Step 1.1 - MCP Resources support (read, list)
feat(phase5): Step 1.2 - MCP Prompts support (list, render)
feat(phase5): Step 1.3 - MCP Sampling proxy
feat(phase5): Step 2 - Semantic tool routing with vector search
feat(phase5): Step 3.1 - Multi-user backend (user profiles, isolation)
feat(phase5): Step 3.2 - i18n infrastructure (ko/en resources)
feat(phase5): Step 4.1 - SSE connection pooling
feat(phase5): Step 4.2 - LLM call cancellation
docs(phase5): Phase 5 documentation updates
```

---

*Phase 5 초안 작성일: 2026-01-31*
*Phase 4 완료 후 확정 예정*
