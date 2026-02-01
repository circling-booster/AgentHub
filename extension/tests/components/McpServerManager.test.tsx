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
    loadTools: vi.fn(),
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

  it('should show expand button for servers', () => {
    mockUseMcpServers.mockReturnValue({
      ...defaultMock,
      servers: [
        { id: 'srv-1', name: 'Test Server', url: 'http://localhost:9000/mcp', enabled: true, registered_at: '' },
      ],
    });

    render(<McpServerManager />);

    // Expand button should be present (▶ or ▼)
    const expandButtons = screen.getAllByRole('button').filter(btn => btn.textContent === '▶' || btn.textContent === '▼');
    expect(expandButtons.length).toBeGreaterThan(0);
  });

  it('should expand server and load tools when expand button clicked', async () => {
    const loadTools = vi.fn();
    mockUseMcpServers.mockReturnValue({
      ...defaultMock,
      loadTools,
      servers: [
        { id: 'srv-1', name: 'Test Server', url: 'http://localhost:9000/mcp', enabled: true, registered_at: '' },
      ],
    });

    render(<McpServerManager />);

    const expandButton = screen.getAllByRole('button').find(btn => btn.textContent === '▶');
    expect(expandButton).toBeDefined();

    // Click to expand
    await act(async () => {
      fireEvent.click(expandButton!);
    });

    // loadTools should be called (since tools are not present)
    expect(loadTools).toHaveBeenCalledWith('srv-1');
  });

  it('should display tools when server is expanded', async () => {
    const loadTools = vi.fn();
    mockUseMcpServers.mockReturnValue({
      ...defaultMock,
      loadTools,
      servers: [
        {
          id: 'srv-1',
          name: 'Test Server',
          url: 'http://localhost:9000/mcp',
          enabled: true,
          registered_at: '',
          tools: [
            { name: 'echo', description: 'Echo tool', input_schema: {} },
            { name: 'search', description: 'Search tool', input_schema: {} },
          ],
        },
      ],
    });

    render(<McpServerManager />);

    const expandButton = screen.getAllByRole('button').find(btn => btn.textContent === '▶');
    await act(async () => {
      fireEvent.click(expandButton!);
    });

    // Tools should be displayed
    expect(screen.getByText('echo')).toBeDefined();
    expect(screen.getByText('search')).toBeDefined();
    expect(screen.getByText('Echo tool')).toBeDefined();
  });

  it('should not call loadTools if tools already loaded', async () => {
    const loadTools = vi.fn();
    mockUseMcpServers.mockReturnValue({
      ...defaultMock,
      loadTools,
      servers: [
        {
          id: 'srv-1',
          name: 'Test Server',
          url: 'http://localhost:9000/mcp',
          enabled: true,
          registered_at: '',
          tools: [{ name: 'echo', description: 'Echo tool', input_schema: {} }],
        },
      ],
    });

    render(<McpServerManager />);

    const expandButton = screen.getAllByRole('button').find(btn => btn.textContent === '▶');
    await act(async () => {
      fireEvent.click(expandButton!);
    });

    // loadTools should NOT be called (tools already present)
    expect(loadTools).not.toHaveBeenCalled();
  });

  it('should collapse server when expand button clicked again', async () => {
    mockUseMcpServers.mockReturnValue({
      ...defaultMock,
      servers: [
        {
          id: 'srv-1',
          name: 'Test Server',
          url: 'http://localhost:9000/mcp',
          enabled: true,
          registered_at: '',
          tools: [{ name: 'echo', description: 'Echo tool', input_schema: {} }],
        },
      ],
    });

    render(<McpServerManager />);

    const expandButton = screen.getAllByRole('button').find(btn => btn.textContent === '▶');

    // Expand
    await act(async () => {
      fireEvent.click(expandButton!);
    });
    expect(screen.getByText('echo')).toBeDefined();

    // Collapse
    const collapseButton = screen.getAllByRole('button').find(btn => btn.textContent === '▼');
    await act(async () => {
      fireEvent.click(collapseButton!);
    });

    // Tools should not be visible
    expect(screen.queryByText('echo')).toBeNull();
  });
});
