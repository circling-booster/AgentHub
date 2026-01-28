"""
AgentHub 공통 테스트 픽스처

이 파일은 모든 테스트에서 공유되는 픽스처를 정의합니다.
pytest가 자동으로 이 파일을 로드합니다.
"""

import pytest

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
