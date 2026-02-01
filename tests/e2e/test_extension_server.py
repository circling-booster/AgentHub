"""Extension ↔ Server E2E Tests

Extension이 사용하는 전체 API 시퀀스를 서버 측에서 검증합니다.
실제 Extension 없이 TestClient로 Extension의 API 호출 패턴을 시뮬레이션합니다.

테스트 시나리오:
1. Health Check → 토큰 교환 → 대화 생성 → SSE 채팅 → 대화 목록 조회
2. MCP 서버 등록 → 목록 조회 → 삭제
3. 토큰 없이 API 호출 시 403

실행:
    pytest tests/e2e/test_extension_server.py -v
"""

import json
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.adapters.inbound.http.app import create_app
from src.adapters.inbound.http.security import token_provider

TEST_TOKEN = "e2e-test-extension-token"


@pytest.fixture
def temp_data_dir() -> Iterator[Path]:
    """임시 데이터 디렉토리"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def app_client(temp_data_dir: Path) -> Iterator[TestClient]:
    """인증되지 않은 TestClient (토큰 교환 테스트용)"""
    token_provider.reset(TEST_TOKEN)
    app = create_app()
    container = app.container
    container.reset_singletons()
    container.settings().storage.data_dir = str(temp_data_dir)

    with TestClient(app) as client:
        yield client

    container.reset_singletons()
    container.unwire()


@pytest.fixture
def authenticated_client(temp_data_dir: Path) -> Iterator[TestClient]:
    """인증된 TestClient"""
    token_provider.reset(TEST_TOKEN)
    app = create_app()
    container = app.container
    container.reset_singletons()
    container.settings().storage.data_dir = str(temp_data_dir)

    with TestClient(app) as client:
        client.headers.update({"X-Extension-Token": TEST_TOKEN})
        yield client

    container.reset_singletons()
    container.unwire()


class TestFullChatFlow:
    """Extension 채팅 전체 흐름 시뮬레이션"""

    def test_health_check(self, app_client):
        """
        Step 1: Health Check (토큰 불필요)
        Extension Background가 30초마다 호출하는 엔드포인트
        """
        response = app_client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"

    def test_token_exchange(self, app_client):
        """
        Step 2: 토큰 교환
        Extension 설치/시작 시 Background가 호출
        """
        response = app_client.post(
            "/auth/token",
            json={"extension_id": "test-extension-id"},
            headers={"Origin": "chrome-extension://test-extension-id"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "token" in data
        assert len(data["token"]) > 0

    def test_create_conversation_and_list(self, authenticated_client):
        """
        Step 3: 대화 생성 + 목록 조회
        Extension Sidepanel에서 새 대화 시작 및 이력 조회
        """
        # 대화 생성
        response = authenticated_client.post(
            "/api/conversations",
            json={"title": "E2E Test Conversation"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        conv = response.json()
        assert "id" in conv
        assert conv["title"] == "E2E Test Conversation"

        # 대화 목록 조회
        list_response = authenticated_client.get("/api/conversations")
        assert list_response.status_code == status.HTTP_200_OK
        conversations = list_response.json()
        assert len(conversations) >= 1
        assert any(c["id"] == conv["id"] for c in conversations)

    def test_chat_stream_with_auto_conversation(self, authenticated_client):
        """
        Step 4: SSE 스트리밍 채팅 (conversation_id 없이)
        Extension이 conversation_id=null로 첫 메시지 전송 시 자동 생성
        """
        payload = {"message": "Hello from E2E test"}

        response = authenticated_client.post("/api/chat/stream", json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert "text/event-stream" in response.headers["content-type"]

        # SSE 이벤트 파싱
        events = []
        for line in response.text.strip().split("\n"):
            if line.startswith("data: "):
                event = json.loads(line[6:])
                events.append(event)

        # conversation_created 이벤트가 첫 번째
        assert len(events) >= 1
        assert events[0]["type"] == "conversation_created"
        assert "conversation_id" in events[0]

    def test_chat_stream_with_existing_conversation(self, authenticated_client):
        """
        Step 5: 기존 대화에 메시지 추가
        Extension이 conversationId를 포함하여 후속 메시지 전송
        """
        # 대화 먼저 생성
        conv_response = authenticated_client.post(
            "/api/conversations",
            json={"title": "E2E Follow-up Test"},
        )
        conv_id = conv_response.json()["id"]

        # 해당 대화에 메시지 전송
        payload = {"conversation_id": conv_id, "message": "Follow-up message"}
        response = authenticated_client.post("/api/chat/stream", json=payload)
        assert response.status_code == status.HTTP_200_OK

        # conversation_created 이벤트가 없어야 함 (이미 존재하는 대화)
        events = []
        for line in response.text.strip().split("\n"):
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))

        conversation_created = [e for e in events if e["type"] == "conversation_created"]
        assert len(conversation_created) == 0


class TestMcpManagementFlow:
    """Extension MCP 서버 관리 흐름 시뮬레이션"""

    def test_list_servers_empty(self, authenticated_client):
        """초기 상태: 서버 목록 비어있음"""
        response = authenticated_client.get("/api/mcp/servers")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @pytest.mark.mcp
    def test_register_and_list_server(self, authenticated_client, request):
        """MCP 서버 등록 후 목록에 표시"""
        if not request.config.getoption("--run-mcp", default=False):
            pytest.skip("MCP 테스트는 --run-mcp 옵션 필요 (로컬 MCP 서버 필요)")

        # 서버 등록
        response = authenticated_client.post(
            "/api/mcp/servers",
            json={"url": "http://127.0.0.1:9000/mcp", "name": "E2E Test Server"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        server = response.json()
        assert "id" in server

        # 목록 조회
        list_response = authenticated_client.get("/api/mcp/servers")
        servers = list_response.json()
        assert len(servers) >= 1
        assert any(s["id"] == server["id"] for s in servers)

    @pytest.mark.mcp
    def test_register_list_and_remove_server(self, authenticated_client, request):
        """MCP 서버 등록 → 조회 → 삭제 전체 사이클"""
        if not request.config.getoption("--run-mcp", default=False):
            pytest.skip("MCP 테스트는 --run-mcp 옵션 필요 (로컬 MCP 서버 필요)")

        # 등록
        reg_response = authenticated_client.post(
            "/api/mcp/servers",
            json={"url": "http://127.0.0.1:9000/mcp", "name": "E2E Remove Test"},
        )
        server_id = reg_response.json()["id"]

        # 조회 확인
        list_response = authenticated_client.get("/api/mcp/servers")
        assert any(s["id"] == server_id for s in list_response.json())

        # 삭제
        delete_response = authenticated_client.delete(f"/api/mcp/servers/{server_id}")
        assert delete_response.status_code == status.HTTP_200_OK

        # 삭제 확인
        list_after = authenticated_client.get("/api/mcp/servers")
        assert not any(s["id"] == server_id for s in list_after.json())


class TestTokenRequired:
    """인증 필수 검증"""

    def test_api_without_token_returns_403(self, app_client):
        """토큰 없이 /api/* 호출 시 403"""
        # 대화 목록
        response = app_client.get("/api/conversations")
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # MCP 서버 목록
        response = app_client.get("/api/mcp/servers")
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # 채팅 스트리밍
        response = app_client.post(
            "/api/chat/stream",
            json={"message": "Hello"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_api_with_wrong_token_returns_403(self, app_client):
        """잘못된 토큰으로 /api/* 호출 시 403"""
        response = app_client.get(
            "/api/conversations",
            headers={"X-Extension-Token": "wrong-token-value"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_health_without_token_ok(self, app_client):
        """/health는 토큰 불필요"""
        response = app_client.get("/health")
        assert response.status_code == status.HTTP_200_OK

    def test_auth_token_without_token_ok(self, app_client):
        """/auth/token은 토큰 불필요 (토큰 교환용)"""
        response = app_client.post(
            "/auth/token",
            json={"extension_id": "test-id"},
            headers={"Origin": "chrome-extension://test-id"},
        )
        assert response.status_code == status.HTTP_200_OK
