# Phase 4: HTML/CSS (Static Layout)

## Overview

**목표:** Playground의 HTML 레이아웃과 CSS 스타일링 작성 (JavaScript 제외)

**TDD 원칙:** HTML/CSS는 **TDD 예외** (E2E로 검증)

**전제 조건:** Phase 1-3 완료 (백엔드 DEV_MODE 지원)

---

## Why No TDD for HTML/CSS?

### TDD 불가능/비효율적인 이유

1. **시각적 요소**: "버튼이 파란색인가?"는 단위 테스트로 검증 어려움
2. **레이아웃**: Grid/Flexbox는 브라우저 렌더링이 필요
3. **반응형**: 다양한 화면 크기는 E2E/Visual Regression 테스트가 적합

### 검증 방법

- **Phase 6 (E2E)**: Playwright로 실제 브라우저에서 검증
- **수동 테스트**: 개발자가 직접 확인 (Step 4.3)

---

## Implementation Steps

### Step 4.1: HTML 레이아웃 작성

**목표:** Playground UI 구조 생성 (JavaScript 없음)

**파일:** `tests/manual/playground/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgentHub Playground</title>
    <link rel="stylesheet" href="css/styles.css">
</head>
<body>
    <!-- Header -->
    <header>
        <h1>AgentHub Playground</h1>
        <div class="health-indicator" data-testid="health-indicator" data-status="loading">
            <span>●</span> <span id="health-status">Checking...</span>
        </div>
    </header>

    <!-- Tab Navigation -->
    <nav class="tab-nav">
        <button class="tab-btn active" data-tab="chat" data-testid="tab-chat">Chat</button>
        <button class="tab-btn" data-tab="mcp" data-testid="tab-mcp">MCP</button>
        <button class="tab-btn" data-tab="a2a" data-testid="tab-a2a">A2A</button>
        <button class="tab-btn" data-tab="conversations" data-testid="tab-conversations">Conversations</button>
        <button class="tab-btn" data-tab="usage" data-testid="tab-usage">Usage</button>
        <button class="tab-btn" data-tab="workflow" data-testid="tab-workflow">Workflow</button>
    </nav>

    <!-- Tab Contents -->
    <main class="tab-content">
        <!-- Chat Tab -->
        <div id="chat-tab" class="tab-pane active">
            <div class="two-panel">
                <!-- Left: Chat UI -->
                <div class="chat-panel">
                    <div class="chat-messages" data-testid="chat-messages">
                        <!-- 메시지는 JS로 동적 생성 (Phase 5) -->
                    </div>
                    <div class="chat-input-wrapper">
                        <input type="text" data-testid="chat-input" placeholder="Type a message..." />
                        <button data-testid="chat-send-btn">Send</button>
                    </div>
                </div>

                <!-- Right: SSE Log -->
                <div class="sse-log-panel">
                    <h3>SSE Events</h3>
                    <pre data-testid="sse-log"></pre>
                    <div data-testid="sse-status">disconnected</div>
                </div>
            </div>
        </div>

        <!-- MCP Tab -->
        <div id="mcp-tab" class="tab-pane">
            <div class="form-group">
                <input type="text" data-testid="mcp-name-input" placeholder="Server Name" />
                <input type="text" data-testid="mcp-url-input" placeholder="Server URL" />
                <button data-testid="mcp-register-btn">Register</button>
            </div>
            <div class="server-list" data-testid="mcp-server-list">
                <!-- 서버 카드는 JS로 동적 생성 (Phase 5) -->
            </div>
        </div>

        <!-- A2A Tab -->
        <div id="a2a-tab" class="tab-pane">
            <div class="form-group">
                <input type="text" data-testid="a2a-name-input" placeholder="Agent Name" />
                <input type="text" data-testid="a2a-url-input" placeholder="Agent URL" />
                <button data-testid="a2a-register-btn">Register</button>
            </div>
            <div class="agent-list" data-testid="a2a-agent-list">
                <!-- 에이전트 카드는 JS로 동적 생성 (Phase 5) -->
            </div>
        </div>

        <!-- Conversations Tab -->
        <div id="conversations-tab" class="tab-pane">
            <button data-testid="conversation-create-btn">Create Conversation</button>
            <div class="conversation-list" data-testid="conversation-list">
                <!-- 대화 목록은 JS로 동적 생성 (Phase 5) -->
            </div>
        </div>

        <!-- Usage Tab -->
        <div id="usage-tab" class="tab-pane">
            <div data-testid="usage-summary">
                <!-- Usage 요약은 JS로 동적 생성 (Phase 5) -->
            </div>
            <div class="form-group">
                <input type="number" data-testid="budget-input" placeholder="Budget ($)" />
                <button data-testid="budget-set-btn">Set Budget</button>
            </div>
            <div data-testid="budget-display"></div>
        </div>

        <!-- Workflow Tab -->
        <div id="workflow-tab" class="tab-pane">
            <div class="form-group">
                <input type="text" data-testid="workflow-name-input" placeholder="Workflow Name" />
                <textarea data-testid="workflow-steps-input" placeholder='["step1", "step2"]'></textarea>
                <button data-testid="workflow-execute-btn">Execute</button>
            </div>
            <div data-testid="workflow-result"></div>
        </div>
    </main>

    <!-- JavaScript 모듈은 Phase 5에서 작성 -->
    <!-- <script type="module" src="js/main.js"></script> -->
</body>
</html>
```

**주요 특징:**
- **Semantic HTML**: header, nav, main 태그 사용
- **data-testid**: Phase 6 E2E 테스트를 위한 안정적인 셀렉터
- **JS 미포함**: JavaScript는 Phase 5에서 TDD로 작성

---

### Step 4.2: CSS 스타일 작성

**목표:** Tailwind-like 스타일링 적용

**파일:** `tests/manual/playground/css/styles.css`

```css
/* Reset */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f5f5f5;
    color: #333;
    line-height: 1.6;
}

/* Header */
header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background: #fff;
    border-bottom: 1px solid #e0e0e0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

header h1 {
    font-size: 1.5rem;
    font-weight: 600;
}

/* Health Indicator */
.health-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
}

.health-indicator[data-status="healthy"] span:first-child {
    color: #28a745;
}

.health-indicator[data-status="error"] span:first-child {
    color: #dc3545;
}

.health-indicator[data-status="loading"] span:first-child {
    color: #6c757d;
}

/* Tab Navigation */
.tab-nav {
    display: flex;
    background: #fff;
    border-bottom: 1px solid #e0e0e0;
    overflow-x: auto;
}

.tab-btn {
    padding: 1rem 2rem;
    border: none;
    background: transparent;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
    font-size: 0.95rem;
    white-space: nowrap;
}

.tab-btn:hover {
    background: #f8f9fa;
}

.tab-btn.active {
    border-bottom-color: #007bff;
    color: #007bff;
    font-weight: 500;
}

/* Tab Content */
.tab-content {
    padding: 2rem;
    max-width: 1400px;
    margin: 0 auto;
}

.tab-pane {
    display: none;
}

.tab-pane.active {
    display: block;
}

/* Two Panel Layout (Chat Tab) */
.two-panel {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    height: 70vh;
}

@media (max-width: 1024px) {
    .two-panel {
        grid-template-columns: 1fr;
        height: auto;
    }
}

.chat-panel, .sse-log-panel {
    background: #fff;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    overflow-y: auto;
}

/* Chat Messages */
.chat-messages {
    height: calc(100% - 60px);
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.chat-message {
    padding: 0.75rem;
    border-radius: 6px;
    max-width: 80%;
}

.chat-message[data-testid*="user"] {
    background: #007bff;
    color: #fff;
    align-self: flex-end;
}

.chat-message[data-testid*="agent"] {
    background: #f1f3f5;
    color: #333;
    align-self: flex-start;
}

/* Chat Input */
.chat-input-wrapper {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
}

.chat-input-wrapper input {
    flex: 1;
    padding: 0.75rem;
    border: 1px solid #ced4da;
    border-radius: 6px;
    font-size: 0.95rem;
}

.chat-input-wrapper input:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.chat-input-wrapper button {
    padding: 0.75rem 1.5rem;
    background: #007bff;
    color: #fff;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    transition: background 0.2s;
}

.chat-input-wrapper button:hover {
    background: #0056b3;
}

/* SSE Log */
.sse-log-panel h3 {
    margin-bottom: 1rem;
    font-size: 1.1rem;
}

.sse-log-panel pre {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 0.85rem;
    font-family: "Courier New", monospace;
    max-height: 50vh;
    overflow-y: auto;
}

.sse-log-panel [data-testid="sse-status"] {
    margin-top: 1rem;
    padding: 0.5rem;
    background: #e9ecef;
    border-radius: 4px;
    text-align: center;
    font-size: 0.85rem;
}

/* Form Groups */
.form-group {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}

.form-group input,
.form-group textarea {
    flex: 1;
    min-width: 200px;
    padding: 0.75rem;
    border: 1px solid #ced4da;
    border-radius: 6px;
    font-size: 0.95rem;
}

.form-group textarea {
    min-height: 100px;
    resize: vertical;
    font-family: "Courier New", monospace;
}

.form-group input:focus,
.form-group textarea:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.form-group button {
    padding: 0.75rem 1.5rem;
    background: #007bff;
    color: #fff;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    transition: background 0.2s;
    white-space: nowrap;
}

.form-group button:hover {
    background: #0056b3;
}

/* Lists (Server, Agent, Conversation) */
.server-list,
.agent-list,
.conversation-list {
    display: grid;
    gap: 1rem;
}

.card {
    background: #fff;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s, box-shadow 0.2s;
}

.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card h3 {
    margin-bottom: 0.5rem;
    font-size: 1.1rem;
}

.card p {
    color: #6c757d;
    font-size: 0.9rem;
}

/* Usage Summary */
[data-testid="usage-summary"] {
    background: #fff;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    margin-bottom: 1.5rem;
}

/* Budget Display */
[data-testid="budget-display"] {
    background: #e7f5ff;
    padding: 1rem;
    border-radius: 6px;
    border-left: 4px solid #007bff;
    font-size: 1.1rem;
    font-weight: 500;
}

/* Workflow Result */
[data-testid="workflow-result"] {
    background: #fff;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    margin-top: 1.5rem;
}

/* Utility Classes */
.hidden {
    display: none !important;
}

.loading {
    opacity: 0.6;
    pointer-events: none;
}
```

**주요 특징:**
- **Responsive**: Grid layout with media queries
- **Accessibility**: Focus states, semantic colors
- **Consistency**: Unified spacing, colors, shadows

---

### Step 4.3: 수동 테스트 (HTML/CSS 확인)

**목표:** 브라우저에서 레이아웃 확인

**테스트 방법:**

```bash
# Static 서버 시작
python -m http.server 3000 --directory tests/manual/playground

# 브라우저 접속
# http://localhost:3000
```

**확인 항목:**

1. **Header**
   - [ ] "AgentHub Playground" 타이틀 표시
   - [ ] Health Indicator 표시 (회색 ● "Checking...")

2. **Tab Navigation**
   - [ ] 6개 탭 버튼 표시
   - [ ] "Chat" 탭이 active 상태 (파란색 밑줄)

3. **Chat Tab**
   - [ ] 좌측: 채팅 패널 (입력창 + Send 버튼)
   - [ ] 우측: SSE Log 패널 (빈 상태)

4. **Other Tabs**
   - [ ] MCP: 등록 폼 + 서버 목록 영역
   - [ ] A2A: 등록 폼 + 에이전트 목록 영역
   - [ ] Conversations: Create 버튼 + 목록 영역
   - [ ] Usage: Budget 입력 폼 + 요약 영역
   - [ ] Workflow: Name/Steps 입력 폼 + 결과 영역

5. **Responsive**
   - [ ] 브라우저 창 크기 조절 시 레이아웃 유지
   - [ ] 모바일 화면에서 Two-panel이 Single-column으로 변경

**JavaScript 동작하지 않음:**
- 탭 클릭해도 전환 안됨 (예상된 동작 - Phase 5에서 구현)
- 버튼 클릭해도 아무 일 없음 (예상된 동작)
- Health Indicator 상태 변경 안됨 (예상된 동작)

---

## Verification

### 1. HTML 유효성 검사
```bash
# W3C HTML Validator (옵션)
npm install -g html-validator-cli
html-validator tests/manual/playground/index.html
```

### 2. CSS 유효성 검사
```bash
# CSS Lint (옵션)
npm install -g csslint
csslint tests/manual/playground/css/styles.css
```

### 3. 수동 시각 검사
- 각 탭 레이아웃 확인
- 폼 요소 정렬 확인
- 반응형 동작 확인

---

## Critical Files

| 파일 | 내용 |
|------|------|
| `tests/manual/playground/index.html` | HTML 레이아웃 (JS 없음) |
| `tests/manual/playground/css/styles.css` | CSS 스타일 |

**생성되지 않는 파일 (Phase 5에서 작성):**
- `js/api-client.js`
- `js/sse-handler.js`
- `js/ui-components.js`
- `js/main.js`

---

## Next Steps

**Phase 5로 이동**: JavaScript 모듈을 TDD로 작성 (Red → Green → Refactor)

**Rollback 조건**: HTML/CSS 레이아웃에 문제 있으면 수정 후 재테스트

---


*Last Updated: 2026-02-05*
*No TDD (HTML/CSS Only)*
*JavaScript: Phase 5에서 TDD로 작성*
