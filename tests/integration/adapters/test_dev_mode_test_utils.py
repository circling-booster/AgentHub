"""Integration Test: DEV_MODE Test Utilities API (Phase 1)

TDD 검증: DEV_MODE 전용 테스트 데이터 초기화 API

Note: 통합 테스트는 API 구조와 기본 동작만 검증합니다.
      실제 데이터 초기화 기능은 E2E 테스트에서 검증합니다.
"""

import pytest
from fastapi.testclient import TestClient


class TestTestUtilsAPIStructure:
    """DEV_MODE 전용 /test/* 엔드포인트 구조 테스트"""

    @pytest.fixture
    def client_dev_mode(self, monkeypatch, tmp_path):
        """DEV_MODE=true 환경의 테스트 클라이언트 (Fresh Container)"""
        monkeypatch.setenv("DEV_MODE", "true")
        # Fresh app with DEV_MODE=true
        from src.adapters.inbound.http.app import create_app

        app = create_app()
        container = app.container
        container.reset_singletons()
        container.settings().storage.data_dir = str(tmp_path)

        with TestClient(app) as client:
            yield client

        # Cleanup
        container.reset_singletons()
        container.unwire()

    def test_state_endpoint_returns_correct_structure(self, client_dev_mode):
        """
        Green: DEV_MODE에서 /test/state 엔드포인트 구조 검증

        Given: DEV_MODE=true
        When: GET /test/state 호출
        Then: 200 OK + 올바른 JSON 구조 반환
        """
        response = client_dev_mode.get("/test/state")

        assert response.status_code == 200
        data = response.json()
        assert "mcp_servers" in data
        assert "a2a_agents" in data
        assert "conversations" in data
        assert isinstance(data["mcp_servers"], int)
        assert isinstance(data["a2a_agents"], int)
        assert isinstance(data["conversations"], int)

    def test_reset_data_endpoint_returns_correct_structure(self, client_dev_mode):
        """
        Green: DEV_MODE에서 /test/reset-data 엔드포인트 구조 검증

        Given: DEV_MODE=true
        When: POST /test/reset-data 호출
        Then: 200 OK + 올바른 JSON 구조 반환
        """
        response = client_dev_mode.post("/test/reset-data")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "reset_complete"
        assert "cleared" in data
        assert isinstance(data["cleared"], dict)
        assert "mcp_servers" in data["cleared"]
        assert "a2a_agents" in data["cleared"]
        assert "conversations" in data["cleared"]
        # 카운트는 >= 0 (초기 상태에 따라 다를 수 있음)
        assert data["cleared"]["mcp_servers"] >= 0
        assert data["cleared"]["a2a_agents"] >= 0
        assert data["cleared"]["conversations"] >= 0

    def test_reset_data_is_idempotent(self, client_dev_mode):
        """
        Green: reset-data를 연속으로 호출해도 안전 (멱등성)

        Given: DEV_MODE=true
        When: POST /test/reset-data 2회 연속 호출
        Then: 모두 200 OK
        """
        # 첫 번째 reset
        reset1 = client_dev_mode.post("/test/reset-data")
        assert reset1.status_code == 200

        # 두 번째 reset (멱등성 확인)
        reset2 = client_dev_mode.post("/test/reset-data")
        assert reset2.status_code == 200
        data = reset2.json()
        # 두 번째 호출 후에는 cleared 카운트가 0이어야 함 (이미 초기화됨)
        assert data["cleared"]["mcp_servers"] == 0
        assert data["cleared"]["a2a_agents"] == 0
        assert data["cleared"]["conversations"] == 0
