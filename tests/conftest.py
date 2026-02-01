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
    """테스트용 MCP 서버 URL (기본, 무인증)"""
    return "http://127.0.0.1:9000/mcp"


@pytest.fixture
def sample_mcp_urls_auth():
    """
    테스트용 MCP 서버 URL (다중 포트, 인증 시나리오)

    Phase 5-B 인증 테스트용 fixture.
    Synapse 다중 포트 모드 (`python -m synapse --multi`) 필요.

    Returns:
        dict: 인증 타입별 URL 매핑
    """
    return {
        "no_auth": "http://127.0.0.1:9000/mcp",  # 무인증 (기본)
        "api_key": "http://127.0.0.1:9001/mcp",  # API Key 인증
        "oauth": "http://127.0.0.1:9002/mcp",  # OAuth 2.0 인증
    }


@pytest.fixture
def sample_endpoint_data():
    """테스트용 엔드포인트 데이터"""
    return {
        "name": "Test MCP Server",
        "url": "https://example.com/mcp",
        "type": "MCP",
    }


# ============================================================
# MCP & A2A Test Server Fixtures (Session-scoped)
# ============================================================


def _get_free_port() -> int:
    """Get a free port for dynamic allocation"""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _is_port_in_use(port: int) -> bool:
    """Check if a port is already in use"""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return False
        except OSError:
            return True


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


@pytest.fixture(scope="session")
def mcp_synapse_server():
    """
    Synapse MCP Server subprocess fixture (port 9000).

    Automatically starts the Synapse server before tests
    and terminates it after the session ends.

    Returns:
        Base URL of the MCP server (http://127.0.0.1:9000/mcp)
    """
    # Synapse 프로젝트 경로
    synapse_dir = Path(r"C:\Users\sungb\Documents\GitHub\MCP_SERVER\MCP_Streamable_HTTP")

    if not synapse_dir.exists():
        pytest.skip(f"Synapse project not found: {synapse_dir}")

    port = 9000
    base_url = f"http://127.0.0.1:{port}"
    mcp_url = f"{base_url}/mcp"

    # 포트가 이미 사용 중이면 기존 서버 사용
    if _is_port_in_use(port):
        print(f"\n⚠ Port {port} already in use, using existing Synapse server: {mcp_url}")
        # Health check로 서버 동작 확인
        try:
            response = httpx.get(base_url, timeout=2.0)
            if response.status_code in (200, 404):  # 404도 서버 응답이므로 OK
                yield mcp_url
                return
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.fail(f"Port {port} in use but server not responding")

    # Synapse subprocess 시작
    proc = subprocess.Popen(
        [sys.executable, "-m", "synapse"],
        cwd=str(synapse_dir),  # Synapse 디렉토리에서 실행
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Health check: MCP 엔드포인트 응답 대기
    start_time = time.time()
    timeout = 15
    while time.time() - start_time < timeout:
        try:
            response = httpx.get(base_url, timeout=2.0)
            if response.status_code in (200, 404):  # Synapse는 root에 404 반환 가능
                break
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        time.sleep(0.5)
    else:
        # Timeout 시 프로세스 종료 및 에러 출력
        proc.terminate()
        stdout, stderr = proc.communicate(timeout=5)
        error_msg = f"Synapse MCP server failed to start on port {port}\n"
        if stderr:
            error_msg += f"STDERR:\n{stderr}\n"
        if stdout:
            error_msg += f"STDOUT:\n{stdout}\n"
        pytest.fail(error_msg)

    print(f"\n✓ Synapse MCP Server started: {mcp_url}")

    yield mcp_url

    # Cleanup
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()

    print("\n✓ Synapse MCP Server stopped")
