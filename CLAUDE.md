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
| **Coverage** | 80% minimum (CI enforced, current: 89.90%) |

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
   - **Search Year**: Always use current year (2026) in queries
   - Details: @docs/developers/guides/standards/README.md

3. **Hexagonal Architecture**
   - Domain does not depend on external systems
   - Adapters implement Domain Port interfaces
   - Use Fake Adapters for testing (no mocking)

4. **TDD Required (Test-First Development)**
   - YOU MUST NOT implement any entity, service, or adapter without writing tests FIRST
   - Follow Red-Green-Refactor cycle: failing test → minimal implementation → refactoring
   - **Treat Tests as Immutable Specifications**: A failure indicates a bug in the implementation, not the test. Only modify tests if the user confirms a requirement change.
   - Import Standard: `from src.domain...` (with `src.` prefix)

5. **TEST SERVERS & ENDPOINTS**
   - YOU SHOULD BE SPECIFIC. @tests/README.md

6. **Playground-First Testing (Phase 6+)**
   - HTTP API/SSE: Implement Playground UI + E2E tests together, defer Extension UI to Production Phase

---

## 🚫 Critical Don'ts

| Prohibited Action | Reason |
|-------------------|--------|
| Import ADK/FastAPI in Domain Layer | Violates hexagonal architecture |
| Write implementation code without tests | TDD required: write tests first (Red-Green-Refactor) |
| Skip Refactoring steps | TDD required: Ensure behavior is preserved while improving structure. |
| Hardcode test endpoints/ports in CLAUDE.md | Violates DRY principle, creates sync burden. Use @tests/README.md reference. |
| Skip commit after Phase completion | Violates Git Workflow, loses traceability |
| Commit directly to main branch | Must use feature/plan-* branch |

---

## 📚 Documentation Strategy

**Hub-and-Spoke Structure:**

All documentation starts from [@docs/MAP.md](docs/MAP.md). MAP.md serves as the central "Hub" providing section overviews, while each section's README.md acts as a "Spoke" with detailed documentation lists.

**AI Accessibility:** [@docs/llms.txt](docs/llms.txt) provides a standardized entry point for AI assistants, listing core documentation paths organized by role (developers/operators/project).

### Linking Policy

| Link Target | Strategy | Example |
|-------------|----------|---------|
| **Same Section** | Direct relative link | `[architecture/](architecture/)` |
| **Different Section (frequent)** | Direct absolute link | `[@tests/README.md](tests/README.md)` |
| **Different Section (occasional)** | MAP reference | "See docs/MAP.md Operators section" |
| **External docs** | Direct link | `[@CLAUDE.md](CLAUDE.md)` |

### Planning Hierarchy

```
Plan > Phase > Step
```

- **Plan**: Independent development cycle/milestone (e.g., `07_hybrid_dual`)
- **Phase**: Architecture layer unit within Plan (e.g., `01_domain_entities.md`)
- **Step**: Implementation step within Phase (e.g., Step 1.1, 1.2, 1.3)

### Frequently Referenced

- **Planning Structure**: [@docs/project/planning/README.md](docs/project/planning/README.md)
- **Current Work**: [@docs/project/planning/active/README.md](docs/project/planning/active/README.md)
- **Test Guide**: [@tests/README.md](tests/README.md)

---

## 🧪 Test Strategy

**TDD Required:**
- Red-Green-Refactor cycle: Write failing test → Minimal implementation → Refactor
- Test Domain with Fake Adapters (no mocking)
- Pytest optimization: `-q --tb=line -x` (95% token reduction)

**Full Details:** [@tests/README.md](tests/README.md) (structure, strategy, markers, options, resources)

---

## 🔄 Document Maintenance

**Trigger-based Required Updates:**

| Trigger | Update Files |
|---------|--------------|
| **Plan Start** | Git: Create `feature/plan-NN-name` branch |
| **Phase Complete** | Git: Commit `docs: complete phase N - name` |
| Plan Complete | `active/README.md` → `completed/README.md`, move folder |
| Coverage Change | Update `tests/README.md` metrics |
| src/ Structure Change | This file's Directory Structure |
| docs/ Structure Change | `docs/MAP.md` Directory Structure |
| ADR Added | `docs/project/decisions/{category}/README.md` |

**Plan Transition Checklist:**
1. Move `active/NN_plan/` → `completed/NN_plan/`
2. Add completed Plan to `completed/README.md` table
3. Update `active/README.md` with next Plan info
4. Git commit: `docs: complete plan NN`, create PR → merge to `main`

---

*Last Optimized: 2026-02-05*
