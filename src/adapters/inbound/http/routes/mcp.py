"""MCP Management Routes

MCP 서버 동적 등록/해제 및 도구 관리 API
"""

import logging

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status
from fastapi.responses import Response

from src.adapters.inbound.http.schemas.mcp import (
    AuthConfigSchema,
    McpServerResponse,
    RegisterMcpServerRequest,
    ToolResponse,
)
from src.config.container import Container
from src.domain.entities.auth_config import AuthConfig
from src.domain.entities.endpoint import EndpointType
from src.domain.exceptions import EndpointNotFoundError
from src.domain.services.registry_service import RegistryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mcp", tags=["MCP"])


def _convert_auth_schema_to_entity(schema: AuthConfigSchema | None) -> AuthConfig | None:
    """
    Pydantic AuthConfigSchema를 Domain AuthConfig로 변환

    Args:
        schema: AuthConfigSchema (API 요청)

    Returns:
        AuthConfig domain entity (None이면 None 반환)
    """
    if not schema:
        return None

    return AuthConfig(
        auth_type=schema.auth_type,
        headers=schema.headers,
        api_key=schema.api_key,
        api_key_header=schema.api_key_header,
        api_key_prefix=schema.api_key_prefix,
        oauth2_client_id=schema.oauth2_client_id,
        oauth2_client_secret=schema.oauth2_client_secret,
        oauth2_token_url=schema.oauth2_token_url,
        oauth2_authorize_url=schema.oauth2_authorize_url,
        oauth2_scope=schema.oauth2_scope,
        oauth2_access_token=schema.oauth2_access_token,
        oauth2_refresh_token=schema.oauth2_refresh_token,
        oauth2_token_expires_at=schema.oauth2_token_expires_at,
    )


@router.post("/servers", response_model=McpServerResponse, status_code=status.HTTP_201_CREATED)
@inject
async def register_mcp_server(
    body: RegisterMcpServerRequest,
    registry: RegistryService = Depends(Provide[Container.registry_service]),
) -> McpServerResponse:
    """
    MCP 서버 등록

    Args:
        body: MCP 서버 URL 및 이름
        registry: RegistryService (DI)

    Returns:
        등록된 MCP 서버 정보

    Raises:
        400: 이미 등록된 URL
        422: 유효하지 않은 URL
        502: MCP 서버 연결 실패
    """
    # URL 정규화 (HttpUrl → str)
    url_str = str(body.url)

    # 기본 이름 생성 (없으면)
    server_name = body.name or f"MCP Server ({url_str})"

    # AuthConfig 변환 (Pydantic → Domain Entity)
    auth_config = _convert_auth_schema_to_entity(body.auth)

    # 도메인 서비스 호출 (auth_config 전달)
    endpoint = await registry.register_endpoint(
        url=url_str, name=server_name, auth_config=auth_config
    )

    # 응답 변환
    return McpServerResponse(
        id=endpoint.id,
        url=endpoint.url,
        name=endpoint.name,
        type=endpoint.type,
        enabled=endpoint.enabled,
        registered_at=endpoint.registered_at,
    )


@router.get("/servers", response_model=list[McpServerResponse])
@inject
async def list_mcp_servers(
    registry: RegistryService = Depends(Provide[Container.registry_service]),
) -> list[McpServerResponse]:
    """
    등록된 MCP 서버 목록 조회

    Returns:
        MCP 서버 목록
    """
    endpoints = await registry.list_endpoints(type_filter=EndpointType.MCP)

    return [
        McpServerResponse(
            id=endpoint.id,
            url=endpoint.url,
            name=endpoint.name,
            type=endpoint.type,
            enabled=endpoint.enabled,
            registered_at=endpoint.registered_at,
            tools=[
                ToolResponse(
                    name=tool.name,
                    description=tool.description,
                    input_schema=tool.input_schema,
                )
                for tool in endpoint.tools
            ],
        )
        for endpoint in endpoints
    ]


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def remove_mcp_server(
    server_id: str,
    registry: RegistryService = Depends(Provide[Container.registry_service]),
) -> Response:
    """
    MCP 서버 해제

    Args:
        server_id: 서버 ID
        registry: RegistryService (DI)

    Raises:
        404: 존재하지 않는 서버 ID
    """
    success = await registry.unregister_endpoint(server_id)

    if not success:
        raise EndpointNotFoundError(f"Endpoint not found: {server_id}")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/servers/{server_id}/tools", response_model=list[ToolResponse])
@inject
async def get_server_tools(
    server_id: str,
    registry: RegistryService = Depends(Provide[Container.registry_service]),
) -> list[ToolResponse]:
    """
    특정 MCP 서버의 도구 목록 조회

    Args:
        server_id: 서버 ID
        registry: RegistryService (DI)

    Returns:
        도구 목록

    Raises:
        404: 존재하지 않는 서버 ID
    """
    tools = await registry.get_endpoint_tools(server_id)

    return [
        ToolResponse(name=tool.name, description=tool.description, input_schema=tool.input_schema)
        for tool in tools
    ]
