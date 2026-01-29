"""HTTP Exception Handler Integration Tests

TDD Phase: RED - 테스트 먼저 작성
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.adapters.inbound.http.exceptions import (
    register_exception_handlers,
)
from src.domain.exceptions import (
    DomainException,
    EndpointConnectionError,
    EndpointNotFoundError,
    EndpointTimeoutError,
    LlmAuthenticationError,
    LlmRateLimitError,
    ToolNotFoundError,
)


@pytest.fixture
def app():
    """FastAPI 앱 인스턴스 (예외 핸들러 등록됨)"""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test/endpoint-not-found")
    async def endpoint_not_found():
        raise EndpointNotFoundError("Endpoint not found: test-server")

    @app.get("/test/tool-not-found")
    async def tool_not_found():
        raise ToolNotFoundError("Tool not found: test_tool")

    @app.get("/test/connection-error")
    async def connection_error():
        raise EndpointConnectionError("Connection refused: test-server")

    @app.get("/test/timeout-error")
    async def timeout_error():
        raise EndpointTimeoutError("Request timeout: test-server")

    @app.get("/test/llm-auth-error")
    async def llm_auth_error():
        raise LlmAuthenticationError("Invalid API key")

    @app.get("/test/llm-rate-limit")
    async def llm_rate_limit():
        raise LlmRateLimitError("Rate limit exceeded")

    @app.get("/test/generic-domain-error")
    async def generic_domain_error():
        raise DomainException("Generic domain error", code="GENERIC_ERROR")

    return app


@pytest.fixture
def client(app):
    """TestClient 인스턴스"""
    return TestClient(app)


class TestDomainExceptionHandler:
    """Domain Exception → HTTP 응답 변환 검증"""

    def test_endpoint_not_found_returns_404(self, client):
        """EndpointNotFoundError → 404 Not Found"""
        # When: EndpointNotFoundError 발생
        response = client.get("/test/endpoint-not-found")

        # Then: 404 응답
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "EndpointNotFoundError"
        assert data["code"] == "EndpointNotFoundError"
        assert "Endpoint not found" in data["message"]

    def test_tool_not_found_returns_404(self, client):
        """ToolNotFoundError → 404 Not Found"""
        # When: ToolNotFoundError 발생
        response = client.get("/test/tool-not-found")

        # Then: 404 응답
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "ToolNotFoundError"
        assert "Tool not found" in data["message"]

    def test_connection_error_returns_502(self, client):
        """EndpointConnectionError → 502 Bad Gateway"""
        # When: 연결 실패
        response = client.get("/test/connection-error")

        # Then: 502 응답
        assert response.status_code == 502
        data = response.json()
        assert data["error"] == "EndpointConnectionError"
        assert "Connection refused" in data["message"]

    def test_timeout_error_returns_504(self, client):
        """EndpointTimeoutError → 504 Gateway Timeout"""
        # When: 타임아웃
        response = client.get("/test/timeout-error")

        # Then: 504 응답
        assert response.status_code == 504
        data = response.json()
        assert data["error"] == "EndpointTimeoutError"
        assert "timeout" in data["message"].lower()

    def test_llm_auth_error_returns_401(self, client):
        """LlmAuthenticationError → 401 Unauthorized"""
        # When: LLM API 인증 실패
        response = client.get("/test/llm-auth-error")

        # Then: 401 응답
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "LlmAuthenticationError"
        assert "API key" in data["message"]

    def test_llm_rate_limit_returns_429(self, client):
        """LlmRateLimitError → 429 Too Many Requests"""
        # When: Rate Limit 초과
        response = client.get("/test/llm-rate-limit")

        # Then: 429 응답
        assert response.status_code == 429
        data = response.json()
        assert data["error"] == "LlmRateLimitError"
        assert "Rate limit" in data["message"]

    def test_generic_domain_error_returns_500(self, client):
        """알 수 없는 DomainException → 500 Internal Server Error"""
        # When: 매핑되지 않은 DomainException
        response = client.get("/test/generic-domain-error")

        # Then: 500 응답 (기본값)
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "DomainException"
        assert data["code"] == "GENERIC_ERROR"


class TestExceptionHandlerRegistration:
    """register_exception_handlers() 함수 검증"""

    def test_register_exception_handlers_adds_handler(self):
        """예외 핸들러 등록 검증"""
        # Given: 빈 FastAPI 앱
        app = FastAPI()

        # When: register_exception_handlers 호출
        register_exception_handlers(app)

        # Then: DomainException 핸들러 등록됨
        # FastAPI는 exception_handlers 딕셔너리에 등록
        assert DomainException in app.exception_handlers
