"""토큰 교환 엔드포인트"""

from fastapi import APIRouter, HTTPException, Request

from ..schemas.auth import TokenRequest, TokenResponse
from ..security import get_extension_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/token", response_model=TokenResponse)
async def exchange_token(request: Request, body: TokenRequest) -> TokenResponse:  # noqa: ARG001
    """
    Chrome Extension 토큰 교환

    Origin 검증:
    - chrome-extension:// Origin만 허용
    - 웹 페이지(https://)에서 호출 시 403 Forbidden

    보안:
    - 토큰 발급은 서버 세션당 동일 (재시작 시 리셋)
    - Extension ID는 로깅용, 검증은 Origin 헤더로 수행
    """
    # Origin 헤더 검증
    origin = request.headers.get("Origin", "")
    if not origin.startswith("chrome-extension://"):
        raise HTTPException(
            status_code=403,
            detail="Invalid origin. Only Chrome Extensions are allowed.",
        )

    # 토큰 반환
    return TokenResponse(token=get_extension_token())
