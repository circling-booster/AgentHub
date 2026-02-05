"""FastAPI 앱 팩토리"""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.container import Container

from .exceptions import register_exception_handlers
from .routes import (
    a2a,
    a2a_card,
    auth,
    chat,
    conversations,
    health,
    mcp,
    oauth,
    usage,
    workflow,
)
from .security import ExtensionAuthMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """애플리케이션 수명 주기 관리

    Startup:
    - SQLite 스토리지 초기화 (테이블 생성)
    - Orchestrator 비동기 초기화 (DynamicToolset + LlmAgent)

    Shutdown:
    - Storage 연결 종료
    - MCP 연결 정리
    """
    # Startup
    container = app.container
    settings = container.settings()

    # Step 7: 로깅 설정 초기화 (최우선)
    from src.config.logging_config import setup_logging

    setup_logging(settings)
    logger.info("AgentHub API starting up")

    # LiteLLM이 os.environ에서 API 키를 읽으므로, Settings에서 로드한 키를 환경변수에 반영
    _export_api_keys(settings)

    # SQLite 스토리지 초기화
    conv_storage = container.conversation_storage()
    await conv_storage.initialize()
    logger.info("SQLite conversation storage initialized")

    usage_storage = container.usage_storage()
    await usage_storage.initialize()
    logger.info("SQLite usage storage initialized")

    # Orchestrator 초기화 (Async Factory Pattern)
    orchestrator = container.orchestrator_adapter()
    await orchestrator.initialize()
    logger.info("Orchestrator initialized")

    # 저장된 엔드포인트 복원
    registry = container.registry_service()
    restore_result = await registry.restore_endpoints()
    logger.info(
        f"Endpoints restored: {len(restore_result['restored'])} succeeded, "
        f"{len(restore_result['failed'])} failed"
    )

    yield

    # Shutdown
    logger.info("AgentHub API shutting down")
    await orchestrator.close()
    logger.info("Orchestrator closed")
    await conv_storage.close()
    await usage_storage.close()
    logger.info("Storage connections closed")


def create_app() -> FastAPI:
    """
    FastAPI 앱 생성

    Middleware 순서 (중요 - Starlette LIFO):
    add_middleware()는 내부적으로 insert(0, ...)을 사용합니다.
    따라서 나중에 추가된 미들웨어가 outermost(먼저 실행)됩니다.

    원하는 실행 순서: CORS → Auth → Router
    - ExtensionAuthMiddleware 먼저 추가 → innermost (나중 실행)
    - CORSMiddleware 나중 추가 → outermost (먼저 실행)

    이유: CORS preflight (OPTIONS)과 403 에러 응답에 CORS 헤더가 포함되어야 함.
    """
    # DI Container 초기화 및 와이어링
    container = Container()
    container.wire(packages=["src.adapters.inbound.http"])

    app = FastAPI(
        title="AgentHub API",
        version="0.1.0",
        description="MCP + A2A 통합 Agent System",
        lifespan=lifespan,
    )
    app.container = container

    # Domain Exception → HTTP 응답 변환
    register_exception_handlers(app)

    # Middleware 순서 (중요 - Starlette LIFO):
    # add_middleware()는 insert(0, ...)를 사용하므로, 나중에 추가한 것이 outermost.
    # 원하는 실행 순서: CORS → Auth → Router
    # 따라서: Auth 먼저 추가 (innermost), CORS 나중 추가 (outermost)
    #
    # 이유: CORS가 outermost여야 403 에러 응답에도 CORS 헤더가 포함됨.
    # 그래야 브라우저가 CORS 에러 대신 실제 403 상태를 볼 수 있음.
    app.add_middleware(ExtensionAuthMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^chrome-extension://[a-zA-Z0-9_-]+$",
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["X-Extension-Token", "Content-Type"],
        allow_credentials=False,
    )

    # 라우터 등록
    app.include_router(auth.router)
    app.include_router(health.router)
    app.include_router(oauth.router)  # OAuth 2.1
    app.include_router(mcp.router)
    app.include_router(a2a.router)
    app.include_router(a2a_card.router)  # A2A Agent Card
    app.include_router(chat.router)
    app.include_router(conversations.router)
    app.include_router(workflow.router)  # Workflow Management
    app.include_router(usage.router)  # Usage & Cost Tracking

    return app


def _export_api_keys(settings) -> None:
    """Settings에서 로드한 API 키를 os.environ에 반영

    pydantic-settings는 .env 파일을 모델 필드로 읽지만 os.environ에 설정하지 않는다.
    LiteLLM은 os.environ에서 직접 API 키를 읽으므로 명시적 반영이 필요하다.
    """
    key_mapping = {
        "ANTHROPIC_API_KEY": settings.anthropic_api_key,
        "OPENAI_API_KEY": settings.openai_api_key,
        "GOOGLE_API_KEY": settings.google_api_key,
    }
    for env_name, value in key_mapping.items():
        if value and value != f"your-{env_name.lower().replace('_', '-')}":
            os.environ[env_name] = value
            logger.info(f"{env_name} exported to environment")
