"""Conversation CRUD API Integration Tests

TDD Phase: RED - 테스트 먼저 작성

Phase 2.5 Extension 사이드패널에서 필요한 대화 관리 API 검증
"""

from fastapi.testclient import TestClient


class TestCreateConversation:
    """POST /api/conversations - 대화 생성"""

    def test_create_conversation_with_title(self, authenticated_client: TestClient):
        """제목 포함 대화 생성 → 201 Created"""
        # Given: 제목이 포함된 요청
        payload = {"title": "Test Conversation"}

        # When: 대화 생성 요청
        response = authenticated_client.post("/api/conversations", json=payload)

        # Then: 201 Created + 대화 정보 반환
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Conversation"
        assert "id" in data
        assert "created_at" in data

    def test_create_conversation_without_title(self, authenticated_client: TestClient):
        """제목 없이 대화 생성 → 201 Created (빈 제목)"""
        # Given: 빈 요청 본문
        payload = {}

        # When: 대화 생성 요청
        response = authenticated_client.post("/api/conversations", json=payload)

        # Then: 201 Created + 빈 제목
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == ""
        assert "id" in data

    def test_create_conversation_without_auth(self, authenticated_client: TestClient):
        """인증 없이 대화 생성 → 403 Forbidden"""
        # Given: 인증 헤더 없는 요청
        payload = {"title": "Unauthorized"}

        # When: 토큰 없이 요청
        response = authenticated_client.post(
            "/api/conversations",
            json=payload,
            headers={"X-Extension-Token": "invalid-token"},
        )

        # Then: 403 Forbidden
        assert response.status_code == 403
