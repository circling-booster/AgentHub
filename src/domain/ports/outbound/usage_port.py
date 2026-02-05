"""Usage Storage Port (도메인 포트, 순수 Python)"""

from abc import ABC, abstractmethod
from datetime import datetime

from src.domain.entities.usage import Usage


class UsageStoragePort(ABC):
    """
    Usage 저장소 포트

    LLM 호출 사용량 및 비용 데이터의 저장/조회 인터페이스
    """

    @abstractmethod
    async def save_usage(self, usage: Usage) -> None:
        """사용량 데이터 저장"""
        pass

    @abstractmethod
    async def get_monthly_total(self, year: int, month: int) -> float:
        """특정 월의 총 비용 조회 (USD)"""
        pass

    @abstractmethod
    async def get_usage_by_model(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, float]:
        """기간별 모델별 비용 조회

        Returns:
            dict: {"model_name": total_cost_usd, ...}
        """
        pass

    @abstractmethod
    async def get_usage_summary(self, start_date: datetime, end_date: datetime) -> dict:
        """기간별 사용량 요약

        Returns:
            dict: {
                "total_cost": float,
                "total_tokens": int,
                "call_count": int,
                "by_model": dict,
            }
        """
        pass
