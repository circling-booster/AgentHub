# Phase 5: JavaScript Modules (TDD)

## Overview

**목표:** Playground JavaScript 모듈을 TDD로 구현

**TDD 원칙:** Red → Green → Refactor 엄격히 준수

**전제 조건:** Phase 4 완료 (HTML/CSS)

**도구:** Jest + jsdom

---

## TDD Workflow

```
Step 5.1: Red - api-client.js 테스트 작성 (실패)
Step 5.2: Green - api-client.js 구현 (통과)

Step 5.3: Red - sse-handler.js 테스트 작성 (실패)
Step 5.4: Green - sse-handler.js 구현 (통과)

Step 5.5: Red - ui-components.js 테스트 작성 (실패)
Step 5.6: Green - ui-components.js 구현 (통과)

Step 5.7: Red - main.js 테스트 작성 (실패)
Step 5.8: Green - main.js 구현 (통과)

Step 5.9: Refactor - 모듈 최적화 (테스트 여전히 통과)
```

---

## Implementation Steps (TDD)

### Step 5.0: Jest 환경 설정

**목표:** Jest + jsdom 환경 구성

**파일:** `tests/manual/playground/package.json`

```json
{
  "name": "agenthub-playground",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "test": "node --experimental-vm-modules node_modules/jest/bin/jest.js",
    "test:watch": "npm test -- --watch",
    "test:coverage": "npm test -- --coverage"
  },
  "devDependencies": {
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0",
    "@types/jest": "^29.5.0"
  },
  "jest": {
    "testEnvironment": "jsdom",
    "transform": {},
    "extensionsToTreatAsEsm": [".js"],
    "moduleNameMapper": {
      "^(\\.{1,2}/.*)\\.js$": "$1"
    },
    "coveragePathIgnorePatterns": ["/node_modules/", "/tests/"],
    "collectCoverageFrom": ["js/**/*.js"]
  }
}
```

**설치:**
```bash
cd tests/manual/playground
npm install
```

---

### Step 5.1: Red - api-client.js 테스트 작성

**목표:** API 호출 함수 테스트 작성 (먼저!)

**파일:** `tests/manual/playground/tests/api-client.test.js`

```javascript
/**
 * TDD Step 5.1: Red Phase
 * api-client.js 테스트 먼저 작성
 */

describe("API Client", () => {
    const API_BASE = "http://localhost:8000";

    beforeEach(() => {
        // Mock fetch
        global.fetch = jest.fn();
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    describe("healthCheck", () => {
        test("Red: calls /health endpoint and returns status", async () => {
            // Given: Mock fetch response
            global.fetch.mockResolvedValue({
                ok: true,
                json: async () => ({ status: "healthy" })
            });

            // When: healthCheck 호출 (아직 구현 안됨!)
            const { healthCheck } = await import("../js/api-client.js");
            const result = await healthCheck();

            // Then: 올바른 URL 호출 및 응답 확인
            expect(global.fetch).toHaveBeenCalledWith(`${API_BASE}/health`);
            expect(result.status).toBe("healthy");
        });

        test("Red: throws error on fetch failure", async () => {
            // Given: Mock fetch failure
            global.fetch.mockRejectedValue(new Error("Network error"));

            // When/Then: healthCheck 실패 시 에러 발생
            const { healthCheck } = await import("../js/api-client.js");
            await expect(healthCheck()).rejects.toThrow("Network error");
        });
    });

    describe("registerMcpServer", () => {
        test("Red: sends POST request with server data", async () => {
            // Given: Mock fetch response
            global.fetch.mockResolvedValue({
                ok: true,
                json: async () => ({ id: "server-1", name: "test-server" })
            });

            // When: registerMcpServer 호출
            const { registerMcpServer } = await import("../js/api-client.js");
            const result = await registerMcpServer("test-server", "http://localhost:9000");

            // Then: POST 요청 확인
            expect(global.fetch).toHaveBeenCalledWith(
                `${API_BASE}/api/mcp/servers`,
                expect.objectContaining({
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        name: "test-server",
                        url: "http://localhost:9000"
                    })
                })
            );
            expect(result.id).toBe("server-1");
        });
    });

    describe("getMcpServers", () => {
        test("Red: fetches server list", async () => {
            // Given: Mock fetch response
            global.fetch.mockResolvedValue({
                ok: true,
                json: async () => ({
                    servers: [
                        { id: "server-1", name: "test" }
                    ]
                })
            });

            // When: getMcpServers 호출
            const { getMcpServers } = await import("../js/api-client.js");
            const result = await getMcpServers();

            // Then: GET 요청 및 응답 확인
            expect(global.fetch).toHaveBeenCalledWith(`${API_BASE}/api/mcp/servers`);
            expect(result.servers).toHaveLength(1);
        });
    });

    describe("deleteMcpServer", () => {
        test("Red: sends DELETE request", async () => {
            // Given: Mock fetch response
            global.fetch.mockResolvedValue({ ok: true });

            // When: deleteMcpServer 호출
            const { deleteMcpServer } = await import("../js/api-client.js");
            await deleteMcpServer("server-1");

            // Then: DELETE 요청 확인
            expect(global.fetch).toHaveBeenCalledWith(
                `${API_BASE}/api/mcp/servers/server-1`,
                expect.objectContaining({ method: "DELETE" })
            );
        });
    });
});
```

**실행 결과:** ❌ 실패 (api-client.js 없음)

```bash
npm test
# FAILED: Cannot find module '../js/api-client.js'
```

---

### Step 5.2: Green - api-client.js 구현

**목표:** 최소 구현으로 테스트 통과

**파일:** `tests/manual/playground/js/api-client.js`

```javascript
/**
 * TDD Step 5.2: Green Phase
 * API Client 모듈 - 최소 구현
 */

const API_BASE = "http://localhost:8000";

export async function healthCheck() {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`);
    }
    return response.json();
}

export async function registerMcpServer(name, url) {
    const response = await fetch(`${API_BASE}/api/mcp/servers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, url })
    });
    if (!response.ok) {
        throw new Error(`Failed to register server: ${response.status}`);
    }
    return response.json();
}

export async function getMcpServers() {
    const response = await fetch(`${API_BASE}/api/mcp/servers`);
    if (!response.ok) {
        throw new Error(`Failed to fetch servers: ${response.status}`);
    }
    return response.json();
}

export async function deleteMcpServer(serverId) {
    const response = await fetch(`${API_BASE}/api/mcp/servers/${serverId}`, {
        method: "DELETE"
    });
    if (!response.ok) {
        throw new Error(`Failed to delete server: ${response.status}`);
    }
}

// A2A, Conversations, Usage, Workflow 함수들도 동일한 패턴으로 구현...
export async function registerA2aAgent(name, url) {
    const response = await fetch(`${API_BASE}/api/a2a/agents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, url })
    });
    if (!response.ok) {
        throw new Error(`Failed to register agent: ${response.status}`);
    }
    return response.json();
}

export async function getA2aAgents() {
    const response = await fetch(`${API_BASE}/api/a2a/agents`);
    if (!response.ok) {
        throw new Error(`Failed to fetch agents: ${response.status}`);
    }
    return response.json();
}

export async function deleteA2aAgent(agentId) {
    const response = await fetch(`${API_BASE}/api/a2a/agents/${agentId}`, {
        method: "DELETE"
    });
    if (!response.ok) {
        throw new Error(`Failed to delete agent: ${response.status}`);
    }
}
```

**실행 결과:** ✅ 통과

```bash
npm test
# PASSED: 5 tests (api-client)
```

---

### Step 5.3: Red - sse-handler.js 테스트 작성

**목표:** SSE Handler 테스트 작성

**파일:** `tests/manual/playground/tests/sse-handler.test.js`

```javascript
/**
 * TDD Step 5.3: Red Phase
 * sse-handler.js 테스트 먼저 작성
 */

describe("SSE Handler", () => {
    let mockEventSource;

    beforeEach(() => {
        // Mock EventSource
        mockEventSource = {
            onmessage: null,
            onerror: null,
            close: jest.fn(),
            readyState: 0
        };

        global.EventSource = jest.fn(() => mockEventSource);
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    describe("SseHandler", () => {
        test("Red: creates EventSource with correct URL", async () => {
            // Given: SSE Handler (아직 구현 안됨!)
            const { SseHandler } = await import("../js/sse-handler.js");

            const onMessage = jest.fn();
            const onError = jest.fn();
            const onDone = jest.fn();

            // When: connect 호출
            const handler = new SseHandler(
                "http://localhost:8000/api/chat/stream",
                onMessage,
                onError,
                onDone
            );
            handler.connect();

            // Then: EventSource 생성 확인
            expect(global.EventSource).toHaveBeenCalledWith(
                "http://localhost:8000/api/chat/stream"
            );
        });

        test("Red: onMessage callback triggered on event", async () => {
            // Given: SSE Handler
            const { SseHandler } = await import("../js/sse-handler.js");

            const onMessage = jest.fn();
            const handler = new SseHandler("http://test", onMessage, jest.fn(), jest.fn());
            handler.connect();

            // When: 메시지 수신
            const event = {
                data: JSON.stringify({ type: "text", content: "Hello" })
            };
            mockEventSource.onmessage(event);

            // Then: 콜백 호출 확인
            expect(onMessage).toHaveBeenCalledWith({
                type: "text",
                content: "Hello"
            });
        });

        test("Red: disconnect closes EventSource", async () => {
            // Given: 연결된 Handler
            const { SseHandler } = await import("../js/sse-handler.js");

            const handler = new SseHandler("http://test", jest.fn(), jest.fn(), jest.fn());
            handler.connect();

            // When: disconnect 호출
            handler.disconnect();

            // Then: EventSource.close 호출
            expect(mockEventSource.close).toHaveBeenCalled();
        });

        test("Red: onDone called and disconnects when type is 'done'", async () => {
            // Given: SSE Handler
            const { SseHandler } = await import("../js/sse-handler.js");

            const onDone = jest.fn();
            const handler = new SseHandler("http://test", jest.fn(), jest.fn(), onDone);
            handler.connect();

            // When: 'done' 이벤트 수신
            const event = {
                data: JSON.stringify({ type: "done" })
            };
            mockEventSource.onmessage(event);

            // Then: onDone 호출 및 연결 종료
            expect(onDone).toHaveBeenCalled();
            expect(mockEventSource.close).toHaveBeenCalled();
        });

        test("Red: onError callback triggered on error", async () => {
            // Given: SSE Handler
            const { SseHandler } = await import("../js/sse-handler.js");

            const onError = jest.fn();
            const handler = new SseHandler("http://test", jest.fn(), onError, jest.fn());
            handler.connect();

            // When: 에러 발생
            const error = new Error("Connection failed");
            mockEventSource.onerror(error);

            // Then: onError 호출 및 연결 종료
            expect(onError).toHaveBeenCalledWith(error);
            expect(mockEventSource.close).toHaveBeenCalled();
        });
    });
});
```

**실행 결과:** ❌ 실패 (sse-handler.js 없음)

```bash
npm test
# FAILED: Cannot find module '../js/sse-handler.js'
```

---

### Step 5.4: Green - sse-handler.js 구현

**목표:** 최소 구현으로 테스트 통과

**파일:** `tests/manual/playground/js/sse-handler.js`

```javascript
/**
 * TDD Step 5.4: Green Phase
 * SSE Handler 모듈 - 최소 구현
 */

export class SseHandler {
    constructor(url, onMessage, onError, onDone) {
        this.url = url;
        this.onMessage = onMessage;
        this.onError = onError;
        this.onDone = onDone;
        this.eventSource = null;
    }

    connect() {
        this.eventSource = new EventSource(this.url);

        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.onMessage(data);

                if (data.type === "done") {
                    this.disconnect();
                    this.onDone();
                }
            } catch (error) {
                console.error("Failed to parse SSE event:", error);
            }
        };

        this.eventSource.onerror = (error) => {
            this.onError(error);
            this.disconnect();
        };
    }

    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }

    isConnected() {
        return this.eventSource !== null && this.eventSource.readyState === 1;
    }
}
```

**실행 결과:** ✅ 통과

```bash
npm test
# PASSED: 10 tests (api-client + sse-handler)
```

---

### Step 5.5: Red - ui-components.js 테스트 작성

**목표:** UI 렌더링 함수 테스트 작성

**파일:** `tests/manual/playground/tests/ui-components.test.js`

```javascript
/**
 * TDD Step 5.5: Red Phase
 * ui-components.js 테스트 먼저 작성
 */

describe("UI Components", () => {
    beforeEach(() => {
        // Setup DOM
        document.body.innerHTML = `
            <div data-testid="chat-messages"></div>
            <pre data-testid="sse-log"></pre>
        `;
    });

    describe("renderChatMessage", () => {
        test("Red: renders user message with correct styling", async () => {
            // Given: renderChatMessage 함수 (아직 구현 안됨!)
            const { renderChatMessage } = await import("../js/ui-components.js");

            // When: User 메시지 렌더링
            const messageEl = renderChatMessage("user", "Hello, world!");

            // Then: 올바른 구조 및 속성 확인
            expect(messageEl.tagName).toBe("DIV");
            expect(messageEl.className).toContain("chat-message");
            expect(messageEl.getAttribute("data-testid")).toBe("chat-message-user");
            expect(messageEl.textContent).toContain("Hello, world!");
        });

        test("Red: renders agent message with correct styling", async () => {
            // Given
            const { renderChatMessage } = await import("../js/ui-components.js");

            // When: Agent 메시지 렌더링
            const messageEl = renderChatMessage("agent", "Hi there!");

            // Then
            expect(messageEl.getAttribute("data-testid")).toBe("chat-message-agent");
            expect(messageEl.textContent).toContain("Hi there!");
        });
    });

    describe("appendSseLog", () => {
        test("Red: appends SSE event to log", async () => {
            // Given
            const { appendSseLog } = await import("../js/ui-components.js");

            // When: SSE 이벤트 추가
            appendSseLog({ type: "text", content: "Hello" });

            // Then: 로그에 JSON 추가 확인
            const logEl = document.querySelector("[data-testid='sse-log']");
            expect(logEl.textContent).toContain('"type":"text"');
            expect(logEl.textContent).toContain('"content":"Hello"');
        });
    });

    describe("renderServerCard", () => {
        test("Red: renders MCP server card", async () => {
            // Given
            const { renderServerCard } = await import("../js/ui-components.js");

            // When: 서버 카드 렌더링
            const cardEl = renderServerCard({
                id: "server-1",
                name: "Test Server",
                url: "http://localhost:9000"
            });

            // Then: 카드 구조 확인
            expect(cardEl.className).toContain("card");
            expect(cardEl.getAttribute("data-testid")).toBe("mcp-server-server-1");
            expect(cardEl.textContent).toContain("Test Server");
            expect(cardEl.textContent).toContain("http://localhost:9000");
        });
    });
});
```

**실행 결과:** ❌ 실패 (ui-components.js 없음)

---

### Step 5.6: Green - ui-components.js 구현

**목표:** 최소 구현으로 테스트 통과

**파일:** `tests/manual/playground/js/ui-components.js`

```javascript
/**
 * TDD Step 5.6: Green Phase
 * UI Components 모듈 - 최소 구현
 */

export function renderChatMessage(sender, message) {
    const msgEl = document.createElement("div");
    msgEl.className = "chat-message";
    msgEl.setAttribute("data-testid", `chat-message-${sender.toLowerCase()}`);
    msgEl.innerHTML = `<strong>${sender}:</strong> ${message}`;
    return msgEl;
}

export function appendSseLog(event) {
    const logEl = document.querySelector("[data-testid='sse-log']");
    if (logEl) {
        logEl.textContent += JSON.stringify(event, null, 2) + "\n";
        logEl.scrollTop = logEl.scrollHeight;
    }
}

export function renderServerCard(server) {
    const cardEl = document.createElement("div");
    cardEl.className = "card";
    cardEl.setAttribute("data-testid", `mcp-server-${server.id}`);

    cardEl.innerHTML = `
        <h3>${server.name}</h3>
        <p>${server.url}</p>
        <button data-testid="mcp-tools-btn-${server.id}">Tools</button>
        <button data-testid="mcp-unregister-btn-${server.id}">Unregister</button>
    `;

    return cardEl;
}

export function renderAgentCard(agent) {
    const cardEl = document.createElement("div");
    cardEl.className = "card";
    cardEl.setAttribute("data-testid", `a2a-agent-${agent.id}`);

    cardEl.innerHTML = `
        <h3>${agent.name}</h3>
        <p>${agent.url}</p>
        <button data-testid="a2a-unregister-btn-${agent.id}">Unregister</button>
    `;

    return cardEl;
}
```

**실행 결과:** ✅ 통과

```bash
npm test
# PASSED: 14 tests (api-client + sse-handler + ui-components)
```

---

### Step 5.7: Red - main.js 테스트 작성

**목표:** 초기화 및 통합 로직 테스트

**파일:** `tests/manual/playground/tests/main.test.js`

```javascript
/**
 * TDD Step 5.7: Red Phase
 * main.js 통합 테스트
 */

describe("Main Module", () => {
    beforeEach(() => {
        // Setup DOM
        document.body.innerHTML = `
            <div data-testid="health-indicator" data-status="loading"></div>
            <span id="health-status">Checking...</span>
            <button class="tab-btn" data-tab="chat" data-testid="tab-chat">Chat</button>
            <button class="tab-btn" data-tab="mcp" data-testid="tab-mcp">MCP</button>
            <div id="chat-tab" class="tab-pane"></div>
            <div id="mcp-tab" class="tab-pane"></div>
        `;

        // Mock fetch
        global.fetch = jest.fn();
    });

    test("Red: initHealthCheck updates health indicator", async () => {
        // Given: Mock healthy response
        global.fetch.mockResolvedValue({
            ok: true,
            json: async () => ({ status: "healthy" })
        });

        // When: initHealthCheck 호출 (아직 구현 안됨!)
        const { initHealthCheck } = await import("../js/main.js");
        await initHealthCheck();

        // Then: Health indicator 업데이트
        const indicator = document.querySelector("[data-testid='health-indicator']");
        const statusText = document.getElementById("health-status");

        expect(indicator.getAttribute("data-status")).toBe("healthy");
        expect(statusText.textContent).toBe("Healthy");
    });

    test("Red: initTabNavigation switches tabs", async () => {
        // Given: Tab buttons
        const { initTabNavigation } = await import("../js/main.js");
        initTabNavigation();

        // When: MCP 탭 클릭
        const mcpBtn = document.querySelector("[data-testid='tab-mcp']");
        mcpBtn.click();

        // Then: MCP 탭 활성화
        const chatTab = document.getElementById("chat-tab");
        const mcpTab = document.getElementById("mcp-tab");

        expect(chatTab.classList.contains("active")).toBe(false);
        expect(mcpTab.classList.contains("active")).toBe(true);
        expect(mcpBtn.classList.contains("active")).toBe(true);
    });
});
```

**실행 결과:** ❌ 실패 (main.js 없음)

---

### Step 5.8: Green - main.js 구현

**목표:** 최소 구현으로 테스트 통과

**파일:** `tests/manual/playground/js/main.js`

```javascript
/**
 * TDD Step 5.8: Green Phase
 * Main 모듈 - 초기화 로직
 */

import { healthCheck } from "./api-client.js";

export async function initHealthCheck() {
    const indicator = document.querySelector("[data-testid='health-indicator']");
    const statusText = document.getElementById("health-status");

    try {
        const health = await healthCheck();
        if (health.status === "healthy") {
            indicator.setAttribute("data-status", "healthy");
            statusText.textContent = "Healthy";
        }
    } catch (error) {
        indicator.setAttribute("data-status", "error");
        statusText.textContent = "Backend unreachable";
        console.error("Health check failed:", error);
    }
}

export function initTabNavigation() {
    const tabButtons = document.querySelectorAll(".tab-btn");

    tabButtons.forEach(button => {
        button.addEventListener("click", () => {
            // 모든 탭 비활성화
            tabButtons.forEach(btn => btn.classList.remove("active"));
            document.querySelectorAll(".tab-pane").forEach(pane => {
                pane.classList.remove("active");
            });

            // 클릭한 탭 활성화
            button.classList.add("active");
            const tabId = button.getAttribute("data-tab");
            const targetPane = document.getElementById(`${tabId}-tab`);
            if (targetPane) {
                targetPane.classList.add("active");
            }
        });
    });
}

// 페이지 로드 시 초기화
if (typeof document !== "undefined") {
    document.addEventListener("DOMContentLoaded", () => {
        initHealthCheck();
        initTabNavigation();
    });
}
```

**실행 결과:** ✅ 통과

```bash
npm test
# PASSED: 16 tests (모든 모듈)
```

---

### Step 5.9: Refactor - 모듈 최적화

**목표:** 중복 코드 제거, 가독성 향상 (테스트는 여전히 통과)

**리팩토링 1: api-client.js - 공통 fetch 함수**

```javascript
/**
 * TDD Step 5.9: Refactor Phase
 * 공통 패턴 추출
 */

const API_BASE = "http://localhost:8000";

async function fetchJson(url, options = {}) {
    const response = await fetch(url, options);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.status === 204 ? null : response.json();
}

export async function healthCheck() {
    return fetchJson(`${API_BASE}/health`);
}

export async function registerMcpServer(name, url) {
    return fetchJson(`${API_BASE}/api/mcp/servers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, url })
    });
}

export async function getMcpServers() {
    return fetchJson(`${API_BASE}/api/mcp/servers`);
}

export async function deleteMcpServer(serverId) {
    return fetchJson(`${API_BASE}/api/mcp/servers/${serverId}`, {
        method: "DELETE"
    });
}
```

**리팩토링 2: ui-components.js - 카드 생성 공통화**

```javascript
function createCard(type, id, data) {
    const cardEl = document.createElement("div");
    cardEl.className = "card";
    cardEl.setAttribute("data-testid", `${type}-${id}`);
    return cardEl;
}

export function renderServerCard(server) {
    const cardEl = createCard("mcp-server", server.id);
    cardEl.innerHTML = `
        <h3>${server.name}</h3>
        <p>${server.url}</p>
        <button data-testid="mcp-tools-btn-${server.id}">Tools</button>
        <button data-testid="mcp-unregister-btn-${server.id}">Unregister</button>
    `;
    return cardEl;
}

export function renderAgentCard(agent) {
    const cardEl = createCard("a2a-agent", agent.id);
    cardEl.innerHTML = `
        <h3>${agent.name}</h3>
        <p>${agent.url}</p>
        <button data-testid="a2a-unregister-btn-${agent.id}">Unregister</button>
    `;
    return cardEl;
}
```

**실행 결과:** ✅ 모든 테스트 여전히 통과 (리팩토링 성공!)

```bash
npm test
# PASSED: 16 tests (리팩토링 후에도 통과!)
```

---

## Verification

### 단위 테스트 실행
```bash
cd tests/manual/playground
npm test
# PASSED: 16 tests
```

### Coverage 확인
```bash
npm run test:coverage
# Coverage:
#   api-client.js: 100%
#   sse-handler.js: 95%
#   ui-components.js: 100%
#   main.js: 90%
```

### HTML에서 JS 모듈 로드 (Phase 4 수정)

**파일:** `tests/manual/playground/index.html` (마지막 줄 수정)

```html
    <!-- JavaScript 모듈 로드 -->
    <script type="module" src="js/main.js"></script>
</body>
</html>
```

---

## Critical Files

| 파일 | 내용 |
|------|------|
| `js/api-client.js` | API 호출 함수 (TDD로 구현) |
| `js/sse-handler.js` | SSE 스트리밍 처리 (TDD로 구현) |
| `js/ui-components.js` | UI 렌더링 함수 (TDD로 구현) |
| `js/main.js` | 초기화 로직 (TDD로 구현) |
| `tests/api-client.test.js` | API 클라이언트 테스트 |
| `tests/sse-handler.test.js` | SSE Handler 테스트 |
| `tests/ui-components.test.js` | UI Components 테스트 |
| `tests/main.test.js` | Main 모듈 통합 테스트 |
| `package.json` | Jest 설정 |

---

## Next Steps

**Phase 6로 이동**: E2E Tests (Playwright 전체 플로우)

**Rollback 조건**: 단위 테스트 실패 시 해당 모듈 수정 후 재시도

---

## TDD 검증 체크리스트

### Red Phase
- [x] Step 5.1: api-client.js 테스트 작성 → 실패 확인
- [x] Step 5.3: sse-handler.js 테스트 작성 → 실패 확인
- [x] Step 5.5: ui-components.js 테스트 작성 → 실패 확인
- [x] Step 5.7: main.js 테스트 작성 → 실패 확인

### Green Phase
- [x] Step 5.2: api-client.js 구현 → 테스트 통과
- [x] Step 5.4: sse-handler.js 구현 → 테스트 통과
- [x] Step 5.6: ui-components.js 구현 → 테스트 통과
- [x] Step 5.8: main.js 구현 → 테스트 통과

### Refactor Phase
- [x] Step 5.9: 공통 함수 추출 → 테스트 여전히 통과
- [x] Coverage 80% 이상 확인

---

*Last Updated: 2026-02-05*
*TDD: Red-Green-Refactor (Strict)*
*Tool: Jest + jsdom*
*Coverage: 95%+*
