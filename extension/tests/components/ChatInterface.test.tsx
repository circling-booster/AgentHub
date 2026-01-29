import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInterface } from '../../components/ChatInterface';

// Mock useChat hook
vi.mock('../../hooks/useChat', () => ({
  useChat: vi.fn(),
}));

import { useChat } from '../../hooks/useChat';
const mockUseChat = vi.mocked(useChat);

describe('ChatInterface', () => {
  it('should render empty state message when no messages', () => {
    mockUseChat.mockReturnValue({
      messages: [],
      conversationId: null,
      streaming: false,
      error: null,
      sendMessage: vi.fn(),
    });

    render(<ChatInterface />);

    expect(screen.getByText('Start a conversation')).toBeDefined();
  });

  it('should render messages list', () => {
    mockUseChat.mockReturnValue({
      messages: [
        { id: '1', role: 'user', content: 'Hello', createdAt: new Date() },
        { id: '2', role: 'assistant', content: 'Hi there!', createdAt: new Date() },
      ],
      conversationId: 'conv-1',
      streaming: false,
      error: null,
      sendMessage: vi.fn(),
    });

    render(<ChatInterface />);

    expect(screen.getByText('Hello')).toBeDefined();
    expect(screen.getByText('Hi there!')).toBeDefined();
  });

  it('should call sendMessage on ChatInput submit', () => {
    const sendMessage = vi.fn();
    mockUseChat.mockReturnValue({
      messages: [],
      conversationId: null,
      streaming: false,
      error: null,
      sendMessage,
    });

    render(<ChatInterface />);

    const input = screen.getByPlaceholderText('Type a message...');
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send' }));

    expect(sendMessage).toHaveBeenCalledWith('Test message');
  });

  it('should disable input during streaming', () => {
    mockUseChat.mockReturnValue({
      messages: [
        { id: '1', role: 'user', content: 'Hello', createdAt: new Date() },
      ],
      conversationId: 'conv-1',
      streaming: true,
      error: null,
      sendMessage: vi.fn(),
    });

    render(<ChatInterface />);

    const input = screen.getByPlaceholderText('Type a message...') as HTMLInputElement;
    expect(input.disabled).toBe(true);
  });

  it('should display error message when error exists', () => {
    mockUseChat.mockReturnValue({
      messages: [],
      conversationId: null,
      streaming: false,
      error: 'Connection failed',
      sendMessage: vi.fn(),
    });

    render(<ChatInterface />);

    expect(screen.getByText('Connection failed')).toBeDefined();
  });

  it('should show streaming indicator during streaming', () => {
    mockUseChat.mockReturnValue({
      messages: [
        { id: '1', role: 'user', content: 'Hello', createdAt: new Date() },
      ],
      conversationId: 'conv-1',
      streaming: true,
      error: null,
      sendMessage: vi.fn(),
    });

    render(<ChatInterface />);

    expect(screen.getByTestId('streaming-indicator')).toBeDefined();
  });
});
