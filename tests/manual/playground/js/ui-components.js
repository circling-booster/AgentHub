/**
 * TDD Step 5.9: Refactor Phase
 * UI Components 모듈 - 카드 생성 공통화
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
        logEl.textContent += JSON.stringify(event) + "\n";
        logEl.scrollTop = logEl.scrollHeight;
    }
}

/**
 * Common card creation helper
 */
function createCard(type, id) {
    const cardEl = document.createElement("div");
    cardEl.className = "card";
    cardEl.setAttribute("data-testid", `${type}-${id}`);
    return cardEl;
}

export function renderServerCard(server) {
    const cardEl = createCard("mcp-server", server.name);
    cardEl.innerHTML = `
        <h3>${server.name}</h3>
        <p>${server.url}</p>
        <button data-testid="mcp-tools-btn-${server.name}">Tools</button>
        <button data-testid="mcp-unregister-btn-${server.name}">Unregister</button>
    `;
    return cardEl;
}

export function renderAgentCard(agent) {
    const cardEl = createCard("a2a-agent", agent.name);
    cardEl.innerHTML = `
        <h3>${agent.name}</h3>
        <p>${agent.url}</p>
        <button data-testid="a2a-unregister-btn-${agent.name}">Unregister</button>
    `;
    return cardEl;
}
