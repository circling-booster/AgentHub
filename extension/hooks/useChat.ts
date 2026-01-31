/**
 * Chat state management hook
 *
 * Handles message sending, SSE streaming events, and conversation state.
 * Communicates with Background Service Worker via chrome.runtime messages.
 * Persists chat state to chrome.storage.session for tab switching.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type { ChatMessage } from '../lib/types';
import { MessageType } from '../lib/messaging';
import type { ExtensionMessage } from '../lib/messaging';
import { ErrorCode } from '../lib/constants';

interface ChatState {
  messages: ChatMessage[];
  conversationId: string | null;
  streaming: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
}

interface StoredChatState {
  conversationId: string | null;
  messages: Array<{
    id: string;
    role: 'user' | 'assistant';
    content: string;
    createdAt: string;
    toolCalls?: Array<{
      name: string;
      arguments: Record<string, unknown>;
      result?: string;
    }>;
    agentTransfer?: string;
  }>;
}

const STORAGE_KEY = 'chatState';

/**
 * 에러 코드를 사용자 친화적 메시지로 변환
 * Step 0: ErrorCode enum 사용 (타입 안전성 강화)
 */
function mapErrorCodeToMessage(errorCode: string | undefined, originalMessage: string): string {
  if (!errorCode) {
    return originalMessage;
  }

  switch (errorCode) {
    case ErrorCode.LLM_RATE_LIMIT:
      return '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.';
    case ErrorCode.LLM_AUTHENTICATION:
      return 'API 인증 오류가 발생했습니다. 설정을 확인해주세요.';
    case ErrorCode.ENDPOINT_CONNECTION:
      return '서버 연결에 실패했습니다. 네트워크를 확인해주세요.';
    case ErrorCode.ENDPOINT_TIMEOUT:
      return '서버 응답 시간이 초과되었습니다. 다시 시도해주세요.';
    case ErrorCode.ENDPOINT_NOT_FOUND:
      return '서버를 찾을 수 없습니다. URL을 확인해주세요.';
    case ErrorCode.TOOL_NOT_FOUND:
      return '도구를 찾을 수 없습니다.';
    case ErrorCode.CONVERSATION_NOT_FOUND:
      return '대화를 찾을 수 없습니다.';
    case ErrorCode.INVALID_URL:
      return '잘못된 URL입니다.';
    case ErrorCode.UNKNOWN:
      return `오류가 발생했습니다: ${originalMessage}`;
    default:
      return originalMessage;
  }
}

export function useChat(): ChatState {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Use ref for streaming state to avoid stale closure in listener
  const streamingRef = useRef(false);

  // Restore chat state from session storage on mount
  useEffect(() => {
    (async () => {
      const stored = await browser.storage.session.get(STORAGE_KEY);
      if (stored[STORAGE_KEY]) {
        const state: StoredChatState = stored[STORAGE_KEY];
        setConversationId(state.conversationId);
        setMessages(
          state.messages.map((msg) => ({
            ...msg,
            createdAt: new Date(msg.createdAt),
          }))
        );
      }
    })();
  }, []);

  // Save chat state to session storage on update
  useEffect(() => {
    (async () => {
      const state: StoredChatState = {
        conversationId,
        messages: messages.map((msg) => ({
          ...msg,
          createdAt: msg.createdAt.toISOString(),
        })),
      };
      await browser.storage.session.set({ [STORAGE_KEY]: state });
    })();
  }, [messages, conversationId]);

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
        } else if (event.type === 'tool_call') {
          // Step 2: tool_call 이벤트 처리
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last && last.role === 'assistant') {
              // Add tool call to existing assistant message
              const toolCalls = last.toolCalls || [];
              return [
                ...prev.slice(0, -1),
                {
                  ...last,
                  toolCalls: [
                    ...toolCalls,
                    { name: event.tool_name, arguments: event.tool_arguments },
                  ],
                },
              ];
            }
            // Create new assistant message with tool call
            return [
              ...prev,
              {
                id: crypto.randomUUID(),
                role: 'assistant',
                content: '',
                createdAt: new Date(),
                toolCalls: [{ name: event.tool_name, arguments: event.tool_arguments }],
              },
            ];
          });
        } else if (event.type === 'tool_result') {
          // Step 2: tool_result 이벤트 처리
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last && last.role === 'assistant' && last.toolCalls) {
              // Update the matching tool call with result
              const updatedToolCalls = last.toolCalls.map((tc) =>
                tc.name === event.tool_name ? { ...tc, result: event.result } : tc
              );
              return [
                ...prev.slice(0, -1),
                { ...last, toolCalls: updatedToolCalls },
              ];
            }
            return prev;
          });
        } else if (event.type === 'agent_transfer') {
          // Step 2: agent_transfer 이벤트 처리
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last && last.role === 'assistant') {
              return [
                ...prev.slice(0, -1),
                { ...last, agentTransfer: event.agent_name },
              ];
            }
            // Create new assistant message with agent transfer
            return [
              ...prev,
              {
                id: crypto.randomUUID(),
                role: 'assistant',
                content: '',
                createdAt: new Date(),
                agentTransfer: event.agent_name,
              },
            ];
          });
        } else if (event.type === 'error') {
          // Step 3: Typed error 이벤트 처리
          const userFriendlyMessage = mapErrorCodeToMessage(event.error_code, event.content);
          setError(userFriendlyMessage);
          setStreaming(false);
          streamingRef.current = false;
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
