"""Chat Route Typed Error Propagation 테스트

Step 3: 도메인 예외가 SSE 에러 이벤트에 typed error_code로 전파되는지 검증
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.adapters.inbound.http.app import create_app
from src.adapters.inbound.http.security import token_provider
from src.domain.exceptions import (
    EndpointConnectionError,
    LlmAuthenticationError,
    LlmRateLimitError,
)

TEST_TOKEN = "test-error-token"


def _parse_sse_events(response) -> list[dict]:
    """SSE 이벤트 파싱 헬퍼"""
    events = []
    for line in response.text.split("\n"):
        if line.startswith("data: "):
            data = line[6:]
            events.append(json.loads(data))
    return events


def _make_failing_orchestrator_service(exception):
    """특정 예외를 발생시키는 OrchestratorService Mock"""
    mock_service = MagicMock()

    async def failing_send(*args, **kwargs):
        """async generator가 즉시 예외를 발생시킴"""
        raise exception
        yield  # noqa: RET503  # async generator로 만들기 위한 unreachable yield

    mock_service.send_message = failing_send
    mock_service.create_conversation = AsyncMock(return_value=MagicMock(id="conv-error-test"))
    return mock_service


class TestChatTypedErrorPropagation:
    """도메인 예외 → SSE error 이벤트 typed code 전파 검증"""

    @pytest.fixture
    def tmp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def _create_client_with_failing_service(self, tmp_dir, exception):
        """특정 예외를 던지는 OrchestratorService를 가진 TestClient 생성"""
        token_provider.reset(TEST_TOKEN)
        app = create_app()
        container = app.container
        container.reset_singletons()
        container.settings().storage.data_dir = str(tmp_dir)

        # DI 컨테이너의 orchestrator_service를 오버라이드
        mock_service = _make_failing_orchestrator_service(exception)
        container.orchestrator_service.override(mock_service)

        client = TestClient(app)
        client.headers.update({"X-Extension-Token": TEST_TOKEN})
        return client, container

    def test_rate_limit_error_has_typed_code(self, tmp_dir):
        """
        Given: LLM이 RateLimitError를 발생시킴
        When: POST /api/chat/stream
        Then: SSE error 이벤트에 error_code="LlmRateLimitError" 포함
        """
        client, container = self._create_client_with_failing_service(
            tmp_dir, LlmRateLimitError("Rate limit exceeded")
        )
        try:
            response = client.post(
                "/api/chat/stream",
                json={"message": "Hello"},
            )
            assert response.status_code == status.HTTP_200_OK
            events = _parse_sse_events(response)
            error_events = [e for e in events if e["type"] == "error"]
            assert len(error_events) >= 1
            assert error_events[0]["error_code"] == "LlmRateLimitError"
            assert "Rate limit exceeded" in error_events[0]["content"]
        finally:
            container.orchestrator_service.reset_override()
            container.reset_singletons()
            container.unwire()

    def test_auth_error_has_typed_code(self, tmp_dir):
        """
        Given: LLM 인증 실패
        When: POST /api/chat/stream
        Then: SSE error 이벤트에 error_code="LlmAuthenticationError" 포함
        """
        client, container = self._create_client_with_failing_service(
            tmp_dir, LlmAuthenticationError("Invalid API key")
        )
        try:
            response = client.post(
                "/api/chat/stream",
                json={"message": "Hello"},
            )
            events = _parse_sse_events(response)
            error_events = [e for e in events if e["type"] == "error"]
            assert len(error_events) >= 1
            assert error_events[0]["error_code"] == "LlmAuthenticationError"
        finally:
            container.orchestrator_service.reset_override()
            container.reset_singletons()
            container.unwire()

    def test_connection_error_has_typed_code(self, tmp_dir):
        """
        Given: 엔드포인트 연결 실패
        When: POST /api/chat/stream
        Then: SSE error 이벤트에 error_code="EndpointConnectionError" 포함
        """
        client, container = self._create_client_with_failing_service(
            tmp_dir, EndpointConnectionError("Connection refused")
        )
        try:
            response = client.post(
                "/api/chat/stream",
                json={"message": "Hello"},
            )
            events = _parse_sse_events(response)
            error_events = [e for e in events if e["type"] == "error"]
            assert len(error_events) >= 1
            assert error_events[0]["error_code"] == "EndpointConnectionError"
        finally:
            container.orchestrator_service.reset_override()
            container.reset_singletons()
            container.unwire()

    def test_unknown_error_has_generic_code(self, tmp_dir):
        """
        Given: 예상하지 못한 예외 발생
        When: POST /api/chat/stream
        Then: SSE error 이벤트에 error_code="UnknownError" 포함
        """
        client, container = self._create_client_with_failing_service(
            tmp_dir, ValueError("Something unexpected")
        )
        try:
            response = client.post(
                "/api/chat/stream",
                json={"message": "Hello"},
            )
            events = _parse_sse_events(response)
            error_events = [e for e in events if e["type"] == "error"]
            assert len(error_events) >= 1
            assert error_events[0]["error_code"] == "UnknownError"
        finally:
            container.orchestrator_service.reset_override()
            container.reset_singletons()
            container.unwire()
