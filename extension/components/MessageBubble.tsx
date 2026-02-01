/**
 * Chat message bubble component
 *
 * Renders a single message with role-based styling.
 * Supports markdown code blocks with syntax highlighting.
 */

import type { ChatMessage } from '../lib/types';
import { parseMessageContent } from '../lib/markdown';
import { CodeBlock } from './CodeBlock';
import { ToolCallIndicator } from './ToolCallIndicator';

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

      {/* Agent Transfer Indicator */}
      {message.agentTransfer && (
        <div
          style={{
            padding: '6px 10px',
            margin: '4px 0',
            borderRadius: '6px',
            backgroundColor: '#e3f2fd',
            border: '1px solid #2196f3',
            fontSize: '0.85rem',
            color: '#1976d2',
          }}
        >
          🔄 Transferred to: <strong>{message.agentTransfer}</strong>
        </div>
      )}

      {/* Tool Calls */}
      {message.toolCalls && message.toolCalls.length > 0 && (
        <div style={{ margin: '8px 0' }}>
          {message.toolCalls.map((toolCall, index) => (
            <ToolCallIndicator
              key={index}
              name={toolCall.name}
              arguments={toolCall.arguments}
              result={toolCall.result}
            />
          ))}
        </div>
      )}

      {/* Message Content */}
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
