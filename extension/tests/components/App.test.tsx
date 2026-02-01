import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { App } from '../../entrypoints/sidepanel/App';

// Mock child components
vi.mock('../../components/ChatInterface', () => ({
  ChatInterface: () => <div data-testid="chat-interface">ChatInterface</div>,
}));

vi.mock('../../components/McpServerManager', () => ({
  McpServerManager: () => <div data-testid="mcp-manager">McpServerManager</div>,
}));

vi.mock('../../components/ServerStatus', () => ({
  ServerStatus: () => <div data-testid="server-status">ServerStatus</div>,
}));

describe('App', () => {
  it('should render Chat tab by default', () => {
    render(<App />);

    expect(screen.getByTestId('chat-interface')).toBeDefined();
  });

  it('should render server status', () => {
    render(<App />);

    expect(screen.getByTestId('server-status')).toBeDefined();
  });

  it('should switch to MCP tab when clicked', () => {
    render(<App />);

    fireEvent.click(screen.getByText('MCP Servers'));

    expect(screen.getByTestId('mcp-manager')).toBeDefined();
    expect(screen.queryByTestId('chat-interface')).toBeNull();
  });

  it('should switch back to Chat tab', () => {
    render(<App />);

    // Go to MCP tab
    fireEvent.click(screen.getByText('MCP Servers'));
    expect(screen.getByTestId('mcp-manager')).toBeDefined();

    // Go back to Chat
    fireEvent.click(screen.getByText('Chat'));
    expect(screen.getByTestId('chat-interface')).toBeDefined();
    expect(screen.queryByTestId('mcp-manager')).toBeNull();
  });

  it('should highlight active tab', () => {
    render(<App />);

    const chatTab = screen.getByText('Chat');
    expect(chatTab.className).toContain('active');

    fireEvent.click(screen.getByText('MCP Servers'));

    const mcpTab = screen.getByText('MCP Servers');
    expect(mcpTab.className).toContain('active');
  });
});
