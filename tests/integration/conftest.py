"""Integration Test Fixtures"""

import pytest


@pytest.fixture(scope="session")
def mcp_test_server_url():
    """MCP 테스트 서버 URL"""
    return "https://example-server.modelcontextprotocol.io/mcp"


@pytest.fixture
def temp_database(tmp_path):
    """임시 SQLite 데이터베이스 경로"""
    return str(tmp_path / "test.db")
