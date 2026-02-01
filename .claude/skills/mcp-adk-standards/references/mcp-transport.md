# MCP Transport Patterns

## Transport Priority

1. **Streamable HTTP** (recommended, 2025-03+)
2. **SSE** (legacy fallback)

## Streamable HTTP Connection

```python
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams

toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://127.0.0.1:9000/mcp",
        timeout=120,
    ),
)
```

## SSE Fallback Connection

```python
from google.adk.tools.mcp_tool import MCPToolset, SseServerParams

toolset = MCPToolset(
    connection_params=SseServerParams(
        url="https://example-server.modelcontextprotocol.io/sse",
        timeout=120,
    ),
)
```

## Auto-Fallback Pattern

Try Streamable HTTP first, fall back to SSE on failure:

```python
async def _create_mcp_toolset(self, url: str) -> MCPToolset:
    # 1. Streamable HTTP (recommended)
    try:
        toolset = MCPToolset(
            connection_params=StreamableHTTPConnectionParams(url=url, timeout=120),
        )
        await toolset.get_tools()  # connection test
        return toolset
    except Exception:
        pass

    # 2. SSE fallback (legacy)
    try:
        toolset = MCPToolset(
            connection_params=SseServerParams(url=url, timeout=120),
        )
        await toolset.get_tools()
        return toolset
    except Exception as e:
        raise ConnectionError(f"Failed to connect to MCP server: {url}") from e
```

## MCP Test Server

Integration testing endpoint: `http://127.0.0.1:9000/mcp`

## Spec References

- [MCP Transports](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports)
- [ADK MCP Integration](https://google.github.io/adk-docs/tools-custom/mcp-tools/)
