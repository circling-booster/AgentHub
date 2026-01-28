# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

**AgentHub** is a Google ADK-based Agent System that integrates MCP servers and A2A agents into a single interface.

- **Project Name**: AgentHub
- **Language**: Python 3.10+
- **License**: Apache 2.0
- **Target Users**: Developers (primary)
- **Architecture**: Hexagonal (Ports and Adapters)

## Core Concept

```
Chrome Extension → AgentHub API Server (ADK) → MCP Servers / A2A Agents
```

- **Chrome Extension**: Main interface for user interaction (Manifest V3 + Offscreen Document)
- **API Server**: Python backend running on localhost:8000
- **Dynamic Registration**: Users can add/remove MCP/A2A endpoints via UI (no restart required)

## Technical Stack

| Component | Technology |
|-----------|------------|
| Agent Framework | Google ADK 1.23.0+ |
| LLM Integration | LiteLLM (Claude, GPT-4, Gemini, etc.) |
| Default Model | `anthropic/claude-sonnet-4-20250514` |
| MCP Transport | Streamable HTTP (SSE fallback for legacy) |
| A2A Protocol | HTTP/JSON-RPC 2.0 |
| Extension | WXT + TypeScript + Offscreen Document |
| DI Container | dependency-injector |
| Settings | pydantic-settings + YAML |
| Database | SQLite (WAL mode) |

## Critical Implementation Patterns

### 1. Extension: Offscreen Document (Required)

Service Worker has 30-second timeout. Use Offscreen Document for long-running LLM requests.

```typescript
// background.ts
await chrome.offscreen.createDocument({
  url: 'offscreen/index.html',
  reasons: [chrome.offscreen.Reason.WORKERS],
  justification: 'Handle long-running LLM API requests',
});
```

### 2. Async Factory Pattern (Required)

MCPToolset.get_tools() is async. Use explicit async initialization.

```python
class AdkOrchestratorAdapter:
    async def initialize(self) -> None:
        """Call from FastAPI startup event"""
        await self._dynamic_toolset.get_tools()
        self._agent = LlmAgent(...)
        self._initialized = True
```

### 3. SQLite WAL Mode (Required)

Prevents "database is locked" errors in async environment.

```python
await conn.execute("PRAGMA journal_mode=WAL")
await conn.execute("PRAGMA busy_timeout=5000")
```

### 4. DynamicToolset with Caching

```python
class DynamicToolset(BaseToolset):
    async def get_tools(self, readonly_context=None) -> list[BaseTool]:
        """TTL-based caching to avoid unnecessary MCP server calls"""
        if self._is_cache_valid(endpoint_id):
            return self._tool_cache[endpoint_id]
        # ... fetch from MCP server
```

## ADK Code Patterns

### Correct Import Structure (ADK 1.23.0+)

```python
from google.adk.agents import LlmAgent
from google.adk.tools import BaseToolset, BaseTool
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams, SseServerParams
from google.adk.models.lite_llm import LiteLlm
from google.adk.a2a.utils.agent_to_a2a import to_a2a
```

### Important Constraints

| Constraint | Description | Solution |
|------------|-------------|----------|
| Google Built-in Tools | SearchTool, CodeExecutionTool work with Gemini only | Use MCP servers instead |
| MCPToolset async | get_tools() is async | Async Factory Pattern |
| Service Worker timeout | 30s idle = termination | Offscreen Document |
| SQLite concurrent writes | "database is locked" | WAL mode + write lock |

## Directory Structure

```
src/
├── domain/                   # Pure Python (no external dependencies)
│   ├── entities/             # Agent, Tool, Endpoint, Conversation
│   ├── services/             # OrchestratorService, ConversationService
│   ├── ports/                # Port interfaces (inbound/outbound)
│   └── exceptions.py         # Domain exceptions
│
├── adapters/
│   ├── inbound/
│   │   ├── http/             # FastAPI routes, schemas, middleware
│   │   └── a2a_server/       # A2A server (ADK to_a2a)
│   └── outbound/
│       ├── adk/              # DynamicToolset, OrchestratorAdapter
│       ├── a2a_client/       # A2A client (JSON-RPC 2.0)
│       └── storage/          # JSON + SQLite (WAL mode)
│
└── config/
    ├── container.py          # DI container
    └── settings.py           # pydantic-settings + YAML

extension/
├── entrypoints/
│   ├── background.ts         # Service Worker (message routing)
│   ├── offscreen/            # Offscreen Document (SSE handling)
│   ├── popup/                # Popup UI
│   └── sidepanel/            # Side panel UI
└── lib/
    ├── api.ts                # REST client
    └── sse.ts                # SSE streaming client
```

## Test Resources

| Type | Resource |
|------|----------|
| MCP Test Server | `https://example-server.modelcontextprotocol.io/mcp` |
| A2A Samples | [a2aproject/a2a-samples](https://github.com/a2aproject/a2a-samples) |

## Working Guidelines

- Communicate in **Korean** unless specified otherwise
- **Use web search actively** for MCP/A2A/ADK information (standards evolve rapidly)
- Always verify API patterns against official documentation before implementation

## Web Search Verification Protocol

Always verify with web search when:
- Implementing new features (check official docs first)
- Using external libraries (confirm current API)
- Uncertain about file formats, directory structures, or configurations
- Information seems outdated or conflicting

**Principle: Verify, Don't Assume**

## Key References

### Official Documentation
- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [ADK MCP Integration](https://google.github.io/adk-docs/tools-custom/mcp-tools/)
- [ADK A2A Integration](https://google.github.io/adk-docs/a2a/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [A2A Protocol](https://a2a-protocol.org/)

### Development Tools
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [dependency-injector](https://python-dependency-injector.ets-labs.org/)
- [WXT Framework](https://wxt.dev/)
- [Chrome Offscreen Documents](https://developer.chrome.com/blog/Offscreen-Documents-in-Manifest-v3)

## Project Documents

| Document | Purpose |
|----------|---------|
| [docs/architecture.md](docs/architecture.md) | Hexagonal architecture overview |
| [docs/implementation-guide.md](docs/implementation-guide.md) | Implementation patterns and code examples |
| [docs/extension-guide.md](docs/extension-guide.md) | Chrome Extension development guide |
| [docs/feasibility-analysis-2026-01.md](docs/feasibility-analysis-2026-01.md) | Technology stack analysis |

## Archive

- `docs/architecture-fixes.md` - Historical implementation decisions (reference only)
- `docs/architecture-proposal.md` - Initial architecture proposals (reference only)
