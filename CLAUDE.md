# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

**AgentHub** is a Google ADK-based Agent System that integrates MCP servers and A2A agents into a single interface.

- **Project Name**: AgentHub (formerly FHLY)
- **Language**: Python 3.10+
- **License**: Apache 2.0
- **Target Users**: Developers (primary)

## Core Concept

```
Chrome Extension → AgentHub API Server (ADK) → MCP Servers / A2A Agents
```

- **Chrome Extension**: Main interface for user interaction
- **API Server**: Python backend running on localhost:8000
- **Dynamic Registration**: Users can add/remove MCP/A2A endpoints via UI

## Technical Stack

| Component | Technology |
|-----------|------------|
| Agent Framework | Google ADK 1.23.0+ |
| LLM Integration | LiteLLM (Claude, GPT-4, Gemini, etc.) |
| MCP Transport | Streamable HTTP |
| A2A Protocol | HTTP/JSON-RPC |
| Extension | JavaScript/TypeScript |

## ADK Code Patterns

### Correct Import Structure

```python
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.models.lite_llm import LiteLlm
from google.adk.a2a.utils.agent_to_a2a import to_a2a
```

### Important Notes

- **Google Built-in Tools** (SearchTool, CodeExecutionTool, etc.) only work with **Gemini models**
- Non-Gemini models (Claude, GPT-4) cannot use Google built-in tools
- Use **Streamable HTTP** for MCP connections (not SSE)

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

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [ADK MCP Integration](https://google.github.io/adk-docs/tools-custom/mcp-tools/)
- [ADK A2A Integration](https://google.github.io/adk-docs/a2a/)
- [ADK LiteLLM](https://google.github.io/adk-docs/agents/models/litellm/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [A2A Protocol](https://a2a-protocol.org/)
- [google-adk (PyPI)](https://pypi.org/project/google-adk/)

## Archive

Legacy documentation is preserved in `_archive/docs/` for historical reference only. Do not use those documents for current development guidance.
