# ADK Import Reference (1.23.0+)

## Verified Import Paths

```python
# Agents
from google.adk.agents import LlmAgent

# Tools
from google.adk.tools import BaseToolset, BaseTool

# MCP Tools
from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool import SseServerParams

# LLM (LiteLLM integration)
from google.adk.models.lite_llm import LiteLlm

# A2A
from google.adk.a2a.utils.agent_to_a2a import to_a2a
```

## Common Wrong Imports

```python
# WRONG - old paths or non-existent
from google.adk import Agent              # -> google.adk.agents.LlmAgent
from google.adk.mcp import MCPToolset     # -> google.adk.tools.mcp_tool.MCPToolset
from google.adk.tools import MCPToolset   # -> google.adk.tools.mcp_tool.MCPToolset
from google.adk.llm import LiteLlm       # -> google.adk.models.lite_llm.LiteLlm
```

## Red Flags

| Error | Cause | Fix |
|-------|-------|-----|
| `ImportError: cannot import name 'X'` | API renamed/removed | Web search latest ADK docs |
| `DeprecationWarning` | Migration needed | Check PyPI changelog |
| `TypeError: unexpected keyword argument` | Parameter changed | Re-verify API signature |

When encountering any import error, **immediately web search** `site:google.github.io/adk-docs` or `site:pypi.org/project/google-adk` for the latest API.
