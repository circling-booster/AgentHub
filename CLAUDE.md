# AgentHub

Google ADK-based MCP + A2A Integrated Agent System

---

## 🎯 Quick Reference

| Item | Details |
|------|---------|
| **Purpose** | Integrate MCP/A2A tools via Chrome Extension in local environment |
| **Language** | Python 3.10+ (Backend) + TypeScript (Extension) |
| **Architecture** | Hexagonal (Ports and Adapters) |
| **Agent Framework** | Google ADK 1.23.0+ with LiteLLM |
| **Default Model** | `openai/gpt-4o-mini` |

**Core Flow:**
```
Chrome Extension → AgentHub API (localhost:8000) → MCP Servers / A2A Agents
```

**Current Status:** See [@docs/STATUS.md](docs/STATUS.md) for real-time progress, coverage, and next actions.

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

**Environment:** Set API keys in `.env` file (ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY)

### Automated Workflow (Hooks)

- **PostToolUse Hook**: Auto ruff formatting after code changes
- **Stop Hook**: Run unit tests on response completion (`pytest tests/unit/ -q --tb=line -x`)
- **UserPromptSubmit Hook**: Full test + coverage verification on commit/pr/push (`pytest tests/ --cov=src --cov-fail-under=80 -q`)
- **Git pre-commit hook**: Block direct commits to main branch
- **GitHub Actions**: Block PRs with <80% coverage

**Note:** All pytest hooks use token-optimized options (`-q --tb=line -x`) to minimize Claude Code context consumption.

Details: `.claude/settings.json` and `.github/workflows/ci.yml`

---

## ⚠️ Critical Constraints & Solutions

| Constraint | Solution |
|------------|----------|
| MCPToolset.get_tools() is async | Async Factory Pattern (FastAPI startup initialization) |
| SQLite concurrent writes | WAL mode + write lock |
| Google Built-in Tools (SearchTool, etc.) | Gemini-only → Replace with MCP servers |

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
   - Details: @docs/guides/standards-verification.md

3. **Hexagonal Architecture**
   - Domain does not depend on external systems
   - Adapters implement Domain Port interfaces
   - Use Fake Adapters for testing (no mocking)

4. **Security First**
   - localhost API requires Token Handshake (prevent Drive-by RCE)
   - Extension ↔ Server X-Extension-Token header verification
   - Details: @docs/guides/implementation-guide.md#9-security-patterns

5. **TDD Required (Test-First Development)**
   - YOU MUST NOT implement any entity, service, or adapter without writing tests FIRST
   - Follow Red-Green-Refactor cycle: failing test → minimal implementation → refactoring
   - Code without tests cannot be committed/PR'd

6. **MCP Transport**
   - Streamable HTTP preferred (2025 recommendation)
   - SSE fallback (legacy server compatibility)

---

## 🚫 Critical Don'ts

| Prohibited Action | Reason |
|-------------------|--------|
| Import ADK/FastAPI in Domain Layer | Violates hexagonal architecture |
| Direct modification of main branch | PreToolUse Hook blocks (exit 2) |
| Use EventSource (SSE) | POST SSE requires fetch ReadableStream |
| Write implementation code without tests | TDD required: write tests first (Red-Green-Refactor) |
| PR without tests | CI blocks if coverage <80% |

---

## 📚 Documentation Strategy

**Situational Reference (Progressive Disclosure):**

| Situation | Reference Document |
|-----------|-------------------|
| **Project Status** | @docs/STATUS.md (progress, coverage, next actions) |
| **Quick Start** | @README.md (installation, usage) |
| **Implementation Patterns** | @docs/guides/implementation-guide.md (code examples) |
| **Security Implementation** | @docs/guides/implementation-guide.md#9-security-patterns |
| **Standards Verification** | @docs/guides/standards-verification.md |
| **Phase Plans** | @docs/roadmap.md |
| **ADR Records** | @docs/decisions/ |

---

## 🧪 Test Strategy (TDD + Hexagonal)

| Phase | Test Type | Target | Coverage Goal |
|-------|-----------|--------|---------------|
| Phase 1 | Unit | Domain Layer | 80% |
| Phase 2 | Integration | MCP Adapter, API | 70% |
| Phase 3 | E2E | Full Stack | Critical Path |

**TDD Principles:**
- Follow Red-Green-Refactor cycle strictly
- Test Domain Layer with Fake Adapters (no external dependencies)
- Isolate tests based on Port interfaces

**Test Linting:** ARG (unused arguments) rule disabled in `tests/` folder (for Fake Adapter signature compliance)

### Pytest Token Optimization

**IMPORTANT:** When working with Claude Code, pytest output consumes tokens from the AI context budget. Use optimized options to reduce costs by **95%**.

| Pytest Options | Token Cost (3 failures) | When to Use |
|----------------|-------------------------|-------------|
| `pytest -v` (default) | ~2,000-5,000+ ❌ | **NEVER** with AI agents |
| `--tb=line` | ~300-500 ⚠️ | Debugging phase |
| `-q --tb=line -x` | ~50-80 🚀 | **RECOMMENDED** for AI |

**Key Options:**
- `-q`: Quiet mode (no verbose headers, success = `.` dot)
- `--tb=line`: One-line traceback (file:line:error only)
- `-x` / `--maxfail=1`: Stop at first failure (prevent "chain explosion")

**Avoid:**
- `-v` (verbose): Prints ALL test names, wasting tokens on PASSED tests
- Long tracebacks: Full call stack is unnecessary when Claude has file context

**References:** [pytest docs](https://docs.pytest.org/en/stable/how-to/output.html) | [AI TDD guide](https://www.builder.io/blog/test-driven-development-ai)

---

## 🧩 Test Resources

> **Policy:** Test with **local servers only**, not external servers.

| Type | Resource | Execution |
|------|----------|-----------|
| MCP Test Server | `http://127.0.0.1:9000/mcp` (local Synapse) | `SYNAPSE_PORT=9000 python -m synapse` |
| A2A Agents | Local A2A Agent Server (in development) | TBD |

**MCP Server Project:** `C:\Users\sungb\Documents\GitHub\MCP_SERVER\MCP_Streamable_HTTP`

---

*Last Optimized: 2026-01-30*
