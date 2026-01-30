"""
AgentHub 공통 테스트 픽스처

이 파일은 모든 테스트에서 공유되는 픽스처를 정의합니다.
pytest가 자동으로 이 파일을 로드합니다.
"""

from dotenv import load_dotenv

# .env 파일 로드 (LLM 테스트에서 API 키 필요)
load_dotenv()

import pytest  # noqa: E402


def pytest_addoption(parser):
    """pytest 커스텀 옵션 추가"""
    parser.addoption(
        "--run-llm",
        action="store_true",
        default=False,
        help="Run LLM integration tests (requires API key)",
    )


# ============================================================
# Session Fixtures (테스트 세션당 1회)
# ============================================================


@pytest.fixture(scope="session")
def test_config():
    """테스트용 설정"""
    return {
        "database": ":memory:",
        "debug": True,
    }


# ============================================================
# Function Fixtures (각 테스트마다)
# ============================================================


@pytest.fixture
def sample_mcp_url():
    """테스트용 MCP 서버 URL"""
    return "https://example-server.modelcontextprotocol.io/mcp"


@pytest.fixture
def sample_endpoint_data():
    """테스트용 엔드포인트 데이터"""
    return {
        "name": "Test MCP Server",
        "url": "https://example.com/mcp",
        "type": "MCP",
    }
