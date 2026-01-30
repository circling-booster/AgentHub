"""A2A Management Routes

A2A 에이전트 동적 등록/해제 및 관리 API
"""

import logging

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status
from fastapi.responses import Response

from src.adapters.inbound.http.schemas.a2a import (
    A2aAgentResponse,
    RegisterA2aAgentRequest,
)
from src.config.container import Container
from src.domain.entities.endpoint import EndpointType
from src.domain.exceptions import EndpointNotFoundError
from src.domain.services.registry_service import RegistryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/a2a", tags=["A2A"])


@router.post("/agents", response_model=A2aAgentResponse, status_code=status.HTTP_201_CREATED)
@inject
async def register_a2a_agent(
    body: RegisterA2aAgentRequest,
    registry: RegistryService = Depends(Provide[Container.registry_service]),
) -> A2aAgentResponse:
    """
    A2A 에이전트 등록

    Args:
        body: A2A 에이전트 URL 및 이름
        registry: RegistryService (DI)

    Returns:
        등록된 A2A 에이전트 정보

    Raises:
        400: 이미 등록된 URL
        422: 유효하지 않은 URL
        502: A2A 에이전트 연결 실패
    """
    # URL 정규화 (HttpUrl → str, trailing slash 제거)
    url_str = str(body.url).rstrip("/")

    # 기본 이름 생성 (없으면)
    agent_name = body.name or f"A2A Agent ({url_str})"

    # 도메인 서비스 호출 - A2A 타입으로 등록
    endpoint = await registry.register_endpoint(
        url=url_str, name=agent_name, endpoint_type=EndpointType.A2A
    )

    # 응답 변환
    return A2aAgentResponse(
        id=endpoint.id,
        url=endpoint.url,
        name=endpoint.name,
        type=endpoint.type.value,
        enabled=endpoint.enabled,
        agent_card=endpoint.agent_card,
        registered_at=endpoint.registered_at.isoformat(),
    )


@router.get("/agents", response_model=list[A2aAgentResponse])
@inject
async def list_a2a_agents(
    registry: RegistryService = Depends(Provide[Container.registry_service]),
) -> list[A2aAgentResponse]:
    """
    등록된 A2A 에이전트 목록 조회

    Returns:
        A2A 에이전트 목록 (type="a2a"만 필터링)
    """
    # A2A 타입만 필터링
    endpoints = await registry.list_endpoints(type_filter=EndpointType.A2A)

    return [
        A2aAgentResponse(
            id=ep.id,
            url=ep.url,
            name=ep.name,
            type=ep.type.value,
            enabled=ep.enabled,
            agent_card=ep.agent_card,
            registered_at=ep.registered_at.isoformat(),
        )
        for ep in endpoints
    ]


@router.get("/agents/{agent_id}", response_model=A2aAgentResponse)
@inject
async def get_a2a_agent(
    agent_id: str,
    registry: RegistryService = Depends(Provide[Container.registry_service]),
) -> A2aAgentResponse:
    """
    특정 A2A 에이전트 상세 조회

    Args:
        agent_id: 에이전트 ID

    Returns:
        A2A 에이전트 정보

    Raises:
        404: 에이전트를 찾을 수 없음
    """
    endpoint = await registry.get_endpoint(agent_id)

    if endpoint is None:
        raise EndpointNotFoundError(f"A2A agent not found: {agent_id}")

    return A2aAgentResponse(
        id=endpoint.id,
        url=endpoint.url,
        name=endpoint.name,
        type=endpoint.type.value,
        enabled=endpoint.enabled,
        agent_card=endpoint.agent_card,
        registered_at=endpoint.registered_at.isoformat(),
    )


@router.get("/agents/{agent_id}/card")
@inject
async def get_a2a_agent_card(
    agent_id: str,
    registry: RegistryService = Depends(Provide[Container.registry_service]),
) -> dict:
    """
    특정 A2A 에이전트의 Agent Card 조회

    Args:
        agent_id: 에이전트 ID

    Returns:
        Agent Card JSON

    Raises:
        404: 에이전트를 찾을 수 없음
    """
    endpoint = await registry.get_endpoint(agent_id)

    if endpoint is None:
        raise EndpointNotFoundError(f"A2A agent not found: {agent_id}")

    if endpoint.agent_card is None:
        return {}

    return endpoint.agent_card


@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def unregister_a2a_agent(
    agent_id: str,
    registry: RegistryService = Depends(Provide[Container.registry_service]),
) -> Response:
    """
    A2A 에이전트 등록 해제

    Args:
        agent_id: 에이전트 ID

    Returns:
        204 No Content

    Raises:
        404: 에이전트를 찾을 수 없음
    """
    success = await registry.unregister_endpoint(agent_id)

    if not success:
        raise EndpointNotFoundError(f"A2A agent not found: {agent_id}")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
