"""Integration Test Fixtures

공통 fixture:
- temp_data_dir: 임시 데이터 디렉토리
- authenticated_client: 인증된 TestClient (lifespan 포함)
- mock_mcp_toolset_in_ci: CI 환경에서만 MCPToolset Mock (autouse)

공통 상수:
- TEST_TOKEN: 테스트용 Extension 토큰
- MCP_TEST_URL: 로컬 MCP 테스트 서버 URL (Synapse)

환경 기반 동작:
- 로컬 (CI 변수 없음): 실제 MCP 서버 사용 (http://localhost:9000/mcp)
- CI (CI=true): Mock MCPToolset 사용 (실제 서버 불필요)
"""

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.adapters.inbound.http.app import create_app
from src.adapters.inbound.http.security import token_provider

# 테스트용 상수
TEST_TOKEN = "test-extension-token"
MCP_TEST_URL = "http://127.0.0.1:9000/mcp"  # 로컬 MCP 테스트 서버 (기본, 무인증)

# Phase 5-B: 다중 포트 인증 테스트용 URL (Synapse --multi)
MCP_AUTH_TEST_URLS = {
    "no_auth": "http://127.0.0.1:9000/mcp",  # 무인증 (기본)
    "api_key": "http://127.0.0.1:9001/mcp",  # API Key 인증
    "oauth": "http://127.0.0.1:9002/mcp",  # OAuth 2.0 인증
}


@pytest.fixture
def temp_data_dir() -> Iterator[Path]:
    """임시 데이터 디렉토리 생성"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(autouse=True)
def mock_mcp_toolset_in_ci():
    """
    CI 환경에서만 MCPToolset Mock 적용 (autouse)

    동작 방식:
    - CI 환경 (CI=true): MCPToolset을 Mock으로 대체
      - 실제 MCP 서버 없이도 테스트 통과
      - GitHub Actions CI에서 자동 적용
    - 로컬 환경: Mock 없이 실제 MCP 서버 사용
      - http://localhost:9000/mcp 서버 필요
      - 더 현실적인 통합 테스트

    실제 MCP 서버 실행:
    ```bash
    cd C:\\Users\\sungb\\Documents\\GitHub\\MCP_SERVER\\MCP_Streamable_HTTP

    # 단일 포트 (기본, 무인증)
    python -m synapse  # Port 9000

    # 다중 포트 (Phase 5-B 인증 테스트)
    # PowerShell:
    # $env:SYNAPSE_PORTS="9000,9001,9002"
    # $env:SYNAPSE_PORT_9000_AUTH="none"
    # $env:SYNAPSE_PORT_9001_AUTH="apikey"
    # $env:SYNAPSE_PORT_9001_API_KEYS='["test-key-1"]'
    # $env:SYNAPSE_PORT_9002_AUTH="oauth"
    # python -m synapse --multi
    ```
    """
    if os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true":
        # CI 환경: Mock MCPToolset 사용
        mock_toolset = AsyncMock()
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test tool"
        mock_tool.input_schema = {"type": "object"}
        mock_toolset.get_tools = AsyncMock(return_value=[mock_tool])
        mock_toolset.close = AsyncMock()

        with patch(
            "src.adapters.outbound.adk.dynamic_toolset.MCPToolset", return_value=mock_toolset
        ):
            yield
    else:
        # 로컬 환경: Mock 없이 실제 서버 사용
        yield


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

    # Container 재설정 (임시 데이터 디렉토리 + LLM 테스트용 모델)
    container.reset_singletons()
    container.settings().storage.data_dir = str(temp_data_dir)
    container.settings().llm.default_model = "openai/gpt-4o-mini"

    # Context manager로 lifespan 트리거
    with TestClient(app) as test_client:
        # 모든 요청에 인증 헤더 추가
        test_client.headers.update({"X-Extension-Token": TEST_TOKEN})
        yield test_client

    # Cleanup
    container.reset_singletons()
    container.unwire()
