/**
 * TDD Step 5.5: Red Phase
 * ui-components.js 테스트 먼저 작성
 */

import { describe, test, expect, beforeEach } from '@jest/globals';

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
            expect(cardEl.getAttribute("data-testid")).toBe("mcp-server-Test Server");
            expect(cardEl.textContent).toContain("Test Server");
            expect(cardEl.textContent).toContain("http://localhost:9000");
        });
    });

    describe("renderAgentCard", () => {
        test("Red: renders A2A agent card", async () => {
            // Given
            const { renderAgentCard } = await import("../js/ui-components.js");

            // When: 에이전트 카드 렌더링
            const cardEl = renderAgentCard({
                id: "agent-1",
                name: "Test Agent",
                url: "http://localhost:9001"
            });

            // Then: 카드 구조 확인
            expect(cardEl.className).toContain("card");
            expect(cardEl.getAttribute("data-testid")).toBe("a2a-agent-Test Agent");
            expect(cardEl.textContent).toContain("Test Agent");
            expect(cardEl.textContent).toContain("http://localhost:9001");
        });
    });
});
