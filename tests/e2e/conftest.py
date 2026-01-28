"""E2E Test Fixtures"""

import pytest


@pytest.fixture(scope="session")
def server_url():
    """테스트 서버 URL"""
    return "http://localhost:8000"
