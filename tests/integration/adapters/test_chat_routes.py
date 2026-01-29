"""Chat Streaming Routes Integration Tests

TDD Phase: GREEN - 구현 완료
"""

import json

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.adapters.inbound.http.app import create_app
from src.adapters.inbound.http.security import token_provider

from .conftest import TEST_TOKEN


class TestChatStreaming:
    """POST /api/chat/stream - SSE 스트리밍 채팅"""

    @pytest.mark.llm
    def test_chat_stream_basic(self, authenticated_client, request):
        """
        Given: 간단한 채팅 메시지
        When: POST /api/chat/stream 호출
        Then: 200 OK, SSE 스트리밍 응답
        """
        if not request.config.getoption("--run-llm"):
            pytest.skip("LLM 테스트는 --run-llm 옵션 필요 (비용 발생)")

        # Given: 채팅 요청
        payload = {"conversation_id": "test-conv-1", "message": "Say hello"}

        # When: 스트리밍 채팅 호출
        with authenticated_client.stream("POST", "/api/chat/stream", json=payload) as response:
            # Then: 200 OK
            assert response.status_code == status.HTTP_200_OK
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

            # SSE 이벤트 파싱
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # "data: " 제거
                    event = json.loads(data)
                    events.append(event)

            # 최소 1개 이벤트 수신
            assert len(events) >= 1

            # 마지막 이벤트는 "done"
            assert events[-1]["type"] == "done"

            # "text" 이벤트 존재
            text_events = [e for e in events if e["type"] == "text"]
            assert len(text_events) > 0

    def test_chat_stream_invalid_request(self, authenticated_client):
        """
        Given: 잘못된 요청 (빈 메시지)
        When: POST /api/chat/stream 호출
        Then: 422 Unprocessable Entity
        """
        # Given: 빈 메시지
        payload = {"conversation_id": "test-conv-1", "message": ""}

        # When: 스트리밍 채팅 호출
        response = authenticated_client.post("/api/chat/stream", json=payload)

        # Then: 422 Validation Error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_chat_stream_without_auth(self, temp_data_dir):
        """
        Given: 인증 토큰 없음
        When: POST /api/chat/stream 호출
        Then: 403 Forbidden
        """
        # Given: 토큰 주입하지 않은 별도 클라이언트 (authenticated_client fixture 사용 X)
        # 이유: authenticated_client fixture는 이미 X-Extension-Token 헤더를 설정하므로,
        # 토큰 없는 요청을 테스트하려면 별도 클라이언트 필요
        token_provider.reset(TEST_TOKEN)
        app = create_app()
        container = app.container
        container.reset_singletons()
        container.settings().storage.data_dir = str(temp_data_dir)

        with TestClient(app) as test_authenticated_client:
            # When: 토큰 헤더 없이 요청
            response = test_authenticated_client.post(
                "/api/chat/stream",
                json={"conversation_id": "test-conv-1", "message": "Hello"},
            )

            # Then: 403 Forbidden
            assert response.status_code == status.HTTP_403_FORBIDDEN

        container.reset_singletons()
        container.unwire()

    @pytest.mark.llm
    def test_chat_stream_multiple_messages(self, authenticated_client, request):
        """
        Given: 동일 conversation_id로 여러 메시지
        When: POST /api/chat/stream 연속 호출
        Then: 각 요청마다 독립적인 스트리밍 응답
        """
        if not request.config.getoption("--run-llm"):
            pytest.skip("LLM 테스트는 --run-llm 옵션 필요 (비용 발생)")

        # Given: 동일 conversation_id
        conv_id = "test-conv-multi"

        # When: 첫 번째 메시지
        payload1 = {"conversation_id": conv_id, "message": "First message"}
        with authenticated_client.stream("POST", "/api/chat/stream", json=payload1) as response1:
            events1 = []
            for line in response1.iter_lines():
                if line.startswith("data: "):
                    events1.append(json.loads(line[6:]))

        # When: 두 번째 메시지
        payload2 = {"conversation_id": conv_id, "message": "Second message"}
        with authenticated_client.stream("POST", "/api/chat/stream", json=payload2) as response2:
            events2 = []
            for line in response2.iter_lines():
                if line.startswith("data: "):
                    events2.append(json.loads(line[6:]))

        # Then: 두 응답 모두 정상
        assert len(events1) >= 1
        assert len(events2) >= 1
        assert events1[-1]["type"] == "done"
        assert events2[-1]["type"] == "done"
