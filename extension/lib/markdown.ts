/**
 * Markdown parsing utilities
 *
 * Extracts code blocks from message content for syntax highlighting.
 */

export interface TextBlock {
  type: 'text';
  content: string;
}

export interface CodeBlock {
  type: 'code';
  language: string;
  code: string;
}

export type ContentBlock = TextBlock | CodeBlock;

/**
 * Parse message content into text and code blocks
 *
 * Supports standard markdown code blocks: ```language\ncode\n```
 */
export function parseMessageContent(content: string): ContentBlock[] {
  if (!content) {
    return [];
  }

  const blocks: ContentBlock[] = [];

  // Regex to match code blocks: ```language\ncode\n```
  // Captures: language (optional) and code content
  const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g;

  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = codeBlockRegex.exec(content)) !== null) {
    // Add text before code block (if any)
    if (match.index > lastIndex) {
      const textContent = content.substring(lastIndex, match.index).trim();
      if (textContent) {
        blocks.push({ type: 'text', content: textContent });
      }
    }

    // Add code block
    const language = match[1] || '';
    const code = match[2].trim();
    blocks.push({ type: 'code', language, code });

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text after last code block
  if (lastIndex < content.length) {
    const textContent = content.substring(lastIndex).trim();
    if (textContent) {
      blocks.push({ type: 'text', content: textContent });
    }
  }

  return blocks;
}
