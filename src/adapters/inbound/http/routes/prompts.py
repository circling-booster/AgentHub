"""Prompts API Routes

SDK Track: MCP Prompts 관리 (list, get)
"""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from src.adapters.inbound.http.schemas.prompts import (
    PromptContentRequest,
    PromptContentResponse,
    PromptListResponse,
    PromptTemplateSchema,
)
from src.config.container import Container
from src.domain.exceptions import EndpointNotFoundError, PromptNotFoundError
from src.domain.services.prompt_service import PromptService

router = APIRouter(tags=["prompts"])


@router.get("/api/mcp/servers/{endpoint_id}/prompts", response_model=PromptListResponse)
@inject
async def list_prompts(
    endpoint_id: str,
    prompt_service: PromptService = Depends(Provide[Container.prompt_service]),
):
    """프롬프트 목록 조회

    Args:
        endpoint_id: MCP 서버 엔드포인트 ID
        prompt_service: PromptService 인스턴스 (DI)

    Returns:
        PromptListResponse: 프롬프트 목록

    Raises:
        HTTPException: 404 - 엔드포인트를 찾을 수 없음
    """
    try:
        prompts = await prompt_service.list_prompts(endpoint_id)
        return PromptListResponse(prompts=[PromptTemplateSchema.from_entity(p) for p in prompts])
    except EndpointNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/api/mcp/servers/{endpoint_id}/prompts/{name}", response_model=PromptContentResponse)
@inject
async def get_prompt(
    endpoint_id: str,
    name: str,
    request_body: PromptContentRequest,
    prompt_service: PromptService = Depends(Provide[Container.prompt_service]),
):
    """프롬프트 렌더링

    Args:
        endpoint_id: MCP 서버 엔드포인트 ID
        name: 프롬프트 이름
        request_body: 프롬프트 렌더링 요청 (arguments)
        prompt_service: PromptService 인스턴스 (DI)

    Returns:
        PromptContentResponse: 렌더링된 프롬프트 콘텐츠

    Raises:
        HTTPException: 404 - 엔드포인트 또는 프롬프트를 찾을 수 없음
    """
    try:
        result = await prompt_service.get_prompt(endpoint_id, name, request_body.arguments)
        return PromptContentResponse(content=result)
    except (EndpointNotFoundError, PromptNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
