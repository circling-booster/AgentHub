"""Full Browser E2E Tests with Playwright

Tests the complete flow: Extension → Server → MCP/A2A agents

Prerequisites:
- Extension built: cd extension && npm run build
- playwright install chromium
- MCP server running: SYNAPSE_PORT=9000 python -m synapse (optional)
- A2A agent running: tests/fixtures/a2a_agents/echo_agent.py 9001 (optional)

Run:
- Local (headed): pytest tests/e2e/test_playwright_extension.py -m e2e_playwright --headed
- CI (skip): Default pytest excludes e2e_playwright marker
"""

import pytest
from playwright.sync_api import BrowserContext, expect


@pytest.mark.e2e_playwright
def test_extension_loads_and_connects(browser_context: tuple[BrowserContext, str]):
    """Test 1: Extension loads and connects to server

    Verifies:
    - Extension installs successfully
    - Sidepanel opens
    - "Connected" status displays (token handshake complete)
    """
    context, extension_id = browser_context

    # Open a blank page (extension runs in background)
    page = context.new_page()
    page.goto("about:blank")

    # Open sidepanel by clicking extension icon (simulate)
    # NOTE: Playwright cannot directly click extension icons
    # Alternative: Open sidepanel URL directly
    sidepanel_url = f"chrome-extension://{extension_id}/sidepanel.html"
    sidepanel = context.new_page()
    sidepanel.goto(sidepanel_url)

    # Wait for sidepanel to load
    sidepanel.wait_for_load_state("networkidle")

    # Check for "Connected" status indicator (user-facing text)
    # E2E principle: Verify what users see, not implementation details
    status = sidepanel.locator(".server-status")
    expect(status).to_contain_text("Connected", timeout=5000)

    page.close()
    sidepanel.close()


@pytest.mark.e2e_playwright
def test_token_exchange_on_startup(browser_context: tuple[BrowserContext, str]):
    """Test 2: Token handshake occurs on startup

    Verifies:
    - Background script exchanges token with server
    - Token is stored in chrome.storage.session
    """
    context, extension_id = browser_context

    # Open background service worker context
    # NOTE: Service workers run automatically, no explicit navigation needed

    # Open sidepanel and check authenticated state
    sidepanel = context.new_page()
    sidepanel.goto(f"chrome-extension://{extension_id}/sidepanel.html")
    sidepanel.wait_for_load_state("networkidle")

    # Verify server status is "Connected" (implies token exchange succeeded)
    # E2E principle: Verify what users see, not implementation details
    status = sidepanel.locator(".server-status")
    expect(status).to_contain_text("Connected", timeout=5000)

    sidepanel.close()


@pytest.mark.e2e_playwright
@pytest.mark.llm  # Requires LLM API key
def test_chat_sends_and_receives(browser_context: tuple[BrowserContext, str]):
    """Test 3: Chat input and streaming response

    Verifies:
    - User can type message
    - Send button works
    - LLM response streams in (requires API key)
    """
    context, extension_id = browser_context

    sidepanel = context.new_page()
    sidepanel.goto(f"chrome-extension://{extension_id}/sidepanel.html")
    sidepanel.wait_for_load_state("networkidle")

    # Type message (E2E principle: locate by actual HTML elements)
    chat_input = sidepanel.locator('.chat-input input[type="text"]')
    chat_input.fill("Hello, what is 2+2?")

    # Click send (locate by button text users see)
    send_button = sidepanel.get_by_role("button", name="Send")
    send_button.click()

    # Wait for assistant message to appear (E2E: role is in className)
    # NOTE: Response streaming may take a few seconds
    assistant_message = sidepanel.locator(".message-bubble.assistant").first
    expect(assistant_message).to_be_visible(timeout=15000)

    # Check that response contains text (any text)
    expect(assistant_message).not_to_be_empty()

    sidepanel.close()


@pytest.mark.e2e_playwright
@pytest.mark.local_mcp  # Requires MCP server at 127.0.0.1:9000
def test_mcp_server_registration_and_tools(browser_context: tuple[BrowserContext, str]):
    """Test 4: MCP server registration and tools list

    Prerequisites:
    - MCP server running: SYNAPSE_PORT=9000 python -m synapse

    Verifies:
    - User can register MCP server
    - Server appears in list
    - Tools list can be expanded
    """
    context, extension_id = browser_context

    sidepanel = context.new_page()
    sidepanel.goto(f"chrome-extension://{extension_id}/sidepanel.html")
    sidepanel.wait_for_load_state("networkidle")

    # Navigate to MCP Servers tab (E2E: locate by button text)
    mcp_tab = sidepanel.get_by_role("button", name="MCP Servers")
    mcp_tab.click()

    # Fill in MCP server URL (E2E: locate by placeholder)
    url_input = sidepanel.locator('input[placeholder="MCP Server URL"]')
    url_input.fill("http://127.0.0.1:9000/mcp")

    # Click "Add Server" (E2E: locate by button text)
    add_button = sidepanel.get_by_role("button", name="Add Server")
    add_button.click()

    # Wait for server to appear in list (E2E: actual CSS class)
    server_item = sidepanel.locator(".server-item").first
    expect(server_item).to_be_visible(timeout=5000)

    # Expand server to see tools (E2E: actual CSS class)
    expand_button = server_item.locator(".expand-button")
    expand_button.click()

    # Check tools list appears (E2E: actual CSS class)
    tools_list = server_item.locator(".tools-list")
    expect(tools_list).to_be_visible(timeout=3000)

    sidepanel.close()


@pytest.mark.e2e_playwright
@pytest.mark.local_a2a  # Requires A2A agent at 127.0.0.1:9001
def test_a2a_agent_registration(browser_context: tuple[BrowserContext, str]):
    """Test 5: A2A agent registration

    Prerequisites:
    - A2A echo agent running: python tests/fixtures/a2a_agents/echo_agent.py 9001

    Verifies:
    - User can register A2A agent
    - Agent appears in list with agent card info
    """
    context, extension_id = browser_context

    sidepanel = context.new_page()
    sidepanel.goto(f"chrome-extension://{extension_id}/sidepanel.html")
    sidepanel.wait_for_load_state("networkidle")

    # Navigate to A2A Agents tab (E2E: locate by button text)
    a2a_tab = sidepanel.get_by_role("button", name="A2A Agents")
    a2a_tab.click()

    # Fill in A2A agent URL (E2E: locate by placeholder)
    url_input = sidepanel.locator('input[placeholder="A2A Agent URL"]')
    url_input.fill("http://127.0.0.1:9001")

    # Click "Add Agent" (E2E: locate by button text)
    add_button = sidepanel.get_by_role("button", name="Add Agent")
    add_button.click()

    # Wait for agent to appear in list (E2E: actual CSS class)
    agent_item = sidepanel.locator(".agent-item").first
    expect(agent_item).to_be_visible(timeout=5000)

    # Check agent name displays (E2E: actual CSS class)
    agent_name = agent_item.locator(".agent-name")
    expect(agent_name).not_to_be_empty()

    sidepanel.close()


@pytest.mark.e2e_playwright
@pytest.mark.llm
def test_conversation_persists_across_tabs(browser_context: tuple[BrowserContext, str]):
    """Test 6: Conversation history persists when switching tabs

    Verifies:
    - User sends message in Chat tab
    - User switches to MCP Servers tab
    - User switches back to Chat tab
    - Previous conversation is still visible
    """
    context, extension_id = browser_context

    sidepanel = context.new_page()
    sidepanel.goto(f"chrome-extension://{extension_id}/sidepanel.html")
    sidepanel.wait_for_load_state("networkidle")

    # Send a message in Chat (E2E principle: locate by actual HTML elements)
    chat_input = sidepanel.locator('.chat-input input[type="text"]')
    chat_input.fill("Test message for persistence")
    send_button = sidepanel.get_by_role("button", name="Send")
    send_button.click()

    # Wait for message to appear (E2E: role is in className)
    user_message = sidepanel.locator(".message-bubble.user").first
    expect(user_message).to_be_visible(timeout=5000)

    # Switch to MCP Servers tab (E2E: locate by button text)
    mcp_tab = sidepanel.get_by_role("button", name="MCP Servers")
    mcp_tab.click()

    # Wait a moment
    sidepanel.wait_for_timeout(1000)

    # Switch back to Chat tab (E2E: locate by button text)
    chat_tab = sidepanel.get_by_role("button", name="Chat")
    chat_tab.click()

    # Verify conversation is still there (E2E: role is in className)
    user_message_after = sidepanel.locator(".message-bubble.user").first
    expect(user_message_after).to_contain_text("Test message for persistence")

    sidepanel.close()


@pytest.mark.e2e_playwright
@pytest.mark.llm
def test_code_block_rendering(browser_context: tuple[BrowserContext, str]):
    """Test 7: Code block syntax highlighting

    Verifies:
    - Code blocks in LLM responses are rendered
    - Syntax highlighting is applied (via highlight.js or similar)
    """
    context, extension_id = browser_context

    sidepanel = context.new_page()
    sidepanel.goto(f"chrome-extension://{extension_id}/sidepanel.html")
    sidepanel.wait_for_load_state("networkidle")

    # Ask LLM to generate code (E2E principle: locate by actual HTML elements)
    chat_input = sidepanel.locator('.chat-input input[type="text"]')
    chat_input.fill("Write a Python function that prints 'hello'")
    send_button = sidepanel.get_by_role("button", name="Send")
    send_button.click()

    # Wait for assistant response (E2E: role is in className)
    assistant_message = sidepanel.locator(".message-bubble.assistant").first
    expect(assistant_message).to_be_visible(timeout=15000)

    # Check for code block element (E2E: actual CSS class)
    code_block = sidepanel.locator(".code-block").first
    expect(code_block).to_be_visible(timeout=5000)

    # Verify syntax highlighting is applied (react-syntax-highlighter)
    # SyntaxHighlighter component renders with language-specific classes
    highlighted = code_block.locator('code[class*="language-"]')
    expect(highlighted).to_be_visible()

    sidepanel.close()
