"""Integration Test Fixtures"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

# 테스트용 상수 (secrets.token_urlsafe(32)와 동일한 길이: 43 characters)
TEST_EXTENSION_TOKEN = "test-extension-token-1234567890abcdefghijkl"


@pytest.fixture(scope="session")
def mcp_test_server_url():
    """MCP 테스트 서버 URL (로컬 Synapse)

    Usage: SYNAPSE_PORT=9000 python -m synapse
    """
    return "http://127.0.0.1:9000/mcp"


@pytest.fixture
def temp_database(tmp_path):
    """임시 SQLite 데이터베이스 경로"""
    return str(tmp_path / "test.db")


@pytest.fixture
def http_client(tmp_path) -> Iterator[TestClient]:
    """
    FastAPI TestClient for HTTP integration tests

    Phase 1.5 Security Layer 테스트용 픽스처
    Phase 4 Part B: Container 재설정으로 임시 데이터베이스 사용

    Note: 인증 토큰은 자동으로 추가되지 않음.
    필요 시 수동으로 헤더 추가 필요.
    """
    from src.adapters.inbound.http.app import create_app
    from src.adapters.inbound.http.security import token_provider

    # 테스트용 토큰 생성 및 주입
    token_provider.reset(TEST_EXTENSION_TOKEN)

    # FastAPI 앱 생성
    app = create_app()
    container = app.container

    # Container 재설정 (임시 데이터 디렉토리)
    container.reset_singletons()
    container.settings().storage.data_dir = str(tmp_path)

    # Context manager로 lifespan 트리거 (SQLite 초기화)
    with TestClient(app) as test_client:
        yield test_client

    # Cleanup
    container.reset_singletons()
    container.unwire()
