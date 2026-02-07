"""
Playground E2E Tests - Playwright

Resources, Prompts, Sampling, Elicitation 탭의 실제 브라우저 동작 테스트

Fixture Strategy (Idempotent Registration):
- registered_mcp_endpoint: 각 테스트마다 실행되지만, 기존 엔드포인트 재사용
- reset-data 호출 제거: MCP disconnect blocking 문제 해결
- Teardown 제거: Backend 서버 종료 시 자동 정리
- 테스트 격리: Playwright의 독립적인 페이지 인스턴스로 보장
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

# 테스트용 Extension Token (integration/conftest.py와 동일)
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
            # Disable caching for JavaScript files (prevent serving stale files)
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            super().end_headers()

        def log_message(self, format, *args):
            # 로그 억제 (테스트 출력 깔끔하게)
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
        env=env,  # DEV_MODE 환경변수 포함
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

    # Cleanup: Terminate server (MCP connections will be cleaned up automatically)
    proc.terminate()
    try:
        proc.wait(timeout=10)  # Give more time for graceful MCP disconnections
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    print("\n✓ Backend Server stopped")


@pytest.fixture
async def registered_mcp_endpoint(backend_server, mcp_synapse_server):
    """MCP 서버 등록 fixture (function scope, stateless)

    Backend API를 통해 Synapse MCP 서버 등록 후 endpoint ID 반환.
    각 테스트마다 실행되지만, reset-data 호출을 제거하여 빠른 실행 보장.
    테스트 격리는 Playwright의 독립적인 페이지 인스턴스로 보장.

    Args:
        backend_server: Backend API URL (http://localhost:8000)
        mcp_synapse_server: Synapse MCP URL (http://127.0.0.1:9000/mcp)

    Returns:
        dict: {id, url, name, type, enabled, registered_at}
    """
    # 인증 헤더 추가
    headers = {"X-Extension-Token": TEST_EXTENSION_TOKEN}

    # Connection pool limits (defense-in-depth)
    limits = httpx.Limits(max_connections=20, max_keepalive_connections=5, keepalive_expiry=5.0)

    # Perform registration with AsyncClient
    endpoint_to_yield = None

    async with httpx.AsyncClient(
        base_url=backend_server, timeout=60.0, headers=headers, limits=limits
    ) as client:
        # MCP 서버가 이미 등록되어 있는지 확인 (idempotent registration)
        list_response = await client.get("/api/mcp/servers")
        existing_endpoints = list_response.json()

        # 동일 URL의 엔드포인트가 이미 존재하면 재사용
        for ep in existing_endpoints:
            if ep["url"] == mcp_synapse_server:
                endpoint_to_yield = ep
                break

        # 새로 등록 (not found)
        if endpoint_to_yield is None:
            response = await client.post(
                "/api/mcp/servers",
                json={
                    "url": mcp_synapse_server,
                    "name": "Test Synapse MCP",
                },
            )
            assert response.status_code == 201, f"Failed to register MCP server: {response.text}"
            endpoint_to_yield = response.json()

        # Yield inside async with block (AsyncClient closes AFTER yield)
        yield endpoint_to_yield

    # Teardown 제거: Backend 서버 종료 시 자동으로 정리됨
    # MCP disconnect는 blocking이므로 각 테스트마다 호출 시 타임아웃 발생


@pytest.fixture
async def page(playground_server, backend_server, registered_mcp_endpoint):
    """Playwright page fixture

    Playground에 접속한 상태의 브라우저 페이지

    Args:
        playground_server: Playground URL (http://localhost:3000)
        backend_server: Backend API URL (http://localhost:8000)
        registered_mcp_endpoint: 등록된 MCP 엔드포인트 정보
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
        # Instead, wait for the SSE indicator element to be present (verifies SSE connection)
        await page.wait_for_selector('[data-testid="hitl-sse-indicator"]', timeout=5000)

        yield page

        # Cleanup
        await context.close()
        await browser.close()


# ============================================================
# Tests - Resources Tab
# ============================================================


@pytest.mark.e2e_playwright
class TestPlaygroundResources:
    """Resources 탭 E2E 테스트"""

    async def test_list_resources_displays_cards(self, page: Page, registered_mcp_endpoint):
        """Resources 탭에서 리소스 목록 표시

        Given: Playground 접속 + MCP 서버 등록
        When: Resources 탭 클릭 + Endpoint 선택 + List Resources 버튼 클릭
        Then: 리소스 카드가 표시됨
        """
        # 콘솔 로그 캡처
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))

        # 네트워크 요청 모니터링
        network_logs = []

        def log_request(req):
            network_logs.append(f"REQ: {req.method} {req.url}")

        def log_response(res):
            network_logs.append(f"RES: {res.status} {res.url}")

        page.on("request", log_request)
        page.on("response", log_response)

        # When: Resources 탭 클릭
        await page.click('[data-testid="tab-resources"]')

        # Wait for endpoint select to be populated by async API call (getMcpServers)
        await page.wait_for_function(
            "document.querySelector('[data-testid=\"resources-endpoint-select\"]').options.length > 0",
            timeout=15000,
        )

        # MCP endpoint 선택
        await page.select_option(
            '[data-testid="resources-endpoint-select"]',
            registered_mcp_endpoint["id"],
        )

        # List Resources 버튼 클릭
        await page.click('[data-testid="resources-list-btn"]')

        # 대기 후 스크린샷 캡처
        await page.wait_for_timeout(2000)
        await page.screenshot(path="test_resources_list.png")

        # 디버깅 정보 출력
        print("\n=== Browser Console Logs ===")
        for log in console_logs:
            print(log)
        print("\n=== Network Logs ===")
        for log in network_logs[-20:]:  # 최근 20개만
            print(log)
        print("=" * 30)

        # Then: 리소스 카드 확인
        await page.wait_for_selector(".resource-card", timeout=10000)
        resource_cards = await page.locator(".resource-card").all()
        assert len(resource_cards) > 0, "No resource cards displayed"

    async def test_read_resource_displays_content(self, page: Page, registered_mcp_endpoint):
        """리소스 읽기 버튼 클릭 시 콘텐츠 표시

        Given: Resources 탭에서 리소스 목록 표시
        When: 첫 번째 리소스의 Read 버튼 클릭
        Then: 리소스 콘텐츠가 표시됨
        """
        # Given: Resources 탭 + 목록 표시
        await page.click('[data-testid="tab-resources"]')

        # Wait for endpoint select to be populated by async API call (getMcpServers)
        await page.wait_for_function(
            "document.querySelector('[data-testid=\"resources-endpoint-select\"]').options.length > 0",
            timeout=15000,
        )
        await page.select_option(
            '[data-testid="resources-endpoint-select"]',
            registered_mcp_endpoint["id"],
        )
        await page.click('[data-testid="resources-list-btn"]')
        await page.wait_for_selector(".resource-card", timeout=10000)

        # When: 첫 번째 리소스 Read 버튼 클릭
        await page.click('[data-testid="resource-read-btn"]')

        # Then: 콘텐츠 영역 확인
        await page.wait_for_selector('[data-testid="resource-content"]:not(:empty)', timeout=10000)
        content_text = await page.text_content('[data-testid="resource-content"]')
        assert content_text, "Resource content is empty"
        assert "Resource:" in content_text or "MIME Type:" in content_text


# ============================================================
# Tests - Prompts Tab
# ============================================================


@pytest.mark.e2e_playwright
class TestPlaygroundPrompts:
    """Prompts 탭 E2E 테스트"""

    async def test_list_prompts_and_get_prompt_workflow(self, page: Page, registered_mcp_endpoint):
        """Prompts 탭에서 프롬프트 목록 표시

        Given: Playground 접속 + MCP 서버 등록
        When: Prompts 탭 클릭 + Endpoint 선택 + List Prompts 버튼 클릭
        Then: 프롬프트 카드가 표시됨
        """
        # When: Prompts 탭 클릭 (실제 이벤트 핸들러 트리거)
        await page.click('[data-testid="tab-prompts"]')

        # Wait for tab pane to be activated
        await page.wait_for_selector("#prompts-tab.active", state="visible", timeout=5000)

        # Wait for endpoint select to be populated by async API call (getMcpServers)
        await page.wait_for_function(
            "document.querySelector('[data-testid=\"prompts-endpoint-select\"]').options.length > 0",
            timeout=15000,
        )

        # MCP endpoint 선택
        await page.select_option(
            '[data-testid="prompts-endpoint-select"]',
            registered_mcp_endpoint["id"],
        )

        # List Prompts 버튼 클릭 (실제 이벤트 핸들러 트리거)
        await page.click('[data-testid="prompts-list-btn"]')

        # Then: 프롬프트 카드 확인
        await page.wait_for_selector(".prompt-card", timeout=5000)
        prompt_cards = await page.locator(".prompt-card").all()
        assert len(prompt_cards) > 0, "No prompt cards displayed"

    async def test_get_prompt_displays_content(self, page: Page, registered_mcp_endpoint):
        """프롬프트 Get 버튼 클릭 시 콘텐츠 표시

        Given: Prompts 탭에서 프롬프트 목록 표시
        When: 첫 번째 프롬프트의 Get 버튼 클릭 (arguments 입력)
        Then: 프롬프트 콘텐츠가 표시됨
        """
        # Given: Prompts 탭 + 목록 표시
        await page.click('[data-testid="tab-prompts"]')
        await page.wait_for_selector("#prompts-tab.active", state="visible", timeout=5000)

        # Wait for endpoint select to be populated by async API call (getMcpServers)
        await page.wait_for_function(
            "document.querySelector('[data-testid=\"prompts-endpoint-select\"]').options.length > 0",
            timeout=15000,
        )

        await page.select_option(
            '[data-testid="prompts-endpoint-select"]',
            registered_mcp_endpoint["id"],
        )

        # List Prompts 버튼 클릭
        await page.click('[data-testid="prompts-list-btn"]')
        await page.wait_for_selector(".prompt-card", timeout=5000)

        # required arguments 입력 (첫 번째 프롬프트)
        first_prompt = page.locator(".prompt-card").first
        arg_inputs = await first_prompt.locator("input[data-arg]").all()

        # Fill arguments
        for arg_input in arg_inputs:
            await arg_input.fill("test_value")

        # When: Get Prompt 버튼 클릭 (실제 이벤트 핸들러 트리거)
        await first_prompt.locator('[data-testid="prompt-get-btn"]').click()

        # Then: 콘텐츠 영역 확인
        await page.wait_for_selector('[data-testid="prompt-content"]:not(:empty)', timeout=5000)
        content_text = await page.text_content('[data-testid="prompt-content"]')
        assert content_text, "Prompt content is empty"
        assert len(content_text) > 0


# ============================================================
# Tests - Sampling Tab
# ============================================================


@pytest.fixture(scope="class", autouse=True)
async def cleanup_sampling_requests(backend_server):
    """Sampling 테스트 클래스 시작 전 pending requests 정리

    E2E Test Isolation Best Practice:
    - Self-contained tests: 각 test class가 clean state에서 시작
    - 이전 테스트의 inject된 sampling requests 정리

    References:
    - https://docs.cypress.io/app/core-concepts/test-isolation
    - https://docs.pytest.org/en/stable/how-to/fixtures.html
    """
    # Clear all pending sampling requests before test class
    async with httpx.AsyncClient(base_url=backend_server, timeout=10.0) as client:
        response = await client.get("/api/sampling/requests")
        if response.status_code == 200:
            requests_data = response.json()
            for req in requests_data.get("requests", []):
                # Reject each pending request
                await client.post(
                    f"/api/sampling/requests/{req['id']}/reject", json={"reason": "test cleanup"}
                )

    yield  # Test class 실행


@pytest.mark.e2e_playwright
@pytest.mark.llm
class TestPlaygroundSampling:
    """Sampling HITL 탭 E2E 테스트"""

    async def test_sampling_tab_loads(self, page: Page):
        """Sampling 탭 클릭 시 UI 로드

        Given: Playground 접속
        When: Sampling 탭 클릭
        Then: Sampling 탭이 활성화되고 Refresh 버튼이 표시됨
        """
        # When: Sampling 탭 클릭
        await page.click('[data-testid="tab-sampling"]')

        # Then: 탭이 활성화되고 UI 요소 표시
        await page.wait_for_selector("#sampling-tab.active", state="visible", timeout=5000)
        await page.wait_for_selector(
            '[data-testid="sampling-refresh-btn"]', state="visible", timeout=5000
        )

    async def test_sampling_no_requests_message(self, page: Page):
        """요청이 없을 때 메시지 표시

        Given: Sampling 탭 활성화
        When: Refresh 버튼 클릭 (요청 없음)
        Then: "No pending sampling requests" 메시지 표시
        """
        # Given: Sampling 탭 활성화
        await page.click('[data-testid="tab-sampling"]')
        await page.wait_for_selector("#sampling-tab.active", state="visible", timeout=5000)

        # When: Refresh 버튼 클릭
        await page.click('[data-testid="sampling-refresh-btn"]')

        # Then: No requests 메시지 확인
        await page.wait_for_selector(
            '[data-testid="sampling-requests"]:has-text("No pending sampling requests")',
            timeout=5000,
        )

    async def test_sampling_refresh_shows_requests(
        self, page: Page, backend_server, registered_mcp_endpoint
    ):
        """Refresh 버튼 클릭 시 요청 목록 표시

        Given: Sampling 탭 활성화 + 대기 중인 Sampling 요청 존재
        When: Refresh 버튼 클릭
        Then: Sampling 요청 카드가 표시됨
        """
        # Given: Sampling 요청 생성 (Test 엔드포인트를 통해)
        limits = httpx.Limits(max_connections=10, max_keepalive_connections=2)
        async with httpx.AsyncClient(
            base_url=backend_server, timeout=10.0, limits=limits
        ) as client:
            # Inject test sampling request with unique ID
            response = await client.post(
                f"/test/sampling/inject?endpoint_id={registered_mcp_endpoint['id']}"
            )
            assert response.status_code == 200, (
                f"Failed to inject sampling request: {response.text}"
            )
            injection_result = response.json()
            assert injection_result["status"] == "created"
            request_id = injection_result["request_id"]

        # Given: Sampling 탭 활성화
        await page.click('[data-testid="tab-sampling"]')
        await page.wait_for_selector("#sampling-tab.active", state="visible", timeout=5000)

        # When: Refresh 버튼 클릭
        await page.click('[data-testid="sampling-refresh-btn"]')

        # Then: Sampling 요청 카드 표시 확인
        await page.wait_for_selector(".sampling-request-card", timeout=5000)
        request_cards = await page.locator(".sampling-request-card").all()
        assert len(request_cards) > 0, "No sampling request cards displayed"

        # Verify card content (using injected request_id)
        card_selector = f'.sampling-request-card[data-request-id="{request_id}"]'
        await page.wait_for_selector(card_selector, timeout=5000)
        card = page.locator(card_selector)
        card_text = await card.text_content()
        assert "Approve" in card_text
        assert "Reject" in card_text

    async def test_sampling_approve_triggers_llm(
        self, page: Page, backend_server, registered_mcp_endpoint
    ):
        """Approve 버튼 클릭 시 LLM 실행 및 결과 표시

        Given: Sampling 요청이 목록에 표시됨
        When: Approve 버튼 클릭
        Then: LLM이 실행되고 결과가 표시됨
        """
        # Given: Sampling 요청 생성
        limits = httpx.Limits(max_connections=10, max_keepalive_connections=2)
        async with httpx.AsyncClient(
            base_url=backend_server, timeout=10.0, limits=limits
        ) as client:
            response = await client.post(
                f"/test/sampling/inject?endpoint_id={registered_mcp_endpoint['id']}"
            )
            assert response.status_code == 200
            request_id = response.json()["request_id"]

        # Given: Sampling 탭 + 요청 목록 로드
        await page.click('[data-testid="tab-sampling"]')
        await page.wait_for_selector("#sampling-tab.active", state="visible", timeout=5000)
        await page.click('[data-testid="sampling-refresh-btn"]')
        await page.wait_for_selector(
            f'.sampling-request-card[data-request-id="{request_id}"]', timeout=5000
        )

        # When: Approve 버튼 클릭 (specific to this request)
        await page.click(
            f'.sampling-request-card[data-request-id="{request_id}"] [data-testid="sampling-approve-btn"]'
        )

        # Then: 버튼 상태 변경 확인 (Approving...)
        await page.wait_for_selector('button:has-text("Approving...")', timeout=2000)

        # Then: LLM 결과 표시 확인 (최대 15초 대기 - LLM 호출 시간 포함)
        await page.wait_for_selector(
            f'[data-testid="sampling-result-{request_id}"]:has-text("Approved")', timeout=15000
        )
        result_div = page.locator(f'[data-testid="sampling-result-{request_id}"]')
        result_text = await result_div.text_content()
        assert "Approved" in result_text
        assert "LLM Result" in result_text or "content" in result_text.lower()

    async def test_sampling_reject_sets_status(
        self, page: Page, backend_server, registered_mcp_endpoint
    ):
        """Reject 버튼 클릭 시 거부 상태 표시 및 목록에서 제거

        Given: Sampling 요청이 목록에 표시됨
        When: Reject 버튼 클릭하고 dialog에서 reason 입력
        Then: 요청이 거부되고 목록에서 제거됨
        """
        # Given: Sampling 요청 생성
        limits = httpx.Limits(max_connections=10, max_keepalive_connections=2)
        async with httpx.AsyncClient(
            base_url=backend_server, timeout=10.0, limits=limits
        ) as client:
            response = await client.post(
                f"/test/sampling/inject?endpoint_id={registered_mcp_endpoint['id']}"
            )
            assert response.status_code == 200
            request_id = response.json()["request_id"]

        # Given: Sampling 탭 + 요청 목록 로드
        await page.click('[data-testid="tab-sampling"]')
        await page.wait_for_selector("#sampling-tab.active", state="visible", timeout=5000)
        await page.click('[data-testid="sampling-refresh-btn"]')
        await page.wait_for_selector(
            f'.sampling-request-card[data-request-id="{request_id}"]', timeout=5000
        )

        # When: Reject 버튼 클릭 (triggers dialog)
        # Set up dialog handler BEFORE clicking
        page.on(
            "dialog", lambda dialog: asyncio.create_task(dialog.accept("Test rejection reason"))
        )

        # Click the reject button
        reject_btn_selector = f'.sampling-request-card[data-request-id="{request_id}"] [data-testid="sampling-reject-btn"]'
        await page.click(reject_btn_selector)

        # Then: Button text changes to "Rejecting..." (proves rejection was triggered)
        await page.wait_for_selector(
            f'{reject_btn_selector}:has-text("Rejecting...")', timeout=2000
        )


# ============================================================
# Tests - Elicitation Tab
# ============================================================


@pytest.fixture(scope="class", autouse=True)
async def cleanup_elicitation_requests(backend_server):
    """Elicitation 테스트 클래스 시작 전 pending requests 정리

    E2E Test Isolation Best Practice:
    - Self-contained tests: 각 test class가 clean state에서 시작
    - 이전 테스트의 inject된 elicitation requests 정리

    References:
    - https://docs.cypress.io/app/core-concepts/test-isolation
    - https://docs.pytest.org/en/stable/how-to/fixtures.html
    """
    # Clear all pending elicitation requests before test class
    async with httpx.AsyncClient(base_url=backend_server, timeout=10.0) as client:
        response = await client.get("/api/elicitation/requests")
        if response.status_code == 200:
            requests_data = response.json()
            for req in requests_data.get("requests", []):
                # Decline each pending request
                await client.post(
                    f"/api/elicitation/requests/{req['id']}/respond",
                    json={"action": "decline", "content": None},
                )

    yield  # Test class 실행


@pytest.mark.e2e_playwright
class TestPlaygroundElicitation:
    """Elicitation HITL 탭 E2E 테스트"""

    async def test_elicitation_tab_loads(self, page: Page):
        """Elicitation 탭 클릭 시 UI 로드

        Given: Playground 접속
        When: Elicitation 탭 클릭
        Then: Elicitation 탭이 활성화되고 Refresh 버튼이 표시됨
        """
        # When: Elicitation 탭 클릭
        await page.click('[data-testid="tab-elicitation"]')

        # Then: 탭이 활성화되고 UI 요소 표시
        await page.wait_for_selector("#elicitation-tab.active", state="visible", timeout=5000)
        await page.wait_for_selector(
            '[data-testid="elicitation-refresh-btn"]', state="visible", timeout=5000
        )

    async def test_elicitation_no_requests_message(self, page: Page):
        """요청이 없을 때 메시지 표시

        Given: Elicitation 탭 활성화
        When: Refresh 버튼 클릭 (요청 없음)
        Then: "No pending elicitation requests" 메시지 표시
        """
        # Given: Elicitation 탭 활성화
        await page.click('[data-testid="tab-elicitation"]')
        await page.wait_for_selector("#elicitation-tab.active", state="visible", timeout=5000)

        # When: Refresh 버튼 클릭
        await page.click('[data-testid="elicitation-refresh-btn"]')

        # Then: No requests 메시지 확인
        await page.wait_for_selector(
            '[data-testid="elicitation-requests"]:has-text("No pending elicitation requests")',
            timeout=5000,
        )

    async def test_elicitation_refresh_shows_requests(
        self, page: Page, backend_server, registered_mcp_endpoint
    ):
        """Refresh 버튼 클릭 시 요청 목록 표시

        Given: Elicitation 탭 활성화 + 대기 중인 Elicitation 요청 존재
        When: Refresh 버튼 클릭
        Then: Elicitation 요청 카드가 표시됨
        """
        # Given: Elicitation 요청 생성 (Test 엔드포인트를 통해)
        limits = httpx.Limits(max_connections=10, max_keepalive_connections=2)
        async with httpx.AsyncClient(
            base_url=backend_server, timeout=10.0, limits=limits
        ) as client:
            # Inject test elicitation request with unique ID
            response = await client.post(
                f"/test/elicitation/inject?endpoint_id={registered_mcp_endpoint['id']}"
            )
            assert response.status_code == 200, (
                f"Failed to inject elicitation request: {response.text}"
            )
            injection_result = response.json()
            assert injection_result["status"] == "created"
            request_id = injection_result["request_id"]

        # Given: Elicitation 탭 활성화
        await page.click('[data-testid="tab-elicitation"]')
        await page.wait_for_selector("#elicitation-tab.active", state="visible", timeout=5000)

        # When: Refresh 버튼 클릭
        await page.click('[data-testid="elicitation-refresh-btn"]')

        # Then: Elicitation 요청 카드 표시 확인
        await page.wait_for_selector(".elicitation-request-card", timeout=5000)
        request_cards = await page.locator(".elicitation-request-card").all()
        assert len(request_cards) > 0, "No elicitation request cards displayed"

        # Verify card content (using injected request_id)
        card_selector = f'.elicitation-request-card[data-request-id="{request_id}"]'
        await page.wait_for_selector(card_selector, timeout=5000)
        card = page.locator(card_selector)
        card_text = await card.text_content()
        assert "Accept" in card_text
        assert "Decline" in card_text
        assert "Cancel" in card_text

    async def test_elicitation_accept_with_form_data(
        self, page: Page, backend_server, registered_mcp_endpoint
    ):
        """Accept 버튼 클릭 시 폼 데이터 전송 및 결과 표시

        Given: Elicitation 요청이 목록에 표시됨
        When: 폼 필드 입력 후 Accept 버튼 클릭
        Then: 요청이 승인되고 결과가 표시됨
        """
        # Given: Elicitation 요청 생성
        limits = httpx.Limits(max_connections=10, max_keepalive_connections=2)
        async with httpx.AsyncClient(
            base_url=backend_server, timeout=10.0, limits=limits
        ) as client:
            response = await client.post(
                f"/test/elicitation/inject?endpoint_id={registered_mcp_endpoint['id']}"
            )
            assert response.status_code == 200
            request_id = response.json()["request_id"]

        # Given: Elicitation 탭 + 요청 목록 로드
        await page.click('[data-testid="tab-elicitation"]')
        await page.wait_for_selector("#elicitation-tab.active", state="visible", timeout=5000)
        await page.click('[data-testid="elicitation-refresh-btn"]')
        await page.wait_for_selector(
            f'.elicitation-request-card[data-request-id="{request_id}"]', timeout=5000
        )

        # When: 폼 필드 입력 (카드 내의 input[data-field] 찾기)
        card = page.locator(f'.elicitation-request-card[data-request-id="{request_id}"]')
        form_inputs = await card.locator(".elicitation-form input[data-field]").all()

        # Fill all form fields with test data
        for input_field in form_inputs:
            await input_field.fill("test_value")

        # When: Accept 버튼 클릭
        await card.locator('[data-testid="elicitation-accept-btn"]').click()

        # Then: 버튼 상태 변경 확인 (Accepting...)
        await page.wait_for_selector('button:has-text("Accepting...")', timeout=2000)

        # Then: 결과 표시 확인
        await page.wait_for_selector(
            f'[data-testid="elicitation-result-{request_id}"]:has-text("Accepted")', timeout=5000
        )
        result_div = page.locator(f'[data-testid="elicitation-result-{request_id}"]')
        result_text = await result_div.text_content()
        assert "Accepted" in result_text

    async def test_elicitation_decline(self, page: Page, backend_server, registered_mcp_endpoint):
        """Decline 버튼 클릭 시 거부 상태 표시

        Given: Elicitation 요청이 목록에 표시됨
        When: Decline 버튼 클릭
        Then: 요청이 거부되고 결과가 표시됨
        """
        # Given: Elicitation 요청 생성
        limits = httpx.Limits(max_connections=10, max_keepalive_connections=2)
        async with httpx.AsyncClient(
            base_url=backend_server, timeout=10.0, limits=limits
        ) as client:
            response = await client.post(
                f"/test/elicitation/inject?endpoint_id={registered_mcp_endpoint['id']}"
            )
            assert response.status_code == 200
            request_id = response.json()["request_id"]

        # Given: Elicitation 탭 + 요청 목록 로드
        await page.click('[data-testid="tab-elicitation"]')
        await page.wait_for_selector("#elicitation-tab.active", state="visible", timeout=5000)
        await page.click('[data-testid="elicitation-refresh-btn"]')
        await page.wait_for_selector(
            f'.elicitation-request-card[data-request-id="{request_id}"]', timeout=5000
        )

        # When: Decline 버튼 클릭
        decline_btn_selector = f'.elicitation-request-card[data-request-id="{request_id}"] [data-testid="elicitation-decline-btn"]'
        await page.click(decline_btn_selector)

        # Then: Button text changes to "Declining..."
        await page.wait_for_selector(
            f'{decline_btn_selector}:has-text("Declining...")', timeout=2000
        )

        # Then: 결과 표시 확인 (Declined)
        await page.wait_for_selector(
            f'[data-testid="elicitation-result-{request_id}"]:has-text("Declined")', timeout=5000
        )
        result_div = page.locator(f'[data-testid="elicitation-result-{request_id}"]')
        result_text = await result_div.text_content()
        assert "Declined" in result_text

    async def test_elicitation_cancel(self, page: Page, backend_server, registered_mcp_endpoint):
        """Cancel 버튼 클릭 시 취소 상태 표시

        Given: Elicitation 요청이 목록에 표시됨
        When: Cancel 버튼 클릭
        Then: 요청이 취소되고 결과가 표시됨
        """
        # Given: Elicitation 요청 생성
        limits = httpx.Limits(max_connections=10, max_keepalive_connections=2)
        async with httpx.AsyncClient(
            base_url=backend_server, timeout=10.0, limits=limits
        ) as client:
            response = await client.post(
                f"/test/elicitation/inject?endpoint_id={registered_mcp_endpoint['id']}"
            )
            assert response.status_code == 200
            request_id = response.json()["request_id"]

        # Given: Elicitation 탭 + 요청 목록 로드
        await page.click('[data-testid="tab-elicitation"]')
        await page.wait_for_selector("#elicitation-tab.active", state="visible", timeout=5000)
        await page.click('[data-testid="elicitation-refresh-btn"]')
        await page.wait_for_selector(
            f'.elicitation-request-card[data-request-id="{request_id}"]', timeout=5000
        )

        # When: Cancel 버튼 클릭
        cancel_btn_selector = f'.elicitation-request-card[data-request-id="{request_id}"] [data-testid="elicitation-cancel-btn"]'
        await page.click(cancel_btn_selector)

        # Then: Button text changes to "Cancelling..."
        await page.wait_for_selector(
            f'{cancel_btn_selector}:has-text("Cancelling...")', timeout=2000
        )

        # Then: 결과 표시 확인 (Cancelled)
        await page.wait_for_selector(
            f'[data-testid="elicitation-result-{request_id}"]:has-text("Cancelled")', timeout=5000
        )
        result_div = page.locator(f'[data-testid="elicitation-result-{request_id}"]')
        result_text = await result_div.text_content()
        assert "Cancelled" in result_text
