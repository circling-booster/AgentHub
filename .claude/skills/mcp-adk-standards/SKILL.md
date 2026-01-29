---
name: mcp-adk-standards
description: "Google ADK and MCP implementation standards for AgentHub. Use when (1) writing ADK adapter code with google.adk.* imports, (2) implementing MCPToolset async patterns (get_tools, connection), (3) creating or modifying DynamicToolset (BaseToolset inheritance), (4) configuring MCP transport (Streamable HTTP or SSE), (5) implementing Async Factory pattern for ADK agents, (6) any code in src/adapters/outbound/adk/. Enforces latest API signatures via mandatory web search verification before writing ADK/MCP code."
---

# MCP & ADK Standards

## CRITICAL: Web Search Verification Protocol

ADK, MCP, and LiteLLM APIs evolve rapidly. **You MUST web search before writing any ADK/MCP code.**

### Mandatory Search Points

| When | Search Query | Purpose |
|------|-------------|---------|
| **Before implementing** | `site:google.github.io/adk-docs {topic}` | Verify API signatures |
| **Before importing** | `google-adk pypi changelog 2026` | Check breaking changes |
| **On ImportError** | `google.adk.{module} import path` | Find renamed modules |
| **MCP transport** | `site:modelcontextprotocol.io transport specification` | Verify transport spec |

### Search-Then-Code Rule

```
1. Web search: latest API signature / import path
2. Compare with references/adk-imports.md
3. If different -> update reference, use latest
4. If same -> proceed with confidence
```

**NEVER guess an import path or API parameter. When uncertain, search first.**

## ADK Import Paths

Verified paths for ADK 1.23.0+. **Always re-verify via web search before use.**

```python
from google.adk.agents import LlmAgent
from google.adk.tools import BaseToolset, BaseTool
from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool import StreamableHTTPConnectionParams, SseServerParams
from google.adk.models.lite_llm import LiteLlm
from google.adk.a2a.utils.agent_to_a2a import to_a2a
```

For full import reference and common mistakes: see [references/adk-imports.md](references/adk-imports.md)

## DynamicToolset Pattern (BaseToolset)

DynamicToolset inherits `BaseToolset` for native ADK Agent integration.

### Required Structure

```python
# src/adapters/outbound/adk/dynamic_toolset.py
from google.adk.tools import BaseToolset, BaseTool
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams, SseServerParams

class DynamicToolset(BaseToolset):
    """ADK BaseToolset subclass for dynamic MCP tool management."""

    def __init__(self, cache_ttl_seconds: int = 300):
        super().__init__()
        self._mcp_toolsets: dict[str, MCPToolset] = {}
        self._tool_cache: dict[str, list[BaseTool]] = {}

    async def get_tools(self, readonly_context=None) -> list[BaseTool]:
        """Called by ADK Agent each turn. Return all active tools."""
        ...

    async def add_mcp_server(self, endpoint) -> list:
        """Connect MCP server (Streamable HTTP first, SSE fallback)."""
        ...

    async def close(self) -> None:
        """Cleanup all MCP connections."""
        ...
```

### Key Constraints

| Constraint | Value | Reason |
|-----------|-------|--------|
| `MAX_ACTIVE_TOOLS` | 30 | Context explosion prevention |
| `cache_ttl` | 300s | Avoid repeated MCP server queries |
| Transport priority | Streamable HTTP > SSE | MCP spec recommendation |

## MCPToolset Async Pattern

`MCPToolset.get_tools()` is async. Never call in sync constructors.

### Async Factory Pattern

```python
class AdkOrchestratorAdapter(OrchestratorPort):
    def __init__(self, model: str, dynamic_toolset: DynamicToolset):
        self._agent: LlmAgent | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Call in FastAPI lifespan, NOT in constructor."""
        if self._initialized:
            return
        await self._dynamic_toolset.get_tools()  # async!
        self._agent = LlmAgent(
            model=LiteLlm(model=self._model_name),
            name="agenthub-agent",
            tools=[self._dynamic_toolset],
        )
        self._initialized = True
```

Integrate via FastAPI lifespan:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await orchestrator.initialize()
    yield
    await orchestrator.close()
```

## MCP Transport

Streamable HTTP first, SSE fallback for legacy servers.

For full transport patterns and auto-fallback code: see [references/mcp-transport.md](references/mcp-transport.md)

### Quick Reference

```python
# Streamable HTTP (preferred)
StreamableHTTPConnectionParams(url=url, timeout=120)

# SSE (legacy fallback)
SseServerParams(url=url, timeout=120)
```

## Hexagonal Boundary Reminder

ADK/MCP code lives **only** in `src/adapters/outbound/adk/`. Domain layer must never import `google.adk.*`.

```
src/domain/          -> pure Python, NO adk imports
src/adapters/outbound/adk/  -> google.adk.* imports OK here
```
