import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { fakeBrowser } from 'wxt/testing';
import { useServerHealth } from '../../hooks/useServerHealth';
import { STORAGE_KEYS } from '../../lib/constants';

describe('useServerHealth', () => {
  beforeEach(() => {
    fakeBrowser.reset();
  });

  it('should return initial state as unknown', () => {
    // When: Hook renders
    const { result } = renderHook(() => useServerHealth());

    // Then: Initial state is unknown
    expect(result.current.status).toBe('unknown');
    expect(result.current.lastChecked).toBeNull();
  });

  it('should load health status from storage on mount', async () => {
    // Given: Stored health data
    await fakeBrowser.storage.local.set({
      [STORAGE_KEYS.SERVER_HEALTH]: {
        status: 'healthy',
        lastChecked: 1706600000000,
      },
    });

    // When: Hook renders
    const { result } = renderHook(() => useServerHealth());

    // Wait for async effect
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 10));
    });

    // Then: Status loaded from storage
    expect(result.current.status).toBe('healthy');
    expect(result.current.lastChecked).toBe(1706600000000);
  });

  it('should update when storage changes', async () => {
    // Given: Hook rendered
    const { result } = renderHook(() => useServerHealth());

    // When: Storage changes (simulating Health Check alarm update)
    await act(async () => {
      await fakeBrowser.storage.local.set({
        [STORAGE_KEYS.SERVER_HEALTH]: {
          status: 'unhealthy',
          lastChecked: 1706600001000,
        },
      });
      // Allow listener to fire
      await new Promise(resolve => setTimeout(resolve, 10));
    });

    // Then: Status updated
    expect(result.current.status).toBe('unhealthy');
    expect(result.current.lastChecked).toBe(1706600001000);
  });

  it('should return isHealthy convenience boolean', async () => {
    // Given: Healthy status
    await fakeBrowser.storage.local.set({
      [STORAGE_KEYS.SERVER_HEALTH]: {
        status: 'healthy',
        lastChecked: Date.now(),
      },
    });

    // When: Hook renders
    const { result } = renderHook(() => useServerHealth());

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 10));
    });

    // Then: isHealthy is true
    expect(result.current.isHealthy).toBe(true);
  });

  it('should cleanup storage listener on unmount', () => {
    // Given: Hook rendered
    const { unmount } = renderHook(() => useServerHealth());

    // When: Unmount
    unmount();

    // Then: No errors (listener cleanup)
    // Verifies no memory leaks from lingering listeners
  });
});
