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
});
