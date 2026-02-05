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

---

## 🚫 Critical Don'ts

| Prohibited Action | Reason |
|-------------------|--------|
| Import ADK/FastAPI in Domain Layer | Violates hexagonal architecture |
| Write implementation code without tests | TDD required: write tests first (Red-Green-Refactor) |
| Skip Refactoring steps | TDD required: Ensure behavior is preserved while improving structure. |
| Hardcode test endpoints/ports in CLAUDE.md | Violates DRY principle, creates sync burden. Use @tests/README.md reference. |

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

**트리거별 업데이트 필수 파일:**

| 트리거 | 업데이트 파일 |
|--------|--------------|
| Plan 완료 | `active/README.md` → `completed/README.md`, 폴더 이동 |
| Coverage 변경 | `tests/README.md` 수치 업데이트 |
| src/ 구조 변경 | 이 파일의 Directory Structure |
| docs/ 구조 변경 | `docs/MAP.md` Directory Structure |
| ADR 추가 | `docs/project/decisions/{category}/README.md` |

**Plan Transition Checklist:**
1. `active/NN_plan/` → `completed/NN_plan/` 이동
2. `completed/README.md` 테이블에 완료 Plan 추가
3. `active/README.md` 다음 Plan 정보로 업데이트
4. Git 커밋: `docs: complete plan NN`

---

*Last Optimized: 2026-02-05*
