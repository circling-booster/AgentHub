/**
 * TDD Step 5.9: Refactor Phase (Complete)
 * API Client 모듈 - 공통 패턴 추출로 코드 중복 제거
 */

const API_BASE = "http://localhost:8000";

/**
 * Common GET request helper
 * @param {string} url - Full URL to fetch
 * @returns {Promise<any>} JSON response
 */
async function fetchGet(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
}

/**
 * Common POST request helper
 * @param {string} url - Full URL to post
 * @param {object} body - Request body
 * @returns {Promise<any>} JSON response
 */
async function fetchPost(url, body) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
}

/**
 * Common DELETE request helper
 * @param {string} url - Full URL to delete
 */
async function fetchDelete(url) {
    const response = await fetch(url, {
        method: "DELETE"
    });
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
}

/**
 * Common PUT request helper
 * @param {string} url - Full URL to put
 * @param {object} body - Request body
 * @returns {Promise<any>} JSON response
 */
async function fetchPut(url, body) {
    const response = await fetch(url, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
}

// Health Check
export async function healthCheck() {
    return fetchGet(`${API_BASE}/health`);
}

// MCP Servers
export async function registerMcpServer(name, url) {
    return fetchPost(`${API_BASE}/api/mcp/servers`, { name, url });
}

export async function getMcpServers() {
    return fetchGet(`${API_BASE}/api/mcp/servers`);
}

export async function deleteMcpServer(serverId) {
    return fetchDelete(`${API_BASE}/api/mcp/servers/${serverId}`);
}

export async function getMcpTools(serverId) {
    return fetchGet(`${API_BASE}/api/mcp/servers/${serverId}/tools`);
}

// A2A Agents
export async function registerA2aAgent(name, url) {
    return fetchPost(`${API_BASE}/api/a2a/agents`, { name, url });
}

export async function getA2aAgents() {
    return fetchGet(`${API_BASE}/api/a2a/agents`);
}

export async function deleteA2aAgent(agentId) {
    return fetchDelete(`${API_BASE}/api/a2a/agents/${agentId}`);
}

// Chat SSE
export function getChatStreamUrl(message, conversationId = null) {
    const params = new URLSearchParams({ message });
    if (conversationId) {
        params.append("conversation_id", conversationId);
    }
    return `${API_BASE}/api/chat/stream?${params.toString()}`;
}

// Conversations CRUD
export async function createConversation(name) {
    return fetchPost(`${API_BASE}/api/conversations`, { title: name });
}

export async function getConversations() {
    return fetchGet(`${API_BASE}/api/conversations`);
}

export async function deleteConversation(conversationId) {
    return fetchDelete(`${API_BASE}/api/conversations/${conversationId}`);
}

export async function getToolCalls(conversationId) {
    return fetchGet(`${API_BASE}/api/conversations/${conversationId}/tool-calls`);
}

export async function addToolCall(conversationId, toolCall) {
    return fetchPost(`${API_BASE}/api/conversations/${conversationId}/tool-calls`, toolCall);
}

// Usage API
export async function getUsage() {
    return fetchGet(`${API_BASE}/api/usage/summary`);
}

export async function getBudget() {
    return fetchGet(`${API_BASE}/api/usage/budget`);
}

export async function setBudget(limit) {
    return fetchPut(`${API_BASE}/api/usage/budget`, { monthly_budget_usd: limit });
}

// Workflow API
export function getWorkflowStreamUrl(name, steps) {
    const params = new URLSearchParams({
        name: name,
        steps: JSON.stringify(steps)
    });
    return `${API_BASE}/api/workflows/execute?${params.toString()}`;
}
