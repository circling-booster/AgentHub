"""Health Check 엔드포인트"""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict:
    """
    서버 상태 확인

    인증 불필요 (EXCLUDED_PATHS에 포함)
    Extension background.ts에서 30초 주기로 호출
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
    }
