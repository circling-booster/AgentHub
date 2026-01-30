/**
 * Chat state management hook
 *
 * Handles message sending, SSE streaming events, and conversation state.
 * Communicates with Background Service Worker via chrome.runtime messages.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type { ChatMessage } from '../lib/types';
import { MessageType } from '../lib/messaging';
import type { ExtensionMessage } from '../lib/messaging';

interface ChatState {
  messages: ChatMessage[];
  conversationId: string | null;
  streaming: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
}

export function useChat(): ChatState {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Use ref for streaming state to avoid stale closure in listener
  const streamingRef = useRef(false);

  // Listen for stream events from Background
  useEffect(() => {
    const listener = (
      message: ExtensionMessage,
      _sender: unknown,
      _sendResponse: (response?: unknown) => void
    ) => {
      if (message.type === MessageType.STREAM_CHAT_EVENT) {
        const event = message.event;

        if (event.type === 'conversation_created') {
          setConversationId(event.conversation_id);
        } else if (event.type === 'text') {
          // Accumulate text into the last assistant message
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last && last.role === 'assistant') {
              // Append to existing assistant message
              return [
                ...prev.slice(0, -1),
                { ...last, content: last.content + event.content },
              ];
            }
            // Create new assistant message
            return [
              ...prev,
              {
                id: crypto.randomUUID(),
                role: 'assistant',
                content: event.content,
                createdAt: new Date(),
              },
            ];
          });
        }
      }

      if (message.type === MessageType.STREAM_CHAT_DONE) {
        setStreaming(false);
        streamingRef.current = false;
      }

      if (message.type === MessageType.STREAM_CHAT_ERROR) {
        setError(message.error);
        setStreaming(false);
        streamingRef.current = false;
      }
    };

    browser.runtime.onMessage.addListener(listener);

    return () => {
      browser.runtime.onMessage.removeListener(listener);
    };
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    // Block if already streaming
    if (streamingRef.current) {
      return;
    }

    setError(null);

    // Add user message to state
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      createdAt: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Set streaming state
    setStreaming(true);
    streamingRef.current = true;

    // Send START_STREAM_CHAT to Background
    await browser.runtime.sendMessage({
      type: MessageType.START_STREAM_CHAT,
      payload: {
        conversationId,
        message: content,
      },
    });
  }, [conversationId]);

  return {
    messages,
    conversationId,
    streaming,
    error,
    sendMessage,
  };
}
