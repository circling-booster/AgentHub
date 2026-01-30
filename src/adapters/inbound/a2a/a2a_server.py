"""A2A Server Exposure - AgentHub를 A2A 프로토콜로 노출

Google ADK의 to_a2a() 유틸리티를 사용하여 LlmAgent를 A2A 서버로 변환
"""

import logging
from typing import Any

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import LlmAgent

logger = logging.getLogger(__name__)


def create_a2a_app(agent: LlmAgent, port: int = 8000) -> Any:
    """
    LlmAgent를 A2A ASGI app으로 변환

    Args:
        agent: ADK LlmAgent 인스턴스
        port: A2A 서버 포트 (기본 8000)

    Returns:
        ASGI app (FastAPI mount 가능)

    Example:
        ```python
        from src.adapters.inbound.a2a.a2a_server import create_a2a_app

        # Container에서 orchestrator adapter의 agent 가져오기
        orchestrator = container.orchestrator_adapter()
        await orchestrator.initialize()
        agent = orchestrator._agent

        # A2A app 생성 및 마운트
        a2a_app = create_a2a_app(agent, port=8000)
        main_app.mount("", a2a_app)  # Root에 마운트하여 /.well-known 경로 노출
        ```
    """
    logger.info(f"Creating A2A app for agent: {agent.name}")

    # ADK to_a2a()를 사용하여 ASGI app 생성
    # Agent Card는 자동 생성되어 /.well-known/agent-card.json에 노출됨
    a2a_app = to_a2a(agent, port=port)

    logger.info(
        "A2A app created successfully. Agent Card available at /.well-known/agent-card.json"
    )

    return a2a_app
