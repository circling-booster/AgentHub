# Phase 6: E2E Tests (Playwright)

## Overview

**목표:** Playground 전체 플로우를 Playwright로 자동화하여 실제 사용자 시나리오 검증

**TDD 원칙:**
- **Red First**: 모든 E2E 시나리오를 먼저 작성 (실패 확인)
- **Green**: Playground 기능 구현 후 테스트 통과
- **Refactor**: 테스트 헬퍼 함수 추출 및 중복 제거

**전제 조건:**
- Phase 1-3 완료 (백엔드 DEV_MODE 지원)
- Phase 4 완료 (Playground Static Files)
- Phase 5 완료 (Unit Tests)

---

## Test Strategy

### E2E 테스트 범위

```
┌─────────────────────────────────────────────────────────────────┐
│                       E2E Test Scenarios                         │
├─────────────────────────────────────────────────────────────────┤
│ 1. Health Check UI                                              │
│    - 서버 시작 → Health API 호출 → 상태 표시 확인              │
│                                                                 │
│ 2. Chat SSE Streaming                                           │
│    - 메시지 입력 → SSE 연결 → 스트리밍 수신 → UI 업데이트       │
│                                                                 │
│ 3. MCP Server Management                                        │
│    - 서버 등록 → 목록 조회 → 도구 조회 → 서버 해제              │
│                                                                 │
│ 4. A2A Agent Management                                         │
│    - 에이전트 등록 → Card 표시 → 에이전트 해제                  │
│                                                                 │
│ 5. Conversations CRUD                                           │
│    - 대화 생성 → 목록 조회 → Tool Calls 조회 → 대화 삭제        │
│                                                                 │
│ 6. Usage & Budget                                               │
│    - Usage 조회 → Budget 설정 → Budget 조회                    │
│                                                                 │
│ 7. Workflow Execution                                           │
│    - Workflow 생성 → 실행 (SSE) → 결과 표시                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Steps (TDD)

### Step 6.1: Red - Health Check E2E 테스트 작성

**목표:** Playground가 Health API를 호출하고 상태를 표시하는지 검증

**테스트 파일:** `tests/e2e/test_playground.py`

```python
import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="module")
def playground_url():
    """Playground URL (static server)"""
    return "http://localhost:3000"

@pytest.fixture(scope="module")
def backend_url():
    """AgentHub API URL (DEV_MODE=true)"""
    return "http://localhost:8000"

class TestPlaygroundHealthCheck:
    """E2E Test: Health Check UI"""

    def test_health_status_displayed_on_load(self, page: Page, playground_url: str):
        """Red: Playground 로드 시 Health 상태가 표시되어야 함"""
        # Given: Playground 접속
        page.goto(playground_url)

        # When: 페이지 로드
        page.wait_for_load_state("networkidle")

        # Then: Health 상태 표시 확인
        health_indicator = page.locator("[data-testid='health-indicator']")
        expect(health_indicator).to_be_visible()
        expect(health_indicator).to_have_text("●")  # Green dot
        expect(health_indicator).to_have_attribute("data-status", "healthy")

    def test_health_check_failure_displays_error(self, page: Page, playground_url: str):
        """Red: Health API 실패 시 에러 상태 표시"""
        # Given: Backend가 중단된 상태 (시뮬레이션)
        # (Note: 실제 테스트에서는 네트워크 차단 또는 서버 중단)

        # When: Playground 접속
        page.goto(playground_url)
        page.wait_for_load_state("networkidle")

        # Then: 에러 상태 표시
        health_indicator = page.locator("[data-testid='health-indicator']")
        expect(health_indicator).to_have_attribute("data-status", "error")

        error_message = page.locator("[data-testid='health-error']")
        expect(error_message).to_contain_text("Backend unreachable")
```

**실행 결과:** ❌ 실패 (Playground HTML/JS 미구현)

**Next Step:** Phase 4로 돌아가 Health Check UI 구현

---

### Step 6.2: Red - Chat SSE 스트리밍 E2E 테스트 작성

**목표:** 사용자가 메시지를 입력하면 SSE로 스트리밍 응답을 받는지 검증

```python
class TestPlaygroundChatStreaming:
    """E2E Test: Chat SSE Streaming"""

    def test_chat_message_sent_and_streamed(self, page: Page, playground_url: str):
        """Red: 메시지 전송 후 SSE 스트리밍 수신"""
        # Given: Chat 탭 활성화
        page.goto(playground_url)
        page.click("[data-testid='tab-chat']")

        # When: 메시지 입력 및 전송
        message_input = page.locator("[data-testid='chat-input']")
        message_input.fill("Hello, AgentHub!")
        page.click("[data-testid='chat-send-btn']")

        # Then: SSE 이벤트 로그에 text 이벤트 표시
        sse_log = page.locator("[data-testid='sse-log']")
        expect(sse_log).to_contain_text('"type":"text"')

        # And: 채팅 UI에 응답 표시
        chat_message = page.locator("[data-testid='chat-message-agent']").last
        expect(chat_message).to_be_visible()
        expect(chat_message).to_contain_text("Hi")  # 응답 내용 일부

    def test_chat_sse_events_displayed_in_log(self, page: Page, playground_url: str):
        """Red: SSE 이벤트가 실시간 로그에 표시"""
        # Given: Chat 탭 활성화
        page.goto(playground_url)
        page.click("[data-testid='tab-chat']")

        # When: 메시지 전송
        page.fill("[data-testid='chat-input']", "Test message")
        page.click("[data-testid='chat-send-btn']")

        # Then: SSE 로그에 이벤트 순서대로 표시
        sse_log = page.locator("[data-testid='sse-log']")
        expect(sse_log).to_contain_text('"type":"text"')
        expect(sse_log).to_contain_text('"type":"tool_call"')
        expect(sse_log).to_contain_text('"type":"done"')

    def test_chat_connection_closed_on_done(self, page: Page, playground_url: str):
        """Red: 'done' 이벤트 수신 시 연결 종료"""
        # Given: Chat 탭 활성화
        page.goto(playground_url)
        page.click("[data-testid='tab-chat']")

        # When: 메시지 전송 및 완료 대기
        page.fill("[data-testid='chat-input']", "Short message")
        page.click("[data-testid='chat-send-btn']")
        page.wait_for_selector("[data-testid='sse-done']")

        # Then: 연결 종료 표시
        connection_status = page.locator("[data-testid='sse-status']")
        expect(connection_status).to_have_text("closed")
```

**실행 결과:** ❌ 실패 (SSE Handler 미구현)

---

### Step 6.3: Red - MCP Server 관리 E2E 테스트 작성

**목표:** MCP 서버 등록/조회/해제 전체 플로우 검증

```python
class TestPlaygroundMcpManagement:
    """E2E Test: MCP Server Management"""

    def test_mcp_server_registration_flow(self, page: Page, playground_url: str):
        """Red: MCP 서버 등록 플로우"""
        # Given: MCP 탭 활성화
        page.goto(playground_url)
        page.click("[data-testid='tab-mcp']")

        # When: 서버 등록 폼 입력
        page.fill("[data-testid='mcp-name-input']", "test-server")
        page.fill("[data-testid='mcp-url-input']", "http://localhost:9000")
        page.click("[data-testid='mcp-register-btn']")

        # Then: 서버 목록에 표시
        server_card = page.locator("[data-testid='mcp-server-test-server']")
        expect(server_card).to_be_visible()
        expect(server_card).to_contain_text("test-server")
        expect(server_card).to_contain_text("http://localhost:9000")

    def test_mcp_tools_list_displayed(self, page: Page, playground_url: str):
        """Red: 등록된 서버의 도구 목록 조회"""
        # Given: 서버가 이미 등록됨
        page.goto(playground_url)
        page.click("[data-testid='tab-mcp']")

        # When: 도구 목록 조회 버튼 클릭
        page.click("[data-testid='mcp-tools-btn-test-server']")

        # Then: 도구 목록 표시
        tools_list = page.locator("[data-testid='mcp-tools-list']")
        expect(tools_list).to_be_visible()
        expect(tools_list).to_contain_text("get_weather")  # 예시 도구

    def test_mcp_server_unregister(self, page: Page, playground_url: str):
        """Red: MCP 서버 해제"""
        # Given: 서버가 등록됨
        page.goto(playground_url)
        page.click("[data-testid='tab-mcp']")

        # When: 해제 버튼 클릭
        page.click("[data-testid='mcp-unregister-btn-test-server']")

        # Then: 서버 카드 사라짐
        server_card = page.locator("[data-testid='mcp-server-test-server']")
        expect(server_card).not_to_be_visible()
```

**실행 결과:** ❌ 실패 (MCP UI 미구현)

---

### Step 6.4: Red - A2A Agent 관리 E2E 테스트 작성

**목표:** A2A 에이전트 등록/해제 플로우 검증

```python
class TestPlaygroundA2aManagement:
    """E2E Test: A2A Agent Management"""

    def test_a2a_agent_registration(self, page: Page, playground_url: str):
        """Red: A2A 에이전트 등록"""
        # Given: A2A 탭 활성화
        page.goto(playground_url)
        page.click("[data-testid='tab-a2a']")

        # When: 에이전트 등록
        page.fill("[data-testid='a2a-name-input']", "math-agent")
        page.fill("[data-testid='a2a-url-input']", "http://localhost:7000")
        page.click("[data-testid='a2a-register-btn']")

        # Then: Agent Card 표시
        agent_card = page.locator("[data-testid='a2a-agent-math-agent']")
        expect(agent_card).to_be_visible()
        expect(agent_card).to_contain_text("math-agent")

    def test_a2a_agent_unregister(self, page: Page, playground_url: str):
        """Red: A2A 에이전트 해제"""
        # Given: 에이전트가 등록됨
        page.goto(playground_url)
        page.click("[data-testid='tab-a2a']")

        # When: 해제 버튼 클릭
        page.click("[data-testid='a2a-unregister-btn-math-agent']")

        # Then: Agent Card 사라짐
        agent_card = page.locator("[data-testid='a2a-agent-math-agent']")
        expect(agent_card).not_to_be_visible()
```

**실행 결과:** ❌ 실패 (A2A UI 미구현)

---

### Step 6.5: Red - Conversations CRUD E2E 테스트 작성

**목표:** 대화 생성/조회/삭제 플로우 검증

```python
class TestPlaygroundConversations:
    """E2E Test: Conversations CRUD"""

    def test_conversation_creation(self, page: Page, playground_url: str):
        """Red: 대화 생성"""
        # Given: Conversations 탭 활성화
        page.goto(playground_url)
        page.click("[data-testid='tab-conversations']")

        # When: 대화 생성 버튼 클릭
        page.click("[data-testid='conversation-create-btn']")

        # Then: 새 대화가 목록에 표시
        conversation_item = page.locator("[data-testid='conversation-item']").first
        expect(conversation_item).to_be_visible()
        expect(conversation_item).to_contain_text("New Conversation")

    def test_conversation_tool_calls_displayed(self, page: Page, playground_url: str):
        """Red: Tool Calls 이력 조회"""
        # Given: 대화 선택
        page.goto(playground_url)
        page.click("[data-testid='tab-conversations']")
        page.click("[data-testid='conversation-item']").first

        # When: Tool Calls 탭 클릭
        page.click("[data-testid='conversation-tool-calls-tab']")

        # Then: Tool Calls 목록 표시
        tool_calls_list = page.locator("[data-testid='tool-calls-list']")
        expect(tool_calls_list).to_be_visible()

    def test_conversation_deletion(self, page: Page, playground_url: str):
        """Red: 대화 삭제"""
        # Given: 대화가 존재함
        page.goto(playground_url)
        page.click("[data-testid='tab-conversations']")

        # When: 삭제 버튼 클릭
        page.click("[data-testid='conversation-delete-btn']").first

        # Then: 대화가 목록에서 사라짐
        conversation_item = page.locator("[data-testid='conversation-item']").first
        expect(conversation_item).not_to_be_visible()
```

**실행 결과:** ❌ 실패 (Conversations UI 미구현)

---

### Step 6.6: Red - Usage & Budget E2E 테스트 작성

**목표:** Usage 조회 및 Budget 설정 플로우 검증

```python
class TestPlaygroundUsage:
    """E2E Test: Usage & Budget"""

    def test_usage_summary_displayed(self, page: Page, playground_url: str):
        """Red: Usage 대시보드 표시"""
        # Given: Usage 탭 활성화
        page.goto(playground_url)
        page.click("[data-testid='tab-usage']")

        # Then: Usage 요약 표시
        usage_summary = page.locator("[data-testid='usage-summary']")
        expect(usage_summary).to_be_visible()
        expect(usage_summary).to_contain_text("Total Tokens:")
        expect(usage_summary).to_contain_text("Total Cost:")

    def test_budget_set_and_retrieved(self, page: Page, playground_url: str):
        """Red: Budget 설정 및 조회"""
        # Given: Usage 탭 활성화
        page.goto(playground_url)
        page.click("[data-testid='tab-usage']")

        # When: Budget 설정
        page.fill("[data-testid='budget-input']", "100.00")
        page.click("[data-testid='budget-set-btn']")

        # Then: Budget 표시 업데이트
        budget_display = page.locator("[data-testid='budget-display']")
        expect(budget_display).to_have_text("$100.00")
```

**실행 결과:** ❌ 실패 (Usage UI 미구현)

---

### Step 6.7: Red - Workflow 실행 E2E 테스트 작성

**목표:** Workflow 생성 및 실행 (SSE) 플로우 검증

```python
class TestPlaygroundWorkflow:
    """E2E Test: Workflow Execution"""

    def test_workflow_creation_form(self, page: Page, playground_url: str):
        """Red: Workflow 생성 폼"""
        # Given: Workflow 탭 활성화
        page.goto(playground_url)
        page.click("[data-testid='tab-workflow']")

        # When: Workflow 생성 폼 입력
        page.fill("[data-testid='workflow-name-input']", "Test Workflow")
        page.fill("[data-testid='workflow-steps-input']", '["step1", "step2"]')

        # Then: 폼 입력 확인
        workflow_name = page.locator("[data-testid='workflow-name-input']")
        expect(workflow_name).to_have_value("Test Workflow")

    def test_workflow_execution_sse_streaming(self, page: Page, playground_url: str):
        """Red: Workflow 실행 SSE 스트리밍"""
        # Given: Workflow가 생성됨
        page.goto(playground_url)
        page.click("[data-testid='tab-workflow']")

        # When: Workflow 실행 버튼 클릭
        page.click("[data-testid='workflow-execute-btn']")

        # Then: SSE 로그에 Workflow 이벤트 표시
        sse_log = page.locator("[data-testid='sse-log']")
        expect(sse_log).to_contain_text('"type":"workflow_started"')
        expect(sse_log).to_contain_text('"type":"workflow_completed"')

    def test_workflow_result_visualization(self, page: Page, playground_url: str):
        """Red: Workflow 결과 시각화"""
        # Given: Workflow 실행 완료
        page.goto(playground_url)
        page.click("[data-testid='tab-workflow']")
        page.click("[data-testid='workflow-execute-btn']")
        page.wait_for_selector("[data-testid='workflow-result']")

        # Then: 결과 표시
        workflow_result = page.locator("[data-testid='workflow-result']")
        expect(workflow_result).to_be_visible()
        expect(workflow_result).to_contain_text("Status: completed")
```

**실행 결과:** ❌ 실패 (Workflow UI 미구현)

---

### Step 6.8: Green - 모든 E2E 테스트 통과

**목표:** Phase 4 (Static Files) 구현 후 모든 E2E 테스트 통과 확인

**실행 방법:**
```bash
# 백엔드 시작 (DEV_MODE)
DEV_MODE=true uvicorn src.main:app --reload &

# Static 서버 시작
python -m http.server 3000 --directory tests/manual/playground &

# E2E 테스트 실행
pytest tests/e2e/test_playground.py -v
```

**예상 결과:** ✅ 모든 테스트 통과

---

### Step 6.9: Refactor - 테스트 헬퍼 함수 추출

**목표:** 중복 코드 제거 및 테스트 가독성 향상

**리팩토링 예시:**

```python
# tests/e2e/helpers/playground_helpers.py

from playwright.sync_api import Page, expect

class PlaygroundHelper:
    """Playground E2E 테스트 헬퍼"""

    def __init__(self, page: Page, playground_url: str):
        self.page = page
        self.playground_url = playground_url

    def navigate_to_tab(self, tab_name: str):
        """특정 탭으로 이동"""
        self.page.goto(self.playground_url)
        self.page.click(f"[data-testid='tab-{tab_name}']")

    def fill_chat_message(self, message: str):
        """Chat 메시지 입력"""
        self.page.fill("[data-testid='chat-input']", message)
        self.page.click("[data-testid='chat-send-btn']")

    def register_mcp_server(self, name: str, url: str):
        """MCP 서버 등록"""
        self.page.fill("[data-testid='mcp-name-input']", name)
        self.page.fill("[data-testid='mcp-url-input']", url)
        self.page.click("[data-testid='mcp-register-btn']")

    def assert_sse_event(self, event_type: str):
        """SSE 이벤트 로그 검증"""
        sse_log = self.page.locator("[data-testid='sse-log']")
        expect(sse_log).to_contain_text(f'"type":"{event_type}"')
```

**리팩토링 후 테스트:**

```python
# tests/e2e/test_playground.py (Refactored)

from tests.e2e.helpers.playground_helpers import PlaygroundHelper

class TestPlaygroundChatStreaming:
    """E2E Test: Chat SSE Streaming (Refactored)"""

    def test_chat_message_sent_and_streamed(
        self, page: Page, playground_url: str
    ):
        """Refactor: 헬퍼 함수 사용"""
        # Given
        helper = PlaygroundHelper(page, playground_url)
        helper.navigate_to_tab("chat")

        # When
        helper.fill_chat_message("Hello, AgentHub!")

        # Then
        helper.assert_sse_event("text")
        helper.assert_sse_event("done")
```

**실행 결과:** ✅ 모든 테스트 여전히 통과 (리팩토링 성공)

---

## Test Fixtures

### Playwright Fixtures

```python
# tests/e2e/conftest.py

import pytest
from playwright.sync_api import Browser, Page
import subprocess
import time

@pytest.fixture(scope="session")
def backend_server():
    """AgentHub API 서버 시작 (DEV_MODE)"""
    env = {"DEV_MODE": "true"}
    process = subprocess.Popen(
        ["uvicorn", "src.main:app", "--port", "8000"],
        env={**os.environ, **env}
    )
    time.sleep(2)  # 서버 시작 대기
    yield
    process.terminate()

@pytest.fixture(scope="session")
def static_server():
    """Playground Static 서버 시작"""
    process = subprocess.Popen(
        ["python", "-m", "http.server", "3000"],
        cwd="tests/manual/playground"
    )
    time.sleep(1)
    yield
    process.terminate()

@pytest.fixture
def playground_page(page: Page, backend_server, static_server):
    """Playground 페이지 (서버 시작 포함)"""
    page.goto("http://localhost:3000")
    yield page
```

---

## Coverage Verification

### E2E Coverage 대상

| 기능 | Coverage | 테스트 클래스 |
|------|----------|--------------|
| Health Check | ✅ | `TestPlaygroundHealthCheck` |
| Chat SSE | ✅ | `TestPlaygroundChatStreaming` |
| MCP Management | ✅ | `TestPlaygroundMcpManagement` |
| A2A Management | ✅ | `TestPlaygroundA2aManagement` |
| Conversations | ✅ | `TestPlaygroundConversations` |
| Usage & Budget | ✅ | `TestPlaygroundUsage` |
| Workflow | ✅ | `TestPlaygroundWorkflow` |

---

## TDD 검증 체크리스트

### Red Phase
- [ ] 모든 E2E 테스트 작성 완료 (Step 6.1-6.7)
- [ ] `pytest tests/e2e/test_playground.py -v` 실행 → 모두 실패 확인
- [ ] 실패 이유: Playground UI/JS 미구현

### Green Phase
- [ ] Phase 4 (Static Files) 구현 완료
- [ ] `pytest tests/e2e/test_playground.py -v` 실행 → 모두 통과
- [ ] 각 테스트가 실제 브라우저에서 정상 동작 확인

### Refactor Phase
- [ ] PlaygroundHelper 클래스 추출
- [ ] 중복 코드 제거 (navigate_to_tab, fill_form 등)
- [ ] `pytest tests/e2e/test_playground.py -v` 재실행 → 여전히 통과
- [ ] 테스트 가독성 향상 확인

---

## Playwright Best Practices

### 1. data-testid 사용
```html
<!-- Good: Stable selector -->
<button data-testid="chat-send-btn">Send</button>

<!-- Bad: Fragile selector -->
<button class="btn-primary">Send</button>
```

### 2. Explicit Waits
```python
# Good: 명시적 대기
page.wait_for_selector("[data-testid='sse-done']")

# Bad: 암묵적 대기 (time.sleep)
time.sleep(5)
```

### 3. Assertions
```python
# Good: Playwright assertions
expect(element).to_be_visible()

# Bad: Python assert
assert element.is_visible()
```

---

## Risk Mitigation

| 위험 | 대응 |
|------|------|
| 서버 시작 실패 | Fixture에서 healthcheck 대기 |
| SSE 타임아웃 | `page.wait_for_event()` 사용 |
| 테스트 격리 실패 | `scope="function"` 사용 |
| Playwright 설치 누락 | CI에서 `playwright install` 명령 추가 |

---

## Next Steps

**Phase 7로 이동**: E2E 테스트 통과 후 문서화 작업 시작

**Phase 4로 복귀**: E2E 테스트 실패 시 Playground UI/JS 구현

**Integration Test 검증**: Phase 1-3 백엔드 테스트 통과 확인

---

*Last Updated: 2026-02-05*
*TDD: Red-Green-Refactor*
*Tool: Playwright*
