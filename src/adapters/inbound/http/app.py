"""FastAPI 앱 팩토리"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import auth, health
from .security import ExtensionAuthMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """애플리케이션 수명 주기 관리

    Phase 2에서 추가 예정:
    - Startup: DI Container 초기화, Orchestrator 비동기 초기화
    - Shutdown: MCP 연결 정리, Storage 종료
    """
    # Startup
    logger.info("AgentHub API starting up")
    yield
    # Shutdown
    logger.info("AgentHub API shutting down")


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
    app = FastAPI(
        title="AgentHub API",
        version="0.1.0",
        description="MCP + A2A 통합 Agent System",
        lifespan=lifespan,
    )

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

    return app
