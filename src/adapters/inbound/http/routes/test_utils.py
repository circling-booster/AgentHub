"""DEV_MODE 전용 테스트 유틸리티 엔드포인트

E2E 테스트 격리를 위한 데이터 초기화 API
프로덕션 환경에서는 절대 사용하지 않음 (DEV_MODE=true에서만 활성화)
"""

import asyncio
import logging

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from src.config.container import Container

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["Test Utils"])

# Cleanup 타임아웃 (초) - 블로킹 방지
UNREGISTER_TIMEOUT = 2.0
CONVERSATION_DELETE_TIMEOUT = 1.0  # 대화 삭제 타임아웃


@router.post("/reset-data")
@inject
async def reset_test_data(
    registry_service=Depends(Provide[Container.registry_service]),
    conversation_storage=Depends(Provide[Container.conversation_storage]),
    endpoint_storage=Depends(Provide[Container.endpoint_storage]),
):
    """
    테스트 데이터 전체 초기화 (강제 삭제 모드)

    E2E 테스트 간 상태를 초기화하여 테스트 격리 보장
    - MCP 서버 전체 해제 (타임아웃 시 강제 삭제)
    - A2A 에이전트 전체 해제 (타임아웃 시 강제 삭제)
    - 대화 전체 삭제

    Note:
        unregister_endpoint가 블로킹될 수 있으므로 타임아웃 적용.
        타임아웃 시 storage에서 직접 삭제하여 테스트 격리 보장.

    Returns:
        dict: {"status": "reset_complete", "cleared": {...}}
    """
    cleared = {"mcp_servers": 0, "a2a_agents": 0, "conversations": 0}
    errors = []
    logger.debug("reset-data: starting cleanup")

    # MCP 서버 전체 해제 (타임아웃 시 강제 삭제)
    logger.debug("reset-data: listing MCP endpoints")
    mcp_endpoints = await registry_service.list_endpoints(type_filter="mcp")
    logger.debug(f"reset-data: found {len(mcp_endpoints)} MCP endpoints")
    for endpoint in mcp_endpoints:
        try:
            # 타임아웃 적용 - 블로킹 방지
            await asyncio.wait_for(
                registry_service.unregister_endpoint(endpoint.id),
                timeout=UNREGISTER_TIMEOUT,
            )
            cleared["mcp_servers"] += 1
        except asyncio.TimeoutError:
            # 타임아웃 시 storage에서 직접 삭제
            await endpoint_storage.delete_endpoint(endpoint.id)
            cleared["mcp_servers"] += 1
            errors.append(f"MCP {endpoint.id}: timeout, force deleted")
        except Exception as e:
            errors.append(f"MCP {endpoint.id}: {str(e)}")

    # A2A 에이전트 전체 해제 (타임아웃 시 강제 삭제)
    logger.debug("reset-data: listing A2A endpoints")
    a2a_endpoints = await registry_service.list_endpoints(type_filter="a2a")
    logger.debug(f"reset-data: found {len(a2a_endpoints)} A2A endpoints")
    for endpoint in a2a_endpoints:
        try:
            await asyncio.wait_for(
                registry_service.unregister_endpoint(endpoint.id),
                timeout=UNREGISTER_TIMEOUT,
            )
            cleared["a2a_agents"] += 1
        except asyncio.TimeoutError:
            await endpoint_storage.delete_endpoint(endpoint.id)
            cleared["a2a_agents"] += 1
            errors.append(f"A2A {endpoint.id}: timeout, force deleted")
        except Exception as e:
            errors.append(f"A2A {endpoint.id}: {str(e)}")

    # 대화 삭제 (타임아웃 적용)
    logger.debug("reset-data: listing conversations")
    conversations = await conversation_storage.list_conversations(limit=1000)
    logger.debug(f"reset-data: found {len(conversations)} conversations to delete")
    for conv in conversations:
        try:
            await asyncio.wait_for(
                conversation_storage.delete_conversation(conv.id),
                timeout=CONVERSATION_DELETE_TIMEOUT,
            )
            cleared["conversations"] += 1
        except asyncio.TimeoutError:
            errors.append(f"Conv {conv.id}: timeout")
        except Exception as e:
            errors.append(f"Conv {conv.id}: {str(e)}")

    result = {"status": "reset_complete", "cleared": cleared}
    if errors:
        result["errors"] = errors
        logger.warning(f"reset-data: completed with errors: {errors}")
    else:
        logger.debug(f"reset-data: completed successfully, cleared={cleared}")

    return result


@router.get("/state")
@inject
async def get_test_state(
    registry_service=Depends(Provide[Container.registry_service]),
    conversation_storage=Depends(Provide[Container.conversation_storage]),
):
    """
    현재 상태 조회

    테스트 디버깅을 위한 상태 확인 엔드포인트
    - MCP 서버 수
    - A2A 에이전트 수
    - 대화 수

    Returns:
        dict: {"mcp_servers": int, "a2a_agents": int, "conversations": int}
    """
    mcp_endpoints = await registry_service.list_endpoints(type_filter="mcp")
    a2a_endpoints = await registry_service.list_endpoints(type_filter="a2a")
    conversations = await conversation_storage.list_conversations(limit=1000)

    return {
        "mcp_servers": len(mcp_endpoints),
        "a2a_agents": len(a2a_endpoints),
        "conversations": len(conversations),
    }
