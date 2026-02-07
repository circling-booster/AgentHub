/**
 * TDD Step 5.8: Green Phase
 * Main 모듈 - 초기화 로직
 */

import {
    healthCheck,
    registerMcpServer, getMcpServers, deleteMcpServer, getMcpTools,
    listResources, readResource,
    listPrompts, getPrompt,
    listSamplingRequests, approveSamplingRequest, rejectSamplingRequest,
    listElicitationRequests, respondElicitationRequest,
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

// HITL SSE Connection (Step 6.5a)
let hitlSseConnection = null;
const API_BASE = "http://localhost:8000";

/**
 * Step 6.5: HTML Attribute Escape Utility
 * Escapes HTML for safe use in HTML attributes (like iframe srcdoc)
 */
function escapeHtmlAttribute(html) {
    return html
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

/**
 * Step 6.5a: HITL SSE Events Connection
 * EventSource로 /api/hitl/events에 연결하여 실시간 HITL 알림 수신
 */
export function initHitlSseConnection() {
    const indicator = document.querySelector("[data-testid='hitl-sse-indicator']");
    const statusText = document.getElementById("hitl-sse-status");

    if (!indicator || !statusText) {
        console.error("HITL SSE indicator elements not found");
        return;
    }

    try {
        // EventSource로 SSE 연결
        hitlSseConnection = new EventSource(`${API_BASE}/api/hitl/events`);

        // 연결 성공
        hitlSseConnection.addEventListener("open", () => {
            console.log("HITL SSE connected");
            indicator.setAttribute("data-status", "connected");
            statusText.textContent = "HITL SSE: Connected";
        });

        // sampling_request 이벤트 수신
        hitlSseConnection.addEventListener("sampling_request", (event) => {
            console.log("Received sampling_request event:", event.data);
            const data = JSON.parse(event.data);

            // Sampling 탭이 활성화되어 있으면 자동 갱신
            const samplingTab = document.getElementById("sampling-tab");
            if (samplingTab && samplingTab.classList.contains("active")) {
                console.log("Auto-refreshing sampling requests...");
                // loadSamplingRequests는 initSamplingHandlers에서 정의됨
                // 직접 호출하기 위해 버튼 클릭 시뮬레이션
                const refreshBtn = document.querySelector("[data-testid='sampling-refresh-btn']");
                if (refreshBtn) {
                    refreshBtn.click();
                }
            }
        });

        // elicitation_request 이벤트 수신
        hitlSseConnection.addEventListener("elicitation_request", (event) => {
            console.log("Received elicitation_request event:", event.data);
            const data = JSON.parse(event.data);

            // Elicitation 탭이 활성화되어 있으면 자동 갱신
            const elicitationTab = document.getElementById("elicitation-tab");
            if (elicitationTab && elicitationTab.classList.contains("active")) {
                console.log("Auto-refreshing elicitation requests...");
                const refreshBtn = document.querySelector("[data-testid='elicitation-refresh-btn']");
                if (refreshBtn) {
                    refreshBtn.click();
                }
            }
        });

        // 에러 처리
        hitlSseConnection.addEventListener("error", (error) => {
            console.error("HITL SSE error:", error);
            indicator.setAttribute("data-status", "error");
            statusText.textContent = "HITL SSE: Error";

            // 자동 재연결 (3초 후)
            setTimeout(() => {
                if (hitlSseConnection) {
                    hitlSseConnection.close();
                }
                console.log("Attempting to reconnect HITL SSE...");
                initHitlSseConnection();
            }, 3000);
        });

    } catch (error) {
        console.error("Failed to initialize HITL SSE:", error);
        indicator.setAttribute("data-status", "error");
        statusText.textContent = "HITL SSE: Failed";
    }
}

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

                        // Step 6.5: MCP Apps Raw Response (iframe sandbox for text/html)
                        if (content.mime_type === 'text/html' && content.text) {
                            // MCP Apps - iframe sandbox 표시
                            resourceContent.innerHTML = `
                                <h3>Resource: ${uri}</h3>
                                <p><strong>MIME Type:</strong> ${content.mime_type}</p>
                                <p><strong>MCP App (Sandboxed):</strong></p>
                                <iframe sandbox="allow-scripts" srcdoc="${escapeHtmlAttribute(content.text)}" style="width: 100%; height: 400px; border: 1px solid #ccc;"></iframe>
                            `;
                        } else {
                            // 일반 리소스 - 텍스트 표시
                            resourceContent.innerHTML = `
                                <h3>Resource: ${uri}</h3>
                                <p><strong>MIME Type:</strong> ${content.mime_type || 'unknown'}</p>
                                ${content.text ? `<pre>${content.text}</pre>` : ''}
                                ${content.blob ? `<p>Binary data (Base64): ${content.blob.substring(0, 50)}...</p>` : ''}
                            `;
                        }
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

export function initPromptsHandlers() {
    const endpointSelect = document.querySelector("[data-testid='prompts-endpoint-select']");
    const listBtn = document.querySelector("[data-testid='prompts-list-btn']");
    const promptsList = document.querySelector("[data-testid='prompts-list']");
    const promptContent = document.querySelector("[data-testid='prompt-content']");

    // Populate endpoint select when tab is activated
    const promptsTab = document.querySelector("[data-testid='tab-prompts']");
    promptsTab.addEventListener("click", async () => {
        try {
            const servers = await getMcpServers();
            endpointSelect.innerHTML = servers.map(s =>
                `<option value="${s.id}">${s.name}</option>`
            ).join('');
        } catch (e) {
            console.error("Failed to load endpoints:", e);
        }
    });

    // List prompts button handler
    listBtn.addEventListener("click", async () => {
        const endpointId = endpointSelect.value;
        if (!endpointId) return;

        try {
            const data = await listPrompts(endpointId);
            promptsList.innerHTML = data.prompts.map(p => {
                const argInputs = p.arguments.map(arg => `
                    <input type="text"
                           data-arg="${arg.name}"
                           placeholder="${arg.name}${arg.required ? ' (required)' : ''}"
                           ${arg.required ? 'required' : ''} />
                `).join('');

                return `
                    <div class="prompt-card" data-name="${p.name}">
                        <h4>${p.name}</h4>
                        <p>${p.description || 'No description'}</p>
                        ${argInputs ? `<div class="prompt-arguments">${argInputs}</div>` : ''}
                        <button data-testid="prompt-get-btn" data-name="${p.name}">Get Prompt</button>
                    </div>
                `;
            }).join('');

            // Add click handlers for get buttons
            promptsList.querySelectorAll('[data-testid="prompt-get-btn"]').forEach(btn => {
                btn.addEventListener("click", async (e) => {
                    const name = e.target.getAttribute("data-name");
                    const card = e.target.closest(".prompt-card");

                    // Collect arguments from input fields
                    const argInputs = card.querySelectorAll('input[data-arg]');
                    const args = {};
                    argInputs.forEach(input => {
                        const argName = input.getAttribute("data-arg");
                        const value = input.value.trim();
                        if (value) {
                            args[argName] = value;
                        }
                    });

                    try {
                        const result = await getPrompt(endpointId, name, args);
                        promptContent.innerHTML = `
                            <h3>Prompt: ${name}</h3>
                            <p><strong>Description:</strong> ${result.description || 'N/A'}</p>
                            <h4>Messages:</h4>
                            ${result.messages.map(msg => `
                                <div class="prompt-message">
                                    <strong>${msg.role}:</strong>
                                    <pre>${JSON.stringify(msg.content, null, 2)}</pre>
                                </div>
                            `).join('')}
                        `;
                    } catch (e) {
                        promptContent.innerHTML = `<p class="error">Failed to get prompt: ${e.message}</p>`;
                    }
                });
            });
        } catch (e) {
            promptsList.innerHTML = `<p class="error">Failed to list prompts: ${e.message}</p>`;
        }
    });
}

export function initSamplingHandlers() {
    const refreshBtn = document.querySelector("[data-testid='sampling-refresh-btn']");
    const requestsContainer = document.querySelector("[data-testid='sampling-requests']");

    // Load sampling requests
    async function loadSamplingRequests() {
        try {
            const data = await listSamplingRequests();
            if (data.requests.length === 0) {
                requestsContainer.innerHTML = '<p class="info">No pending sampling requests</p>';
                return;
            }

            requestsContainer.innerHTML = data.requests.map(req => `
                <div class="sampling-request-card" data-request-id="${req.id}">
                    <h4>Request ID: ${req.id}</h4>
                    <p><strong>Endpoint:</strong> ${req.endpoint_id}</p>
                    <p><strong>Status:</strong> ${req.status}</p>
                    <p><strong>Max Tokens:</strong> ${req.max_tokens}</p>
                    <details>
                        <summary>Messages</summary>
                        <pre>${JSON.stringify(req.messages, null, 2)}</pre>
                    </details>
                    ${req.system_prompt ? `<p><strong>System:</strong> ${req.system_prompt}</p>` : ''}
                    <div class="button-group">
                        <button class="approve-btn" data-testid="sampling-approve-btn" data-request-id="${req.id}">Approve</button>
                        <button class="reject-btn" data-testid="sampling-reject-btn" data-request-id="${req.id}">Reject</button>
                    </div>
                    <div class="sampling-result" data-testid="sampling-result-${req.id}"></div>
                </div>
            `).join('');

            // Add click handlers for approve/reject buttons
            requestsContainer.querySelectorAll('.approve-btn').forEach(btn => {
                btn.addEventListener("click", async (e) => {
                    const requestId = e.target.getAttribute("data-request-id");
                    const resultDiv = requestsContainer.querySelector(`[data-testid="sampling-result-${requestId}"]`);

                    try {
                        btn.disabled = true;
                        btn.textContent = "Approving...";
                        const result = await approveSamplingRequest(requestId);
                        resultDiv.innerHTML = `
                            <h5>✓ Approved (LLM Result):</h5>
                            <pre>${JSON.stringify(result.result, null, 2)}</pre>
                        `;
                        resultDiv.style.color = 'green';
                        setTimeout(() => loadSamplingRequests(), 2000);
                    } catch (e) {
                        resultDiv.innerHTML = `<p class="error">Failed to approve: ${e.message}</p>`;
                    }
                });
            });

            requestsContainer.querySelectorAll('.reject-btn').forEach(btn => {
                btn.addEventListener("click", async (e) => {
                    const requestId = e.target.getAttribute("data-request-id");
                    const resultDiv = requestsContainer.querySelector(`[data-testid="sampling-result-${requestId}"]`);
                    const reason = prompt("Rejection reason (optional):");

                    try {
                        btn.disabled = true;
                        btn.textContent = "Rejecting...";
                        await rejectSamplingRequest(requestId, reason || "");
                        resultDiv.innerHTML = '<p style="color: red;">✗ Rejected</p>';
                        setTimeout(() => loadSamplingRequests(), 2000);
                    } catch (e) {
                        resultDiv.innerHTML = `<p class="error">Failed to reject: ${e.message}</p>`;
                    }
                });
            });
        } catch (e) {
            requestsContainer.innerHTML = `<p class="error">Failed to load sampling requests: ${e.message}</p>`;
        }
    }

    // Refresh button handler
    refreshBtn.addEventListener("click", loadSamplingRequests);

    // Load on tab activation
    const samplingTab = document.querySelector("[data-testid='tab-sampling']");
    samplingTab.addEventListener("click", loadSamplingRequests);
}

export function initElicitationHandlers() {
    const refreshBtn = document.querySelector("[data-testid='elicitation-refresh-btn']");
    const requestsContainer = document.querySelector("[data-testid='elicitation-requests']");

    // Load elicitation requests
    async function loadElicitationRequests() {
        try {
            const data = await listElicitationRequests();
            if (data.requests.length === 0) {
                requestsContainer.innerHTML = '<p class="info">No pending elicitation requests</p>';
                return;
            }

            requestsContainer.innerHTML = data.requests.map(req => {
                const schemaFields = Object.keys(req.requested_schema.properties || {});
                const formInputs = schemaFields.map(field => {
                    const fieldSchema = req.requested_schema.properties[field];
                    const isRequired = (req.requested_schema.required || []).includes(field);
                    return `
                        <div class="form-field">
                            <label>${field}${isRequired ? ' *' : ''}:</label>
                            <input type="text"
                                   data-field="${field}"
                                   placeholder="${fieldSchema.description || field}"
                                   ${isRequired ? 'required' : ''} />
                        </div>
                    `;
                }).join('');

                return `
                    <div class="elicitation-request-card" data-request-id="${req.id}">
                        <h4>Request ID: ${req.id}</h4>
                        <p><strong>Endpoint:</strong> ${req.endpoint_id}</p>
                        <p><strong>Message:</strong> ${req.message}</p>
                        <p><strong>Status:</strong> ${req.status}</p>
                        <details>
                            <summary>Requested Schema</summary>
                            <pre>${JSON.stringify(req.requested_schema, null, 2)}</pre>
                        </details>
                        <div class="elicitation-form">
                            ${formInputs}
                        </div>
                        <div class="button-group">
                            <button class="accept-btn" data-testid="elicitation-accept-btn" data-request-id="${req.id}">Accept</button>
                            <button class="decline-btn" data-testid="elicitation-decline-btn" data-request-id="${req.id}">Decline</button>
                            <button class="cancel-btn" data-testid="elicitation-cancel-btn" data-request-id="${req.id}">Cancel</button>
                        </div>
                        <div class="elicitation-result" data-testid="elicitation-result-${req.id}"></div>
                    </div>
                `;
            }).join('');

            // Add click handlers for accept/decline/cancel buttons
            requestsContainer.querySelectorAll('.accept-btn').forEach(btn => {
                btn.addEventListener("click", async (e) => {
                    const requestId = e.target.getAttribute("data-request-id");
                    const card = requestsContainer.querySelector(`[data-request-id="${requestId}"]`);
                    const resultDiv = requestsContainer.querySelector(`[data-testid="elicitation-result-${requestId}"]`);

                    // Collect form data
                    const inputs = card.querySelectorAll('.elicitation-form input[data-field]');
                    const content = {};
                    inputs.forEach(input => {
                        const field = input.getAttribute("data-field");
                        const value = input.value.trim();
                        if (value) {
                            content[field] = value;
                        }
                    });

                    try {
                        btn.disabled = true;
                        btn.textContent = "Accepting...";
                        await respondElicitationRequest(requestId, "accept", content);
                        resultDiv.innerHTML = '<p style="color: green;">✓ Accepted</p>';
                        setTimeout(() => loadElicitationRequests(), 2000);
                    } catch (e) {
                        resultDiv.innerHTML = `<p class="error">Failed to accept: ${e.message}</p>`;
                        btn.disabled = false;
                        btn.textContent = "Accept";
                    }
                });
            });

            requestsContainer.querySelectorAll('.decline-btn').forEach(btn => {
                btn.addEventListener("click", async (e) => {
                    const requestId = e.target.getAttribute("data-request-id");
                    const resultDiv = requestsContainer.querySelector(`[data-testid="elicitation-result-${requestId}"]`);

                    try {
                        btn.disabled = true;
                        btn.textContent = "Declining...";
                        await respondElicitationRequest(requestId, "decline");
                        resultDiv.innerHTML = '<p style="color: orange;">✗ Declined</p>';
                        setTimeout(() => loadElicitationRequests(), 2000);
                    } catch (e) {
                        resultDiv.innerHTML = `<p class="error">Failed to decline: ${e.message}</p>`;
                        btn.disabled = false;
                        btn.textContent = "Decline";
                    }
                });
            });

            requestsContainer.querySelectorAll('.cancel-btn').forEach(btn => {
                btn.addEventListener("click", async (e) => {
                    const requestId = e.target.getAttribute("data-request-id");
                    const resultDiv = requestsContainer.querySelector(`[data-testid="elicitation-result-${requestId}"]`);

                    try {
                        btn.disabled = true;
                        btn.textContent = "Cancelling...";
                        await respondElicitationRequest(requestId, "cancel");
                        resultDiv.innerHTML = '<p style="color: gray;">⊗ Cancelled</p>';
                        setTimeout(() => loadElicitationRequests(), 2000);
                    } catch (e) {
                        resultDiv.innerHTML = `<p class="error">Failed to cancel: ${e.message}</p>`;
                        btn.disabled = false;
                        btn.textContent = "Cancel";
                    }
                });
            });
        } catch (e) {
            requestsContainer.innerHTML = `<p class="error">Failed to load elicitation requests: ${e.message}</p>`;
        }
    }

    // Refresh button handler
    refreshBtn.addEventListener("click", loadElicitationRequests);

    // Load on tab activation
    const elicitationTab = document.querySelector("[data-testid='tab-elicitation']");
    elicitationTab.addEventListener("click", loadElicitationRequests);
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
        initPromptsHandlers();
        initSamplingHandlers();
        initElicitationHandlers();
        initA2aHandlers();
        initConversationsHandlers();
        initUsageHandlers();
        initWorkflowHandlers();
        initHitlSseConnection();  // Step 6.5a: HITL SSE Events
    });
}
