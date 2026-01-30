---
name: agenthub-extension
description: Chrome Extension development with WXT framework, Manifest V3, Offscreen Document patterns, and secure localhost API integration. Use when (1) developing WXT-based Chrome extensions, (2) implementing Offscreen Document for long-running tasks (SSE streaming, LLM requests), (3) securing localhost API communication with Token Handshake pattern, (4) working with Service Worker lifecycle and message routing, (5) implementing Sidepanel or Popup UI with server communication. Specifically designed for AgentHub's architecture with localhost API server and Extension client security requirements.
---

# AgentHub Extension Development

Expert Chrome Extension development for AgentHub project using WXT framework, Manifest V3, and secure localhost API patterns.

## Core Architecture

AgentHub Extension connects to a localhost API server (`http://localhost:8000`) with these components:

```
Extension (Chrome)
├── Background Service Worker (message routing, health checks)
├── Offscreen Document (SSE streaming, long-running API calls)
├── Sidepanel UI (chat interface, user controls)
└── Content Scripts (page interaction - optional)
     ↓ HTTP + SSE
AgentHub API Server (localhost:8000)
```

## Quick Start Workflows

### 1. Initialize WXT Project

```bash
# From extension/ directory
npm create wxt@latest
# Select: TypeScript, React (or Vue/Svelte)

# Install dependencies
npm install

# Start dev mode (HMR enabled)
npm run dev
```

### 2. Configure Manifest Permissions

Edit `wxt.config.ts`:

```typescript
import { defineConfig } from 'wxt';

export default defineConfig({
  modules: ['@wxt-dev/module-react'],
  manifest: {
    name: 'AgentHub',
    description: 'MCP + A2A 통합 AI Agent 인터페이스',
    permissions: [
      'activeTab',
      'storage',
      'sidePanel',
      'offscreen',      // Offscreen Document (Chrome 109+)
      'alarms',         // Health Check scheduling
    ],
    host_permissions: [
      'http://localhost:8000/*',
      'http://127.0.0.1:8000/*',
    ],
  },
});
```

### 3. Implement Token Handshake Security

**Why:** Localhost APIs are vulnerable to Drive-by RCE attacks from malicious websites.

**Pattern:** Server generates a one-time token at startup, Extension exchanges token on installation.

See [references/token-handshake.md](references/token-handshake.md) for complete implementation.

**Quick implementation:**

```typescript
// background.ts
let extensionToken: string | null = null;

async function initializeAuth(): Promise<boolean> {
  const response = await fetch('http://localhost:8000/auth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ extension_id: chrome.runtime.id }),
  });

  if (response.ok) {
    const { token } = await response.json();
    extensionToken = token;
    await chrome.storage.session.set({ extensionToken: token });
    return true;
  }
  return false;
}

// Auto-run on startup
chrome.runtime.onStartup.addListener(initializeAuth);
```

### 4. Create Offscreen Document for SSE Streaming

**Why:** Service Worker has 30-second timeout, LLM responses take longer.

**Solution:** Offscreen Document runs independently of Service Worker lifecycle.

See [references/offscreen-document.md](references/offscreen-document.md) for detailed patterns.

**File structure:**

```
entrypoints/
├── offscreen/
│   ├── index.html
│   └── main.ts       # SSE streaming handler
├── background.ts     # Offscreen lifecycle manager
└── sidepanel/
    └── main.tsx      # UI that triggers streaming
```

**Offscreen Document template:** See [assets/templates/offscreen/](assets/templates/offscreen/)

### 5. Implement SSE POST Streaming

**Challenge:** EventSource only supports GET, AgentHub uses POST.

**Solution:** fetch + ReadableStream

See [references/sse-streaming.md](references/sse-streaming.md) for complete implementation.

**Quick pattern:**

```typescript
// lib/sse.ts
export async function streamChat(
  conversationId: string,
  message: string,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch('http://localhost:8000/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Extension-Token': await getExtensionToken(),
    },
    body: JSON.stringify({ conversation_id: conversationId, message }),
    signal,
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const event = JSON.parse(line.slice(6));
        onEvent(event);
      }
    }
  }
}
```

## WXT Framework Patterns

### Entrypoints Auto-Detection

WXT automatically detects entrypoints from directory structure:

```
entrypoints/
├── background.ts      → Service Worker
├── popup/
│   └── index.html     → Popup (action)
├── sidepanel/
│   └── index.html     → Side Panel
├── offscreen/
│   └── index.html     → Offscreen Document
└── content.ts         → Content Script
```

### Development with HMR

```bash
# Dev mode (auto-reload on changes)
npm run dev

# Load unpacked extension
chrome://extensions/ → Enable Developer Mode → Load unpacked → .output/chrome-mv3
```

### Building for Production

```bash
# Build
npm run build

# Output: .output/chrome-mv3.zip (ready for Chrome Web Store)
```

## Security Checklist

- [ ] Token Handshake implemented (server + extension)
- [ ] `chrome.storage.session` used (not `local` - tokens cleared on browser close)
- [ ] `X-Extension-Token` header on all `/api/*` requests
- [ ] CORS configured: `chrome-extension://<EXTENSION_ID>`
- [ ] No token logging to console
- [ ] Input validation on all user input
- [ ] No `innerHTML` with external data (XSS prevention)

## Common Issues & Solutions

### Service Worker Dies After 30 Seconds

**Solution:** Use Offscreen Document for long-running operations.

```typescript
// background.ts
async function ensureOffscreenDocument() {
  const existingContexts = await chrome.runtime.getContexts({
    contextTypes: [chrome.runtime.ContextType.OFFSCREEN_DOCUMENT],
  });

  if (existingContexts.length === 0) {
    await chrome.offscreen.createDocument({
      url: 'offscreen/index.html',
      reasons: [chrome.offscreen.Reason.WORKERS],
      justification: 'Handle long-running LLM API requests',
    });
  }
}
```

### Messages Not Passing Between Scripts

**Fix:** Return `true` for async `sendResponse`:

```typescript
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  handleMessageAsync(message).then(sendResponse);
  return true; // Keep channel open for async
});
```

### SSE Connection Drops

**Cause:** Service Worker termination.

**Solution:** Run SSE in Offscreen Document, route events via messages.

### Extension Not Connecting to Server

**Check:**
1. Server running on `localhost:8000`
2. Token exchange successful (check `chrome.storage.session`)
3. CORS headers correct (`chrome-extension://<ID>`)
4. `host_permissions` in manifest

## References

- [WXT Framework Documentation](https://wxt.dev/)
- [Chrome Offscreen Documents API](https://developer.chrome.com/docs/extensions/reference/api/offscreen)
- [Manifest V3 Migration Guide](https://developer.chrome.com/docs/extensions/migrating/)

## Bundled Resources

### references/

- **wxt-patterns.md** - WXT entrypoint patterns and configuration
- **offscreen-document.md** - Detailed Offscreen Document lifecycle and patterns
- **token-handshake.md** - Complete Token Handshake security implementation
- **sse-streaming.md** - SSE POST streaming with fetch ReadableStream
- **manifest-v3-reference.md** - Manifest V3 permissions and API reference

### assets/templates/

- **offscreen/** - Offscreen Document HTML/TS template
- **background/** - Background Service Worker template
- **sidepanel/** - Sidepanel UI template (React)

### scripts/

- **check_extension_security.py** - Security vulnerability scanner (XSS, token leaks, CSP violations)
