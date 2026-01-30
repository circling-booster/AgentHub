/**
 * Chat message bubble component
 *
 * Renders a single message with role-based styling.
 */

import type { ChatMessage } from '../lib/types';

interface MessageBubbleProps {
  message: ChatMessage;
}

const ROLE_LABELS: Record<string, string> = {
  user: 'You',
  assistant: 'Agent',
};

export function MessageBubble({ message }: MessageBubbleProps) {
  return (
    <div
      data-testid="message-bubble"
      className={`message-bubble ${message.role}`}
    >
      <span className="message-role">{ROLE_LABELS[message.role]}</span>
      <div className="message-content">{message.content}</div>
    </div>
  );
}
