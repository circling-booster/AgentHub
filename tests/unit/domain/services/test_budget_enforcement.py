"""Budget Enforcement Tests (TDD RED)"""

import pytest

from src.domain.exceptions import BudgetExceededError
from src.domain.services.cost_service import CostService
from tests.unit.fakes.fake_usage_storage import FakeUsageStorage


class TestBudgetEnforcement:
    """Budget 차단 로직 테스트"""

    @pytest.fixture
    async def cost_service_with_exceeded_budget(self):
        """예산 초과 상태의 CostService"""
        storage = FakeUsageStorage()
        service = CostService(usage_port=storage, monthly_budget_usd=100.0)

        # 110달러 사용 (110% 초과 → blocked)
        from datetime import datetime

        from src.domain.entities.usage import Usage

        usage = Usage(
            model="openai/gpt-4o",
            prompt_tokens=1000,
            completion_tokens=2000,
            total_tokens=3000,
            cost_usd=110.0,
            created_at=datetime.now(),
        )
        await storage.save_usage(usage)
        return service

    async def test_check_budget_raises_error_when_exceeded(self, cost_service_with_exceeded_budget):
        """예산 초과 시 BudgetExceededError 발생"""
        # When/Then
        with pytest.raises(BudgetExceededError) as exc_info:
            await cost_service_with_exceeded_budget.enforce_budget()

        # 에러 메시지 검증
        assert "Budget exceeded" in str(exc_info.value)
        assert exc_info.value.code == "BudgetExceededError"

    async def test_check_budget_allows_when_under_limit(self):
        """예산 이하일 때는 정상 통과"""
        # Given
        storage = FakeUsageStorage()
        service = CostService(usage_port=storage, monthly_budget_usd=100.0)

        # 50달러 사용 (50% → safe)
        from datetime import datetime

        from src.domain.entities.usage import Usage

        usage = Usage(
            model="openai/gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            cost_usd=50.0,
            created_at=datetime.now(),
        )
        await storage.save_usage(usage)

        # When/Then: 예외 발생하지 않음
        await service.enforce_budget()  # Should not raise

    async def test_budget_status_blocked_when_110_percent(self):
        """110% 초과 시 can_proceed=False"""
        # Given
        storage = FakeUsageStorage()
        service = CostService(usage_port=storage, monthly_budget_usd=100.0)

        # 110달러 사용
        from datetime import datetime

        from src.domain.entities.usage import Usage

        usage = Usage(
            model="openai/gpt-4o",
            prompt_tokens=1000,
            completion_tokens=2000,
            total_tokens=3000,
            cost_usd=110.0,
            created_at=datetime.now(),
        )
        await storage.save_usage(usage)

        # When
        status = await service.check_budget()

        # Then
        assert status.can_proceed is False
        assert status.alert_level == "blocked"
