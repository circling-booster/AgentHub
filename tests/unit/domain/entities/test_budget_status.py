"""BudgetStatus 엔티티 테스트"""

from src.domain.entities.usage import BudgetStatus


class TestBudgetStatus:
    """BudgetStatus 엔티티 테스트"""

    def test_safe_budget_status(self):
        """안전 범위 내 예산 (0-89%)"""
        # Given
        monthly_budget = 100.0
        current_spending = 50.0  # 50%

        # When
        status = BudgetStatus(
            monthly_budget=monthly_budget,
            current_spending=current_spending,
            usage_percentage=50.0,
            alert_level="safe",
            can_proceed=True,
        )

        # Then
        assert status.alert_level == "safe"
        assert status.can_proceed is True
        assert status.get_alert_message() == "Budget within safe limits"

    def test_warning_budget_status(self):
        """경고 범위 예산 (90-99%)"""
        # Given
        monthly_budget = 100.0
        current_spending = 95.0  # 95%

        # When
        status = BudgetStatus(
            monthly_budget=monthly_budget,
            current_spending=current_spending,
            usage_percentage=95.0,
            alert_level="warning",
            can_proceed=True,
        )

        # Then
        assert status.alert_level == "warning"
        assert status.can_proceed is True
        assert "95.0%" in status.get_alert_message()
        assert "$95.00/$100.00" in status.get_alert_message()

    def test_critical_budget_status(self):
        """심각 범위 예산 (100-109%)"""
        # Given
        monthly_budget = 100.0
        current_spending = 105.0  # 105%

        # When
        status = BudgetStatus(
            monthly_budget=monthly_budget,
            current_spending=current_spending,
            usage_percentage=105.0,
            alert_level="critical",
            can_proceed=True,
        )

        # Then
        assert status.alert_level == "critical"
        assert status.can_proceed is True  # 아직 허용
        assert "exceeded" in status.get_alert_message()
        assert "105.0%" in status.get_alert_message()

    def test_blocked_budget_status(self):
        """차단 범위 예산 (110%+)"""
        # Given
        monthly_budget = 100.0
        current_spending = 115.0  # 115%

        # When
        status = BudgetStatus(
            monthly_budget=monthly_budget,
            current_spending=current_spending,
            usage_percentage=115.0,
            alert_level="blocked",
            can_proceed=False,
        )

        # Then
        assert status.alert_level == "blocked"
        assert status.can_proceed is False  # API 호출 차단
        assert "hard limit" in status.get_alert_message()
        assert "blocked" in status.get_alert_message().lower()
