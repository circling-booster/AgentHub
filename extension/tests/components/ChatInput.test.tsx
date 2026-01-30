import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInput } from '../../components/ChatInput';

describe('ChatInput', () => {
  it('should render input and submit button', () => {
    render(<ChatInput onSend={vi.fn()} disabled={false} />);

    expect(screen.getByPlaceholderText('Type a message...')).toBeDefined();
    expect(screen.getByRole('button', { name: 'Send' })).toBeDefined();
  });

  it('should call onSend with input value on submit', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} disabled={false} />);

    const input = screen.getByPlaceholderText('Type a message...');
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send' }));

    expect(onSend).toHaveBeenCalledWith('Hello');
  });

  it('should clear input after submit', () => {
    render(<ChatInput onSend={vi.fn()} disabled={false} />);

    const input = screen.getByPlaceholderText('Type a message...') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send' }));

    expect(input.value).toBe('');
  });

  it('should send on Enter key press', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} disabled={false} />);

    const input = screen.getByPlaceholderText('Type a message...');
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(onSend).toHaveBeenCalledWith('Hello');
  });

  it('should not send empty message', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} disabled={false} />);

    fireEvent.click(screen.getByRole('button', { name: 'Send' }));
    expect(onSend).not.toHaveBeenCalled();
  });

  it('should not send whitespace-only message', () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} disabled={false} />);

    const input = screen.getByPlaceholderText('Type a message...');
    fireEvent.change(input, { target: { value: '   ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send' }));

    expect(onSend).not.toHaveBeenCalled();
  });

  it('should disable input and button when disabled prop is true', () => {
    render(<ChatInput onSend={vi.fn()} disabled={true} />);

    const input = screen.getByPlaceholderText('Type a message...') as HTMLInputElement;
    const button = screen.getByRole('button', { name: 'Send' }) as HTMLButtonElement;

    expect(input.disabled).toBe(true);
    expect(button.disabled).toBe(true);
  });
});
