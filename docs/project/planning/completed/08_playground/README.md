# Plan 08: Playground Implementation

## Overview

**목표:** 백엔드 API를 Extension 없이 빠르게 테스트할 수 있는 수동 테스트 도구 구현

**핵심 원칙:**
- **TDD Required**: 모든 구현은 테스트 먼저 작성 (Red → Green → Refactor)
- **헥사고날 아키텍처**: Settings → Security → Middleware → Static Files 순서로 레이어 구현
- **테스트 격리**: 단위/통합/E2E 테스트 명확히 구분

**현재 상태:**
- Branch: `feature/plan-08-playground`
- Test Coverage: 89.94%
- Phase Progress: See [Implementation Phases](#implementation-phases) below

---

## User Decisions

| 항목 | 선택 |
|------|------|
| **Tech Stack** | Vanilla HTML/JS |
| **Auth Mode** | DEV_MODE=true (개발 모드 분리) |
| **Location** | `tests/manual/` |
| **SSE Display** | 실시간 로그 + 채팅 UI |
| **OAuth** | 제외 (복잡도 감소) |
| **Workflow** | 포함 |
| **구현 순서** | 기능 우선 → 문서화 마지막 |

---

## Implementation Phases

각 Phase는 **헥사고날 아키텍처 레이어**에 정렬되며, **TDD 사이클(Red-Green-Refactor)**을 따릅니다.

| Phase | Layer | Status | 문서 |
|-------|-------|--------|------|
| **Phase 1** | Settings (Config) | ✅ Done | [01_settings_layer.md](01_settings_layer.md) |
| **Phase 2** | Security (Auth) | ✅ Done | [02_security_layer.md](02_security_layer.md) |
| **Phase 3** | CORS Middleware | ✅ Done | [03_cors_middleware.md](03_cors_middleware.md) |
| **Phase 4** | HTML/CSS (Static Layout) | ✅ Done | [04_playground_static.md](04_playground_static.md) |
| **Phase 5** | JavaScript Modules (TDD) | ✅ Done | [05_unit_tests.md](05_unit_tests.md) |
| **Phase 6** | E2E Tests (Playwright) | ✅ Done | [06_e2e_tests.md](06_e2e_tests.md) |
| **Phase 7** | Documentation | ✅ Done | [07_documentation.md](07_documentation.md) |

**Status Icons:**
- ⏸️ **Pending** - 대기 중
- 🔄 **In Progress** - 진행 중 (항상 1개만)
- ✅ **Done** - 완료

**순서대로 구현 필수**:
- Phase 1-3 (백엔드 DEV_MODE)
- Phase 4 (HTML/CSS만)
- Phase 5 (JS 모듈을 TDD로 구현)
- Phase 6 (E2E 테스트)
- Phase 7 (문서화)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Playground (Vanilla HTML/JS)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Chat Tab    │  │ MCP Tab     │  │ Conversations Tab       │  │
│  │ (SSE)       │  │ (CRUD)      │  │ (CRUD + Tool Calls)     │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
└─────────┼────────────────┼─────────────────────┼────────────────┘
          │                │                     │
          │ http://localhost:3000 (Static Server)│
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                  AgentHub API (DEV_MODE=true)                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    CORS Middleware (Phase 3)                 │ │
│  │          DEV_MODE: allow localhost:* origins                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Security Layer (Phase 2)                  │ │
│  │     DEV_MODE + localhost Origin: Skip Token Verification    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Settings Layer (Phase 1)                  │ │
│  │              dev_mode: bool = False (from env)               │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌───────────────────────────┴───────────────────────────────┐  │
│  │                    HTTP Routes (Existing)                  │  │
│  │  /health  /api/chat/stream  /api/mcp/servers/*            │  │
│  │  /api/a2a/agents/*  /api/conversations/*  /api/usage/*    │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Playground Features

### 필수 (Core Features)
- [x] Health Check
- [x] Chat SSE 스트리밍 (메인 기능)
- [x] MCP 서버 등록/해제/도구 조회
- [x] A2A 에이전트 등록/해제
- [x] Conversations CRUD
- [x] Usage/Budget 조회

### 고급 (Advanced)
- [x] Workflow 생성/실행 (SSE)

### 제외
- OAuth 플로우 (외부 Provider 필요)
- Circuit Breaker, Retry, Chaos (API 없음)

---

## Test Strategy

### 1. Unit Tests (Phase 5)
**위치:** `tests/manual/playground/tests/`
**대상:** JavaScript 모듈 (api-client.js, sse-handler.js, ui-components.js)
**도구:** Jest (예정)
**TDD 필수:** Red (테스트 작성) → Green (구현) → Refactor

### 2. Integration Tests (Phase 1-3)
**위치:** `tests/integration/adapters/`
**대상:** Settings, Security, CORS 백엔드 로직
**도구:** pytest
**TDD 필수:** Red (테스트 작성) → Green (구현) → Refactor

### 3. E2E Tests (Phase 6)
**위치:** `tests/e2e/test_playground.py`
**대상:** Playground 전체 플로우 (Health → Chat → MCP → Workflow)
**도구:** Playwright
**TDD 필수:** Red (시나리오 작성) → Green (기능 구현) → Refactor

---

## File Structure

```
# 백엔드 (Phase 1-3)
src/
├── config/
│   └── settings.py                  # Phase 1: dev_mode 필드 추가
├── adapters/inbound/http/
│   ├── app.py                       # Phase 3: CORS 조건부 확장
│   └── security.py                  # Phase 2: Auth 우회 조건

# 프론트엔드 (Phase 4)
tests/manual/playground/
├── index.html                       # 메인 UI (탭 네비게이션)
├── css/
│   └── styles.css                   # Tailwind-like 스타일
└── js/
    ├── api-client.js                # API 호출 모듈
    ├── sse-handler.js               # SSE 스트리밍 처리
    └── ui-components.js             # UI 렌더링 함수

# 테스트 (Phase 5-6)
tests/
├── integration/adapters/
│   ├── test_dev_mode_settings.py    # Phase 1 통합 테스트
│   ├── test_dev_mode_security.py    # Phase 2 통합 테스트
│   └── test_dev_mode_cors.py        # Phase 3 통합 테스트
├── e2e/
│   └── test_playground.py           # Phase 6 E2E 테스트
└── manual/playground/tests/         # Phase 5 단위 테스트 (JS)
    ├── api-client.test.js
    ├── sse-handler.test.js
    └── ui-components.test.js

# 문서 (Phase 7)
docs/developers/guides/playground/
├── README.md                        # Playground 개요
├── quickstart.md                    # 설치 및 실행
├── backend-api.md                   # API 테스트 가이드
└── sse-streaming.md                 # SSE 디버깅 가이드
```

---

## Verification

### 백엔드 DEV_MODE 테스트
```bash
DEV_MODE=true uvicorn src.main:app --reload
# 브라우저: http://localhost:8000/health
```

### Playground 기능 테스트
```bash
# Static 파일 서버
python -m http.server 3000 --directory tests/manual/playground

# 브라우저: http://localhost:3000
# - Health 상태 확인
# - Chat 스트리밍 테스트
# - MCP 서버 등록 테스트
```

### E2E 테스트 실행
```bash
pytest tests/e2e/test_playground.py -v
```

---

## Critical Files Summary

| 구분 | 파일 | Phase |
|------|------|-------|
| **Settings** | `src/config/settings.py` | 1 |
| **Security** | `src/adapters/inbound/http/security.py` | 2 |
| **CORS** | `src/adapters/inbound/http/app.py` | 3 |
| **HTML/CSS** | `tests/manual/playground/index.html`, `css/styles.css` | 4 |
| **API Client** | `tests/manual/playground/js/api-client.js` | 5 (TDD) |
| **SSE Handler** | `tests/manual/playground/js/sse-handler.js` | 5 (TDD) |
| **UI Components** | `tests/manual/playground/js/ui-components.js` | 5 (TDD) |
| **Main Module** | `tests/manual/playground/js/main.js` | 5 (TDD) |
| **JS Unit Tests** | `tests/manual/playground/tests/*.test.js` | 5 |
| **E2E Tests** | `tests/e2e/test_playground.py` | 6 |
| **Docs** | `docs/developers/guides/playground/README.md` | 7 |

---

## Design Decisions

### DEV_MODE 분리
- **프로덕션**: Extension만 허용 (chrome-extension://)
- **개발**: localhost 허용 + 토큰 검증 우회
- **보안**: DEV_MODE=true는 로컬 개발 환경에만 사용

### Vanilla HTML/JS
- **이유**: 빌드 도구 불필요, 즉시 실행 가능
- **트레이드오프**: 타입 안정성 낮음 (ESLint로 보완)

### SSE 이벤트 로그 + 채팅 UI
- **이유**: 디버깅 용이성 + 사용자 경험
- **구조**: 좌측(채팅) + 우측(로그) 2패널

---

## Risk Mitigation

| 위험 | 대응 |
|------|------|
| DEV_MODE 프로덕션 유출 | `.env.example`에 DEV_MODE=false 명시, 문서에 경고 추가 |
| CORS 보안 취약점 | DEV_MODE 시에만 localhost 허용, Origin 검증 유지 |
| 테스트 복잡도 | Phase 5 (단위) → Phase 6 (E2E) 순차 구현 |
| Playwright 설정 | 기존 `tests/e2e/` 구조 재사용 |

---

## TDD 원칙 (CRITICAL)

**모든 Phase는 반드시 다음 순서를 따릅니다:**

1. **Red**: 테스트 작성 → 실행 → 실패 확인
2. **Green**: 최소 구현 → 테스트 통과
3. **Refactor**: 코드 개선 → 테스트 여전히 통과

**TDD 적용:**
- **Phase 1-3 (백엔드)**: pytest 통합 테스트 (TDD 필수)
- **Phase 4 (HTML/CSS)**: TDD 예외 (E2E로 검증, 수동 테스트)
- **Phase 5 (JS 모듈)**: Jest 단위 테스트 (TDD 엄격히 준수)
- **Phase 6 (E2E)**: Playwright (Red → Green → Refactor)
- **Phase 7 (문서)**: TDD 예외

---

## Review Checklist

### 구현 전 검증
- [ ] Phase가 헥사고날 레이어에 정렬되었는가?
- [ ] 각 Phase에 TDD 사이클이 명시되었는가?
- [ ] Phase 6이 E2E 테스트로 명확히 정의되었는가?
- [ ] 테스트 전략이 단위/통합/E2E로 구분되었는가?

### 구현 중 검증
- [ ] 테스트를 먼저 작성했는가? (Red)
- [ ] 최소 구현으로 통과했는가? (Green)
- [ ] 리팩토링 후에도 테스트가 통과하는가? (Refactor)

### 구현 후 검증
- [ ] 모든 단위/통합 테스트 통과 (`pytest tests/unit tests/integration -q`)
- [ ] E2E 테스트 통과 (`pytest tests/e2e/test_playground.py -v`)
- [ ] Coverage 80% 이상 (`pytest --cov=src --cov-fail-under=80`)

---

*Last Updated: 2026-02-05*
*Structure: Phase-based (Plan > Phase > Step)*
*TDD: Red-Green-Refactor Enforced*
