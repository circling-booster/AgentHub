/**
 * SSE POST streaming client
 *
 * EventSource only supports GET, so we use fetch + ReadableStream
 * for POST-based SSE streaming.
 */

import { API_BASE } from './constants';
import type { StreamEvent } from './types';

/**
 * Stream chat with POST-based SSE
 *
 * @param conversationId - Conversation ID (null for new conversation)
 * @param message - User message
 * @param onEvent - Callback for each SSE event
 * @param signal - AbortSignal for cancellation
 * @throws Error if HTTP error or network error
 */
export async function streamChat(
  conversationId: string | null,
  message: string,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      message,
    }),
    signal,
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('Response body is not readable');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      // Check abort signal before each read
      if (signal?.aborted) {
        throw new Error('Stream aborted by user');
      }

      const { done, value } = await reader.read();

      if (done) break;

      // Decode chunk and append to buffer
      buffer += decoder.decode(value, { stream: true });

      // Split by newlines
      const lines = buffer.split('\n');

      // Keep last incomplete line in buffer
      buffer = lines.pop() || '';

      // Process complete lines
      for (const line of lines) {
        // Skip empty lines
        if (!line.trim()) continue;

        // Parse SSE data lines
        if (line.startsWith('data: ')) {
          const data = line.slice(6); // Remove 'data: ' prefix
          if (data) {
            try {
              const event: StreamEvent = JSON.parse(data);
              onEvent(event);
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
