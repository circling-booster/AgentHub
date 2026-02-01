/**
 * Offscreen Document handler functions
 *
 * Separated for testability (unit tests can import and test these directly)
 */

import { streamChat, StreamEvent } from './sse';
import { MessageType } from './messaging';
import type { ExtensionMessage } from './messaging';
import type { PageContext } from './types';

interface StreamChatPayload {
  conversationId: string | null;
  message: string;
  requestId: string;
  token: string;
  page_context?: PageContext;
}

// Active stream tracking
const activeStreams = new Map<string, AbortController>();

/**
 * Handle STREAM_CHAT message from Background
 */
export async function handleStreamChat(payload: StreamChatPayload): Promise<void> {
  const { conversationId, message, requestId, token, page_context } = payload;

  // Create AbortController for this stream
  const controller = new AbortController();
  activeStreams.set(requestId, controller);

  try {
    await streamChat(
      conversationId,
      message,
      // Forward each SSE event to Background
      (event: StreamEvent) => {
        browser.runtime.sendMessage({
          type: MessageType.STREAM_CHAT_EVENT,
          requestId,
          event,
        } as ExtensionMessage);
      },
      controller.signal,
      token,
      page_context,
    );

    // Stream completed successfully
    await browser.runtime.sendMessage({
      type: MessageType.STREAM_CHAT_DONE,
      requestId,
    } as ExtensionMessage);
  } catch (error) {
    // Stream error
    await browser.runtime.sendMessage({
      type: MessageType.STREAM_CHAT_ERROR,
      requestId,
      error: error instanceof Error ? error.message : 'Unknown error',
    } as ExtensionMessage);
  } finally {
    // Cleanup
    activeStreams.delete(requestId);
  }
}

/**
 * Handle CANCEL_STREAM message from Background
 */
export function handleCancelStream(requestId: string): boolean {
  const controller = activeStreams.get(requestId);
  if (controller) {
    controller.abort();
    activeStreams.delete(requestId);
    return true;
  }
  return false;
}

/**
 * Get count of active streams (for testing)
 */
export function getActiveStreamCount(): number {
  return activeStreams.size;
}

/**
 * Clear all active streams (for testing cleanup)
 */
export function clearActiveStreams(): void {
  activeStreams.clear();
}
