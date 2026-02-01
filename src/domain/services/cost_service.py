"""CostService (순수 Python, 외부 의존성 없음)"""

from datetime import datetime

from src.domain.entities.usage import BudgetStatus, Usage
from src.domain.exceptions import BudgetExceededError
from src.domain.ports.outbound.usage_port import UsageStoragePort


class CostService:
    """
    비용 추적 및 예산 관리 서비스

    LLM 호출 비용을 추적하고 월별 예산 대비 사용량을 모니터링합니다.
    """

    # Budget 정책 임계값
    WARNING_THRESHOLD = 0.9  # 90%: 경고
    CRITICAL_THRESHOLD = 1.0  # 100%: 심각
    HARD_LIMIT_THRESHOLD = 1.1  # 110%: 차단

    def __init__(self, usage_port: UsageStoragePort, monthly_budget_usd: float = 100.0):
        """
        Args:
            usage_port: 사용량 저장소 포트
            monthly_budget_usd: 월별 예산 (USD)
        """
        self._storage = usage_port
        self._monthly_budget = monthly_budget_usd

    async def record_usage(self, usage: Usage) -> None:
        """LLM 호출 비용 기록"""
        await self._storage.save_usage(usage)

    async def check_budget(self) -> BudgetStatus:
        """예산 상태 확인 (경고/차단 여부)

        Returns:
            BudgetStatus: 예산 상태 (alert_level, can_proceed 등)
        """
        now = datetime.now()
        current_spending = await self._storage.get_monthly_total(now.year, now.month)
        usage_pct = current_spending / self._monthly_budget

        # 경고 수준 판정
        if usage_pct >= self.HARD_LIMIT_THRESHOLD:
            alert_level = "blocked"
            can_proceed = False  # 🚫 API 호출 차단
        elif usage_pct >= self.CRITICAL_THRESHOLD:
            alert_level = "critical"
            can_proceed = True  # ⚠️ 허용하되 Extension 경고 표시
        elif usage_pct >= self.WARNING_THRESHOLD:
            alert_level = "warning"
            can_proceed = True  # ⚠️ 허용하되 Extension 경고 표시
        else:
            alert_level = "safe"
            can_proceed = True

        return BudgetStatus(
            monthly_budget=self._monthly_budget,
            current_spending=current_spending,
            usage_percentage=round(usage_pct * 100, 2),  # 부동소수점 정밀도 수정
            alert_level=alert_level,
            can_proceed=can_proceed,
        )

    async def enforce_budget(self) -> None:
        """예산 초과 시 예외 발생 (110% hard limit)

        LLM 호출 전에 이 메서드를 호출하여 예산을 체크합니다.
        110% 초과 시 BudgetExceededError를 발생시켜 호출을 차단합니다.

        Raises:
            BudgetExceededError: 예산 110% 초과 시 (can_proceed=False)
        """
        status = await self.check_budget()

        if not status.can_proceed:
            raise BudgetExceededError(
                f"Budget exceeded: {status.usage_percentage:.1f}% of monthly budget "
                f"(${status.current_spending:.2f} / ${status.monthly_budget:.2f}). "
                f"API calls are blocked until next month."
            )

    async def get_monthly_summary(self) -> dict:
        """월별 사용량 요약

        Returns:
            dict: {
                "total_cost": float,
                "total_tokens": int,
                "call_count": int,
                "by_model": dict[str, float],
            }
        """
        now = datetime.now()
        # 이번 달 1일 00:00부터 현재까지
        start_date = datetime(now.year, now.month, 1)
        end_date = now

        return await self._storage.get_usage_summary(start_date, end_date)
