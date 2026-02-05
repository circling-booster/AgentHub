"""Fake Usage Storage (테스트용 인메모리 구현)"""

from datetime import datetime

from src.domain.entities.usage import Usage
from src.domain.ports.outbound.usage_port import UsageStoragePort


class FakeUsageStorage(UsageStoragePort):
    """인메모리 Usage 저장소 (테스트 전용)"""

    def __init__(self):
        self._usages: list[Usage] = []

    async def save_usage(self, usage: Usage) -> None:
        """사용량 데이터 저장"""
        self._usages.append(usage)

    async def get_monthly_total(self, year: int, month: int) -> float:
        """특정 월의 총 비용 조회 (USD)"""
        total = 0.0
        for usage in self._usages:
            if usage.created_at.year == year and usage.created_at.month == month:
                total += usage.cost_usd
        return total

    async def get_usage_by_model(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, float]:
        """기간별 모델별 비용 조회"""
        by_model: dict[str, float] = {}
        for usage in self._usages:
            if start_date <= usage.created_at <= end_date:
                by_model[usage.model] = by_model.get(usage.model, 0.0) + usage.cost_usd
        return by_model

    async def get_usage_summary(self, start_date: datetime, end_date: datetime) -> dict:
        """기간별 사용량 요약"""
        total_cost = 0.0
        total_tokens = 0
        call_count = 0
        by_model: dict[str, float] = {}

        for usage in self._usages:
            if start_date <= usage.created_at <= end_date:
                total_cost += usage.cost_usd
                total_tokens += usage.total_tokens
                call_count += 1
                by_model[usage.model] = by_model.get(usage.model, 0.0) + usage.cost_usd

        return {
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "call_count": call_count,
            "by_model": by_model,
        }
