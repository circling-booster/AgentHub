#!/usr/bin/env python
"""A2A Echo Agent for Testing

ADK-based echo agent that returns user input without LLM.
Can be run as a standalone A2A server for integration tests.

Usage:
    python tests/fixtures/a2a_agents/echo_agent.py [port]

Example:
    python tests/fixtures/a2a_agents/echo_agent.py 9001
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from google.adk.a2a.utils.agent_to_a2a import to_a2a  # noqa: E402
from google.adk.agents import BaseAgent  # noqa: E402


class EchoAgent(BaseAgent):
    """
    Echo agent that returns user input without LLM calls.

    Uses callback pattern to bypass LLM execution entirely.
    """

    def __init__(self):
        super().__init__(
            name="echo_agent",
            description="A simple echo agent that returns user input for testing A2A integration",
        )

    async def _run_async_impl(self, request: str) -> str:
        """
        Main execution method - returns echo response.

        Args:
            request: User input string

        Returns:
            Echo response with prefix
        """
        return f"Echo: {request}"


def main():
    """Run echo agent as A2A server"""
    import warnings

    import uvicorn

    # Suppress experimental warnings
    warnings.filterwarnings("ignore", message=".*EXPERIMENTAL.*")

    # Get port from command line (default 9001)
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9001

    # Create echo agent
    agent = EchoAgent()

    # Convert to A2A ASGI app (don't pass port here)
    a2a_app = to_a2a(agent)

    print(f"Starting Echo A2A Agent on port {port}...", flush=True)
    print(f"Agent Card: http://127.0.0.1:{port}/.well-known/agent.json", flush=True)
    print(f"Health Check: http://127.0.0.1:{port}/health", flush=True)

    # Run ASGI server
    uvicorn.run(a2a_app, host="127.0.0.1", port=port, log_level="error")


if __name__ == "__main__":
    main()
