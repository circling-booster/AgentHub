/**
 * Chat interface component
 *
 * Combines message list, input, and streaming indicator.
 * Uses useChat hook for state management.
 */

import { useRef, useEffect } from 'react';
import { useChat } from '../hooks/useChat';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';

export function ChatInterface() {
  const { messages, streaming, error, sendMessage } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="chat-interface">
      <div className="messages-container">
        {messages.length === 0 && !error && (
          <div className="empty-state">Start a conversation</div>
        )}

        {error && <div className="error-message">{error}</div>}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {streaming && (
          <div data-testid="streaming-indicator" className="streaming-indicator">
            Thinking...
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <ChatInput onSend={sendMessage} disabled={streaming} />
    </div>
  );
}
