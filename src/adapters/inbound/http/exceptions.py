"""HTTP Exception Handlers

Domain Exception을 HTTP 응답으로 변환하는 중앙 집중식 예외 처리.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.domain.exceptions import (
    BudgetExceededError,
    ConversationNotFoundError,
    DomainException,
    DuplicateEndpointError,
    EndpointConnectionError,
    EndpointNotFoundError,
    EndpointTimeoutError,
    LlmAuthenticationError,
    LlmRateLimitError,
    ToolNotFoundError,
)


class ErrorResponse(BaseModel):
    """에러 응답 스키마"""

    error: str
    code: str
    message: str


# Domain Exception → HTTP 상태 코드 매핑
EXCEPTION_STATUS_MAP: dict[type[DomainException], int] = {
    # 400 Bad Request
    DuplicateEndpointError: status.HTTP_400_BAD_REQUEST,
    # 401 Unauthorized
    LlmAuthenticationError: status.HTTP_401_UNAUTHORIZED,
    # 403 Forbidden
    BudgetExceededError: status.HTTP_403_FORBIDDEN,
    # 404 Not Found
    EndpointNotFoundError: status.HTTP_404_NOT_FOUND,
    ToolNotFoundError: status.HTTP_404_NOT_FOUND,
    ConversationNotFoundError: status.HTTP_404_NOT_FOUND,
    # 429 Too Many Requests
    LlmRateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
    # 502 Bad Gateway
    EndpointConnectionError: status.HTTP_502_BAD_GATEWAY,
    # 504 Gateway Timeout
    EndpointTimeoutError: status.HTTP_504_GATEWAY_TIMEOUT,
}


async def domain_exception_handler(_request: Request, exc: DomainException) -> JSONResponse:
    """
    Domain Exception을 HTTP 응답으로 변환

    Args:
        _request: FastAPI Request 객체 (핸들러 시그니처용, 현재 미사용)
        exc: Domain Layer에서 발생한 예외

    Returns:
        JSONResponse with error details
    """
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=type(exc).__name__,
            code=exc.code,
            message=exc.message,
        ).model_dump(),
    )


def register_exception_handlers(app) -> None:
    """
    FastAPI 앱에 예외 핸들러 등록

    Args:
        app: FastAPI 애플리케이션 인스턴스
    """
    app.add_exception_handler(DomainException, domain_exception_handler)
