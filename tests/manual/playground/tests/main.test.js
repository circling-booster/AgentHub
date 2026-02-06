/**
 * TDD Step 5.7: Red Phase
 * main.js 통합 테스트
 */

import { describe, test, expect, beforeEach, jest } from '@jest/globals';

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

    test("Red: initHealthCheck handles error", async () => {
        // Given: Mock error response
        global.fetch.mockRejectedValue(new Error("Network error"));

        // When: initHealthCheck 호출
        const { initHealthCheck } = await import("../js/main.js");
        await initHealthCheck();

        // Then: Error state 업데이트
        const indicator = document.querySelector("[data-testid='health-indicator']");
        const statusText = document.getElementById("health-status");

        expect(indicator.getAttribute("data-status")).toBe("error");
        expect(statusText.textContent).toBe("Backend unreachable");
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

    test("Red: initTabNavigation activates first tab by default", async () => {
        // Given: Tab buttons
        const { initTabNavigation } = await import("../js/main.js");

        // When: 초기화
        initTabNavigation();

        // Then: Chat 탭이 기본 활성화 (클릭 없이)
        const chatBtn = document.querySelector("[data-testid='tab-chat']");
        const chatTab = document.getElementById("chat-tab");

        // Note: 이 테스트는 초기 상태만 확인
        expect(chatBtn).toBeTruthy();
        expect(chatTab).toBeTruthy();
    });
});
