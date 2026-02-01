# Offscreen Document Template

## Files Structure

```
entrypoints/offscreen/
├── index.html      # Minimal HTML wrapper
└── main.ts         # Message handler and SSE logic
```

## index.html Pattern

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Offscreen Document</title>
</head>
<body>
  <script type="module" src="./main.ts"></script>
</body>
</html>
```

## main.ts Pattern

```typescript
// Message type definitions
interface StreamRequest {
  type: 'STREAM_CHAT';
  payload: {
    conversationId: string;
    message: string;
    requestId: string;
  };
}

// Listen for messages from Background
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'STREAM_CHAT') {
    handleStreamChat(message.payload);
    sendResponse({ received: true });
  }
  return true;
});

// Handle SSE streaming
async function handleStreamChat(payload) {
  try {
    // Import SSE utility
    const { streamChat } = await import('~/lib/sse');

    // Start streaming
    await streamChat(
      payload.conversationId,
      payload.message,
      (event) => {
        // Forward events to Background
        chrome.runtime.sendMessage({
          type: 'STREAM_CHAT_EVENT',
          requestId: payload.requestId,
          event,
        });
      }
    );

    // Notify completion
    chrome.runtime.sendMessage({
      type: 'STREAM_CHAT_DONE',
      requestId: payload.requestId,
    });
  } catch (error) {
    // Notify error
    chrome.runtime.sendMessage({
      type: 'STREAM_CHAT_ERROR',
      requestId: payload.requestId,
      error: error.message,
    });
  }
}
```

See [references/offscreen-document.md](../../../references/offscreen-document.md) for complete patterns.
