"""Integration Test Fixtures"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def mcp_test_server_url():
    """MCP 테스트 서버 URL"""
    return "https://example-server.modelcontextprotocol.io/mcp"


@pytest.fixture
def temp_database(tmp_path):
    """임시 SQLite 데이터베이스 경로"""
    return str(tmp_path / "test.db")


@pytest.fixture
def http_client():
    """
    FastAPI TestClient for HTTP integration tests

    Phase 1.5 Security Layer 테스트용 픽스처
    """
    from adapters.inbound.http.app import create_app

    app = create_app()
    return TestClient(app)
