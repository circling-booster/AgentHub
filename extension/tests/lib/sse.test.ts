import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { streamChat } from '../../lib/sse';
import type { StreamEvent } from '../../lib/types';

describe('SSE Client', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('streamChat', () => {
    it('should parse conversation_created event', async () => {
      // Given: Server returns conversation_created event
      const mockReader = createMockReader([
        'data: {"type":"conversation_created","conversation_id":"conv-123"}\n\n',
      ]);
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        body: { getReader: () => mockReader },
      });

      const events: StreamEvent[] = [];
      const onEvent = (event: StreamEvent) => events.push(event);

      // When: Call streamChat
      await streamChat('conv-123', 'Hello', onEvent);

      // Then: conversation_created event parsed
      expect(events).toHaveLength(1);
      expect(events[0]).toEqual({
        type: 'conversation_created',
        conversation_id: 'conv-123',
      });
    });

    it('should parse text event', async () => {
      // Given: Server returns text event
      const mockReader = createMockReader([
        'data: {"type":"text","content":"Hello World"}\n\n',
      ]);
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        body: { getReader: () => mockReader },
      });

      const events: StreamEvent[] = [];
      const onEvent = (event: StreamEvent) => events.push(event);

      // When: Call streamChat
      await streamChat(null, 'Test', onEvent);

      // Then: text event parsed
      expect(events).toHaveLength(1);
      expect(events[0]).toEqual({
        type: 'text',
        content: 'Hello World',
      });
    });

    it('should parse done event', async () => {
      // Given: Server returns done event
      const mockReader = createMockReader([
        'data: {"type":"text","content":"Response"}\n\n',
        'data: {"type":"done"}\n\n',
      ]);
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        body: { getReader: () => mockReader },
      });

      const events: StreamEvent[] = [];
      const onEvent = (event: StreamEvent) => events.push(event);

      // When: Call streamChat
      await streamChat(null, 'Test', onEvent);

      // Then: Both events parsed
      expect(events).toHaveLength(2);
      expect(events[1]).toEqual({ type: 'done' });
    });

    it('should parse error event', async () => {
      // Given: Server returns error event
      const mockReader = createMockReader([
        'data: {"type":"error","message":"Something went wrong"}\n\n',
      ]);
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        body: { getReader: () => mockReader },
      });

      const events: StreamEvent[] = [];
      const onEvent = (event: StreamEvent) => events.push(event);

      // When: Call streamChat
      await streamChat(null, 'Test', onEvent);

      // Then: error event parsed
      expect(events).toHaveLength(1);
      expect(events[0]).toEqual({
        type: 'error',
        message: 'Something went wrong',
      });
    });

    it('should handle buffer boundaries correctly', async () => {
      // Given: Event split across multiple chunks
      const mockReader = createMockReader([
        'data: {"type":"text",',
        '"content":"Partial"}\n\n',
        'data: {"type":"done"}\n\n',
      ]);
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        body: { getReader: () => mockReader },
      });

      const events: StreamEvent[] = [];
      const onEvent = (event: StreamEvent) => events.push(event);

      // When: Call streamChat
      await streamChat(null, 'Test', onEvent);

      // Then: Both events parsed correctly
      expect(events).toHaveLength(2);
      expect(events[0]).toEqual({
        type: 'text',
        content: 'Partial',
      });
      expect(events[1]).toEqual({ type: 'done' });
    });

    it('should include X-Extension-Token header', async () => {
      // Given: Token in session storage
      const mockReader = createMockReader(['data: {"type":"done"}\n\n']);
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        body: { getReader: () => mockReader },
      });

      // When: Call streamChat
      await streamChat(null, 'Test', () => {});

      // Then: Fetch called with token header
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/chat/stream',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify({
            conversation_id: null,
            message: 'Test',
          }),
        })
      );
    });

    it('should support AbortSignal for cancellation', async () => {
      // Given: Stream with multiple chunks, abort in middle
      const controller = new AbortController();

      // Create reader that will be aborted mid-stream
      let readCount = 0;
      const mockReader = {
        read: vi.fn(async () => {
          readCount++;
          if (readCount === 1) {
            // First read succeeds
            const encoder = new TextEncoder();
            return { done: false, value: encoder.encode('data: {"type":"text","content":"First"}\n\n') };
          }
          // Second read will check abort (controller aborted before this)
          return { done: true, value: undefined };
        }),
        releaseLock: vi.fn(),
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        body: { getReader: () => mockReader },
      });

      const events: StreamEvent[] = [];

      // When: Start stream, then abort after first event
      const streamPromise = streamChat(null, 'Test', (e) => {
        events.push(e);
        // Abort after receiving first event
        controller.abort();
      }, controller.signal);

      // Then: Should throw abort error
      await expect(streamPromise).rejects.toThrow('Stream aborted by user');

      // Verify: First event was received before abort
      expect(events).toHaveLength(1);
      expect(events[0]).toEqual({ type: 'text', content: 'First' });
    });

    it('should throw on HTTP error response', async () => {
      // Given: Server returns 500
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      // When/Then: Should throw
      await expect(streamChat(null, 'Test', () => {})).rejects.toThrow(
        'HTTP 500: Internal Server Error'
      );
    });

    it('should throw on network error', async () => {
      // Given: Network error
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      // When/Then: Should throw
      await expect(streamChat(null, 'Test', () => {})).rejects.toThrow('Network error');
    });

    it('should handle multiple events in single chunk', async () => {
      // Given: Multiple events in one chunk
      const mockReader = createMockReader([
        'data: {"type":"text","content":"First"}\n\ndata: {"type":"text","content":"Second"}\n\n',
      ]);
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        body: { getReader: () => mockReader },
      });

      const events: StreamEvent[] = [];
      const onEvent = (event: StreamEvent) => events.push(event);

      // When: Call streamChat
      await streamChat(null, 'Test', onEvent);

      // Then: Both events parsed
      expect(events).toHaveLength(2);
      expect(events[0]).toEqual({ type: 'text', content: 'First' });
      expect(events[1]).toEqual({ type: 'text', content: 'Second' });
    });

    it('should ignore empty lines', async () => {
      // Given: Stream with empty lines
      const mockReader = createMockReader([
        '\n',
        'data: {"type":"text","content":"Content"}\n\n',
        '\n',
        'data: {"type":"done"}\n\n',
      ]);
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        body: { getReader: () => mockReader },
      });

      const events: StreamEvent[] = [];
      const onEvent = (event: StreamEvent) => events.push(event);

      // When: Call streamChat
      await streamChat(null, 'Test', onEvent);

      // Then: Only data events parsed
      expect(events).toHaveLength(2);
    });
  });
});

// Helper: Create mock ReadableStreamDefaultReader
function createMockReader(chunks: string[]) {
  let index = 0;
  return {
    read: vi.fn(async () => {
      if (index >= chunks.length) {
        return { done: true, value: undefined };
      }
      const chunk = chunks[index++];
      const encoder = new TextEncoder();
      return { done: false, value: encoder.encode(chunk) };
    }),
    releaseLock: vi.fn(),
  };
}
