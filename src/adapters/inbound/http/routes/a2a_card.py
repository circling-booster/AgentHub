"""A2A Agent Card Endpoint

AgentHub를 A2A 프로토콜로 노출하기 위한 Agent Card 제공
"""

import logging

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)

router = APIRouter(tags=["A2A"])


@router.get("/.well-known/agent-card.json")
async def get_agent_card(request: Request):
    """
    A2A Agent Card 제공

    A2A 프로토콜 스펙에 따라 AgentHub의 Agent Card를 제공합니다.
    다른 A2A 에이전트가 이 엔드포인트를 통해 AgentHub의 capabilities를 확인할 수 있습니다.

    Returns:
        Agent Card JSON

    A2A Spec Reference:
    - Agent Card는 /.well-known/agent.json 또는 /.well-known/agent-card.json에 위치
    - 필수 필드: agentId (또는 agent_id), name, skills (또는 capabilities)
    """
    # FastAPI Request에서 Container 가져오기
    container = request.app.container

    # Container에서 orchestrator 인스턴스 가져오기
    orchestrator = container.orchestrator_adapter()

    # Orchestrator의 agent 정보 가져오기
    agent = orchestrator._agent

    if agent is None:
        logger.error("Orchestrator agent not initialized")
        # 초기화되지 않은 경우 최소 카드 반환
        return {
            "agentId": "agenthub",
            "name": "AgentHub",
            "description": "MCP + A2A Integrated Agent System",
            "skills": [],
        }

    # Agent Card 생성
    # ADK Agent의 name, instruction을 기반으로 Card 구성
    agent_card = {
        "agentId": "agenthub",
        "name": agent.name or "AgentHub",
        "description": orchestrator._instruction or "AI agent with tool capabilities",
        "skills": [
            {
                "name": "chat",
                "description": "Conversational AI with tool calling capabilities",
            },
            {
                "name": "tool_execution",
                "description": "Execute MCP tools dynamically registered by users",
            },
        ],
        "endpoints": {
            "a2a": {
                "protocol": "a2a",
                "url": "/.well-known/agent-card.json",
            }
        },
        "version": "1.0.0",
    }

    logger.info(f"Agent Card served for agent: {agent.name}")
    return agent_card
