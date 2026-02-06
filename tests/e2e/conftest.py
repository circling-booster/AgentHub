"""E2E Test Fixtures - Playwright Browser Tests

Fixtures for full browser E2E tests with Chrome Extension.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from playwright.sync_api import BrowserContext, sync_playwright


def _wait_for_health(url: str, timeout: int = 10) -> bool:
    """Wait for server health endpoint to respond"""
    import urllib.error
    import urllib.request

    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.5)
    return False


@pytest.fixture(scope="session")
def server_url():
    """테스트 서버 URL (환경변수 기반)

    Env var: E2E_SERVER_PORT (default: 8000)
    """
    port = int(os.environ.get("E2E_SERVER_PORT", "8000"))
    return f"http://localhost:{port}"


@pytest.fixture(scope="session")
def extension_path() -> Path:
    """Extension 빌드 경로 (WXT chrome-mv3 output)"""
    repo_root = Path(__file__).parent.parent.parent
    ext_path = repo_root / "extension" / ".output" / "chrome-mv3"

    if not ext_path.exists():
        raise FileNotFoundError(
            f"Extension not built. Run: cd extension && npm run build\nExpected path: {ext_path}"
        )

    return ext_path


@pytest.fixture(scope="session")
def server_process():
    """서버 subprocess 시작 (session scope)

    NOTE: auth.py의 _token_issued 전역 상태는 서버 재시작 시 자동 리셋됨.
    별도 처리 불필요.

    Env var: E2E_SERVER_PORT (default: 8000)
    """
    port = int(os.environ.get("E2E_SERVER_PORT", "8000"))
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.main:app",
            "--host",
            "localhost",
            "--port",
            str(port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path(__file__).parent.parent.parent,  # Repository root
        env={**os.environ},  # Inherit environment variables (.env API keys)
    )

    # Wait for server to be ready
    if not _wait_for_health(f"http://localhost:{port}/health", timeout=10):
        proc.terminate()
        proc.wait(timeout=5)
        raise RuntimeError("Server failed to start within 10 seconds")

    yield proc

    # Cleanup
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


@pytest.fixture
def browser_context(
    extension_path: Path, server_process: subprocess.Popen, a2a_echo_agent: str
) -> tuple[BrowserContext, str]:
    """Playwright browser context with extension loaded

    Note: a2a_echo_agent fixture ensures A2A test agent is running

    Returns:
        (context, extension_id): Browser context and extension ID
    """
    with sync_playwright() as p:
        # Launch persistent context with extension
        context = p.chromium.launch_persistent_context(
            user_data_dir="",  # Temporary profile
            headless=False,  # Extensions require headed mode
            args=[
                f"--disable-extensions-except={extension_path}",
                f"--load-extension={extension_path}",
                "--no-sandbox",  # Required for CI environments
            ],
        )

        # Get extension ID from service worker
        # Wait for service worker to be ready
        if len(context.service_workers) == 0:
            sw = context.wait_for_event("serviceworker", timeout=10000)
        else:
            sw = context.service_workers[0]

        # Extract extension ID from chrome-extension://ID/...
        extension_id = sw.url.split("/")[2]

        yield context, extension_id

        context.close()
