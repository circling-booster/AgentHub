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


class TestListConversations:
    """GET /api/conversations - 대화 목록 조회"""

    def test_list_conversations_empty(self, authenticated_client: TestClient):
        """대화 없을 때 빈 목록 반환"""
        # When: 대화 목록 조회
        response = authenticated_client.get("/api/conversations")

        # Then: 200 OK + 빈 목록
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_conversations_with_data(self, authenticated_client: TestClient):
        """대화 생성 후 목록 조회 시 결과 포함"""
        # Given: 대화 2개 생성
        authenticated_client.post("/api/conversations", json={"title": "First"})
        authenticated_client.post("/api/conversations", json={"title": "Second"})

        # When: 대화 목록 조회
        response = authenticated_client.get("/api/conversations")

        # Then: 200 OK + 2개 대화 반환
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # 각 대화에 필수 필드 포함
        for conv in data:
            assert "id" in conv
            assert "title" in conv
            assert "created_at" in conv

    def test_list_conversations_with_limit(self, authenticated_client: TestClient):
        """limit 파라미터로 결과 수 제한"""
        # Given: 대화 3개 생성
        for i in range(3):
            authenticated_client.post("/api/conversations", json={"title": f"Conv {i}"})

        # When: limit=2로 조회
        response = authenticated_client.get("/api/conversations?limit=2")

        # Then: 200 OK + 최대 2개 반환
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_conversations_without_auth(self, authenticated_client: TestClient):
        """인증 없이 목록 조회 → 403 Forbidden"""
        # When: 잘못된 토큰으로 요청
        response = authenticated_client.get(
            "/api/conversations",
            headers={"X-Extension-Token": "invalid-token"},
        )

        # Then: 403 Forbidden
        assert response.status_code == 403


class TestConversationDeletion:
    """DELETE /api/conversations/{id} - 대화 삭제"""

    def test_delete_conversation_success(self, authenticated_client: TestClient):
        """대화 삭제 성공 → 204 No Content"""
        # Given: 대화 생성
        response = authenticated_client.post(
            "/api/conversations", json={"title": "Test Conversation"}
        )
        assert response.status_code == 201
        conversation_id = response.json()["id"]

        # When: 대화 삭제
        delete_response = authenticated_client.delete(
            f"/api/conversations/{conversation_id}"
        )

        # Then: 204 No Content
        assert delete_response.status_code == 204

        # And: 대화가 목록에서 사라짐
        list_response = authenticated_client.get("/api/conversations")
        conversations = list_response.json()
        assert conversation_id not in [c["id"] for c in conversations]

    def test_delete_conversation_not_found(self, authenticated_client: TestClient):
        """존재하지 않는 대화 삭제 → 404 Not Found"""
        # When: 존재하지 않는 ID 삭제
        response = authenticated_client.delete("/api/conversations/nonexistent-id")

        # Then: 404 Not Found
        assert response.status_code == 404

    def test_delete_conversation_removes_tool_calls(self, authenticated_client: TestClient):
        """대화 삭제 시 관련 tool calls도 함께 삭제"""
        # Given: 대화 + 메시지 생성 (tool calls 포함 가능)
        response = authenticated_client.post(
            "/api/conversations", json={"title": "Test"}
        )
        assert response.status_code == 201
        conversation_id = response.json()["id"]

        # When: 대화 삭제
        delete_response = authenticated_client.delete(
            f"/api/conversations/{conversation_id}"
        )
        assert delete_response.status_code == 204

        # Then: Tool Calls도 함께 삭제 (GET 시 404)
        tool_calls_response = authenticated_client.get(
            f"/api/conversations/{conversation_id}/tool-calls"
        )
        assert tool_calls_response.status_code == 404
