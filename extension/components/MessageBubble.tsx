/**
 * Chat message bubble component
 *
 * Renders a single message with role-based styling.
 * Supports markdown code blocks with syntax highlighting.
 */

import type { ChatMessage } from '../lib/types';
import { parseMessageContent } from '../lib/markdown';
import { CodeBlock } from './CodeBlock';

interface MessageBubbleProps {
  message: ChatMessage;
}

const ROLE_LABELS: Record<string, string> = {
  user: 'You',
  assistant: 'Agent',
};

export function MessageBubble({ message }: MessageBubbleProps) {
  const contentBlocks = parseMessageContent(message.content);

  return (
    <div
      data-testid="message-bubble"
      className={`message-bubble ${message.role}`}
    >
      <span className="message-role">{ROLE_LABELS[message.role]}</span>
      <div className="message-content">
        {contentBlocks.map((block, index) => {
          if (block.type === 'text') {
            return (
              <div key={index} className="text-block">
                {block.content}
              </div>
            );
          }

          return (
            <CodeBlock
              key={index}
              language={block.language}
              code={block.code}
            />
          );
        })}
      </div>
    </div>
  );
}
