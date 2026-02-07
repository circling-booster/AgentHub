"""Usage API 통합 테스트"""

import os
import tempfile
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from src.adapters.outbound.storage.sqlite_usage import SqliteUsageStorage
from src.domain.entities.usage import Usage
from src.domain.services.cost_service import CostService
from src.main import app


class TestUsageAPI:
    """Usage API 통합 테스트

    authenticated_client fixture 사용하여:
    - temp_data_dir을 사용한 독립 storage
    - usage_storage 자동 초기화
    - X-Extension-Token 헤더 자동 추가
    """

    @pytest.fixture
    async def usage_service_with_data(self):
        """사용량 데이터가 포함된 CostService"""
        # 임시 DB 생성
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        # Storage 초기화
        storage = SqliteUsageStorage(db_path=db_path)
        await storage.initialize()

        # 테스트 데이터 삽입
        now = datetime.now()
        usage1 = Usage(
            model="openai/gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            cost_usd=0.03,
            created_at=now,
        )
        usage2 = Usage(
            model="openai/gpt-4o",
            prompt_tokens=500,
            completion_tokens=1000,
            total_tokens=1500,
            cost_usd=0.15,
            created_at=now,
        )

        await storage.save_usage(usage1)
        await storage.save_usage(usage2)

        # CostService 생성
        cost_service = CostService(usage_port=storage, monthly_budget_usd=100.0)

        yield cost_service

        # Cleanup
        await storage.close()
        os.unlink(db_path)

    async def test_get_usage_summary_requires_auth(self, authenticated_client):
        """인증 필요 (X-Extension-Token 헤더)"""
        # Given: 인증 토큰 없는 client (authenticated_client는 기본으로 토큰 포함)
        client_without_auth = TestClient(app)

        # When: 토큰 없이 요청
        response = client_without_auth.get("/api/usage/summary")

        # Then: 403 Forbidden
        assert response.status_code == 403
        assert response.json()["error"] == "Unauthorized"

    async def test_get_usage_summary(self, authenticated_client):
        """사용량 요약 조회"""
        # authenticated_client는 이미 X-Extension-Token 헤더 포함
        # When
        response = authenticated_client.get("/api/usage/summary")

        # Then
        assert response.status_code == 200
        data = response.json()

        assert "total_cost" in data
        assert "total_tokens" in data
        assert "call_count" in data
        assert "by_model" in data

    async def test_get_usage_by_model(self, authenticated_client):
        """모델별 사용량 조회"""
        # When
        response = authenticated_client.get("/api/usage/by-model")

        # Then
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, dict)

    async def test_get_budget_status(self, authenticated_client):
        """예산 상태 조회"""
        # When
        response = authenticated_client.get("/api/usage/budget")

        # Then
        assert response.status_code == 200
        data = response.json()

        assert "monthly_budget" in data
        assert "current_spending" in data
        assert "usage_percentage" in data
        assert "alert_level" in data
        assert "can_proceed" in data

    async def test_update_budget(self, authenticated_client):
        """예산 설정 업데이트"""
        # When
        response = authenticated_client.put(
            "/api/usage/budget",
            json={"monthly_budget_usd": 200.0},
        )

        # Then
        assert response.status_code == 200
        data = response.json()

        assert data["monthly_budget"] == 200.0
