import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInterface } from '../../components/ChatInterface';

// Mock useChat hook
vi.mock('../../hooks/useChat', () => ({
  useChat: vi.fn(),
}));

// Mock usePageContext hook
vi.mock('../../lib/hooks/usePageContext', () => ({
  usePageContext: vi.fn(),
}));

import { useChat } from '../../hooks/useChat';
import { usePageContext } from '../../lib/hooks/usePageContext';
const mockUseChat = vi.mocked(useChat);
const mockUsePageContext = vi.mocked(usePageContext);

describe('ChatInterface', () => {
  beforeEach(() => {
    // Default mock for usePageContext
    mockUsePageContext.mockReturnValue({
      enabled: false,
      context: null,
      loading: false,
      toggleEnabled: vi.fn(),
      fetchContext: vi.fn(),
    });
  });

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

  it('should render page context toggle', () => {
    mockUseChat.mockReturnValue({
      messages: [],
      conversationId: null,
      streaming: false,
      error: null,
      sendMessage: vi.fn(),
    });

    render(<ChatInterface />);

    const toggle = screen.getByLabelText('Include page context');
    expect(toggle).toBeDefined();
    expect((toggle as HTMLInputElement).checked).toBe(false);
  });

  it('should call toggleEnabled when page context checkbox is clicked', () => {
    const toggleEnabled = vi.fn();
    mockUsePageContext.mockReturnValue({
      enabled: false,
      context: null,
      loading: false,
      toggleEnabled,
      fetchContext: vi.fn(),
    });

    mockUseChat.mockReturnValue({
      messages: [],
      conversationId: null,
      streaming: false,
      error: null,
      sendMessage: vi.fn(),
    });

    render(<ChatInterface />);

    const toggle = screen.getByLabelText('Include page context') as HTMLInputElement;
    fireEvent.click(toggle);

    expect(toggleEnabled).toHaveBeenCalledTimes(1);
  });

  it('should show checked toggle when page context is enabled', () => {
    mockUsePageContext.mockReturnValue({
      enabled: true,
      context: { url: 'https://example.com', title: 'Test', selectedText: '', metaDescription: '', mainContent: '' },
      loading: false,
      toggleEnabled: vi.fn(),
      fetchContext: vi.fn(),
    });

    mockUseChat.mockReturnValue({
      messages: [],
      conversationId: null,
      streaming: false,
      error: null,
      sendMessage: vi.fn(),
    });

    render(<ChatInterface />);

    const toggle = screen.getByLabelText('Include page context') as HTMLInputElement;
    expect(toggle.checked).toBe(true);
  });
});
