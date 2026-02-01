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
from collections.abc import AsyncGenerator
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from google.adk.a2a.utils.agent_to_a2a import to_a2a  # noqa: E402
from google.adk.agents import BaseAgent  # noqa: E402
from google.adk.events import Event  # noqa: E402
from google.adk.runners import InvocationContext  # noqa: E402
from google.genai.types import Content, Part  # noqa: E402


class EchoAgent(BaseAgent):
    """
    Echo agent that returns user input without LLM calls.

    Implements BaseAgent with correct signature for A2A integration testing.
    """

    def __init__(self):
        super().__init__(
            name="echo_agent",
            description=(
                "Echo agent that repeats and mirrors user input. "
                "Use this agent when the user explicitly asks to echo, "
                "repeat, mirror, or copy back their message. "
                "This agent simply returns the exact text provided by the user "
                "without any processing or modification. "
                "Ideal for testing A2A delegation and verification."
            ),
        )

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Main execution method - returns echo response as Event stream.

        Args:
            ctx: Invocation context containing user message

        Yields:
            Event with echo response
        """
        # Extract user message from context
        user_message = ""
        if ctx.user_content:
            if isinstance(ctx.user_content, str):
                user_message = ctx.user_content
            elif isinstance(ctx.user_content, Content):
                # Extract text from Content parts
                for part in ctx.user_content.parts:
                    if hasattr(part, "text") and part.text:
                        user_message += part.text

        # Yield echo response as Event
        echo_text = f"Echo: {user_message}"
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=Content(parts=[Part(text=echo_text)]),
        )


def main():
    """Run echo agent as A2A server"""
    import warnings

    import uvicorn

    # Suppress experimental warnings
    warnings.filterwarnings("ignore", message=".*EXPERIMENTAL.*")

    # Get port from command line (default 9003)
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9003

    # Create echo agent
    agent = EchoAgent()

    # Convert to A2A ASGI app with correct host/port for agent card
    a2a_app = to_a2a(agent, host="127.0.0.1", port=port)

    print(f"Starting Echo A2A Agent on port {port}...", flush=True)
    print(f"Agent Card: http://127.0.0.1:{port}/.well-known/agent.json", flush=True)

    # Run ASGI server
    uvicorn.run(a2a_app, host="127.0.0.1", port=port, log_level="error")


if __name__ == "__main__":
    main()
