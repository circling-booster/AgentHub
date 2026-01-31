"""
AgentHub 공통 테스트 픽스처

이 파일은 모든 테스트에서 공유되는 픽스처를 정의합니다.
pytest가 자동으로 이 파일을 로드합니다.
"""

import subprocess
import sys
import time
from pathlib import Path

import httpx
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


def pytest_configure(config):
    """pytest 마커 등록"""
    config.addinivalue_line("markers", "local_a2a: mark test as requiring local A2A agent")
    config.addinivalue_line("markers", "local_mcp: mark test as requiring local MCP server")


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
    return "http://127.0.0.1:9000/mcp"


@pytest.fixture
def sample_endpoint_data():
    """테스트용 엔드포인트 데이터"""
    return {
        "name": "Test MCP Server",
        "url": "https://example.com/mcp",
        "type": "MCP",
    }


# ============================================================
# A2A Test Server Fixtures (Session-scoped)
# ============================================================


def _get_free_port() -> int:
    """Get a free port for dynamic allocation"""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _wait_for_health(url: str, timeout: int = 10) -> bool:
    """
    Wait for A2A server to be ready by checking agent card endpoint.

    Args:
        url: Base URL (checks {url}/.well-known/agent.json)
        timeout: Max seconds to wait

    Returns:
        True if ready, False if timeout
    """
    agent_card_url = f"{url}/.well-known/agent.json"
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = httpx.get(agent_card_url, timeout=2.0)
            if response.status_code == 200:
                return True
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        time.sleep(0.5)

    return False


@pytest.fixture(scope="session")
def a2a_echo_agent():
    """
    A2A Echo Agent subprocess fixture (port 9001).

    Automatically starts the echo agent server before tests
    and terminates it after the session ends.

    Returns:
        Base URL of the echo agent (http://127.0.0.1:9001)
    """
    # Echo agent script path
    echo_script = Path(__file__).parent / "fixtures" / "a2a_agents" / "echo_agent.py"

    if not echo_script.exists():
        pytest.skip(f"Echo agent script not found: {echo_script}")

    port = 9001
    base_url = f"http://127.0.0.1:{port}"

    # Start echo agent subprocess
    proc = subprocess.Popen(
        [sys.executable, str(echo_script), str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait for health check (A2A server may take 15s to start)
    if not _wait_for_health(base_url, timeout=20):
        proc.terminate()
        stdout, stderr = proc.communicate(timeout=5)
        error_msg = f"Echo agent failed to start on port {port}\n"
        if stderr:
            error_msg += f"STDERR:\n{stderr}\n"
        if stdout:
            error_msg += f"STDOUT:\n{stdout}\n"
        pytest.fail(error_msg)

    print(f"\n✓ A2A Echo Agent started: {base_url}")

    yield base_url

    # Cleanup
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()

    print("\n✓ A2A Echo Agent stopped")


@pytest.fixture(scope="session")
def a2a_math_agent():
    """
    A2A Math Agent subprocess fixture (dynamic port).

    Automatically starts the math agent server before tests
    and terminates it after the session ends.

    Returns:
        Base URL of the math agent (http://127.0.0.1:{port})
    """
    math_script = Path(__file__).parent / "fixtures" / "a2a_agents" / "math_agent.py"

    if not math_script.exists():
        pytest.skip(f"Math agent script not found: {math_script}")

    port = _get_free_port()
    base_url = f"http://127.0.0.1:{port}"

    # Start math agent subprocess
    proc = subprocess.Popen(
        [sys.executable, str(math_script), str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait for health check (LLM agent may take longer to start)
    if not _wait_for_health(base_url, timeout=30):
        proc.terminate()
        stdout, stderr = proc.communicate(timeout=5)
        error_msg = f"Math agent failed to start on port {port}\n"
        if stderr:
            error_msg += f"STDERR:\n{stderr}\n"
        if stdout:
            error_msg += f"STDOUT:\n{stdout}\n"
        pytest.fail(error_msg)

    print(f"\n✓ A2A Math Agent started: {base_url}")

    yield base_url

    # Cleanup
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()

    print("\n✓ A2A Math Agent stopped")
