"""Playground HITL SSE Events E2E Tests

TDD Step 6.5a: E2E Test for Real-time HITL Event Streaming

Tests the EventSource connection and event broadcasting from backend to Playground UI.
"""

import asyncio
import http.server
import os
import socketserver
import subprocess
import sys
import threading
import time
from pathlib import Path

import httpx
import pytest
from playwright.async_api import Page, async_playwright

# Test Extension Token
TEST_EXTENSION_TOKEN = "test-extension-token"


# ============================================================
# Fixtures - Server Lifecycle
# ============================================================


@pytest.fixture(scope="session")
def playground_server():
    """Playground HTTP 서버 (localhost:3000)

    Python http.server로 Playground 정적 파일 서빙
    """
    playground_dir = Path(__file__).parent.parent / "manual" / "playground"
    port = int(os.environ.get("PLAYGROUND_PORT", "3000"))

    # SimpleHTTPServer 시작 (별도 스레드)
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(playground_dir), **kwargs)

        def end_headers(self):
            # Disable caching for JavaScript files
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            super().end_headers()

        def log_message(self, format, *args):
            # Suppress logs
            pass

    httpd = socketserver.TCPServer(("", port), Handler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    # Health check
    base_url = f"http://localhost:{port}"
    start_time = time.time()
    while time.time() - start_time < 10:
        try:
            response = httpx.get(base_url, timeout=2.0)
            if response.status_code == 200:
                break
        except (httpx.ConnectError, httpx.TimeoutException):
            time.sleep(0.5)
    else:
        httpd.shutdown()
        pytest.fail(f"Playground server failed to start on port {port}")

    print(f"\n✓ Playground Server started: {base_url}")

    yield base_url

    # Cleanup
    httpd.shutdown()
    print("\n✓ Playground Server stopped")


@pytest.fixture(scope="session")
def backend_server():
    """AgentHub API 서버 (localhost:8000)

    uvicorn으로 FastAPI 서버 시작 (DEV_MODE + Dual-Track 활성화)
    """
    port = int(os.environ.get("BACKEND_PORT", "8000"))
    repo_root = Path(__file__).parent.parent.parent

    # DEV_MODE 활성화하여 localhost 요청 시 토큰 검증 우회
    # Dual-Track 활성화하여 SDK Track (Resources, Prompts, HITL) 사용
    env = {**os.environ}
    env["DEV_MODE"] = "true"
    env["MCP__ENABLE_DUAL_TRACK"] = "true"

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
        cwd=str(repo_root),
        env=env,
    )

    # Health check
    base_url = f"http://localhost:{port}"
    start_time = time.time()
    while time.time() - start_time < 15:
        try:
            response = httpx.get(f"{base_url}/health", timeout=2.0)
            if response.status_code == 200:
                break
        except (httpx.ConnectError, httpx.TimeoutException):
            time.sleep(0.5)
    else:
        # Timeout 시 stderr 출력
        proc.terminate()
        stdout, stderr = proc.communicate(timeout=5)
        error_msg = f"Backend server failed to start on port {port}\n"
        if stderr:
            error_msg += f"STDERR:\n{stderr.decode('utf-8', errors='replace')}\n"
        pytest.fail(error_msg)

    print(f"\n✓ Backend Server started: {base_url}")

    yield base_url

    # Cleanup
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    print("\n✓ Backend Server stopped")


@pytest.fixture
async def registered_mcp_endpoint(backend_server, mcp_synapse_server):
    """MCP 서버 등록 fixture (function scope, stateless)

    Backend API를 통해 Synapse MCP 서버 등록 후 endpoint ID 반환.
    """
    headers = {"X-Extension-Token": TEST_EXTENSION_TOKEN}

    async with httpx.AsyncClient(base_url=backend_server, timeout=60.0, headers=headers) as client:
        # MCP 서버가 이미 등록되어 있는지 확인 (idempotent registration)
        list_response = await client.get("/api/mcp/servers")
        existing_endpoints = list_response.json()

        # 동일 URL의 엔드포인트가 이미 존재하면 재사용
        for ep in existing_endpoints:
            if ep["url"] == mcp_synapse_server:
                yield ep
                return

        # 새로 등록
        response = await client.post(
            "/api/mcp/servers",
            json={
                "url": mcp_synapse_server,
                "name": "Test Synapse MCP",
            },
        )
        assert response.status_code == 201, f"Failed to register MCP server: {response.text}"
        endpoint = response.json()

        yield endpoint


class PageWithConsole:
    """Helper class to store page and console logs together"""

    def __init__(self, page: Page):
        self.page = page
        self.console_logs = []

    def setup_console_listener(self):
        """Set up console listener before page load"""
        self.page.on("console", lambda msg: self.console_logs.append(f"{msg.type}: {msg.text}"))


@pytest.fixture
async def page(playground_server, backend_server, registered_mcp_endpoint):
    """Playwright page fixture

    Playground에 접속한 상태의 브라우저 페이지
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Playground 접속
        await page.goto(playground_server)

        # Wait for page to be fully loaded
        await page.wait_for_load_state("domcontentloaded")

        # Note: Do NOT wait for "networkidle" as SSE connection keeps network active
        # Instead, wait for the SSE indicator element to be present (will be connected in the tests)
        await page.wait_for_selector('[data-testid="hitl-sse-indicator"]', timeout=5000)

        yield page

        # Cleanup
        await context.close()
        await browser.close()


@pytest.fixture
async def page_with_console(playground_server, backend_server, registered_mcp_endpoint):
    """Playwright page fixture with console logging

    Returns PageWithConsole object with page and console_logs list.
    Console listener is set up BEFORE page load to capture all logs.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Create wrapper and set up console listener BEFORE loading page
        page_wrapper = PageWithConsole(page)
        page_wrapper.setup_console_listener()

        # Playground 접속
        await page.goto(playground_server)

        # Wait for page to be fully loaded
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_selector('[data-testid="hitl-sse-indicator"]', timeout=5000)

        yield page_wrapper

        # Cleanup
        await context.close()
        await browser.close()


# ============================================================
# Tests - HITL SSE Events
# ============================================================


@pytest.mark.e2e_playwright
class TestPlaygroundHitlSse:
    """HITL SSE Events 실시간 스트리밍 E2E 테스트"""

    async def test_sse_connection_established_on_page_load(self, page: Page):
        """Playground 페이지 로드 시 SSE 자동 연결

        Given: Playground 접속 (fixture에서 이미 로드됨)
        When: 페이지 확인
        Then: HITL SSE 연결 상태가 "connected"로 표시됨

        Note: Console logs are captured after page load, so "HITL SSE connected"
        message may have already been logged. We verify the connection status instead.
        """
        # Wait for SSE connection indicator to be connected
        await page.wait_for_selector(
            '[data-testid="hitl-sse-indicator"][data-status="connected"]', timeout=10000
        )

        # Verify status text
        status_text = await page.text_content("#hitl-sse-status")
        assert status_text == "HITL SSE: Connected"

    async def test_sampling_request_event_triggers_auto_refresh(
        self, page_with_console, backend_server, registered_mcp_endpoint
    ):
        """sampling_request 이벤트 수신 시 Sampling 탭 자동 갱신

        Given: Playground 접속 + Sampling 탭 활성화
        When: Backend가 sampling_request 이벤트 브로드캐스트
        Then: Browser console에 이벤트 수신 로그 출력 + 자동 갱신 트리거
        """
        page = page_with_console.page
        console_logs = page_with_console.console_logs

        # Wait for SSE connection
        await page.wait_for_selector(
            '[data-testid="hitl-sse-indicator"][data-status="connected"]', timeout=10000
        )

        # Navigate to Sampling tab
        await page.click('[data-testid="tab-sampling"]')
        await page.wait_for_selector("#sampling-tab.active", state="visible", timeout=5000)

        # Inject sampling request using backend API
        async with httpx.AsyncClient(base_url=backend_server, timeout=10.0) as client:
            response = await client.post(
                f"/test/sampling/inject?endpoint_id={registered_mcp_endpoint['id']}"
            )
            assert response.status_code == 200, (
                f"Failed to inject sampling request: {response.text}"
            )
            request_id = response.json()["request_id"]

        # Wait for SSE event to be received (check console logs)
        await asyncio.sleep(2)  # Give time for event propagation

        # Verify console logs
        print("\n=== Browser Console Logs (Sampling) ===")
        for log in console_logs:
            print(log)
        print("=" * 30)

        # Check for event reception log
        event_logs = [log for log in console_logs if "Received sampling_request event" in log]
        assert len(event_logs) > 0, "sampling_request event not received"

        # Check for auto-refresh log
        refresh_logs = [log for log in console_logs if "Auto-refreshing sampling requests" in log]
        assert len(refresh_logs) > 0, "Auto-refresh not triggered for sampling tab"

        # Verify that the request appears in the UI (auto-refresh worked)
        await page.wait_for_selector(
            f'.sampling-request-card[data-request-id="{request_id}"]', timeout=5000
        )
        card = page.locator(f'.sampling-request-card[data-request-id="{request_id}"]')
        card_text = await card.text_content()
        assert "Approve" in card_text

    async def test_elicitation_request_event_triggers_auto_refresh(
        self, page_with_console, backend_server, registered_mcp_endpoint
    ):
        """elicitation_request 이벤트 수신 시 Elicitation 탭 자동 갱신

        Given: Playground 접속 + Elicitation 탭 활성화
        When: Backend가 elicitation_request 이벤트 브로드캐스트
        Then: Browser console에 이벤트 수신 로그 출력 + 자동 갱신 트리거
        """
        page = page_with_console.page
        console_logs = page_with_console.console_logs

        # Wait for SSE connection
        await page.wait_for_selector(
            '[data-testid="hitl-sse-indicator"][data-status="connected"]', timeout=10000
        )

        # Navigate to Elicitation tab
        await page.click('[data-testid="tab-elicitation"]')
        await page.wait_for_selector("#elicitation-tab.active", state="visible", timeout=5000)

        # Inject elicitation request using backend API
        async with httpx.AsyncClient(base_url=backend_server, timeout=10.0) as client:
            response = await client.post(
                f"/test/elicitation/inject?endpoint_id={registered_mcp_endpoint['id']}"
            )
            assert response.status_code == 200, (
                f"Failed to inject elicitation request: {response.text}"
            )
            request_id = response.json()["request_id"]

        # Wait for SSE event to be received (check console logs)
        await asyncio.sleep(2)  # Give time for event propagation

        # Verify console logs
        print("\n=== Browser Console Logs (Elicitation) ===")
        for log in console_logs:
            print(log)
        print("=" * 30)

        # Check for event reception log
        event_logs = [log for log in console_logs if "Received elicitation_request event" in log]
        assert len(event_logs) > 0, "elicitation_request event not received"

        # Check for auto-refresh log
        refresh_logs = [
            log for log in console_logs if "Auto-refreshing elicitation requests" in log
        ]
        assert len(refresh_logs) > 0, "Auto-refresh not triggered for elicitation tab"

        # Verify that the request appears in the UI (auto-refresh worked)
        await page.wait_for_selector(
            f'.elicitation-request-card[data-request-id="{request_id}"]', timeout=5000
        )
        card = page.locator(f'.elicitation-request-card[data-request-id="{request_id}"]')
        card_text = await card.text_content()
        assert "Accept" in card_text

    async def test_sse_event_not_triggered_when_wrong_tab_active(
        self, page_with_console, backend_server, registered_mcp_endpoint
    ):
        """다른 탭이 활성화되어 있을 때는 자동 갱신 트리거 안 됨

        Given: Playground 접속 + Chat 탭 활성화 (Sampling/Elicitation 아님)
        When: Backend가 sampling_request 이벤트 브로드캐스트
        Then: 이벤트는 수신되지만 자동 갱신은 트리거되지 않음
        """
        page = page_with_console.page
        console_logs = page_with_console.console_logs

        # Wait for SSE connection
        await page.wait_for_selector(
            '[data-testid="hitl-sse-indicator"][data-status="connected"]', timeout=10000
        )

        # Stay on Chat tab (default active tab)
        await page.wait_for_selector("#chat-tab.active", state="visible", timeout=5000)

        # Inject sampling request using backend API
        async with httpx.AsyncClient(base_url=backend_server, timeout=10.0) as client:
            response = await client.post(
                f"/test/sampling/inject?endpoint_id={registered_mcp_endpoint['id']}"
            )
            assert response.status_code == 200

        # Wait for SSE event to be received
        await asyncio.sleep(2)

        # Verify console logs
        print("\n=== Browser Console Logs (Wrong Tab) ===")
        for log in console_logs:
            print(log)
        print("=" * 30)

        # Check that event was received
        event_logs = [log for log in console_logs if "Received sampling_request event" in log]
        assert len(event_logs) > 0, "sampling_request event not received"

        # Check that auto-refresh was NOT triggered (since wrong tab is active)
        refresh_logs = [log for log in console_logs if "Auto-refreshing sampling requests" in log]
        assert len(refresh_logs) == 0, (
            "Auto-refresh should not be triggered when Sampling tab is not active"
        )

    async def test_sse_connection_resilience(self, page: Page):
        """SSE 연결이 페이지 로드 후 유지되는지 확인

        Given: Playground 접속 + SSE 연결됨
        When: 5초 대기
        Then: 연결 상태가 여전히 "connected"
        """
        # Wait for initial SSE connection
        await page.wait_for_selector(
            '[data-testid="hitl-sse-indicator"][data-status="connected"]', timeout=10000
        )

        # Wait for 5 seconds to test connection stability
        await asyncio.sleep(5)

        # Verify connection is still active
        indicator_status = await page.get_attribute(
            '[data-testid="hitl-sse-indicator"]', "data-status"
        )
        assert indicator_status == "connected", "SSE connection lost after 5 seconds"

        status_text = await page.text_content("#hitl-sse-status")
        assert status_text == "HITL SSE: Connected", "SSE status text changed unexpectedly"
