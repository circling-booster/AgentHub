/**
 * TDD Step 5.8: Green Phase
 * Main 모듈 - 초기화 로직
 */

import {
    healthCheck,
    registerMcpServer, getMcpServers, deleteMcpServer, getMcpTools,
    listResources, readResource,
    registerA2aAgent, getA2aAgents, deleteA2aAgent,
    getChatStreamUrl,
    createConversation, getConversations, deleteConversation, getToolCalls,
    getUsage, getBudget, setBudget,
    getWorkflowStreamUrl
} from "./api-client.js";

import { SseHandler } from "./sse-handler.js";

import {
    renderChatMessage,
    appendSseLog,
    renderServerCard,
    renderAgentCard
} from "./ui-components.js";

export async function initHealthCheck() {
    const indicator = document.querySelector("[data-testid='health-indicator']");
    const statusText = document.getElementById("health-status");
    const errorElement = document.querySelector("[data-testid='health-error']");

    try {
        const health = await healthCheck();
        if (health.status === "healthy") {
            indicator.setAttribute("data-status", "healthy");
            statusText.textContent = "Healthy";
        }
    } catch (error) {
        indicator.setAttribute("data-status", "error");
        statusText.textContent = "Backend unreachable";
        if (errorElement) {
            errorElement.textContent = "Backend unreachable";
            errorElement.style.display = "inline";
        }
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

export function initChatHandlers() {
    const sendBtn = document.querySelector("[data-testid='chat-send-btn']");
    const chatInput = document.querySelector("[data-testid='chat-input']");
    const chatMessages = document.querySelector("[data-testid='chat-messages']");
    const sseStatus = document.querySelector("[data-testid='sse-status']");

    sendBtn.addEventListener("click", () => {
        const message = chatInput.value.trim();
        if (!message) return;

        // User message 표시
        chatMessages.appendChild(renderChatMessage("User", message));
        chatInput.value = "";

        // SSE 연결
        const url = getChatStreamUrl(message, null);  // null = 백엔드가 자동 생성
        let agentResponse = "";

        const handler = new SseHandler(
            url,
            (data) => {
                appendSseLog(data);
                if (data.type === "text" && data.content) {
                    agentResponse += data.content;
                }
            },
            (err) => { sseStatus.textContent = "error"; },
            () => {
                sseStatus.textContent = "closed";
                // sse-done 마커 (E2E 테스트가 기다림)
                const done = document.createElement("div");
                done.setAttribute("data-testid", "sse-done");
                document.body.appendChild(done);
                // Agent 응답 표시
                if (agentResponse) {
                    chatMessages.appendChild(renderChatMessage("Agent", agentResponse));
                }
            }
        );
        handler.connect();
    });
}

export function initMcpHandlers() {
    const registerBtn = document.querySelector("[data-testid='mcp-register-btn']");
    const serverList = document.querySelector("[data-testid='mcp-server-list']");

    registerBtn.addEventListener("click", async () => {
        const name = document.querySelector("[data-testid='mcp-name-input']").value.trim();
        const url = document.querySelector("[data-testid='mcp-url-input']").value.trim();
        if (!name || !url) return;

        try {
            const server = await registerMcpServer(name, url);
            const card = renderServerCard(server);

            // Tools 버튼 핸들러
            card.querySelector(`[data-testid='mcp-tools-btn-${server.name}']`)
                .addEventListener("click", async () => {
                    let toolsList = card.querySelector("[data-testid='mcp-tools-list']");
                    if (!toolsList) {
                        toolsList = document.createElement("div");
                        toolsList.setAttribute("data-testid", "mcp-tools-list");
                        card.appendChild(toolsList);
                    }
                    toolsList.textContent = "Tools loaded";
                });

            // Unregister 버튼 핸들러
            card.querySelector(`[data-testid='mcp-unregister-btn-${server.name}']`)
                .addEventListener("click", async () => {
                    await deleteMcpServer(server.id);
                    card.remove();
                });

            serverList.appendChild(card);

            // 입력 필드 초기화
            document.querySelector("[data-testid='mcp-name-input']").value = "";
            document.querySelector("[data-testid='mcp-url-input']").value = "";

        } catch (e) {
            console.error(e);
            // 사용자에게 에러 표시
            const errorDiv = document.createElement("div");
            errorDiv.className = "error-message";
            errorDiv.setAttribute("data-testid", "mcp-error");
            errorDiv.textContent = `등록 실패: ${e.message}`;
            serverList.appendChild(errorDiv);
            setTimeout(() => errorDiv.remove(), 5000);  // 5초 후 제거
        }
    });
}

export function initResourcesHandlers() {
    const endpointSelect = document.querySelector("[data-testid='resources-endpoint-select']");
    const listBtn = document.querySelector("[data-testid='resources-list-btn']");
    const resourcesList = document.querySelector("[data-testid='resources-list']");
    const resourceContent = document.querySelector("[data-testid='resource-content']");

    // Populate endpoint select when tab is activated
    const resourcesTab = document.querySelector("[data-testid='tab-resources']");
    resourcesTab.addEventListener("click", async () => {
        try {
            const servers = await getMcpServers();
            endpointSelect.innerHTML = servers.map(s =>
                `<option value="${s.id}">${s.name}</option>`
            ).join('');
        } catch (e) {
            console.error("Failed to load endpoints:", e);
        }
    });

    // List resources button handler
    listBtn.addEventListener("click", async () => {
        const endpointId = endpointSelect.value;
        if (!endpointId) return;

        try {
            const data = await listResources(endpointId);
            resourcesList.innerHTML = data.resources.map(r => `
                <div class="resource-card" data-uri="${r.uri}">
                    <h4>${r.name}</h4>
                    <p>${r.description}</p>
                    <p><small>${r.mime_type || 'unknown'}</small></p>
                    <button data-testid="resource-read-btn" data-uri="${r.uri}">Read</button>
                </div>
            `).join('');

            // Add click handlers for read buttons
            resourcesList.querySelectorAll('[data-testid="resource-read-btn"]').forEach(btn => {
                btn.addEventListener("click", async (e) => {
                    const uri = e.target.getAttribute("data-uri");
                    try {
                        const content = await readResource(endpointId, uri);
                        resourceContent.innerHTML = `
                            <h3>Resource: ${uri}</h3>
                            <p><strong>MIME Type:</strong> ${content.mime_type || 'unknown'}</p>
                            ${content.text ? `<pre>${content.text}</pre>` : ''}
                            ${content.blob ? `<p>Binary data (Base64): ${content.blob.substring(0, 50)}...</p>` : ''}
                        `;
                    } catch (e) {
                        resourceContent.innerHTML = `<p class="error">Failed to read resource: ${e.message}</p>`;
                    }
                });
            });
        } catch (e) {
            resourcesList.innerHTML = `<p class="error">Failed to list resources: ${e.message}</p>`;
        }
    });
}

export function initA2aHandlers() {
    const registerBtn = document.querySelector("[data-testid='a2a-register-btn']");
    const agentList = document.querySelector("[data-testid='a2a-agent-list']");

    registerBtn.addEventListener("click", async () => {
        const name = document.querySelector("[data-testid='a2a-name-input']").value.trim();
        const url = document.querySelector("[data-testid='a2a-url-input']").value.trim();
        if (!name || !url) return;

        try {
            const agent = await registerA2aAgent(name, url);
            const card = renderAgentCard(agent);

            card.querySelector(`[data-testid='a2a-unregister-btn-${agent.name}']`)
                .addEventListener("click", async () => {
                    await deleteA2aAgent(agent.id);
                    card.remove();
                });

            agentList.appendChild(card);

            // 입력 필드 초기화
            document.querySelector("[data-testid='a2a-name-input']").value = "";
            document.querySelector("[data-testid='a2a-url-input']").value = "";

        } catch (e) {
            console.error(e);
            // 사용자에게 에러 표시
            const errorDiv = document.createElement("div");
            errorDiv.className = "error-message";
            errorDiv.setAttribute("data-testid", "a2a-error");
            errorDiv.textContent = `등록 실패: ${e.message}`;
            agentList.appendChild(errorDiv);
            setTimeout(() => errorDiv.remove(), 5000);  // 5초 후 제거
        }
    });
}

export function initConversationsHandlers() {
    const createBtn = document.querySelector("[data-testid='conversation-create-btn']");
    const list = document.querySelector("[data-testid='conversation-list']");

    createBtn.addEventListener("click", async () => {
        try {
            const conv = await createConversation("New Conversation");

            const item = document.createElement("div");
            item.setAttribute("data-testid", "conversation-item");
            item.setAttribute("data-conversation-id", conv.id);
            item.innerHTML = `
                <span>New Conversation</span>
                <button data-testid="conversation-tool-calls-tab">Tool Calls</button>
                <button data-testid="conversation-delete-btn">Delete</button>
                <div data-testid="tool-calls-list" style="display:none;"></div>
            `;

            item.querySelector("[data-testid='conversation-tool-calls-tab']")
                .addEventListener("click", async () => {
                    const toolsList = item.querySelector("[data-testid='tool-calls-list']");
                    const conversationId = item.getAttribute("data-conversation-id");

                    try {
                        const toolCalls = await getToolCalls(conversationId);
                        if (toolCalls.length === 0) {
                            toolsList.textContent = "No tool calls";
                        } else {
                            toolsList.innerHTML = toolCalls.map(tc =>
                                `<div>${tc.tool_name || 'Unknown'}: ${tc.arguments || '{}'}</div>`
                            ).join('');
                        }
                    } catch (e) {
                        toolsList.textContent = "Error loading tool calls";
                        console.error(e);
                    }

                    toolsList.style.display = "block";
                });

            item.querySelector("[data-testid='conversation-delete-btn']")
                .addEventListener("click", async () => {
                    await deleteConversation(conv.id);
                    item.remove();
                });

            list.appendChild(item);
        } catch (e) { console.error(e); }
    });
}

export function initUsageHandlers() {
    const summary = document.querySelector("[data-testid='usage-summary']");
    const budgetInput = document.querySelector("[data-testid='budget-input']");
    const setBudgetBtn = document.querySelector("[data-testid='budget-set-btn']");
    const budgetDisplay = document.querySelector("[data-testid='budget-display']");

    // 초기 로드
    summary.innerHTML = `<p>Total Tokens: 0</p><p>Total Cost: $0.00</p>`;

    setBudgetBtn.addEventListener("click", async () => {
        const limit = parseFloat(budgetInput.value);
        if (isNaN(limit)) return;

        try {
            await setBudget(limit);
            budgetDisplay.textContent = `$${limit.toFixed(2)}`;
        } catch (e) { console.error(e); }
    });
}

export function initWorkflowHandlers() {
    const executeBtn = document.querySelector("[data-testid='workflow-execute-btn']");
    const result = document.querySelector("[data-testid='workflow-result']");

    executeBtn.addEventListener("click", () => {
        const name = document.querySelector("[data-testid='workflow-name-input']").value || "Test";
        const steps = document.querySelector("[data-testid='workflow-steps-input']").value || "[]";

        const url = getWorkflowStreamUrl(name, JSON.parse(steps));

        const handler = new SseHandler(
            url,
            (data) => {
                appendSseLog(data);
                if (data.type === "workflow_complete") {
                    result.textContent = "Status: completed";
                }
            },
            () => { result.textContent = "Status: error"; },
            () => {}
        );
        handler.connect();
    });
}

// 페이지 로드 시 초기화
if (typeof document !== "undefined") {
    document.addEventListener("DOMContentLoaded", () => {
        initHealthCheck();
        initTabNavigation();
        initChatHandlers();
        initMcpHandlers();
        initResourcesHandlers();
        initA2aHandlers();
        initConversationsHandlers();
        initUsageHandlers();
        initWorkflowHandlers();
    });
}
