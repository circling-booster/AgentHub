import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MessageBubble } from '../../components/MessageBubble';
import type { ChatMessage } from '../../lib/types';

describe('MessageBubble', () => {
  const userMessage: ChatMessage = {
    id: 'msg-1',
    role: 'user',
    content: 'Hello, agent!',
    createdAt: new Date('2026-01-30T00:00:00Z'),
  };

  const assistantMessage: ChatMessage = {
    id: 'msg-2',
    role: 'assistant',
    content: 'Hi there! How can I help?',
    createdAt: new Date('2026-01-30T00:00:01Z'),
  };

  it('should render user message with user style', () => {
    render(<MessageBubble message={userMessage} />);

    expect(screen.getByText('Hello, agent!')).toBeDefined();
    expect(screen.getByTestId('message-bubble').className).toContain('user');
  });

  it('should render assistant message with assistant style', () => {
    render(<MessageBubble message={assistantMessage} />);

    expect(screen.getByText('Hi there! How can I help?')).toBeDefined();
    expect(screen.getByTestId('message-bubble').className).toContain('assistant');
  });

  it('should display role label', () => {
    render(<MessageBubble message={userMessage} />);
    expect(screen.getByText('You')).toBeDefined();
  });

  it('should display assistant role label', () => {
    render(<MessageBubble message={assistantMessage} />);
    expect(screen.getByText('Agent')).toBeDefined();
  });

  it('should render code blocks with syntax highlighting', () => {
    const messageWithCode: ChatMessage = {
      id: 'msg-3',
      role: 'assistant',
      content: 'Here is code:\n```python\nprint("hello")\n```',
      createdAt: new Date(),
    };

    render(<MessageBubble message={messageWithCode} />);

    // Check that code block is rendered
    expect(screen.getByTestId('code-block')).toBeDefined();

    // Check language label
    expect(screen.getByText('python')).toBeDefined();
  });

  it('should render multiple code blocks in a message', () => {
    const messageWithMultipleCode: ChatMessage = {
      id: 'msg-4',
      role: 'assistant',
      content: 'First:\n```js\nconst x = 1;\n```\nSecond:\n```py\nprint(2)\n```',
      createdAt: new Date(),
    };

    render(<MessageBubble message={messageWithMultipleCode} />);

    // Check that both code blocks are rendered
    const codeBlocks = screen.getAllByTestId('code-block');
    expect(codeBlocks).toHaveLength(2);

    // Check language labels
    expect(screen.getByText('js')).toBeDefined();
    expect(screen.getByText('py')).toBeDefined();
  });

  it('should render text and code blocks together', () => {
    const mixedMessage: ChatMessage = {
      id: 'msg-5',
      role: 'assistant',
      content: 'Here is a function:\n```typescript\nfunction add(a: number, b: number) { return a + b; }\n```\nThis adds two numbers.',
      createdAt: new Date(),
    };

    render(<MessageBubble message={mixedMessage} />);

    // Check text content
    expect(screen.getByText('Here is a function:')).toBeDefined();
    expect(screen.getByText('This adds two numbers.')).toBeDefined();

    // Check code block
    expect(screen.getByTestId('code-block')).toBeDefined();
    expect(screen.getByText('typescript')).toBeDefined();
  });
});
