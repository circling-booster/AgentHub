"""Usage API 엔드포인트 (Step 3: Cost Tracking)"""

from datetime import datetime

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from src.adapters.inbound.http.schemas.usage import (
    BudgetStatusSchema,
    UpdateBudgetRequest,
    UsageSummarySchema,
)
from src.config.container import Container
from src.domain.services.cost_service import CostService

router = APIRouter(prefix="/api/usage", tags=["Usage"])


@router.get("/summary", response_model=UsageSummarySchema)
@inject
async def get_usage_summary(
    cost_service: CostService = Depends(Provide[Container.cost_service]),
):
    """월별 사용량 요약 조회

    Returns:
        UsageSummarySchema: 총 비용, 총 토큰, 호출 횟수, 모델별 비용
    """
    summary = await cost_service.get_monthly_summary()
    return UsageSummarySchema(**summary)


@router.get("/by-model", response_model=dict[str, float])
@inject
async def get_usage_by_model(
    cost_service: CostService = Depends(Provide[Container.cost_service]),
):
    """모델별 사용량 조회

    Returns:
        dict: {"model_name": cost_usd, ...}
    """
    now = datetime.now()
    start_date = datetime(now.year, now.month, 1)
    end_date = now

    # UsageStoragePort 직접 접근 (cost_service 내부 _storage 사용)
    by_model = await cost_service._storage.get_usage_by_model(start_date, end_date)
    return by_model


@router.get("/budget", response_model=BudgetStatusSchema)
@inject
async def get_budget_status(
    cost_service: CostService = Depends(Provide[Container.cost_service]),
):
    """예산 상태 조회

    Returns:
        BudgetStatusSchema: 월별 예산, 현재 지출, 사용률, 경고 수준
    """
    status = await cost_service.check_budget()
    return BudgetStatusSchema(
        monthly_budget=status.monthly_budget,
        current_spending=status.current_spending,
        usage_percentage=status.usage_percentage,
        alert_level=status.alert_level,
        can_proceed=status.can_proceed,
    )


@router.put("/budget", response_model=BudgetStatusSchema)
@inject
async def update_budget(
    request: UpdateBudgetRequest,
    cost_service: CostService = Depends(Provide[Container.cost_service]),
):
    """예산 설정 업데이트

    Args:
        request: UpdateBudgetRequest (monthly_budget_usd)

    Returns:
        BudgetStatusSchema: 업데이트된 예산 상태
    """
    # CostService의 _monthly_budget 업데이트
    cost_service._monthly_budget = request.monthly_budget_usd

    # 업데이트된 예산 상태 반환
    status = await cost_service.check_budget()
    return BudgetStatusSchema(
        monthly_budget=status.monthly_budget,
        current_spending=status.current_spending,
        usage_percentage=status.usage_percentage,
        alert_level=status.alert_level,
        can_proceed=status.can_proceed,
    )
