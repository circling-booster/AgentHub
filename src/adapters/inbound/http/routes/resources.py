"""Resources API Routes

SDK Track: MCP Resources 관리 (list, read)
"""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from src.adapters.inbound.http.schemas.resources import (
    ResourceContentSchema,
    ResourceListResponse,
    ResourceSchema,
)
from src.config.container import Container
from src.domain.exceptions import EndpointNotFoundError, ResourceNotFoundError
from src.domain.services.resource_service import ResourceService

router = APIRouter(tags=["resources"])


@router.get("/api/mcp/servers/{endpoint_id}/resources", response_model=ResourceListResponse)
@inject
async def list_resources(
    endpoint_id: str,
    resource_service: ResourceService = Depends(Provide[Container.resource_service]),
):
    """리소스 목록 조회

    Args:
        endpoint_id: MCP 서버 엔드포인트 ID
        resource_service: ResourceService 인스턴스 (DI)

    Returns:
        ResourceListResponse: 리소스 목록

    Raises:
        HTTPException: 404 - 엔드포인트를 찾을 수 없음
    """
    try:
        resources = await resource_service.list_resources(endpoint_id)
        return ResourceListResponse(resources=[ResourceSchema.from_entity(r) for r in resources])
    except EndpointNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/api/mcp/servers/{endpoint_id}/resources/{uri:path}", response_model=ResourceContentSchema
)
@inject
async def read_resource(
    endpoint_id: str,
    uri: str,
    resource_service: ResourceService = Depends(Provide[Container.resource_service]),
):
    """리소스 콘텐츠 읽기

    Args:
        endpoint_id: MCP 서버 엔드포인트 ID
        uri: 리소스 URI (path parameter로 전체 URI 수용)
        resource_service: ResourceService 인스턴스 (DI)

    Returns:
        ResourceContentSchema: 리소스 콘텐츠 (text 또는 blob)

    Raises:
        HTTPException: 404 - 엔드포인트 또는 리소스를 찾을 수 없음
    """
    try:
        content = await resource_service.read_resource(endpoint_id, uri)
        return ResourceContentSchema.from_entity(content)
    except (EndpointNotFoundError, ResourceNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
