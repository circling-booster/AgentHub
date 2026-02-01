"""Usage API 스키마"""

from pydantic import BaseModel, Field


class BudgetStatusSchema(BaseModel):
    """예산 상태 스키마"""

    monthly_budget: float = Field(..., description="월별 예산 (USD)")
    current_spending: float = Field(..., description="현재 지출 (USD)")
    usage_percentage: float = Field(..., description="사용률 (%)")
    alert_level: str = Field(..., description="경고 수준 (safe/warning/critical/blocked)")
    can_proceed: bool = Field(..., description="API 호출 허용 여부")


class UsageSummarySchema(BaseModel):
    """사용량 요약 스키마"""

    total_cost: float = Field(..., description="총 비용 (USD)")
    total_tokens: int = Field(..., description="총 토큰 수")
    call_count: int = Field(..., description="호출 횟수")
    by_model: dict[str, float] = Field(..., description="모델별 비용")


class UpdateBudgetRequest(BaseModel):
    """예산 업데이트 요청"""

    monthly_budget_usd: float = Field(..., gt=0, description="월별 예산 (USD, 양수)")
