import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { fakeBrowser } from 'wxt/testing';
import { useMcpServers } from '../../hooks/useMcpServers';
import * as apiModule from '../../lib/api';

describe('useMcpServers', () => {
  beforeEach(() => {
    fakeBrowser.reset();
    vi.restoreAllMocks();
  });

  it('should return initial empty state', () => {
    // When: Hook renders
    const { result } = renderHook(() => useMcpServers());

    // Then: Empty state
    expect(result.current.servers).toEqual([]);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should load servers via loadServers()', async () => {
    // Given: API returns servers
    vi.spyOn(apiModule, 'listMcpServers').mockResolvedValue([
      {
        id: 'srv-1',
        name: 'Test Server',
        url: 'http://localhost:9000/mcp',
        enabled: true,
        registered_at: '2026-01-30T00:00:00Z',
        tools: [{ name: 'tool1', description: 'A tool', input_schema: {} }],
      },
    ]);

    // When: Load servers
    const { result } = renderHook(() => useMcpServers());

    await act(async () => {
      await result.current.loadServers();
    });

    // Then: Servers loaded
    expect(result.current.servers).toHaveLength(1);
    expect(result.current.servers[0].name).toBe('Test Server');
    expect(result.current.loading).toBe(false);
  });

  it('should set loading state during loadServers()', async () => {
    // Given: Slow API
    let resolveApi: (value: any) => void;
    vi.spyOn(apiModule, 'listMcpServers').mockImplementation(
      () => new Promise(resolve => { resolveApi = resolve; })
    );

    const { result } = renderHook(() => useMcpServers());

    // When: Start loading
    let loadPromise: Promise<void>;
    act(() => {
      loadPromise = result.current.loadServers();
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

  it('should handle loadServers error', async () => {
    // Given: API fails
    vi.spyOn(apiModule, 'listMcpServers').mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useMcpServers());

    // When: Load servers fails
    await act(async () => {
      await result.current.loadServers();
    });

    // Then: Error state set
    expect(result.current.error).toBe('Network error');
    expect(result.current.servers).toEqual([]);
    expect(result.current.loading).toBe(false);
  });

  it('should add server via addServer()', async () => {
    // Given: Register API succeeds, list refreshes
    vi.spyOn(apiModule, 'registerMcpServer').mockResolvedValue({
      id: 'srv-new',
      name: 'New Server',
      url: 'http://localhost:9001/mcp',
      enabled: true,
      registered_at: '2026-01-30T00:00:00Z',
    });
    vi.spyOn(apiModule, 'listMcpServers').mockResolvedValue([
      {
        id: 'srv-new',
        name: 'New Server',
        url: 'http://localhost:9001/mcp',
        enabled: true,
        registered_at: '2026-01-30T00:00:00Z',
      },
    ]);

    const { result } = renderHook(() => useMcpServers());

    // When: Add server
    await act(async () => {
      await result.current.addServer('http://localhost:9001/mcp', 'New Server');
    });

    // Then: registerMcpServer called and list refreshed
    expect(apiModule.registerMcpServer).toHaveBeenCalledWith('http://localhost:9001/mcp', 'New Server');
    expect(result.current.servers).toHaveLength(1);
    expect(result.current.servers[0].id).toBe('srv-new');
  });

  it('should remove server via removeServer()', async () => {
    // Given: Existing server
    vi.spyOn(apiModule, 'listMcpServers')
      .mockResolvedValueOnce([
        { id: 'srv-1', name: 'S1', url: 'http://a', enabled: true, registered_at: '' },
      ])
      .mockResolvedValueOnce([]);
    vi.spyOn(apiModule, 'removeMcpServer').mockResolvedValue(undefined);

    const { result } = renderHook(() => useMcpServers());

    // Load initial servers
    await act(async () => {
      await result.current.loadServers();
    });
    expect(result.current.servers).toHaveLength(1);

    // When: Remove server
    await act(async () => {
      await result.current.removeServer('srv-1');
    });

    // Then: removeMcpServer called and list refreshed
    expect(apiModule.removeMcpServer).toHaveBeenCalledWith('srv-1');
    expect(result.current.servers).toHaveLength(0);
  });

  it('should handle addServer error', async () => {
    // Given: Register fails
    vi.spyOn(apiModule, 'registerMcpServer').mockRejectedValue(new Error('Connection refused'));

    const { result } = renderHook(() => useMcpServers());

    // When: Add server fails
    await act(async () => {
      await result.current.addServer('http://bad-server/mcp');
    });

    // Then: Error state set
    expect(result.current.error).toBe('Connection refused');
  });
});
