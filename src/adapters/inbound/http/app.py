"""FastAPI 앱 팩토리"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import auth, health
from .security import ExtensionAuthMiddleware


def create_app() -> FastAPI:
    """
    FastAPI 앱 생성

    Middleware 순서 (중요):
    1. CORSMiddleware 먼저 추가 -> outermost (요청을 먼저 처리)
    2. ExtensionAuthMiddleware 나중 추가 -> innermost

    이유: CORS preflight (OPTIONS) 요청이 Auth 검증 전에 처리되어야 함.
    참조: https://medium.com/@saurabhbatham17/navigating-middleware-ordering-in-fastapi-a-cors-dilemma-8be88ab2ee7b
    """
    app = FastAPI(
        title="AgentHub API",
        version="0.1.0",
        description="MCP + A2A 통합 Agent System",
    )

    # CORS: Chrome Extension만 허용 (regex 패턴)
    # Critical Fix: allow_origins=["chrome-extension://*"]는 작동하지 않음
    # FastAPI/Starlette는 allow_origin_regex를 사용해야 함
    # 패턴: chrome-extension:// 뒤에 알파벳, 숫자, 하이픈, 언더스코어 허용
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^chrome-extension://[a-zA-Z0-9_-]+$",
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["X-Extension-Token", "Content-Type"],
        allow_credentials=False,
    )

    # 보안 미들웨어 (Token 검증)
    app.add_middleware(ExtensionAuthMiddleware)

    # 라우터 등록
    app.include_router(auth.router)
    app.include_router(health.router)

    return app
