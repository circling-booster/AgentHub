/**
 * TDD Step 5.1: Red Phase
 * api-client.js 테스트 먼저 작성
 */

import { describe, test, expect, beforeEach, afterEach, jest } from '@jest/globals';

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

    describe("registerA2aAgent", () => {
        test("Red: sends POST request with agent data", async () => {
            // Given: Mock fetch response
            global.fetch.mockResolvedValue({
                ok: true,
                json: async () => ({ id: "agent-1", name: "test-agent" })
            });

            // When: registerA2aAgent 호출
            const { registerA2aAgent } = await import("../js/api-client.js");
            const result = await registerA2aAgent("test-agent", "http://localhost:9001");

            // Then: POST 요청 확인
            expect(global.fetch).toHaveBeenCalledWith(
                `${API_BASE}/api/a2a/agents`,
                expect.objectContaining({
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        name: "test-agent",
                        url: "http://localhost:9001"
                    })
                })
            );
            expect(result.id).toBe("agent-1");
        });
    });

    describe("getA2aAgents", () => {
        test("Red: fetches agent list", async () => {
            // Given: Mock fetch response
            global.fetch.mockResolvedValue({
                ok: true,
                json: async () => ({
                    agents: [
                        { id: "agent-1", name: "test" }
                    ]
                })
            });

            // When: getA2aAgents 호출
            const { getA2aAgents } = await import("../js/api-client.js");
            const result = await getA2aAgents();

            // Then: GET 요청 및 응답 확인
            expect(global.fetch).toHaveBeenCalledWith(`${API_BASE}/api/a2a/agents`);
            expect(result.agents).toHaveLength(1);
        });
    });

    describe("deleteA2aAgent", () => {
        test("Red: sends DELETE request", async () => {
            // Given: Mock fetch response
            global.fetch.mockResolvedValue({ ok: true });

            // When: deleteA2aAgent 호출
            const { deleteA2aAgent } = await import("../js/api-client.js");
            await deleteA2aAgent("agent-1");

            // Then: DELETE 요청 확인
            expect(global.fetch).toHaveBeenCalledWith(
                `${API_BASE}/api/a2a/agents/agent-1`,
                expect.objectContaining({ method: "DELETE" })
            );
        });
    });

    // Chat SSE (누락 기능 추가)
    describe("getChatStreamUrl", () => {
        test("Red: returns SSE stream URL for chat", async () => {
            // Given: Chat message and conversation ID
            const { getChatStreamUrl } = await import("../js/api-client.js");

            // When: getChatStreamUrl 호출
            const url = getChatStreamUrl("Hello", "conv-1");

            // Then: 올바른 URL 반환 (query params 포함)
            expect(url).toContain(`${API_BASE}/api/chat/stream`);
            expect(url).toContain("message=Hello");
            expect(url).toContain("conversation_id=conv-1");
        });
    });

    // MCP Tools (누락 기능 추가)
    describe("getMcpTools", () => {
        test("Red: fetches tools for MCP server", async () => {
            // Given: Mock fetch response
            global.fetch.mockResolvedValue({
                ok: true,
                json: async () => ({
                    tools: [
                        { name: "search", description: "Search tool" }
                    ]
                })
            });

            // When: getMcpTools 호출
            const { getMcpTools } = await import("../js/api-client.js");
            const result = await getMcpTools("server-1");

            // Then: GET 요청 및 응답 확인
            expect(global.fetch).toHaveBeenCalledWith(
                `${API_BASE}/api/mcp/servers/server-1/tools`
            );
            expect(result.tools).toHaveLength(1);
        });
    });

    // Conversations CRUD (누락 기능 추가)
    describe("createConversation", () => {
        test("Red: creates new conversation", async () => {
            // Given: Mock fetch response
            global.fetch.mockResolvedValue({
                ok: true,
                json: async () => ({ id: "conv-1", name: "Test Conv" })
            });

            // When: createConversation 호출
            const { createConversation } = await import("../js/api-client.js");
            const result = await createConversation("Test Conv");

            // Then: POST 요청 확인
            expect(global.fetch).toHaveBeenCalledWith(
                `${API_BASE}/api/conversations`,
                expect.objectContaining({
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ title: "Test Conv" })
                })
            );
            expect(result.id).toBe("conv-1");
        });
    });

    describe("getConversations", () => {
        test("Red: fetches conversation list", async () => {
            // Given: Mock fetch response
            global.fetch.mockResolvedValue({
                ok: true,
                json: async () => ({
                    conversations: [
                        { id: "conv-1", name: "Test" }
                    ]
                })
            });

            // When: getConversations 호출
            const { getConversations } = await import("../js/api-client.js");
            const result = await getConversations();

            // Then: GET 요청 및 응답 확인
            expect(global.fetch).toHaveBeenCalledWith(`${API_BASE}/api/conversations`);
            expect(result.conversations).toHaveLength(1);
        });
    });

    describe("deleteConversation", () => {
        test("Red: sends DELETE request", async () => {
            // Given: Mock fetch response
            global.fetch.mockResolvedValue({ ok: true });

            // When: deleteConversation 호출
            const { deleteConversation } = await import("../js/api-client.js");
            await deleteConversation("conv-1");

            // Then: DELETE 요청 확인
            expect(global.fetch).toHaveBeenCalledWith(
                `${API_BASE}/api/conversations/conv-1`,
                expect.objectContaining({ method: "DELETE" })
            );
        });
    });

    describe("addToolCall", () => {
        test("Red: adds tool call to conversation", async () => {
            // Given: Mock fetch response
            global.fetch.mockResolvedValue({
                ok: true,
                json: async () => ({ success: true })
            });

            // When: addToolCall 호출
            const { addToolCall } = await import("../js/api-client.js");
            const toolCall = { tool: "search", args: { query: "test" } };
            await addToolCall("conv-1", toolCall);

            // Then: POST 요청 확인
            expect(global.fetch).toHaveBeenCalledWith(
                `${API_BASE}/api/conversations/conv-1/tool-calls`,
                expect.objectContaining({
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(toolCall)
                })
            );
        });
    });

    // Usage API (누락 기능 추가)
    describe("getUsage", () => {
        test("Red: fetches usage statistics", async () => {
            // Given: Mock fetch response
            global.fetch.mockResolvedValue({
                ok: true,
                json: async () => ({
                    total_tokens: 1000,
                    total_cost: 0.05
                })
            });

            // When: getUsage 호출
            const { getUsage } = await import("../js/api-client.js");
            const result = await getUsage();

            // Then: GET 요청 및 응답 확인
            expect(global.fetch).toHaveBeenCalledWith(`${API_BASE}/api/usage/summary`);
            expect(result.total_tokens).toBe(1000);
        });
    });

    describe("getBudget", () => {
        test("Red: fetches budget limits", async () => {
            // Given: Mock fetch response
            global.fetch.mockResolvedValue({
                ok: true,
                json: async () => ({
                    limit: 10.0,
                    used: 5.0
                })
            });

            // When: getBudget 호출
            const { getBudget } = await import("../js/api-client.js");
            const result = await getBudget();

            // Then: GET 요청 및 응답 확인
            expect(global.fetch).toHaveBeenCalledWith(`${API_BASE}/api/usage/budget`);
            expect(result.limit).toBe(10.0);
        });
    });

    describe("setBudget", () => {
        test("Red: sets budget limit", async () => {
            // Given: Mock fetch response
            global.fetch.mockResolvedValue({
                ok: true,
                json: async () => ({ success: true })
            });

            // When: setBudget 호출
            const { setBudget } = await import("../js/api-client.js");
            await setBudget(20.0);

            // Then: PUT 요청 확인
            expect(global.fetch).toHaveBeenCalledWith(
                `${API_BASE}/api/usage/budget`,
                expect.objectContaining({
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ monthly_budget_usd: 20.0 })
                })
            );
        });
    });

    // Workflow API (누락 기능 추가)
    describe("getWorkflowStreamUrl", () => {
        test("Red: returns SSE stream URL for workflow", async () => {
            // Given: Workflow data
            const { getWorkflowStreamUrl } = await import("../js/api-client.js");

            // When: getWorkflowStreamUrl 호출
            const url = getWorkflowStreamUrl("my-workflow", ["step1", "step2"]);

            // Then: 올바른 URL 반환
            expect(url).toContain(`${API_BASE}/api/workflows/execute`);
            expect(url).toContain("name=my-workflow");
        });
    });
});
