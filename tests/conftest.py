"""
AgentHub 공통 테스트 픽스처

이 파일은 모든 테스트에서 공유되는 픽스처를 정의합니다.
pytest가 자동으로 이 파일을 로드합니다.
"""

import contextlib
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

# .env 파일 로드 (LLM 테스트에서 API 키 필요)
load_dotenv()

import pytest  # noqa: E402


def pytest_sessionstart(session):  # noqa: ARG001 - pytest hook signature
    """pytest 세션 시작 시 litellm verbose logging 비활성화

    litellm의 LoggingWorker가 atexit 핸들러에서 이미 닫힌 파일에
    로그를 작성하려 시도하는 문제를 방지합니다.

    Issue: ValueError: I/O operation on closed file
    Solution: verbose logging을 비활성화하여 LoggingWorker 사용 방지
    """
    # Suppress litellm verbose logging
    os.environ["LITELLM_LOG"] = "ERROR"

    # Disable litellm callbacks for tests (우리의 AgentHubLogger는 영향 없음)
    try:
        import litellm

        litellm.suppress_debug_info = True
        litellm.set_verbose = False
    except ImportError:
        pass


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


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001 - pytest hook signature
    """pytest 세션 종료 시 litellm LoggingWorker 정리

    litellm의 LoggingWorker가 atexit 핸들러에서 이미 닫힌 파일에
    로그를 작성하려 시도하는 문제를 방지합니다.

    Issue: ValueError: I/O operation on closed file
    Solution: pytest 종료 전에 LoggingWorker를 명시적으로 종료하고
    atexit 핸들러를 제거합니다.
    """
    import atexit

    try:
        # Method 1: LoggingWorker stop + atexit 해제
        from litellm.litellm_core_utils.logging_worker import logging_worker_thread

        if logging_worker_thread is not None:
            # Stop the worker thread
            if hasattr(logging_worker_thread, "stop"):
                logging_worker_thread.stop()

            # Unregister atexit handler to prevent _flush_on_exit from firing
            if hasattr(logging_worker_thread, "_flush_on_exit"):
                with contextlib.suppress(Exception):
                    atexit.unregister(logging_worker_thread._flush_on_exit)
    except (ImportError, AttributeError):
        pass

    try:
        # Method 2: Suppress litellm verbose logger and all handlers
        import logging

        for logger_name in ("litellm", "LiteLLM", "LiteLLM Router", "LiteLLM Proxy"):
            target_logger = logging.getLogger(logger_name)
            target_logger.handlers.clear()
            target_logger.propagate = False
    except Exception:
        pass


# ============================================================
# Test History Logging (Phase Gate Protocol)
# ============================================================


def pytest_runtest_makereport(item, call):
    """
    Record test execution history to JSONL for AI feedback.

    Enables Phase Gate Protocol:
    1. AI reads tests/logs/phase_history.jsonl before each Phase/Step
    2. Identifies past failures to avoid regressions
    3. Provides context for current vs past issues

    JSONL Format (one JSON object per line):
    {
        "timestamp": "2026-02-08T10:30:45.123",
        "nodeid": "tests/unit/domain/entities/test_resource.py::TestResource::test_create",
        "outcome": "passed" | "failed" | "skipped",
        "duration": 0.123,
        "phase": "domain_entities",  # From PHASE_CONTEXT env var
        "error": "AssertionError: ..." (if failed)
    }
    """
    if call.when != "call":  # Only log test call phase (not setup/teardown)
        return

    import json
    from datetime import datetime

    # Create logs directory if needed
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # JSONL file path
    history_file = log_dir / "phase_history.jsonl"

    # Extract phase context from environment (set by AI/user)
    phase = os.environ.get("PHASE_CONTEXT", "unknown")

    # Build history record
    record = {
        "timestamp": datetime.now().isoformat(timespec="milliseconds"),
        "nodeid": item.nodeid,
        "outcome": "passed" if call.excinfo is None else "failed",
        "duration": round(call.duration, 3),
        "phase": phase,
    }

    # Add error info if failed
    if call.excinfo is not None:
        record["error"] = str(call.excinfo.value)[:500]  # Truncate to 500 chars

    # Append to JSONL (atomic write)
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


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
    """테스트용 MCP 서버 URL (기본, 무인증)

    환경변수 MCP_TEST_PORT로 포트 오버라이드 가능 (기본: 9000)
    """
    port = int(os.environ.get("MCP_TEST_PORT", "9000"))
    return f"http://127.0.0.1:{port}/mcp"


@pytest.fixture
def sample_mcp_urls_auth():
    """
    테스트용 MCP 서버 URL (다중 포트, 인증 시나리오)

    Phase 5-B 인증 테스트용 fixture.
    Synapse 다중 포트 모드 (`python -m synapse --multi`) 필요.

    환경변수 MCP_TEST_PORT로 기본 포트 오버라이드 가능 (기본: 9000).
    다중 포트는 기본 포트 + 1, +2로 자동 설정.

    Returns:
        dict: 인증 타입별 URL 매핑
    """
    base_port = int(os.environ.get("MCP_TEST_PORT", "9000"))
    return {
        "no_auth": f"http://127.0.0.1:{base_port}/mcp",  # 무인증 (기본)
        "api_key": f"http://127.0.0.1:{base_port + 1}/mcp",  # API Key 인증
        "oauth": f"http://127.0.0.1:{base_port + 2}/mcp",  # OAuth 2.0 인증
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


def _subprocess_popen_safe(cmd: list, **kwargs) -> tuple[subprocess.Popen, Path | None]:
    """Start subprocess with pipe-deadlock-safe I/O handling.

    On long-running subprocesses (uvicorn servers), stdout/stderr PIPE buffers
    (64KB) fill up and block the child process, causing deadlocks on teardown.

    Solution: Redirect stdout to DEVNULL, stderr to a temp file for startup
    diagnostics. Caller must clean up the temp file.

    On Windows, uses CREATE_NEW_PROCESS_GROUP for reliable termination.

    Returns:
        (process, stderr_path): Process and path to stderr temp file (or None)
    """
    # Create temp file for stderr (startup diagnostics)
    stderr_file = tempfile.NamedTemporaryFile(  # noqa: SIM115
        mode="w", suffix=".log", prefix="agenthub_test_", delete=False
    )
    stderr_path = Path(stderr_file.name)

    # Windows: CREATE_NEW_PROCESS_GROUP for reliable termination
    creationflags = 0
    if platform.system() == "Windows":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=stderr_file,
        creationflags=creationflags,
        **kwargs,
    )

    return proc, stderr_path


def _terminate_process_safe(proc: subprocess.Popen, stderr_path: Path | None = None) -> None:
    """Safely terminate a subprocess without deadlock risk.

    Args:
        proc: The subprocess to terminate
        stderr_path: Path to stderr temp file to clean up
    """
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)

    # Clean up stderr temp file
    if stderr_path and stderr_path.exists():
        with contextlib.suppress(OSError):
            stderr_path.unlink()


def _read_stderr_file(stderr_path: Path | None) -> str:
    """Read stderr from temp file for diagnostics."""
    if stderr_path and stderr_path.exists():
        try:
            return stderr_path.read_text(errors="replace")
        except OSError:
            return ""
    return ""


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
    A2A Echo Agent subprocess fixture (기본 포트: 9003).

    환경변수 A2A_ECHO_PORT로 포트 오버라이드 가능.
    pytest-xdist 병렬 실행 시 포트 충돌 방지용.

    Automatically starts the echo agent server before tests
    and terminates it after the session ends.

    Returns:
        Base URL of the echo agent (http://127.0.0.1:{port})
    """
    # Echo agent script path
    echo_script = Path(__file__).parent / "fixtures" / "a2a_agents" / "echo_agent.py"

    if not echo_script.exists():
        pytest.skip(f"Echo agent script not found: {echo_script}")

    # 환경변수로 포트 오버라이드 가능 (기본: 9003)
    port = int(os.environ.get("A2A_ECHO_PORT", "9003"))
    base_url = f"http://127.0.0.1:{port}"

    # Start echo agent subprocess (pipe-deadlock-safe)
    proc, stderr_path = _subprocess_popen_safe(
        [sys.executable, str(echo_script), str(port)],
    )

    # Wait for health check (A2A server may take 15s to start)
    if not _wait_for_health(base_url, timeout=20):
        stderr_content = _read_stderr_file(stderr_path)
        _terminate_process_safe(proc, stderr_path)
        error_msg = f"Echo agent failed to start on port {port}\n"
        if stderr_content:
            error_msg += f"STDERR:\n{stderr_content}\n"
        pytest.fail(error_msg)

    print(f"\n✓ A2A Echo Agent started: {base_url}")

    yield base_url

    # Cleanup (deadlock-safe)
    _terminate_process_safe(proc, stderr_path)

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

    # Start math agent subprocess (pipe-deadlock-safe)
    proc, stderr_path = _subprocess_popen_safe(
        [sys.executable, str(math_script), str(port)],
    )

    # Wait for health check (LLM agent may take longer to start)
    if not _wait_for_health(base_url, timeout=30):
        stderr_content = _read_stderr_file(stderr_path)
        _terminate_process_safe(proc, stderr_path)
        error_msg = f"Math agent failed to start on port {port}\n"
        if stderr_content:
            error_msg += f"STDERR:\n{stderr_content}\n"
        pytest.fail(error_msg)

    print(f"\n✓ A2A Math Agent started: {base_url}")

    yield base_url

    # Cleanup (deadlock-safe)
    _terminate_process_safe(proc, stderr_path)

    print("\n✓ A2A Math Agent stopped")


@pytest.fixture(
    scope="session", autouse=(os.getenv("CI") != "true" and os.getenv("GITHUB_ACTIONS") != "true")
)
def mcp_synapse_server():
    """
    Synapse MCP Server subprocess fixture (다중 포트 모드).

    로컬 환경에서만 자동 실행 (autouse).
    CI 환경에서는 mock_mcp_toolset_in_ci가 대신 동작.

    환경변수 MCP_TEST_PORT로 기본 포트 오버라이드 가능 (기본: 9000).
    다중 포트는 기본 포트 + 1, +2로 자동 설정 (예: 8888, 8889, 8890).

    Automatically starts the Synapse server with --multi flag:
    - Port {base}: No auth (backward-compatible)
    - Port {base+1}: API Key auth (X-API-Key header)
    - Port {base+2}: OAuth 2.0 (Authorization: Bearer <token>)

    Returns:
        Base URL of the MCP server (http://127.0.0.1:{port}/mcp)
    """
    # Synapse 프로젝트 경로 (환경변수 또는 기본값)
    synapse_dir = Path(
        os.environ.get(
            "SYNAPSE_DIR",
            str(Path.home() / "Documents" / "GitHub" / "MCP_SERVER" / "MCP_Streamable_HTTP"),
        )
    )

    if not synapse_dir.exists():
        pytest.skip(f"Synapse project not found: {synapse_dir}")

    # 환경변수로 포트 오버라이드 가능 (기본: 9000)
    port = int(os.environ.get("MCP_TEST_PORT", "9000"))
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

    # 다중 포트 환경변수 설정 (동적 포트 지원)
    port_auth = port
    port_apikey = port + 1
    port_oauth = port + 2

    env = os.environ.copy()
    env["SYNAPSE_PORTS"] = f"{port_auth},{port_apikey},{port_oauth}"
    env[f"SYNAPSE_PORT_{port_auth}_AUTH"] = "none"
    env[f"SYNAPSE_PORT_{port_apikey}_AUTH"] = "apikey"
    env[f"SYNAPSE_PORT_{port_apikey}_API_KEYS"] = '["test-key-1","test-key-2"]'
    env[f"SYNAPSE_PORT_{port_oauth}_AUTH"] = "oauth"
    env[f"SYNAPSE_PORT_{port_oauth}_OAUTH_ISSUER"] = "https://mock-issuer.example.com"

    # Synapse subprocess 시작 (다중 포트 모드, pipe-deadlock-safe)
    proc, stderr_path = _subprocess_popen_safe(
        [sys.executable, "-m", "synapse", "--multi"],
        cwd=str(synapse_dir),  # Synapse 디렉토리에서 실행
        env=env,  # 환경변수 전달
    )

    # Health check: MCP 엔드포인트 응답 대기
    start_time = time.time()
    health_timeout = 30  # Synapse 서버 시작 시간 여유 확보 (10-15초 소요)
    while time.time() - start_time < health_timeout:
        try:
            response = httpx.get(base_url, timeout=2.0)
            if response.status_code in (200, 404):  # Synapse는 root에 404 반환 가능
                break
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        time.sleep(0.5)
    else:
        # Timeout 시 프로세스 종료 및 에러 출력
        stderr_content = _read_stderr_file(stderr_path)
        _terminate_process_safe(proc, stderr_path)
        error_msg = f"Synapse MCP server failed to start on port {port}\n"
        if stderr_content:
            error_msg += f"STDERR:\n{stderr_content}\n"
        pytest.fail(error_msg)

    print(f"\n✓ Synapse MCP Server started (multi-port): {mcp_url} (9000-9002)")

    yield mcp_url

    # Cleanup (deadlock-safe)
    _terminate_process_safe(proc, stderr_path)

    print("\n✓ Synapse MCP Server stopped")
