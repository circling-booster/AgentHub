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
   - YOU MUST USE skill(/tdd).
   - YOU MUST NOT implement any entity, service, or adapter without writing tests FIRST
   - Follow Red-Green-Refactor cycle: failing test → minimal implementation → refactoring
   - Code without tests cannot be committed/PR'd
   - **Treat Tests as Immutable Specifications**: A failure indicates a bug in the implementation, not the test. Only modify tests if the user confirms a requirement change.

6. **MCP Transport**
   - Streamable HTTP preferred (2025 recommendation)
   - SSE fallback (legacy server compatibility)

7. **Protocol Standards Compliance** ⭐
   - **MCP Core Features**: MUST follow official MCP specification (Streamable HTTP, Resources when ADK supports)
   - **A2A Protocol**: MUST implement based on A2A 0.3 specification (gRPC transport, Security Cards when ADK supports)
   - **Custom Extensions**: MUST isolate in Plugin System to prevent vendor lock-in and ensure protocol upgradability

8. **TEST SERVERS & ENDPOINTS**
   - YOU SHOULD BE SPECIFIC. @tests/README.md
---

## 🚫 Critical Don'ts

| Prohibited Action | Reason |
|-------------------|--------|
| Import ADK/FastAPI in Domain Layer | Violates hexagonal architecture |
| Direct modification of main branch | PreToolUse Hook blocks (exit 2) |
| Use EventSource (SSE) | POST SSE requires fetch ReadableStream |
| Write implementation code without tests | TDD required: write tests first (Red-Green-Refactor) |
| Skip Refactoring steps | TDD required: Ensure behavior is preserved while improving structure. |

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

**TDD Principles:**
- Follow Red-Green-Refactor cycle strictly
- Test Domain Layer with Fake Adapters (no external dependencies)
- Isolate tests based on Port interfaces

**Test Linting:** ARG (unused arguments) rule disabled in `tests/` folder (for Fake Adapter signature compliance)

### Pytest Token Optimization

**AI Context Budget:** Use `-q --tb=line -x` to reduce pytest output tokens by 95%.

- `-q`: Quiet mode (dot summary)
- `--tb=line`: One-line traceback
- `-x`: Stop at first failure
- **Avoid `-v`**: Wastes tokens on passed tests

**Reference:** [pytest docs](https://docs.pytest.org/en/stable/how-to/output.html)

---

## 🧩 Test Resources

> **Policy:** Test with **local servers first**, external servers only when necessary.

### MCP Servers

| Type | Endpoint | Auth | Usage | Execution |
|------|----------|------|-------|-----------|
| **Local (Synapse)** | `http://127.0.0.1:9000/mcp` | None (default) | Phase 1-4 tests | `python -m synapse` |
| **Local (Multi-port)** | `http://127.0.0.1:9001/mcp` | API Key | Phase 5-B auth tests | `python -m synapse --multi` |
| **Local (Multi-port)** | `http://127.0.0.1:9002/mcp` | OAuth 2.0 | Phase 5-B OAuth tests | `python -m synapse --multi` |
| **External (MCP Apps)** | `https://remote-mcp-server-authless.idosalomon.workers.dev/mcp` | None | Phase 6-B MCP Apps verification | External server |

**Local MCP Server Project:** `C:\Users\sungb\Documents\GitHub\MCP_SERVER\MCP_Streamable_HTTP`

**Multi-port Configuration:**
- Multiprocessing-based (each port = independent process)
- Port 9000: No auth (default, backward-compatible)
- Port 9001: API Key auth (`X-API-Key` header)
- Port 9002: OAuth 2.0 (`Authorization: Bearer <token>`)
- Dev/test only (production: use reverse proxy + single port)

### A2A Agents

| Type | Endpoint | Usage | Execution |
|------|----------|-------|-----------|
| **Echo Agent** | `http://127.0.0.1:9003` | Phase 3+ A2A tests | conftest subprocess auto-start |
| **Math Agent** | Dynamic port | Phase 5-A A2A verification | conftest subprocess auto-start |

---

*Last Optimized: 2026-01-31*
