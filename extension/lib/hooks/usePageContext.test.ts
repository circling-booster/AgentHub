/**
 * Tests for usePageContext hook
 * Phase 5 Part C - Frontend Page Context Toggle
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { usePageContext } from './usePageContext';
import * as backgroundHandlers from '../background-handlers';
import type { PageContext } from '../types';

// Mock background-handlers module
vi.mock('../background-handlers', () => ({
  requestPageContext: vi.fn(),
}));

describe('usePageContext', () => {
  const mockPageContext: PageContext = {
    url: 'https://example.com',
    title: 'Example Page',
    selectedText: 'selected text',
    metaDescription: 'description',
    mainContent: 'main content',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with disabled state and no context', () => {
    // When
    const { result } = renderHook(() => usePageContext());

    // Then
    expect(result.current.enabled).toBe(false);
    expect(result.current.context).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('should toggle enabled state', () => {
    // Given
    const { result } = renderHook(() => usePageContext());

    // When
    act(() => {
      result.current.toggleEnabled();
    });

    // Then
    expect(result.current.enabled).toBe(true);

    // When - toggle again
    act(() => {
      result.current.toggleEnabled();
    });

    // Then
    expect(result.current.enabled).toBe(false);
  });

  it('should fetch context when enabled is toggled on', async () => {
    // Given
    vi.mocked(backgroundHandlers.requestPageContext).mockResolvedValue(mockPageContext);
    const { result } = renderHook(() => usePageContext());

    // When
    await act(async () => {
      result.current.toggleEnabled();
      // Wait for async effect
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    // Then
    expect(backgroundHandlers.requestPageContext).toHaveBeenCalledTimes(1);
    expect(result.current.context).toEqual(mockPageContext);
    expect(result.current.enabled).toBe(true);
  });

  it('should not fetch context when toggled off', async () => {
    // Given
    vi.mocked(backgroundHandlers.requestPageContext).mockResolvedValue(mockPageContext);
    const { result } = renderHook(() => usePageContext());

    // Enable first
    await act(async () => {
      result.current.toggleEnabled();
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    vi.clearAllMocks();

    // When - toggle off
    await act(async () => {
      result.current.toggleEnabled();
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    // Then
    expect(backgroundHandlers.requestPageContext).not.toHaveBeenCalled();
    expect(result.current.enabled).toBe(false);
  });

  it('should manually fetch context via fetchContext', async () => {
    // Given
    vi.mocked(backgroundHandlers.requestPageContext).mockResolvedValue(mockPageContext);
    const { result } = renderHook(() => usePageContext());

    // When
    await act(async () => {
      await result.current.fetchContext();
    });

    // Then
    expect(backgroundHandlers.requestPageContext).toHaveBeenCalledTimes(1);
    expect(result.current.context).toEqual(mockPageContext);
  });

  it('should set loading state during fetch', async () => {
    // Given
    let resolveRequest: (value: PageContext) => void;
    const requestPromise = new Promise<PageContext>((resolve) => {
      resolveRequest = resolve;
    });
    vi.mocked(backgroundHandlers.requestPageContext).mockReturnValue(requestPromise);

    const { result } = renderHook(() => usePageContext());

    // When - start fetch
    act(() => {
      result.current.fetchContext();
    });

    // Then - loading should be true
    expect(result.current.loading).toBe(true);

    // When - complete fetch
    await act(async () => {
      resolveRequest!(mockPageContext);
      await requestPromise;
    });

    // Then - loading should be false
    expect(result.current.loading).toBe(false);
    expect(result.current.context).toEqual(mockPageContext);
  });

  it('should handle fetch failure gracefully', async () => {
    // Given
    vi.mocked(backgroundHandlers.requestPageContext).mockResolvedValue(null);
    const { result } = renderHook(() => usePageContext());

    // When
    await act(async () => {
      await result.current.fetchContext();
    });

    // Then
    expect(result.current.context).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('should clear context when disabled', async () => {
    // Given
    vi.mocked(backgroundHandlers.requestPageContext).mockResolvedValue(mockPageContext);
    const { result } = renderHook(() => usePageContext());

    // Enable and fetch
    await act(async () => {
      result.current.toggleEnabled();
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    expect(result.current.context).toEqual(mockPageContext);

    // When - disable
    await act(async () => {
      result.current.toggleEnabled();
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    // Then - context should be cleared
    expect(result.current.context).toBeNull();
  });
});
