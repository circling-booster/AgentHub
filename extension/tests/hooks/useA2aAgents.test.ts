import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { fakeBrowser } from 'wxt/testing';
import { useA2aAgents } from '../../hooks/useA2aAgents';
import * as apiModule from '../../lib/api';

describe('useA2aAgents', () => {
  beforeEach(() => {
    fakeBrowser.reset();
    vi.restoreAllMocks();
  });

  it('should return initial empty state', () => {
    // When: Hook renders
    const { result } = renderHook(() => useA2aAgents());

    // Then: Empty state
    expect(result.current.agents).toEqual([]);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should load agents via loadAgents()', async () => {
    // Given: API returns agents
    vi.spyOn(apiModule, 'listA2aAgents').mockResolvedValue([
      {
        id: 'a2a-1',
        name: 'Test Agent',
        url: 'http://localhost:9001',
        type: 'a2a',
        enabled: true,
        agent_card: { name: 'TestAgent' },
        registered_at: '2026-01-30T00:00:00Z',
      },
    ]);

    // When: Load agents
    const { result } = renderHook(() => useA2aAgents());

    await act(async () => {
      await result.current.loadAgents();
    });

    // Then: Agents loaded
    expect(result.current.agents).toHaveLength(1);
    expect(result.current.agents[0].name).toBe('Test Agent');
    expect(result.current.loading).toBe(false);
  });

  it('should set loading state during loadAgents()', async () => {
    // Given: Slow API
    let resolveApi: (value: any) => void;
    vi.spyOn(apiModule, 'listA2aAgents').mockImplementation(
      () => new Promise(resolve => { resolveApi = resolve; })
    );

    const { result } = renderHook(() => useA2aAgents());

    // When: Start loading
    let loadPromise: Promise<void>;
    act(() => {
      loadPromise = result.current.loadAgents();
    });

    // Then: Loading is true
    expect(result.current.loading).toBe(true);

    // Resolve API
    await act(async () => {
      resolveApi!([]);
      await loadPromise!;
    });

    expect(result.current.loading).toBe(false);
  });

  it('should handle loadAgents error', async () => {
    // Given: API fails
    vi.spyOn(apiModule, 'listA2aAgents').mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useA2aAgents());

    // When: Load agents fails
    await act(async () => {
      await result.current.loadAgents();
    });

    // Then: Error state set
    expect(result.current.error).toBe('Network error');
    expect(result.current.agents).toEqual([]);
    expect(result.current.loading).toBe(false);
  });

  it('should add agent via addAgent()', async () => {
    // Given: Register API succeeds, list refreshes
    vi.spyOn(apiModule, 'registerA2aAgent').mockResolvedValue({
      id: 'a2a-new',
      name: 'New Agent',
      url: 'http://localhost:9002',
      type: 'a2a',
      enabled: true,
      agent_card: null,
      registered_at: '2026-01-30T00:00:00Z',
    });
    vi.spyOn(apiModule, 'listA2aAgents').mockResolvedValue([
      {
        id: 'a2a-new',
        name: 'New Agent',
        url: 'http://localhost:9002',
        type: 'a2a',
        enabled: true,
        agent_card: null,
        registered_at: '2026-01-30T00:00:00Z',
      },
    ]);

    const { result } = renderHook(() => useA2aAgents());

    // When: Add agent
    await act(async () => {
      await result.current.addAgent('http://localhost:9002', 'New Agent');
    });

    // Then: registerA2aAgent called and list refreshed
    expect(apiModule.registerA2aAgent).toHaveBeenCalledWith('http://localhost:9002', 'New Agent');
    expect(result.current.agents).toHaveLength(1);
    expect(result.current.agents[0].id).toBe('a2a-new');
  });

  it('should remove agent via removeAgent()', async () => {
    // Given: Existing agent
    vi.spyOn(apiModule, 'listA2aAgents')
      .mockResolvedValueOnce([
        { id: 'a2a-1', name: 'Agent1', url: 'http://a', type: 'a2a', enabled: true, agent_card: null, registered_at: '' },
      ])
      .mockResolvedValueOnce([]);
    vi.spyOn(apiModule, 'removeA2aAgent').mockResolvedValue(undefined);

    const { result } = renderHook(() => useA2aAgents());

    // Load initial agents
    await act(async () => {
      await result.current.loadAgents();
    });
    expect(result.current.agents).toHaveLength(1);

    // When: Remove agent
    await act(async () => {
      await result.current.removeAgent('a2a-1');
    });

    // Then: removeA2aAgent called and list refreshed
    expect(apiModule.removeA2aAgent).toHaveBeenCalledWith('a2a-1');
    expect(result.current.agents).toHaveLength(0);
  });

  it('should handle addAgent error', async () => {
    // Given: Register fails
    vi.spyOn(apiModule, 'registerA2aAgent').mockRejectedValue(new Error('Connection refused'));

    const { result } = renderHook(() => useA2aAgents());

    // When: Add agent fails
    await act(async () => {
      await result.current.addAgent('http://bad-agent');
    });

    // Then: Error state set
    expect(result.current.error).toBe('Connection refused');
  });
});
