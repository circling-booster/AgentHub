import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { A2aAgentManager } from '../../components/A2aAgentManager';

// Mock useA2aAgents hook
vi.mock('../../hooks/useA2aAgents', () => ({
  useA2aAgents: vi.fn(),
}));

import { useA2aAgents } from '../../hooks/useA2aAgents';
const mockUseA2aAgents = vi.mocked(useA2aAgents);

describe('A2aAgentManager', () => {
  const defaultMock = {
    agents: [],
    loading: false,
    error: null,
    loadAgents: vi.fn(),
    addAgent: vi.fn(),
    removeAgent: vi.fn(),
  };

  beforeEach(() => {
    mockUseA2aAgents.mockReturnValue({ ...defaultMock });
  });

  it('should render agent URL input and add button', () => {
    render(<A2aAgentManager />);

    expect(screen.getByPlaceholderText('A2A Agent URL')).toBeDefined();
    expect(screen.getByRole('button', { name: 'Add Agent' })).toBeDefined();
  });

  it('should call loadAgents on mount', () => {
    const loadAgents = vi.fn();
    mockUseA2aAgents.mockReturnValue({ ...defaultMock, loadAgents });

    render(<A2aAgentManager />);

    expect(loadAgents).toHaveBeenCalled();
  });

  it('should render agent list', () => {
    mockUseA2aAgents.mockReturnValue({
      ...defaultMock,
      agents: [
        { id: 'a2a-1', name: 'Test Agent', url: 'http://localhost:9001', type: 'a2a', enabled: true, agent_card: null, registered_at: '' },
        { id: 'a2a-2', name: 'Another Agent', url: 'http://localhost:9002', type: 'a2a', enabled: true, agent_card: null, registered_at: '' },
      ],
    });

    render(<A2aAgentManager />);

    expect(screen.getByText('Test Agent')).toBeDefined();
    expect(screen.getByText('Another Agent')).toBeDefined();
  });

  it('should call addAgent when form submitted', async () => {
    const addAgent = vi.fn();
    mockUseA2aAgents.mockReturnValue({ ...defaultMock, addAgent });

    render(<A2aAgentManager />);

    const input = screen.getByPlaceholderText('A2A Agent URL');
    fireEvent.change(input, { target: { value: 'http://localhost:9001' } });

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Add Agent' }));
    });

    expect(addAgent).toHaveBeenCalledWith('http://localhost:9001');
  });

  it('should not add agent with empty URL', async () => {
    const addAgent = vi.fn();
    mockUseA2aAgents.mockReturnValue({ ...defaultMock, addAgent });

    render(<A2aAgentManager />);

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Add Agent' }));
    });

    expect(addAgent).not.toHaveBeenCalled();
  });

  it('should call removeAgent when remove button clicked', async () => {
    const removeAgent = vi.fn();
    mockUseA2aAgents.mockReturnValue({
      ...defaultMock,
      removeAgent,
      agents: [
        { id: 'a2a-1', name: 'Test Agent', url: 'http://localhost:9001', type: 'a2a', enabled: true, agent_card: null, registered_at: '' },
      ],
    });

    render(<A2aAgentManager />);

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Remove' }));
    });

    expect(removeAgent).toHaveBeenCalledWith('a2a-1');
  });

  it('should show loading state', () => {
    mockUseA2aAgents.mockReturnValue({ ...defaultMock, loading: true });

    render(<A2aAgentManager />);

    expect(screen.getByText('Loading...')).toBeDefined();
  });

  it('should show error message', () => {
    mockUseA2aAgents.mockReturnValue({ ...defaultMock, error: 'Failed to connect' });

    render(<A2aAgentManager />);

    expect(screen.getByText('Failed to connect')).toBeDefined();
  });

  it('should show empty state when no agents', () => {
    render(<A2aAgentManager />);

    expect(screen.getByText('No A2A agents registered')).toBeDefined();
  });

  it('should show expand button for agents', () => {
    mockUseA2aAgents.mockReturnValue({
      ...defaultMock,
      agents: [
        { id: 'a2a-1', name: 'Test Agent', url: 'http://localhost:9001', type: 'a2a', enabled: true, agent_card: { name: 'TestAgent' }, registered_at: '' },
      ],
    });

    render(<A2aAgentManager />);

    // Expand button should be present (▶ or ▼)
    const expandButtons = screen.getAllByRole('button').filter(btn => btn.textContent === '▶' || btn.textContent === '▼');
    expect(expandButtons.length).toBeGreaterThan(0);
  });

  it('should display agent card when expanded', async () => {
    mockUseA2aAgents.mockReturnValue({
      ...defaultMock,
      agents: [
        {
          id: 'a2a-1',
          name: 'Test Agent',
          url: 'http://localhost:9001',
          type: 'a2a',
          enabled: true,
          agent_card: { name: 'TestAgent', description: 'A test agent', capabilities: ['chat'] },
          registered_at: '',
        },
      ],
    });

    render(<A2aAgentManager />);

    const expandButton = screen.getAllByRole('button').find(btn => btn.textContent === '▶');
    await act(async () => {
      fireEvent.click(expandButton!);
    });

    // Agent card should be displayed
    expect(screen.getByText(/TestAgent/)).toBeDefined();
  });

  it('should collapse agent when expand button clicked again', async () => {
    mockUseA2aAgents.mockReturnValue({
      ...defaultMock,
      agents: [
        {
          id: 'a2a-1',
          name: 'Test Agent',
          url: 'http://localhost:9001',
          type: 'a2a',
          enabled: true,
          agent_card: { name: 'TestAgent' },
          registered_at: '',
        },
      ],
    });

    render(<A2aAgentManager />);

    const expandButton = screen.getAllByRole('button').find(btn => btn.textContent === '▶');

    // Expand
    await act(async () => {
      fireEvent.click(expandButton!);
    });
    expect(screen.getByText(/TestAgent/)).toBeDefined();

    // Collapse
    const collapseButton = screen.getAllByRole('button').find(btn => btn.textContent === '▼');
    await act(async () => {
      fireEvent.click(collapseButton!);
    });

    // Agent card should not be visible
    expect(screen.queryByText(/TestAgent/)).toBeNull();
  });
});
