# SSE POST Streaming with fetch ReadableStream

Complete guide for implementing Server-Sent Events (SSE) with POST requests in Chrome Extensions.

## Problem: EventSource Limitations

Standard `EventSource` API only supports GET requests:

```typescript
// ❌ EventSource cannot send POST with body
const eventSource = new EventSource('http://localhost:8000/api/chat/stream');
// No way to send { conversation_id, message }
```

**AgentHub Requirement:** POST `/api/chat/stream` with JSON body.

## Solution: fetch + ReadableStream

Use `fetch()` with `text/event-stream` and manually parse the stream.

### Complete Implementation

```typescript
// lib/sse.ts

const API_BASE = 'http://localhost:8000/api';

export interface StreamEvent {
  type: 'text' | 'tool_call' | 'tool_result' | 'done' | 'error';
  content?: string;
  name?: string;
  arguments?: Record<string, unknown>;
  result?: unknown;
  message?: string;
}

export async function streamChat(
  conversationId: string,
  message: string,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  // Get authentication token
  const token = await getExtensionToken();

  if (!token) {
    throw new Error('Not authenticated');
  }

  // Send POST request
  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
      'X-Extension-Token': token,
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      message: message,
    }),
    signal, // Support abort
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  // Get ReadableStream reader
  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('Response body is not readable');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      // Decode chunk
      buffer += decoder.decode(value, { stream: true });

      // Split by newlines
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line

      // Process complete lines
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6); // Remove "data: " prefix

          if (data) {
            try {
              const event: StreamEvent = JSON.parse(data);
              onEvent(event);

              // Stop on done or error
              if (event.type === 'done' || event.type === 'error') {
                return;
              }
            } catch (e) {
              console.error('Failed to parse SSE event:', e);
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

async function getExtensionToken(): Promise<string | null> {
  const stored = await chrome.storage.session.get('extensionToken');
  return stored.extensionToken || null;
}
```

## Server-Side Implementation (FastAPI)

### SSE Streaming Endpoint

```python
# src/adapters/inbound/http/routes/chat.py
import asyncio
import json
import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("/stream")
async def chat_stream(
    request: Request,
    body: ChatRequest,
    orchestrator: OrchestratorService = Depends(...),
):
    """
    SSE streaming endpoint (POST)

    Event format:
    - data: {"type": "text", "content": "..."}\n\n
    - data: {"type": "tool_call", "name": "...", "arguments": {...}}\n\n
    - data: {"type": "done"}\n\n
    - data: {"type": "error", "message": "..."}\n\n
    """
    async def generate():
        try:
            async for chunk in orchestrator.chat(
                body.conversation_id,
                body.message,
            ):
                # Check client disconnection (Zombie Task prevention)
                if await request.is_disconnected():
                    logger.info(f"Client disconnected, stopping stream for {body.conversation_id}")
                    break

                event_data = json.dumps({"type": "text", "content": chunk})
                yield f"data: {event_data}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except asyncio.CancelledError:
            logger.info(f"Stream cancelled for {body.conversation_id}")
            raise  # Re-raise CancelledError

        except Exception as e:
            logger.error(f"Stream error: {e}")
            error_data = json.dumps({"type": "error", "message": str(e)})
            yield f"data: {error_data}\n\n"

        finally:
            logger.debug(f"Stream cleanup for {body.conversation_id}")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
```

## Usage Patterns

### Pattern 1: Basic Streaming

```typescript
// Simple usage
await streamChat(
  'conv-123',
  'Hello, how are you?',
  (event) => {
    if (event.type === 'text') {
      console.log(event.content);
    } else if (event.type === 'done') {
      console.log('Streaming complete');
    }
  }
);
```

### Pattern 2: With Abort Signal

```typescript
// User can cancel streaming
const controller = new AbortController();

// Show cancel button
document.getElementById('cancel-button').onclick = () => {
  controller.abort();
};

try {
  await streamChat(
    'conv-123',
    'Generate a long essay...',
    (event) => {
      appendToUI(event);
    },
    controller.signal
  );
} catch (error) {
  if (error.name === 'AbortError') {
    console.log('User cancelled streaming');
  }
}
```

### Pattern 3: React Integration

```typescript
// React component
import { useState } from 'react';

function ChatInterface() {
  const [messages, setMessages] = useState<StreamEvent[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [abortController, setAbortController] = useState<AbortController | null>(null);

  const handleSendMessage = async (text: string) => {
    setStreaming(true);
    const controller = new AbortController();
    setAbortController(controller);

    try {
      await streamChat(
        'conv-123',
        text,
        (event) => {
          if (event.type === 'text') {
            setMessages(prev => [...prev, event]);
          }
        },
        controller.signal
      );
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Streaming error:', error);
      }
    } finally {
      setStreaming(false);
      setAbortController(null);
    }
  };

  const handleCancel = () => {
    abortController?.abort();
  };

  return (
    <div>
      <MessageList messages={messages} />
      <ChatInput onSend={handleSendMessage} disabled={streaming} />
      {streaming && <button onClick={handleCancel}>Cancel</button>}
    </div>
  );
}
```

### Pattern 4: Retry on Error

```typescript
async function streamChatWithRetry(
  conversationId: string,
  message: string,
  onEvent: (event: StreamEvent) => void,
  maxRetries: number = 3
): Promise<void> {
  let attempts = 0;

  while (attempts < maxRetries) {
    try {
      await streamChat(conversationId, message, onEvent);
      return; // Success
    } catch (error) {
      attempts++;

      if (attempts >= maxRetries) {
        throw error;
      }

      // Exponential backoff
      const delay = Math.min(1000 * Math.pow(2, attempts), 10000);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
```

## Event Types

### text

```json
{
  "type": "text",
  "content": "This is the LLM response..."
}
```

### tool_call

```json
{
  "type": "tool_call",
  "name": "search_web",
  "arguments": {
    "query": "weather in Seoul"
  }
}
```

### tool_result

```json
{
  "type": "tool_result",
  "name": "search_web",
  "result": {
    "temperature": "15°C",
    "condition": "Sunny"
  }
}
```

### done

```json
{
  "type": "done"
}
```

### error

```json
{
  "type": "error",
  "message": "Network timeout"
}
```

## Error Handling

### Network Errors

```typescript
try {
  await streamChat(convId, message, onEvent);
} catch (error) {
  if (error.name === 'AbortError') {
    // User cancelled
    showNotification('Cancelled by user');
  } else if (error.message.includes('Failed to fetch')) {
    // Server not running
    showError('Server not available. Is AgentHub running?');
  } else {
    // Other errors
    showError(`Error: ${error.message}`);
  }
}
```

### Server-Side Errors

```typescript
await streamChat(convId, message, (event) => {
  if (event.type === 'error') {
    // Server sent error event
    showError(`Server error: ${event.message}`);
  }
});
```

### Connection Timeout

```typescript
const TIMEOUT_MS = 120000; // 2 minutes

const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

try {
  await streamChat(convId, message, onEvent, controller.signal);
} catch (error) {
  if (error.name === 'AbortError') {
    showError('Request timed out');
  }
} finally {
  clearTimeout(timeoutId);
}
```

## Performance Optimization

### Batch Updates

Instead of updating UI for every event, batch updates:

```typescript
let eventBuffer: StreamEvent[] = [];
let updateScheduled = false;

await streamChat(convId, message, (event) => {
  eventBuffer.push(event);

  if (!updateScheduled) {
    updateScheduled = true;
    requestAnimationFrame(() => {
      setMessages(prev => [...prev, ...eventBuffer]);
      eventBuffer = [];
      updateScheduled = false;
    });
  }
});
```

### Debounce Rendering

For very fast streams, debounce rendering:

```typescript
let debounceTimer: NodeJS.Timeout | null = null;

await streamChat(convId, message, (event) => {
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }

  debounceTimer = setTimeout(() => {
    updateUI(event);
  }, 16); // ~60fps
});
```

## Testing

### Manual Test

```typescript
// Test SSE connection in DevTools console
await streamChat(
  'test-conv',
  'Hello',
  (event) => console.log('Event:', event)
);
```

### Server Health Check

```typescript
async function testServerConnection(): Promise<boolean> {
  try {
    const response = await fetch('http://localhost:8000/health');
    return response.ok;
  } catch {
    return false;
  }
}
```

## Common Issues

### Issue 1: No Events Received

**Check:**
1. Server running on `localhost:8000`
2. CORS headers correct
3. Token authentication successful
4. Server sending `data: ` prefixed lines

### Issue 2: Stream Cuts Off

**Cause:** Service Worker terminated.

**Fix:** Run SSE in Offscreen Document (see offscreen-document.md).

### Issue 3: Partial JSON Errors

**Cause:** JSON split across chunks.

**Fix:** Use buffer to accumulate complete lines (already implemented above).

### Issue 4: Memory Leak

**Cause:** Reader not released.

**Fix:** Always call `reader.releaseLock()` in finally block.

## Security Checklist

- [ ] Token included in `X-Extension-Token` header
- [ ] HTTPS in production (localhost HTTP OK for dev)
- [ ] Input validation on message content
- [ ] Rate limiting on server side
- [ ] Abort signal support (prevent zombie requests)
- [ ] No sensitive data logged to console

## References

- [Fetch API - ReadableStream](https://developer.mozilla.org/en-US/docs/Web/API/Streams_API/Using_readable_streams)
- [Server-Sent Events Specification](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [Chrome Extensions Fetch API](https://developer.chrome.com/docs/extensions/reference/api/fetch)
