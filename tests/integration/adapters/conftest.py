"""Integration Test Fixtures

공통 fixture:
- temp_data_dir: 임시 데이터 디렉토리
- authenticated_client: 인증된 TestClient (lifespan 포함)
"""

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.adapters.inbound.http.app import create_app
from src.adapters.inbound.http.security import token_provider

# 테스트용 토큰
TEST_TOKEN = "test-extension-token"


@pytest.fixture
def temp_data_dir() -> Iterator[Path]:
    """임시 데이터 디렉토리 생성"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def authenticated_client(temp_data_dir: Path) -> Iterator[TestClient]:
    """
    인증된 TestClient 인스턴스 (공통 fixture)

    특징:
    - 테스트용 토큰 주입
    - 독립 스토리지 (임시 디렉토리)
    - Lifespan 이벤트 트리거 (SQLite 초기화)
    - X-Extension-Token 헤더 자동 추가
    """
    # 테스트용 토큰 주입
    token_provider.reset(TEST_TOKEN)

    # FastAPI 앱 생성
    app = create_app()
    container = app.container

    # Container 재설정 (임시 데이터 디렉토리)
    container.reset_singletons()
    container.settings().storage.data_dir = str(temp_data_dir)

    # Context manager로 lifespan 트리거
    with TestClient(app) as test_client:
        # 모든 요청에 인증 헤더 추가
        test_client.headers.update({"X-Extension-Token": TEST_TOKEN})
        yield test_client

    # Cleanup
    container.reset_singletons()
    container.unwire()
