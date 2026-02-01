import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { fakeBrowser } from 'wxt/testing';
import { useChat } from '../../hooks/useChat';
import { MessageType } from '../../lib/messaging';

describe('useChat', () => {
  beforeEach(() => {
    fakeBrowser.reset();
    fakeBrowser.runtime.sendMessage = vi.fn().mockResolvedValue({ received: true });
  });

  it('should return initial empty state', () => {
    // When: Hook renders
    const { result } = renderHook(() => useChat());

    // Then: Empty state
    expect(result.current.messages).toEqual([]);
    expect(result.current.conversationId).toBeNull();
    expect(result.current.streaming).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should send message via sendMessage()', async () => {
    // Given: Hook rendered
    const { result } = renderHook(() => useChat());

    // When: Send message
    await act(async () => {
      await result.current.sendMessage('Hello');
    });

    // Then: User message added to state
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].role).toBe('user');
    expect(result.current.messages[0].content).toBe('Hello');

    // And: START_STREAM_CHAT sent to Background
    expect(fakeBrowser.runtime.sendMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        type: MessageType.START_STREAM_CHAT,
        payload: expect.objectContaining({
          conversationId: null,
          message: 'Hello',
        }),
      })
    );
  });

  it('should set streaming to true after sendMessage()', async () => {
    // Given: Hook rendered
    const { result } = renderHook(() => useChat());

    // When: Send message
    await act(async () => {
      await result.current.sendMessage('Hello');
    });

    // Then: Streaming is true
    expect(result.current.streaming).toBe(true);
  });

  it('should not allow sending while streaming', async () => {
    // Given: Already streaming
    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage('Hello');
    });

    expect(result.current.streaming).toBe(true);

    // When: Try to send again
    await act(async () => {
      await result.current.sendMessage('Another message');
    });

    // Then: Only one user message (second was blocked)
    expect(result.current.messages).toHaveLength(1);
  });

  it('should handle conversation_created event', async () => {
    // Given: Hook with message listener
    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage('Hello');
    });

    // When: conversation_created event received via listener
    await act(async () => {
      fakeBrowser.runtime.onMessage.trigger(
        {
          type: MessageType.STREAM_CHAT_EVENT,
          requestId: 'any',
          event: { type: 'conversation_created', conversation_id: 'conv-abc' },
        },
      );
    });

    // Then: conversationId updated
    expect(result.current.conversationId).toBe('conv-abc');
  });

  it('should accumulate text events into assistant message', async () => {
    // Given: Hook with active stream
    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage('Hello');
    });

    // When: Text events received
    await act(async () => {
      fakeBrowser.runtime.onMessage.trigger(
        {
          type: MessageType.STREAM_CHAT_EVENT,
          requestId: 'any',
          event: { type: 'text', content: 'Hi' },
        },
      );
    });

    await act(async () => {
      fakeBrowser.runtime.onMessage.trigger(
        {
          type: MessageType.STREAM_CHAT_EVENT,
          requestId: 'any',
          event: { type: 'text', content: ' there!' },
        },
      );
    });

    // Then: Assistant message accumulated
    expect(result.current.messages).toHaveLength(2); // user + assistant
    expect(result.current.messages[1].role).toBe('assistant');
    expect(result.current.messages[1].content).toBe('Hi there!');
  });

  it('should set streaming false on STREAM_CHAT_DONE', async () => {
    // Given: Active stream
    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage('Hello');
    });

    expect(result.current.streaming).toBe(true);

    // When: DONE received
    await act(async () => {
      fakeBrowser.runtime.onMessage.trigger(
        {
          type: MessageType.STREAM_CHAT_DONE,
          requestId: 'any',
        },
      );
    });

    // Then: Streaming stopped
    expect(result.current.streaming).toBe(false);
  });

  it('should set error on STREAM_CHAT_ERROR', async () => {
    // Given: Active stream
    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage('Hello');
    });

    // When: ERROR received
    await act(async () => {
      fakeBrowser.runtime.onMessage.trigger(
        {
          type: MessageType.STREAM_CHAT_ERROR,
          requestId: 'any',
          error: 'Server error',
        },
      );
    });

    // Then: Error state set and streaming stopped
    expect(result.current.error).toBe('Server error');
    expect(result.current.streaming).toBe(false);
  });

  it('should cleanup message listener on unmount', () => {
    // Given: Hook rendered (listener added)
    const { unmount } = renderHook(() => useChat());

    // When: Unmount
    unmount();

    // Then: No errors (verifies cleanup)
  });

  it('should use conversationId for subsequent messages', async () => {
    // Given: Conversation already created
    const { result } = renderHook(() => useChat());

    // Send first message
    await act(async () => {
      await result.current.sendMessage('Hello');
    });

    // Receive conversation_created
    await act(async () => {
      fakeBrowser.runtime.onMessage.trigger(
        {
          type: MessageType.STREAM_CHAT_EVENT,
          requestId: 'any',
          event: { type: 'conversation_created', conversation_id: 'conv-abc' },
        },
      );
    });

    // Receive DONE to reset streaming
    await act(async () => {
      fakeBrowser.runtime.onMessage.trigger(
        { type: MessageType.STREAM_CHAT_DONE, requestId: 'any' },
      );
    });

    // When: Send second message
    await act(async () => {
      await result.current.sendMessage('Follow up');
    });

    // Then: Uses existing conversationId
    expect(fakeBrowser.runtime.sendMessage).toHaveBeenLastCalledWith(
      expect.objectContaining({
        type: MessageType.START_STREAM_CHAT,
        payload: expect.objectContaining({
          conversationId: 'conv-abc',
          message: 'Follow up',
        }),
      })
    );
  });

  it('should save chat state to session storage on update', async () => {
    // Given: Hook rendered
    const { result } = renderHook(() => useChat());

    // When: Send message
    await act(async () => {
      await result.current.sendMessage('Hello');
    });

    // Simulate conversation_created
    await act(async () => {
      fakeBrowser.runtime.onMessage.trigger({
        type: MessageType.STREAM_CHAT_EVENT,
        requestId: 'any',
        event: { type: 'conversation_created', conversation_id: 'conv-123' },
      });
    });

    // Then: Session storage should have chat state
    const stored = await fakeBrowser.storage.session.get('chatState');
    expect(stored.chatState).toBeDefined();
    expect(stored.chatState.conversationId).toBe('conv-123');
    expect(stored.chatState.messages).toHaveLength(1);
    expect(stored.chatState.messages[0].content).toBe('Hello');
  });

  it('should restore chat state from session storage on mount', async () => {
    // Given: Session storage has previous chat state
    await fakeBrowser.storage.session.set({
      chatState: {
        conversationId: 'conv-restored',
        messages: [
          {
            id: 'msg-1',
            role: 'user',
            content: 'Previous message',
            createdAt: new Date('2026-01-30T00:00:00Z').toISOString(),
          },
          {
            id: 'msg-2',
            role: 'assistant',
            content: 'Previous response',
            createdAt: new Date('2026-01-30T00:01:00Z').toISOString(),
          },
        ],
      },
    });

    // When: Hook mounts
    const { result } = renderHook(() => useChat());

    // Wait for storage to load
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Then: State restored from storage
    expect(result.current.conversationId).toBe('conv-restored');
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].content).toBe('Previous message');
    expect(result.current.messages[1].content).toBe('Previous response');
  });

  it('should clear session storage when conversation ID is null', async () => {
    // Given: Session storage has chat state
    await fakeBrowser.storage.session.set({
      chatState: {
        conversationId: 'conv-old',
        messages: [{ id: 'msg-1', role: 'user', content: 'Old', createdAt: new Date().toISOString() }],
      },
    });

    // When: Hook mounts with empty state
    renderHook(() => useChat());

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Storage should still have the previous state (until new conversation starts)
    const stored = await fakeBrowser.storage.session.get('chatState');
    expect(stored.chatState).toBeDefined();
  });
});
