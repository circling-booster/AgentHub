"""Localhost API 보안 (Drive-by RCE 방지)

Zero-Trust 보안 원칙:
1. Token Handshake: 서버 시작 시 난수 토큰 생성, Extension만 교환
2. Middleware 검증: 모든 /api/* 요청에 X-Extension-Token 헤더 필수
3. CORS 제한: chrome-extension:// Origin만 허용

Phase 2 추가: DEV_MODE + localhost Origin 시 토큰 검증 우회
"""

import secrets
from typing import ClassVar
from urllib.parse import urlparse

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class TokenProvider:
    """
    토큰 관리 클래스 (테스트 용이성 개선)

    기존 모듈 레벨 전역 변수 대신 클래스로 래핑하여
    테스트에서 토큰 주입 가능
    """

    def __init__(self) -> None:
        self._token: str | None = None

    def get_token(self) -> str:
        """토큰 lazy 생성 (서버 시작 시 1회만)"""
        if self._token is None:
            self._token = secrets.token_urlsafe(32)
        return self._token

    def reset(self, new_token: str | None = None) -> None:
        """
        토큰 재설정

        Args:
            new_token: 주입할 토큰. None이면 새 토큰 생성
        """
        if new_token is None:
            # None일 경우 새 토큰 생성
            self._token = secrets.token_urlsafe(32)
        else:
            self._token = new_token


# 싱글톤 인스턴스
token_provider = TokenProvider()


def get_extension_token() -> str:
    """Extension 초기화 시 토큰 반환"""
    return token_provider.get_token()


def is_localhost_origin(origin: str | None) -> bool:
    """
    Origin이 localhost인지 확인 (Phase 2 Refactor)

    Args:
        origin: HTTP Origin 헤더 값

    Returns:
        True if hostname is exactly "localhost" or starts with "127.0.0.1"

    Security:
        - HTTPS는 제외 (프로덕션 환경 모방 방지)
        - hostname을 정확히 파싱하여 부분 매칭 방지
          (예: "http://localhost.example.com"은 False)
        - None/빈 문자열/잘못된 URL은 False 반환
    """
    if not origin:
        return False

    try:
        parsed = urlparse(origin)
        # HTTP만 허용 (HTTPS 제외)
        if parsed.scheme != "http":
            return False

        hostname = parsed.hostname or ""
        # hostname이 정확히 "localhost"이거나 "127.0.0.1"로 시작하는 경우만 True
        return hostname == "localhost" or hostname.startswith("127.0.0.1")
    except (ValueError, AttributeError):
        return False


class ExtensionAuthMiddleware(BaseHTTPMiddleware):
    """
    Chrome Extension 인증 미들웨어

    모든 /api/* 요청에 X-Extension-Token 헤더 검증.
    토큰 불일치 시 403 Forbidden 반환하여 Drive-by RCE 공격 차단.

    Phase 2: DEV_MODE + localhost Origin 시 토큰 검증 우회
    """

    # 인증 제외 경로 (Public endpoints)
    EXCLUDED_PATHS: ClassVar[set[str]] = {
        "/health",
        "/auth/token",
        "/docs",
        "/openapi.json",
        "/redoc",
    }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """요청 처리 전 토큰 검증"""
        path = request.url.path
        method = request.method

        # CORS preflight (OPTIONS) 요청은 검증 생략
        # CORS 미들웨어가 처리해야 하므로 Auth 검증 불필요
        if method == "OPTIONS":
            return await call_next(request)

        # 제외 경로는 검증 생략
        if path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # API 경로는 토큰 검증 필수
        if path.startswith("/api/"):
            # Phase 2: DEV_MODE + localhost Origin 시 토큰 검증 우회
            from src.config.settings import Settings

            settings = Settings()

            if settings.dev_mode:
                origin = request.headers.get("origin")
                # DEV_MODE: localhost 요청은 Origin 없어도 허용 (EventSource 지원)
                if origin is None or is_localhost_origin(origin):
                    return await call_next(request)  # Skip auth for dev playground

            token = request.headers.get("X-Extension-Token")
            if token != get_extension_token():
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "Unauthorized",
                        "message": "Invalid or missing extension token",
                    },
                )

        return await call_next(request)
