"""Usage 엔티티 테스트 (TDD Red Phase)"""

from datetime import datetime

import pytest

from src.domain.entities.usage import Usage


class TestUsageInitialization:
    """Usage 엔티티 초기화 테스트"""

    def test_creates_usage_with_required_fields(self):
        """필수 필드로 Usage 생성"""
        usage = Usage(
            model="openai/gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.0025,
        )

        assert usage.model == "openai/gpt-4o-mini"
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
        assert usage.cost_usd == 0.0025
        assert isinstance(usage.created_at, datetime)

    def test_created_at_defaults_to_now(self):
        """created_at이 현재 시간으로 기본 설정"""
        before = datetime.now()
        usage = Usage(
            model="claude-3-sonnet",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.003,
        )
        after = datetime.now()

        assert before <= usage.created_at <= after

    def test_custom_created_at(self):
        """사용자 정의 created_at 지정"""
        custom_time = datetime(2025, 1, 1, 12, 0, 0)
        usage = Usage(
            model="gemini-pro",
            prompt_tokens=200,
            completion_tokens=100,
            total_tokens=300,
            cost_usd=0.001,
            created_at=custom_time,
        )

        assert usage.created_at == custom_time


class TestUsageValidation:
    """Usage 엔티티 검증 테스트"""

    def test_validates_positive_prompt_tokens(self):
        """prompt_tokens는 0 이상이어야 함"""
        with pytest.raises(ValueError, match="prompt_tokens must be non-negative"):
            Usage(
                model="test",
                prompt_tokens=-10,
                completion_tokens=50,
                total_tokens=40,
                cost_usd=0.001,
            )

    def test_validates_positive_completion_tokens(self):
        """completion_tokens는 0 이상이어야 함"""
        with pytest.raises(ValueError, match="completion_tokens must be non-negative"):
            Usage(
                model="test",
                prompt_tokens=100,
                completion_tokens=-50,
                total_tokens=50,
                cost_usd=0.001,
            )

    def test_validates_positive_total_tokens(self):
        """total_tokens는 0 이상이어야 함"""
        with pytest.raises(ValueError, match="total_tokens must be non-negative"):
            Usage(
                model="test",
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=-150,
                cost_usd=0.001,
            )

    def test_validates_positive_cost(self):
        """비용은 0 이상이어야 함"""
        with pytest.raises(ValueError):
            Usage(
                model="test",
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                cost_usd=-0.001,
            )

    def test_validates_total_tokens_matches_sum(self):
        """total_tokens = prompt_tokens + completion_tokens"""
        with pytest.raises(
            ValueError, match="total_tokens must equal prompt_tokens \\+ completion_tokens"
        ):
            Usage(
                model="test",
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=200,  # 잘못된 합계
                cost_usd=0.001,
            )


class TestUsageEquality:
    """Usage 엔티티 동등성 테스트"""

    def test_usage_equality(self):
        """같은 값의 Usage는 동등"""
        time = datetime(2025, 1, 1, 12, 0, 0)
        usage1 = Usage(
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.005,
            created_at=time,
        )
        usage2 = Usage(
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.005,
            created_at=time,
        )

        assert usage1 == usage2

    def test_usage_inequality(self):
        """다른 값의 Usage는 불평등"""
        time = datetime(2025, 1, 1, 12, 0, 0)
        usage1 = Usage(
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.005,
            created_at=time,
        )
        usage2 = Usage(
            model="gpt-3.5-turbo",  # 다른 모델
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.002,  # 다른 비용
            created_at=time,
        )

        assert usage1 != usage2
