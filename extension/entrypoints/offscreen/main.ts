/**
 * Offscreen Document - SSE Streaming Handler
 *
 * Responsibilities:
 * - Receive STREAM_CHAT messages from Background
 * - Execute long-running SSE streaming (bypasses Service Worker 30s timeout)
 * - Forward SSE events to Background → UI
 * - Handle stream cancellation via CANCEL_STREAM
 */

import { MessageType } from '../../lib/messaging';
import type { ExtensionMessage } from '../../lib/messaging';
import { handleStreamChat, handleCancelStream } from '../../lib/offscreen-handlers';

// ==================== Message Handler ====================

browser.runtime.onMessage.addListener((
  message: ExtensionMessage,
  _sender,
  sendResponse
) => {
  // Handle STREAM_CHAT from Background
  if (message.type === MessageType.STREAM_CHAT) {
    handleStreamChat(message.payload)
      .then(() => sendResponse({ received: true }))
      .catch((error) => {
        console.error('[Offscreen] Stream error:', error);
        sendResponse({ error: error.message });
      });
    return true; // Keep channel open for async
  }

  // Handle CANCEL_STREAM from Background
  if (message.type === MessageType.CANCEL_STREAM) {
    const cancelled = handleCancelStream(message.requestId);
    sendResponse({ cancelled });
    return false;
  }

  return false;
});

console.log('[Offscreen] Document loaded and ready');
