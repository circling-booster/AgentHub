# AgentHub

Google ADK 기반 MCP + A2A 통합 Agent System

---

## 🎯 What You Need to Know First

| 항목 | 내용 |
|------|------|
| **목적** | 로컬 환경에서 MCP/A2A 도구를 Chrome Extension으로 통합 |
| **Language** | Python 3.10+ (Backend) + TypeScript (Extension) |
| **Architecture** | Hexagonal (Ports and Adapters) |
| **Agent Framework** | Google ADK 1.23.0+ with LiteLLM |
| **Default Model** | `anthropic/claude-sonnet-4-20250514` |

**Core Flow:**
```
Chrome Extension → AgentHub API (localhost:8000) → MCP Servers / A2A Agents
```

---

## 📁 Directory Structure

```
src/
├── domain/           # Pure Python (no external dependencies)
│   ├── entities/     # Agent, Tool, Endpoint, Conversation
│   ├── services/     # OrchestratorService, ConversationService
│   └── ports/        # Port interfaces (inbound/outbound)
├── adapters/
│   ├── inbound/      # FastAPI HTTP, A2A Server
│   └── outbound/     # ADK, A2A Client, Storage (SQLite WAL)
└── config/           # DI container, pydantic-settings + YAML

extension/            # Chrome Extension (WXT + TypeScript)
├── entrypoints/      # background, offscreen, popup, sidepanel
└── lib/              # API client, SSE streaming

tests/                # TDD (80% coverage target)
├── unit/             # Domain Layer (Fake Adapters)
├── integration/      # Adapters + External systems
└── e2e/              # Full stack (Extension + Server)
```

---

## 🚀 How to Work

### Quick Start

```bash
# Server
uvicorn src.main:app --host localhost --port 8000

# Extension dev
cd extension && npm run dev

# Tests
pytest
pytest --cov=src --cov-report=html
```

**Environment:** `.env` 파일에 API 키 설정 (ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY)

### Development Workflow

**자동화 (Hooks):**
- **PreToolUse Hook**: main 브랜치 직접 Edit/Write 차단 (항상 feature 브랜치 사용)
- **Stop Hook**: 응답 완료 시 자동 실행 (ruff 린트/포맷, pytest)
- **GitHub Actions**: PR 시 커버리지 80% 미만 차단

자세한 내용: `.claude/settings.json` 및 `.github/workflows/ci.yml` 참조

---

## ⚠️ Critical Constraints & Solutions

| 제약 | 해결책 |
|------|--------|
| Service Worker 30s timeout | Offscreen Document 사용 |
| MCPToolset.get_tools() is async | Async Factory Pattern (FastAPI startup 초기화) |
| SQLite concurrent writes | WAL mode + write lock |
| Google Built-in Tools (SearchTool 등) | Gemini 전용 → MCP 서버로 대체 |

---

## 🔐 Key Principles

**IMPORTANT: 이 원칙들은 반드시 준수해야 합니다.**

1. **Domain Layer 순수성**
   - YOU MUST NOT import 외부 라이브러리 (ADK, FastAPI, SQLite 등) in `src/domain/`
   - 도메인은 순수 Python만 사용 (헥사고날 아키텍처 핵심)

2. **Standards Verification Protocol (교차 검증)**
   - MCP/A2A/ADK는 빠르게 진화하는 표준
   - **Plan 단계**: 아키텍처/API 설계 전 웹 검색으로 최신 스펙 확인
   - **구현 단계**: 코드 작성 전 API 메서드명/파라미터 재검증
   - IMPORTANT: Plan → 구현 간 스펙 변경 가능성 있으므로 **양 단계 모두 검색 필수**
   - 상세: @docs/standards-verification.md

3. **Hexagonal Architecture**
   - 도메인이 외부에 의존하지 않음
   - 어댑터가 도메인 Port 인터페이스를 구현
   - 테스트 시 Fake Adapter 사용 (Mocking 금지)

4. **Security First**
   - localhost API는 Token Handshake 필수 (Drive-by RCE 방지)
   - Extension ↔ Server 간 X-Extension-Token 헤더 검증
   - 상세: @docs/implementation-guide.md#9-보안-패턴

5. **TDD 필수 (Test-First Development)**
   - YOU MUST NOT implement any entity, service, or adapter without writing tests FIRST
   - Red-Green-Refactor 사이클 엄수: 실패하는 테스트 → 최소 구현 → 리팩토링
   - 테스트 없는 구현 코드는 커밋/PR 불가

6. **MCP Transport**
   - Streamable HTTP 우선 (2025년 권장)
   - SSE fallback (레거시 서버 호환)

---

## 🚫 Critical Don'ts

| 금지 사항 | 이유 |
|----------|------|
| Domain Layer에 ADK/FastAPI import | 헥사고날 아키텍처 위반 |
| main 브랜치 직접 수정 | PreToolUse Hook 차단 (exit 2) |
| .env 파일 커밋 | 보안 위험 |
| EventSource 사용 (SSE) | POST SSE는 fetch ReadableStream 필요 |
| 테스트 없이 구현 코드 작성 | TDD 필수: 반드시 테스트 먼저 작성 (Red-Green-Refactor) |
| 테스트 없이 PR | 80% 커버리지 미만 시 CI 차단 |

---

## 📚 Documentation Strategy

**상황별 참조 문서 (Progressive Disclosure):**

| 상황 | 참조 문서 |
|------|----------|
| **프로젝트 이해** | @README.md (빠른 시작, 설치) |
| **아키텍처 설계** | @docs/architecture.md (헥사고날 구조) |
| **구현 패턴** | @docs/implementation-guide.md (코드 예시) |
| **Extension 개발** | @docs/extension-guide.md (Offscreen Document) |
| **보안 구현** | @docs/implementation-guide.md#9-보안-패턴 |
| **Standards 검증** | @docs/standards-verification.md |
| **Phase 계획** | @docs/roadmap.md |
| **리스크 평가** | @docs/risk-assessment.md |
| **ADR 기록** | @docs/decisions/ |

---

## 🧪 Test Strategy (TDD + Hexagonal)

| Phase | 테스트 유형 | 대상 | 커버리지 목표 |
|-------|-----------|------|--------------|
| Phase 1 | Unit | Domain Layer | 80% |
| Phase 2 | Integration | MCP Adapter, API | 70% |
| Phase 3 | E2E | Full Stack | Critical Path |

**TDD 원칙:**
- Red-Green-Refactor 사이클 엄수
- Domain Layer는 Fake Adapter로 테스트 (외부 의존성 없이)
- Port 인터페이스 기반 테스트 격리

**테스트 린트:** `tests/` 폴더에서 ARG (미사용 인자) 규칙 비활성화됨 (Fake Adapter 시그니처 준수 목적)

---

## 🤖 품질 검증 체크리스트

| 시점 | 필요 작업 |
|------|----------|
| Entity/Service 구현 전 | TDD 테스트 먼저 작성 |
| 아키텍처 변경 시 | 헥사고날 아키텍처 원칙 준수 검토 |
| 보안 코드 작성 후 | 보안 취약점 검토 |
| 기능 완료/PR 전 | 코드 품질 및 아키텍처 리뷰 |

---

## 🌐 Working Guidelines

- **한국어**로 소통 (별도 지시 없으면)
- **웹 검색 교차 검증** (MCP/A2A/ADK):
  - **Plan 단계**: 설계 전 최신 스펙/Breaking Changes 확인
  - **구현 단계**: 코드 작성 전 API 시그니처 재검증
  - 불확실 시 즉시 웹 검색 (추측 금지)
- **Fake Adapter 패턴**: 테스트 시 Mocking 대신 Fake 구현체 사용
- **코드 패턴**: @docs/implementation-guide.md 참조

---

## 🧩 Test Resources

| Type | Resource |
|------|----------|
| MCP Test Server | `https://example-server.modelcontextprotocol.io/mcp` |
| A2A Samples | github.com/a2aproject/a2a-samples |

---

## 📝 Folder Documentation

**중요 폴더는 README.md 포함해야 함:**

| 폴더 | 우선순위 | 생성 시점 |
|------|:-------:|----------|
| `src/` | 🔴 필수 | Phase 1 시작 |
| `src/domain/` | 🔴 필수 | Phase 1 완료 |
| `src/config/` | 🔴 필수 | Phase 1 완료 |
| `tests/` | 🔴 필수 | Phase 1 완료 |
| `src/adapters/` | 🟡 중요 | Phase 2 완료 |
| `extension/` | 🟢 권장 | Phase 2.5 완료 |

상세 정책: @.claude/folder-readme-guide.md

---

*최적화 완료: 2026-01-29*
