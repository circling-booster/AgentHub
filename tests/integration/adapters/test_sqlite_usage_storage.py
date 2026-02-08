"""SQLite Usage Storage 통합 테스트"""

import os
import tempfile
from datetime import datetime

import pytest

from src.adapters.outbound.storage.sqlite_usage import SqliteUsageStorage
from src.domain.entities.usage import Usage


class TestSqliteUsageStorage:
    """SQLite Usage Storage 통합 테스트"""

    @pytest.fixture
    async def usage_storage(self):
        """임시 SQLite 데이터베이스 픽스처"""
        # 임시 파일 생성
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        storage = SqliteUsageStorage(db_path=db_path)
        await storage.initialize()

        yield storage

        await storage.close()
        # 임시 파일 삭제
        if os.path.exists(db_path):
            os.unlink(db_path)

    async def test_save_and_retrieve_usage(self, usage_storage):
        """사용량 저장 및 조회"""
        # Given
        usage = Usage(
            model="openai/gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.01,
        )

        # When
        await usage_storage.save_usage(usage)

        # Then
        total = await usage_storage.get_monthly_total(datetime.now().year, datetime.now().month)
        assert total == 0.01

    async def test_get_usage_by_model(self, usage_storage):
        """모델별 비용 조회"""
        # Given
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
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        end_date = now

        by_model = await usage_storage.get_usage_by_model(start_date, end_date)

        # Then
        assert by_model["openai/gpt-4o-mini"] == 10.0
        assert by_model["anthropic/claude-sonnet-4"] == 20.0

    async def test_get_usage_summary(self, usage_storage):
        """사용량 요약 조회"""
        # Given: 3개의 사용량 기록
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
        await usage_storage.save_usage(
            Usage(
                model="openai/gpt-4o-mini",
                prompt_tokens=50,
                completion_tokens=25,
                total_tokens=75,
                cost_usd=5.0,
            )
        )

        # When
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        end_date = now

        summary = await usage_storage.get_usage_summary(start_date, end_date)

        # Then
        assert summary["total_cost"] == 35.0
        assert summary["total_tokens"] == 525
        assert summary["call_count"] == 3
        assert summary["by_model"]["openai/gpt-4o-mini"] == 15.0
        assert summary["by_model"]["anthropic/claude-sonnet-4"] == 20.0
