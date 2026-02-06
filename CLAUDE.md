# AgentHub

Google ADK-based MCP + A2A Integrated Agent System

---

## 🎯 Quick Reference

| Item | Details |
|------|---------|
| **Purpose** | Integrate MCP/A2A tools via Chrome Extension in local environment |
| **Architecture** | Hexagonal (Ports and Adapters) |
| **Agent Framework** | Google ADK 1.23.0+ with LiteLLM |
| **Default Model** | `openai/gpt-4o-mini` |
| **Development Platform** | Windows (requires `.venv` activation) |

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

## 🚀 Quick Start

```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# Server
uvicorn src.main:app --host localhost --port 8000

# Extension dev
cd extension && npm run dev

# Tests (Token-optimized)
pytest -q --tb=line -x                    # Fast failure detection
pytest --cov=src --cov-fail-under=80 -q   # Coverage verification
```

---

## 🔐 Key Principles

**IMPORTANT: These principles MUST be followed.**

1. **Domain Layer Purity**
   - YOU MUST NOT import external libraries (ADK, FastAPI, SQLite, etc.) in `src/domain/`
   - Domain uses pure Python only (core of hexagonal architecture)

2. **Standards Verification Protocol (Cross-Validation)**
   - MCP/A2A/ADK are rapidly evolving standards
   - **Plan Phase**: Verify latest specs via web search before architecture/API design
   - **Implementation Phase**: Re-verify API method names/parameters before coding
   - IMPORTANT: Specs may change between Plan → Implementation, so **search BOTH phases**
   - Details: @docs/developers/guides/standards/README.md

3. **Hexagonal Architecture**
   - Domain does not depend on external systems
   - Adapters implement Domain Port interfaces
   - Use Fake Adapters for testing (no mocking)

4. **TDD Required (Test-First Development)**
   - YOU MUST NOT implement any entity, service, or adapter without writing tests FIRST
   - Follow Red-Green-Refactor cycle: failing test → minimal implementation → refactoring
   - **Treat Tests as Immutable Specifications**: A failure indicates a bug in the implementation, not the test. Only modify tests if the user confirms a requirement change.

5. **TEST SERVERS & ENDPOINTS**
   - YOU SHOULD BE SPECIFIC. @tests/README.md

6. **Test Environment Isolation**
   - Tests MUST NOT depend on `.env` for test-specific config (use `monkeypatch.setenv()`)
   - App creation in fixtures: use `create_app()`, never `from src.main import app`
   - Machine-specific paths: use env vars with `Path.home()` fallback

---

## 🚫 Critical Don'ts

| Prohibited Action | Reason |
|-------------------|--------|
| Import ADK/FastAPI in Domain Layer | Violates hexagonal architecture |
| Write implementation code without tests | TDD required: write tests first (Red-Green-Refactor) |
| Skip Refactoring steps | TDD required: Ensure behavior is preserved while improving structure. |
| Write technical debt, spaghetti code, or temporary workarounds | All code must be clean, maintainable, and production-ready from the start |
| Hardcode test endpoints/ports in CLAUDE.md | Violates DRY principle, creates sync burden. Use @tests/README.md reference. |
| Use Windows path separators (\) in Git Bash | Git Bash requires forward slashes (/) for paths, not backslashes (\) |
| Run pytest/uvicorn without activating .venv | Required dependencies (pytest-playwright, FastAPI, etc.) are only in virtual environment |
| Hardcode paths/ports in test code | Use env vars with defaults: `os.environ.get("KEY", "default")` |

---

## 📚 Documentation Strategy

**Progressive Disclosure (프랙탈 구조):**

모든 문서는 [@docs/MAP.md](docs/MAP.md)에서 시작합니다. MAP.md는 전체 구조의 "메타 지도"이며, 각 섹션의 README.md가 상세 지도(Sub-Map) 역할을 합니다.

**Planning Hierarchy:**
```
Plan > Phase > Step
```

- **Plan**: 하나의 독립적인 개발 주기/마일스톤 (예: `07_hybrid_dual`)
- **Phase**: Plan 내부의 아키텍처 레이어 단위 (예: `01_domain_entities.md`)
- **Step**: Phase 내부의 구현 단계 (예: Step 1.1, 1.2, 1.3)

**자주 참조:**
- **Planning 구조**: [@docs/project/planning/README.md](docs/project/planning/README.md)
- **현재 작업**: [@docs/project/planning/active/README.md](docs/project/planning/active/README.md)
- **테스트 가이드**: [@tests/README.md](tests/README.md)

---

## 🧪 Test Strategy

**TDD Required:**
- Red-Green-Refactor cycle: Write failing test → Minimal implementation → Refactor
- Test Domain with Fake Adapters (no mocking)
- Pytest optimization: `-q --tb=line -x` (95% token reduction)

**Full Details:** [@tests/README.md](tests/README.md) (구조, 전략, 마커, 옵션, 리소스)

---

## 🔄 Document Maintenance

### Quick Reference: 문서 동기화

| 변경 사항 | 업데이트 대상 |
|-----------|--------------|
| **src/ 구조** | `CLAUDE.md` Directory Structure |
| **docs/ 구조** | `docs/MAP.md` Directory Structure |
| **Coverage** | `tests/README.md` 수치 |
| **ADR 추가** | `docs/project/decisions/{category}/README.md` |

### Plan Lifecycle

**Plan Start Checklist:**
1. 새 Plan 폴더 생성: `docs/project/planning/active/NN_descriptive_name/`
2. `active/README.md` "Current Work" 업데이트 (Plan 번호, Branch, 목표)
3. Git branch 생성: `git checkout -b feature/plan-NN-descriptive-name`
4. Plan README.md에 현재 상황 기록 (Coverage, 완료 기능, 이슈)

**Plan Transition (완료 시):**
1. `completed/README.md`에 완료 Plan 추가
2. `active/README.md` 다음 Plan으로 업데이트
3. Git 커밋: `docs: complete plan NN`

### Phase Lifecycle

**Phase Workflow (매 Phase 반복):**
1. **시작**: Plan README.md Status ⏸️ → 🔄
2. **완료**: Status 🔄 → ✅
3. **Rule**: 항상 1개 Phase만 🔄 유지

---

*Last Optimized: 2026-02-05*
