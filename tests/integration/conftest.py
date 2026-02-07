"""Integration Test Fixtures"""

from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# 테스트용 상수 (DRY: adapters/conftest.py TEST_TOKEN과 통합)
TEST_EXTENSION_TOKEN = "test-extension-token"


# Re-export authenticated_client from adapters/conftest.py
# This makes it available to all integration tests, not just adapters/ subdirectory
@pytest.fixture
async def authenticated_client(tmp_path: Path) -> AsyncIterator[TestClient]:
    """
    인증된 TestClient 인스턴스 (공통 fixture)

    특징:
    - 테스트용 토큰 주입
    - 독립 스토리지 (임시 데이터 디렉토리)
    - Lifespan 이벤트 트리거 (SQLite 초기화)
    - X-Extension-Token 헤더 자동 추가
    - Container override로 테스트용 storage 주입

    Note: tests/integration/adapters/conftest.py의 authenticated_client와 동일한 구현
    """
    from dependency_injector import providers

    from src.adapters.inbound.http.app import create_app
    from src.adapters.inbound.http.security import token_provider
    from src.adapters.outbound.storage.sqlite_conversation_storage import (
        SqliteConversationStorage,
    )
    from src.adapters.outbound.storage.sqlite_usage import SqliteUsageStorage

    # 테스트용 토큰 주입
    token_provider.reset(TEST_EXTENSION_TOKEN)

    # FastAPI 앱 생성
    app = create_app()
    container = app.container

    # Container 재설정 (임시 데이터 디렉토리 + LLM 테스트용 모델)
    container.reset_singletons()
    container.settings().storage.data_dir = str(tmp_path)
    container.settings().llm.default_model = "openai/gpt-4o-mini"

    # Override providers with correct paths
    conv_db_path = str(tmp_path / "agenthub.db")
    usage_db_path = str(tmp_path / "usage.db")

    container.conversation_storage.override(
        providers.Singleton(SqliteConversationStorage, db_path=conv_db_path)
    )
    container.usage_storage.override(providers.Singleton(SqliteUsageStorage, db_path=usage_db_path))

    # Context manager로 lifespan 트리거
    with TestClient(app) as test_client:
        # 모든 요청에 인증 헤더 추가
        test_client.headers.update({"X-Extension-Token": TEST_EXTENSION_TOKEN})

        # Storage 초기화 (override된 인스턴스)
        conv_storage = container.conversation_storage()
        usage_storage = container.usage_storage()
        orchestrator = container.orchestrator_adapter()

        # 비동기 초기화
        await conv_storage.initialize()
        await usage_storage.initialize()
        await orchestrator.initialize()

        yield test_client

        # Cleanup: 연결 종료
        await conv_storage.close()
        await usage_storage.close()
        await orchestrator.close()

    # Cleanup
    container.conversation_storage.reset_override()
    container.usage_storage.reset_override()
    container.reset_singletons()
    container.unwire()


@pytest.fixture(scope="session")
def mcp_test_server_url():
    """MCP 테스트 서버 URL (로컬 Synapse)

    Usage: MCP_TEST_PORT=9000 python -m synapse
    Env var: MCP_TEST_PORT (default: 9000)
    """
    import os

    port = int(os.environ.get("MCP_TEST_PORT", "9000"))
    return f"http://127.0.0.1:{port}/mcp"


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
