"""CostService 테스트"""

from datetime import datetime

import pytest

from src.domain.entities.usage import Usage
from src.domain.services.cost_service import CostService
from tests.unit.fakes.fake_usage_storage import FakeUsageStorage


class TestCostService:
    """CostService 테스트"""

    @pytest.fixture
    def usage_storage(self):
        """Fake Usage Storage 픽스처"""
        return FakeUsageStorage()

    @pytest.fixture
    def cost_service(self, usage_storage):
        """CostService 픽스처 (월 예산 $100)"""
        return CostService(usage_port=usage_storage, monthly_budget_usd=100.0)

    async def test_record_usage(self, cost_service, usage_storage):
        """사용량 기록"""
        # Given
        usage = Usage(
            model="openai/gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.01,
        )

        # When
        await cost_service.record_usage(usage)

        # Then
        total = await usage_storage.get_monthly_total(datetime.now().year, datetime.now().month)
        assert total == 0.01

    async def test_check_budget_safe(self, cost_service, usage_storage):
        """안전 범위 예산 (0-89%)"""
        # Given: 현재 지출 $50 (50%)
        await usage_storage.save_usage(
            Usage(
                model="openai/gpt-4o-mini",
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                cost_usd=50.0,
            )
        )

        # When
        status = await cost_service.check_budget()

        # Then
        assert status.alert_level == "safe"
        assert status.can_proceed is True
        assert status.usage_percentage == 50.0

    async def test_check_budget_warning(self, cost_service, usage_storage):
        """경고 범위 예산 (90-99%)"""
        # Given: 현재 지출 $95 (95%)
        await usage_storage.save_usage(
            Usage(
                model="openai/gpt-4o-mini",
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                cost_usd=95.0,
            )
        )

        # When
        status = await cost_service.check_budget()

        # Then
        assert status.alert_level == "warning"
        assert status.can_proceed is True
        assert status.usage_percentage == 95.0

    async def test_check_budget_critical(self, cost_service, usage_storage):
        """심각 범위 예산 (100-109%)"""
        # Given: 현재 지출 $105 (105%)
        await usage_storage.save_usage(
            Usage(
                model="openai/gpt-4o-mini",
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                cost_usd=105.0,
            )
        )

        # When
        status = await cost_service.check_budget()

        # Then
        assert status.alert_level == "critical"
        assert status.can_proceed is True  # 아직 허용
        assert status.usage_percentage == 105.0

    async def test_check_budget_blocked(self, cost_service, usage_storage):
        """차단 범위 예산 (110%+)"""
        # Given: 현재 지출 $115 (115%)
        await usage_storage.save_usage(
            Usage(
                model="openai/gpt-4o-mini",
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                cost_usd=115.0,
            )
        )

        # When
        status = await cost_service.check_budget()

        # Then
        assert status.alert_level == "blocked"
        assert status.can_proceed is False  # API 호출 차단
        assert status.usage_percentage == 115.0

    async def test_get_monthly_summary(self, cost_service, usage_storage):
        """월별 사용량 요약"""
        # Given: 여러 모델 사용
        await usage_storage.save_usage(
            Usage(
                model="openai/gpt-4o-mini",
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                cost_usd=10.0,
            )
        )
        await usage_storage.save_usage(
            Usage(
                model="anthropic/claude-sonnet-4",
                prompt_tokens=200,
                completion_tokens=100,
                total_tokens=300,
                cost_usd=20.0,
            )
        )

        # When
        summary = await cost_service.get_monthly_summary()

        # Then
        assert summary["total_cost"] == 30.0
        assert summary["total_tokens"] == 450
        assert summary["call_count"] == 2
        assert summary["by_model"]["openai/gpt-4o-mini"] == 10.0
        assert summary["by_model"]["anthropic/claude-sonnet-4"] == 20.0
