"""
OAuth 2.1 Routes

OAuth Authorization 및 Callback 엔드포인트
"""

import logging
import secrets
import time

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from src.adapters.outbound.oauth.oauth_adapter import HttpxOAuthAdapter
from src.config.container import Container
from src.domain.exceptions import OAuthStateValidationError, OAuthTokenExchangeError
from src.domain.services.oauth_service import OAuthService
from src.domain.services.registry_service import RegistryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oauth", tags=["OAuth"])

# 임시 state 저장소 (메모리)
# TODO Phase 5-B 완료 후: Redis 또는 암호화된 session storage로 대체
_state_storage: dict[str, tuple[str, float]] = {}  # {state: (server_id, expires_at)}
STATE_EXPIRY_SECONDS = 300  # 5분


def _generate_state(server_id: str) -> str:
    """CSRF 방지용 state 토큰 생성"""
    state = secrets.token_urlsafe(32)
    _state_storage[state] = (server_id, time.time() + STATE_EXPIRY_SECONDS)
    return state


def _validate_and_consume_state(state: str) -> str:
    """State 검증 및 소비 (1회 사용)"""
    if state not in _state_storage:
        raise OAuthStateValidationError("Invalid or expired state parameter")

    server_id, expires_at = _state_storage.pop(state)

    if time.time() > expires_at:
        raise OAuthStateValidationError("State parameter expired")

    return server_id


@router.get("/authorize")
@inject
async def oauth_authorize(
    server_id: str,
    registry: RegistryService = Depends(Provide[Container.registry_service]),
):
    """
    OAuth Authorization 시작

    1. State 토큰 생성 (CSRF 방지)
    2. Authorization URL 생성
    3. OAuth Provider로 리다이렉트

    Query Params:
        server_id: MCP 서버 ID

    Returns:
        302 Redirect to OAuth Provider
    """
    # 엔드포인트 조회
    endpoint = await registry.get_endpoint(server_id)
    if not endpoint.auth_config or endpoint.auth_config.auth_type != "oauth2":
        raise HTTPException(status_code=400, detail="OAuth not configured for this server")

    # State 생성
    state = _generate_state(server_id)

    # Authorization URL 생성
    oauth_service = OAuthService()
    authorize_url = oauth_service.build_authorize_url(endpoint.auth_config, state)

    logger.info(f"OAuth authorize initiated for server {server_id}, redirecting to {authorize_url}")

    # OAuth Provider로 리다이렉트
    return RedirectResponse(url=authorize_url, status_code=302)


@router.get("/callback")
@inject
async def oauth_callback(
    code: str,
    state: str,
    registry: RegistryService = Depends(Provide[Container.registry_service]),
):
    """
    OAuth Callback 처리

    1. State 검증 (CSRF 방지)
    2. Authorization Code → Access Token 교환
    3. AuthConfig 업데이트
    4. 성공 페이지 반환

    Query Params:
        code: Authorization code (OAuth provider에서 발급)
        state: State token (검증용)

    Returns:
        200 Success HTML 페이지
    """
    try:
        # 1. State 검증
        server_id = _validate_and_consume_state(state)

    except OAuthStateValidationError as e:
        logger.warning(f"OAuth callback state validation failed: {e.message}")
        raise HTTPException(status_code=400, detail=f"Invalid state: {e.message}")

    try:
        # 2. 엔드포인트 조회
        endpoint = await registry.get_endpoint(server_id)
        if not endpoint.auth_config or endpoint.auth_config.auth_type != "oauth2":
            raise HTTPException(status_code=400, detail="OAuth not configured")

        # 3. Authorization Code → Access Token 교환
        oauth_adapter = HttpxOAuthAdapter()
        token_response = await oauth_adapter.exchange_code_for_token(
            code=code,
            auth_config=endpoint.auth_config,
            redirect_uri="http://localhost:8000/oauth/callback",
        )

        # 4. AuthConfig 업데이트
        endpoint.auth_config.oauth2_access_token = token_response.access_token
        if token_response.refresh_token:
            endpoint.auth_config.oauth2_refresh_token = token_response.refresh_token
        endpoint.auth_config.oauth2_token_expires_at = time.time() + token_response.expires_in

        # 5. 저장 (RegistryService를 통해)
        # TODO: RegistryService에 update_endpoint_auth() 메서드 추가 필요
        # 현재는 메모리에만 업데이트됨

        logger.info(
            f"OAuth token obtained for server {server_id}, expires in {token_response.expires_in}s"
        )

        # 6. 성공 페이지 반환
        return HTMLResponse(
            content="""
            <html>
                <head><title>OAuth Success</title></head>
                <body>
                    <h1>Authentication Successful</h1>
                    <p>You can now close this window and return to AgentHub.</p>
                    <script>
                        // Auto-close after 3 seconds
                        setTimeout(() => window.close(), 3000);
                    </script>
                </body>
            </html>
            """,
            status_code=200,
        )

    except OAuthTokenExchangeError as e:
        logger.error(f"OAuth token exchange failed: {e.message}")
        raise HTTPException(status_code=502, detail=f"Token exchange failed: {e.message}")

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail="OAuth callback failed")
