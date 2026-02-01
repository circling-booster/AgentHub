#!/usr/bin/env python
"""A2A Math Agent for Testing

ADK LlmAgent-based math specialist that uses LLM for actual reasoning.
Can be run as a standalone A2A server for integration tests.

Design Decision (ADR-9): Uses ADK LlmAgent instead of LangGraph.
LangGraph agents should be integrated via A2A protocol as independent
servers, not embedded. For testing purposes, ADK LlmAgent is sufficient.

Usage:
    python tests/fixtures/a2a_agents/math_agent.py [port]

Example:
    python tests/fixtures/a2a_agents/math_agent.py 9002
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Run math agent as A2A server"""
    import warnings

    import uvicorn
    from google.adk.a2a.utils.agent_to_a2a import to_a2a
    from google.adk.agents import LlmAgent
    from google.adk.models.lite_llm import LiteLlm

    # Suppress experimental warnings
    warnings.filterwarnings("ignore", message=".*EXPERIMENTAL.*")

    # Get port from command line (default 9002)
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9002

    # Create math specialist agent using LLM
    agent = LlmAgent(
        name="math_agent",
        model=LiteLlm(model="openai/gpt-4o-mini"),
        description=(
            "Mathematics specialist agent that solves math problems. "
            "Delegate to this agent when the user asks math questions, "
            "calculations, arithmetic, algebra, or calculus problems. "
            "This agent uses an LLM to provide step-by-step solutions."
        ),
        instruction=(
            "You are a mathematics specialist. Solve math problems accurately "
            "with step-by-step explanations. Handle arithmetic, algebra, "
            "calculus, and other mathematical topics."
        ),
    )

    # Convert to A2A ASGI app
    a2a_app = to_a2a(agent, host="127.0.0.1", port=port)

    print(f"Starting Math A2A Agent on port {port}...", flush=True)
    print(f"Agent Card: http://127.0.0.1:{port}/.well-known/agent.json", flush=True)

    # Run ASGI server
    uvicorn.run(a2a_app, host="127.0.0.1", port=port, log_level="error")


if __name__ == "__main__":
    main()
