# Offscreen Document Patterns

Complete guide for implementing Offscreen Documents in Chrome Extensions to handle long-running tasks that exceed Service Worker timeout.

## Problem: Service Worker 30-Second Timeout

Chrome Service Workers terminate after 30 seconds of inactivity:

```
Service Worker Lifecycle:
Start → Event Handler → 30s idle → TERMINATE
```

**Issues:**
- LLM responses can take 30+ seconds
- SSE streams require persistent connection
- Fetch timeout if response doesn't arrive within 30s
- Long-running operations interrupted

## Solution: Offscreen Document

Offscreen Documents run independently of Service Worker lifecycle:

```
Service Worker (30s timeout)
    ↓ create & message
Offscreen Document (independent lifecycle)
    ↓ SSE stream
Server (long-running response)
```

### Key Characteristics

| Feature | Service Worker | Offscreen Document |
|---------|---------------|-------------------|
| **Lifecycle** | 30s idle timeout | Independent, long-running |
| **DOM Access** | ❌ No | ✅ Yes |
| **Fetch Timeout** | 30s | Unlimited |
| **API Access** | Full Extensions API | Limited (runtime only) |
| **Count** | 1 per extension | 1 per profile |

## Implementation Pattern

### 1. File Structure

```
entrypoints/
├── background.ts      # Service Worker (manages Offscreen)
├── offscreen/
│   ├── index.html     # Offscreen Document HTML
│   └── main.ts        # SSE streaming logic
└── sidepanel/
    └── main.tsx       # UI (triggers streaming)
```

### 2. Offscreen Document HTML

```html
<!-- entrypoints/offscreen/index.html -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>AgentHub Offscreen</title>
</head>
<body>
  <script type="module" src="./main.ts"></script>
</body>
</html>
```

### 3. Offscreen Document Logic

```typescript
// entrypoints/offscreen/main.ts
import { streamChat, StreamEvent } from '../lib/sse';

interface StreamChatRequest {
  type: 'STREAM_CHAT';
  payload: {
    conversationId: string;
    message: string;
    requestId: string;
  };
}

interface StreamChatResponse {
  type: 'STREAM_CHAT_EVENT' | 'STREAM_CHAT_DONE' | 'STREAM_CHAT_ERROR';
  requestId: string;
  event?: StreamEvent;
  error?: string;
}

// Listen for messages from Background
chrome.runtime.onMessage.addListener((
  message: StreamChatRequest,
  sender,
  sendResponse
) => {
  if (message.type === 'STREAM_CHAT') {
    handleStreamChat(message.payload);
    sendResponse({ received: true });
  }
  return true;
});

async function handleStreamChat(payload: {
  conversationId: string;
  message: string;
  requestId: string;
}) {
  const { conversationId, message, requestId } = payload;

  try {
    // SSE streaming (long-running)
    await streamChat(
      conversationId,
      message,
      (event: StreamEvent) => {
        // Forward each event to Background
        chrome.runtime.sendMessage({
          type: 'STREAM_CHAT_EVENT',
          requestId,
          event,
        } as StreamChatResponse);
      }
    );

    // Notify completion
    chrome.runtime.sendMessage({
      type: 'STREAM_CHAT_DONE',
      requestId,
    } as StreamChatResponse);

  } catch (error) {
    // Notify error
    chrome.runtime.sendMessage({
      type: 'STREAM_CHAT_ERROR',
      requestId,
      error: error instanceof Error ? error.message : 'Unknown error',
    } as StreamChatResponse);
  }
}

console.log('[Offscreen] Document loaded and ready');
```

### 4. Background Service Worker

```typescript
// entrypoints/background.ts
const OFFSCREEN_DOCUMENT_PATH = 'offscreen/index.html';

// Active streaming requests tracking
const activeRequests = new Map<string, {
  resolve: (value: void) => void;
  onEvent: (event: any) => void;
}>();

// ==================== Offscreen Lifecycle ====================

async function ensureOffscreenDocument(): Promise<void> {
  // Check if already exists
  const existingContexts = await chrome.runtime.getContexts({
    contextTypes: [chrome.runtime.ContextType.OFFSCREEN_DOCUMENT],
    documentUrls: [chrome.runtime.getURL(OFFSCREEN_DOCUMENT_PATH)],
  });

  if (existingContexts.length > 0) {
    return; // Already exists
  }

  // Create new Offscreen Document
  await chrome.offscreen.createDocument({
    url: OFFSCREEN_DOCUMENT_PATH,
    reasons: [chrome.offscreen.Reason.WORKERS],
    justification: 'Handle long-running LLM API requests that exceed Service Worker timeout',
  });

  console.log('[Background] Offscreen document created');
}

// ==================== Message Routing ====================

// UI → Background → Offscreen
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // UI requests streaming
  if (message.type === 'START_STREAM_CHAT') {
    handleStartStreamChat(message.payload, sender.tab?.id);
    sendResponse({ received: true });
    return true;
  }

  // Offscreen sends events
  if (message.type === 'STREAM_CHAT_EVENT') {
    const request = activeRequests.get(message.requestId);
    if (request) {
      request.onEvent(message.event);
    }
    return false;
  }

  // Offscreen sends done/error
  if (message.type === 'STREAM_CHAT_DONE' || message.type === 'STREAM_CHAT_ERROR') {
    const request = activeRequests.get(message.requestId);
    if (request) {
      request.resolve();
      activeRequests.delete(message.requestId);
    }

    // Forward to UI
    broadcastToUI(message);
    return false;
  }

  return false;
});

async function handleStartStreamChat(
  payload: { conversationId: string; message: string },
  tabId?: number
) {
  const requestId = crypto.randomUUID();

  // Ensure Offscreen Document exists
  await ensureOffscreenDocument();

  // Track request
  activeRequests.set(requestId, {
    resolve: () => {},
    onEvent: (event) => {
      // Forward events to UI
      if (tabId) {
        chrome.tabs.sendMessage(tabId, {
          type: 'STREAM_CHAT_EVENT',
          requestId,
          event,
        });
      }
    },
  });

  // Forward to Offscreen Document
  chrome.runtime.sendMessage({
    type: 'STREAM_CHAT',
    payload: {
      ...payload,
      requestId,
    },
  });
}

function broadcastToUI(message: any) {
  chrome.runtime.sendMessage(message).catch(() => {
    // UI not listening, ignore
  });
}
```

### 5. UI Integration (Sidepanel)

```typescript
// entrypoints/sidepanel/main.tsx
function ChatInterface() {
  const [messages, setMessages] = useState<StreamEvent[]>([]);
  const [streaming, setStreaming] = useState(false);

  const handleSendMessage = async (text: string) => {
    setStreaming(true);

    // Listen for events from Background
    const listener = (message: any) => {
      if (message.type === 'STREAM_CHAT_EVENT') {
        setMessages(prev => [...prev, message.event]);
      } else if (message.type === 'STREAM_CHAT_DONE') {
        setStreaming(false);
        chrome.runtime.onMessage.removeListener(listener);
      } else if (message.type === 'STREAM_CHAT_ERROR') {
        console.error('Streaming error:', message.error);
        setStreaming(false);
        chrome.runtime.onMessage.removeListener(listener);
      }
    };

    chrome.runtime.onMessage.addListener(listener);

    // Send message to Background
    await chrome.runtime.sendMessage({
      type: 'START_STREAM_CHAT',
      payload: {
        conversationId: 'conv-1',
        message: text,
      },
    });
  };

  return (
    <div>
      <MessageList messages={messages} />
      <ChatInput onSend={handleSendMessage} disabled={streaming} />
    </div>
  );
}
```

## Advanced Patterns

### Pattern 1: Retry on Offscreen Termination

```typescript
// background.ts
async function ensureOffscreenDocument(): Promise<void> {
  try {
    const existingContexts = await chrome.runtime.getContexts({
      contextTypes: [chrome.runtime.ContextType.OFFSCREEN_DOCUMENT],
    });

    if (existingContexts.length === 0) {
      await chrome.offscreen.createDocument({
        url: OFFSCREEN_DOCUMENT_PATH,
        reasons: [chrome.offscreen.Reason.WORKERS],
        justification: 'Handle long-running LLM API requests',
      });
    }
  } catch (error) {
    // Offscreen may have been terminated, retry once
    console.warn('[Background] Offscreen creation failed, retrying:', error);
    await new Promise(resolve => setTimeout(resolve, 100));
    await chrome.offscreen.createDocument({
      url: OFFSCREEN_DOCUMENT_PATH,
      reasons: [chrome.offscreen.Reason.WORKERS],
      justification: 'Handle long-running LLM API requests',
    });
  }
}
```

### Pattern 2: Graceful Shutdown

```typescript
// offscreen/main.ts
let activeStream: AbortController | null = null;

window.addEventListener('beforeunload', () => {
  // Abort ongoing streams
  if (activeStream) {
    activeStream.abort();
  }
});

async function handleStreamChat(payload) {
  const controller = new AbortController();
  activeStream = controller;

  try {
    await streamChat(
      payload.conversationId,
      payload.message,
      (event) => {
        chrome.runtime.sendMessage({ type: 'STREAM_CHAT_EVENT', event });
      },
      controller.signal // Pass abort signal
    );
  } finally {
    activeStream = null;
  }
}
```

### Pattern 3: Multiple Concurrent Streams

```typescript
// offscreen/main.ts
const activeStreams = new Map<string, AbortController>();

async function handleStreamChat(payload: { requestId: string; ... }) {
  const controller = new AbortController();
  activeStreams.set(payload.requestId, controller);

  try {
    await streamChat(
      payload.conversationId,
      payload.message,
      (event) => {
        chrome.runtime.sendMessage({
          type: 'STREAM_CHAT_EVENT',
          requestId: payload.requestId,
          event,
        });
      },
      controller.signal
    );
  } finally {
    activeStreams.delete(payload.requestId);
  }
}

// Handle cancellation
chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'CANCEL_STREAM') {
    const controller = activeStreams.get(message.requestId);
    if (controller) {
      controller.abort();
      activeStreams.delete(message.requestId);
    }
  }
});
```

## Limitations & Workarounds

### Limitation 1: Only Runtime API Available

**Problem:** Offscreen Documents can only use `chrome.runtime` API.

**Workaround:** Proxy other API calls through Background Service Worker.

```typescript
// offscreen/main.ts - Need to access chrome.storage
chrome.runtime.sendMessage({
  type: 'STORAGE_GET',
  key: 'settings',
});

// background.ts - Proxy storage access
chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'STORAGE_GET') {
    chrome.storage.local.get(message.key).then(result => {
      // Send back to offscreen
    });
  }
});
```

### Limitation 2: One Document Per Profile

**Problem:** Can't create multiple Offscreen Documents simultaneously.

**Workaround:** Multiplex requests within single Offscreen Document using `requestId`.

```typescript
// Single Offscreen handles multiple requests
const activeRequests = new Map<string, StreamHandler>();

chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'STREAM_CHAT') {
    const { requestId, ...payload } = message.payload;
    handleStreamChat(requestId, payload);
  }
});
```

## Debugging

### Check if Offscreen Document is Running

```typescript
// background.ts
const contexts = await chrome.runtime.getContexts({
  contextTypes: [chrome.runtime.ContextType.OFFSCREEN_DOCUMENT],
});
console.log('Offscreen contexts:', contexts);
```

### View Offscreen Document Console

1. Open `chrome://extensions/`
2. Enable Developer Mode
3. Find your extension
4. Click "Inspect views: offscreen.html"

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Offscreen document already exists" | Trying to create duplicate | Check existence first |
| "Invalid reasons" | Wrong reason type | Use `chrome.offscreen.Reason.WORKERS` |
| "Document not found" | Path incorrect | Use `chrome.runtime.getURL()` |

## Testing Checklist

- [ ] Offscreen Document created on first request
- [ ] Streams complete successfully (>30s responses)
- [ ] Events forwarded from Offscreen → Background → UI
- [ ] Concurrent streams handled correctly
- [ ] Offscreen recreated after termination
- [ ] Graceful shutdown on extension disable
- [ ] Console logs visible in Offscreen inspector

## Performance Considerations

**Memory:** Offscreen Documents consume memory. Close when not needed.

**Best Practice:** Create on-demand, keep alive during streaming, consider closing after idle period.

```typescript
let offscreenIdleTimeout: NodeJS.Timeout | null = null;

async function handleStreamComplete() {
  // Close Offscreen after 5 minutes of inactivity
  if (offscreenIdleTimeout) {
    clearTimeout(offscreenIdleTimeout);
  }

  offscreenIdleTimeout = setTimeout(async () => {
    const contexts = await chrome.runtime.getContexts({
      contextTypes: [chrome.runtime.ContextType.OFFSCREEN_DOCUMENT],
    });

    if (contexts.length > 0) {
      await chrome.offscreen.closeDocument();
      console.log('[Background] Closed idle Offscreen Document');
    }
  }, 5 * 60 * 1000);
}
```
