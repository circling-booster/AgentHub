import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { fakeBrowser } from 'wxt/testing';
import { MessageType } from '../../lib/messaging';
import { handleStreamChat, handleCancelStream, getActiveStreamCount, clearActiveStreams } from '../../lib/offscreen-handlers';
import * as sseModule from '../../lib/sse';

describe('Offscreen Document Handlers', () => {
  beforeEach(() => {
    fakeBrowser.reset();
    global.fetch = vi.fn();
    clearActiveStreams();
  });

  afterEach(() => {
    clearActiveStreams();
  });

  describe('handleStreamChat', () => {
    it('should call streamChat and forward events to Background', async () => {
      // Given: Mock streamChat
      const mockStreamChat = vi.spyOn(sseModule, 'streamChat').mockImplementation(
        async (_conversationId, _message, onEvent, _signal) => {
          // Simulate SSE events
          onEvent({ type: 'text', content: 'Hello' });
          onEvent({ type: 'text', content: ' World' });
        }
      );

      const sendMessage = vi.fn().mockResolvedValue(undefined);
      fakeBrowser.runtime.sendMessage = sendMessage;

      // When: Handle stream chat
      await handleStreamChat({
        conversationId: 'conv-123',
        message: 'Test message',
        requestId: 'req-123',
      });

      // Then: streamChat called with correct parameters
      expect(mockStreamChat).toHaveBeenCalledWith(
        'conv-123',
        'Test message',
        expect.any(Function),
        expect.any(AbortSignal)
      );

      // Events forwarded to Background
      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.STREAM_CHAT_EVENT,
        requestId: 'req-123',
        event: { type: 'text', content: 'Hello' },
      });

      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.STREAM_CHAT_EVENT,
        requestId: 'req-123',
        event: { type: 'text', content: ' World' },
      });

      // Done message sent
      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.STREAM_CHAT_DONE,
        requestId: 'req-123',
      });
    });

    it('should send STREAM_CHAT_DONE when stream completes successfully', async () => {
      // Given: Mock streamChat completes without error
      vi.spyOn(sseModule, 'streamChat').mockResolvedValue(undefined);

      const sendMessage = vi.fn().mockResolvedValue(undefined);
      fakeBrowser.runtime.sendMessage = sendMessage;

      // When: Handle stream chat
      await handleStreamChat({
        conversationId: 'conv-123',
        message: 'Test',
        requestId: 'req-123',
      });

      // Then: DONE message sent
      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.STREAM_CHAT_DONE,
        requestId: 'req-123',
      });
    });

    it('should send STREAM_CHAT_ERROR when stream fails', async () => {
      // Given: streamChat throws error
      vi.spyOn(sseModule, 'streamChat').mockRejectedValue(new Error('Connection failed'));

      const sendMessage = vi.fn().mockResolvedValue(undefined);
      fakeBrowser.runtime.sendMessage = sendMessage;

      // When: Handle stream chat
      await handleStreamChat({
        conversationId: null,
        message: 'Test',
        requestId: 'req-123',
      });

      // Then: ERROR message sent
      expect(sendMessage).toHaveBeenCalledWith({
        type: MessageType.STREAM_CHAT_ERROR,
        requestId: 'req-123',
        error: 'Connection failed',
      });
    });

    it('should cleanup stream from activeStreams after completion', async () => {
      // Given: Mock streamChat
      vi.spyOn(sseModule, 'streamChat').mockResolvedValue(undefined);
      fakeBrowser.runtime.sendMessage = vi.fn().mockResolvedValue(undefined);

      // When: Handle stream chat
      await handleStreamChat({
        conversationId: null,
        message: 'Test',
        requestId: 'req-123',
      });

      // Then: Stream removed from active streams
      expect(getActiveStreamCount()).toBe(0);
    });
  });

  describe('handleCancelStream', () => {
    it('should abort active stream and return true', async () => {
      // Given: Active stream
      vi.spyOn(sseModule, 'streamChat').mockImplementation(
        async (_c, _m, _onEvent, signal) => {
          // Simulate long-running stream
          await new Promise((resolve, reject) => {
            signal?.addEventListener('abort', () => reject(new Error('Aborted')));
          });
        }
      );

      fakeBrowser.runtime.sendMessage = vi.fn().mockResolvedValue(undefined);

      // Start stream (don't await - it will hang)
      const streamPromise = handleStreamChat({
        conversationId: null,
        message: 'Test',
        requestId: 'req-123',
      });

      // Wait for stream to start
      await new Promise(resolve => setTimeout(resolve, 10));

      // When: Cancel stream
      const result = handleCancelStream('req-123');

      // Then: Returns true and stream aborted
      expect(result).toBe(true);
      expect(getActiveStreamCount()).toBe(0);

      // Cleanup: stream completes normally (error is caught and sent as message)
      await streamPromise; // Should resolve, not reject

      // Verify ERROR message was sent
      const sendMessage = fakeBrowser.runtime.sendMessage as any;
      expect(sendMessage).toHaveBeenCalledWith(
        expect.objectContaining({
          type: MessageType.STREAM_CHAT_ERROR,
          requestId: 'req-123',
        })
      );
    });

    it('should return false for non-existent stream', () => {
      // Given: No active stream
      // When: Cancel non-existent stream
      const result = handleCancelStream('non-existent');

      // Then: Returns false
      expect(result).toBe(false);
    });
  });

  describe('Concurrent Streams', () => {
    it('should manage multiple concurrent streams', async () => {
      // Given: Mock streamChat with delay
      vi.spyOn(sseModule, 'streamChat').mockImplementation(
        async () => {
          await new Promise(resolve => setTimeout(resolve, 50));
        }
      );

      fakeBrowser.runtime.sendMessage = vi.fn().mockResolvedValue(undefined);

      // When: Start multiple streams concurrently
      const stream1 = handleStreamChat({
        conversationId: null,
        message: 'Test 1',
        requestId: 'req-1',
      });

      const stream2 = handleStreamChat({
        conversationId: null,
        message: 'Test 2',
        requestId: 'req-2',
      });

      // Then: Both streams active
      // (Check before they complete)
      await new Promise(resolve => setTimeout(resolve, 10));
      expect(getActiveStreamCount()).toBe(2);

      // Wait for completion
      await Promise.all([stream1, stream2]);

      // All streams cleaned up
      expect(getActiveStreamCount()).toBe(0);
    });
  });
});
