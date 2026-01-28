"""Auth API 스키마"""

from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    """토큰 교환 요청"""

    extension_id: str = Field(..., description="Chrome Extension ID")


class TokenResponse(BaseModel):
    """토큰 교환 응답"""

    token: str = Field(..., description="API access token")
