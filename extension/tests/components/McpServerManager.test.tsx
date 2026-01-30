import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { McpServerManager } from '../../components/McpServerManager';

// Mock useMcpServers hook
vi.mock('../../hooks/useMcpServers', () => ({
  useMcpServers: vi.fn(),
}));

import { useMcpServers } from '../../hooks/useMcpServers';
const mockUseMcpServers = vi.mocked(useMcpServers);

describe('McpServerManager', () => {
  const defaultMock = {
    servers: [],
    loading: false,
    error: null,
    loadServers: vi.fn(),
    addServer: vi.fn(),
    removeServer: vi.fn(),
  };

  beforeEach(() => {
    mockUseMcpServers.mockReturnValue({ ...defaultMock });
  });

  it('should render server URL input and add button', () => {
    render(<McpServerManager />);

    expect(screen.getByPlaceholderText('MCP Server URL')).toBeDefined();
    expect(screen.getByRole('button', { name: 'Add Server' })).toBeDefined();
  });

  it('should call loadServers on mount', () => {
    const loadServers = vi.fn();
    mockUseMcpServers.mockReturnValue({ ...defaultMock, loadServers });

    render(<McpServerManager />);

    expect(loadServers).toHaveBeenCalled();
  });

  it('should render server list', () => {
    mockUseMcpServers.mockReturnValue({
      ...defaultMock,
      servers: [
        { id: 'srv-1', name: 'Test Server', url: 'http://localhost:9000/mcp', enabled: true, registered_at: '' },
        { id: 'srv-2', name: 'Another', url: 'http://localhost:9001/mcp', enabled: true, registered_at: '' },
      ],
    });

    render(<McpServerManager />);

    expect(screen.getByText('Test Server')).toBeDefined();
    expect(screen.getByText('Another')).toBeDefined();
  });

  it('should call addServer when form submitted', async () => {
    const addServer = vi.fn();
    mockUseMcpServers.mockReturnValue({ ...defaultMock, addServer });

    render(<McpServerManager />);

    const input = screen.getByPlaceholderText('MCP Server URL');
    fireEvent.change(input, { target: { value: 'http://localhost:9000/mcp' } });

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Add Server' }));
    });

    expect(addServer).toHaveBeenCalledWith('http://localhost:9000/mcp');
  });

  it('should not add server with empty URL', async () => {
    const addServer = vi.fn();
    mockUseMcpServers.mockReturnValue({ ...defaultMock, addServer });

    render(<McpServerManager />);

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Add Server' }));
    });

    expect(addServer).not.toHaveBeenCalled();
  });

  it('should call removeServer when remove button clicked', async () => {
    const removeServer = vi.fn();
    mockUseMcpServers.mockReturnValue({
      ...defaultMock,
      removeServer,
      servers: [
        { id: 'srv-1', name: 'Test Server', url: 'http://localhost:9000/mcp', enabled: true, registered_at: '' },
      ],
    });

    render(<McpServerManager />);

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Remove' }));
    });

    expect(removeServer).toHaveBeenCalledWith('srv-1');
  });

  it('should show loading state', () => {
    mockUseMcpServers.mockReturnValue({ ...defaultMock, loading: true });

    render(<McpServerManager />);

    expect(screen.getByText('Loading...')).toBeDefined();
  });

  it('should show error message', () => {
    mockUseMcpServers.mockReturnValue({ ...defaultMock, error: 'Failed to connect' });

    render(<McpServerManager />);

    expect(screen.getByText('Failed to connect')).toBeDefined();
  });

  it('should show empty state when no servers', () => {
    render(<McpServerManager />);

    expect(screen.getByText('No MCP servers registered')).toBeDefined();
  });
});
