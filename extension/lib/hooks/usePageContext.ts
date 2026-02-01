/**
 * usePageContext hook
 * Phase 5 Part C - Page Context Toggle
 *
 * Manages page context state and provides toggle functionality
 */
import { useState, useEffect, useCallback } from 'react';
import { requestPageContext } from '../background-handlers';
import type { PageContext } from '../types';

interface UsePageContextReturn {
  enabled: boolean;
  context: PageContext | null;
  loading: boolean;
  toggleEnabled: () => void;
  fetchContext: () => Promise<void>;
}

/**
 * Custom hook for managing page context state
 *
 * @returns {UsePageContextReturn} Page context state and controls
 */
export function usePageContext(): UsePageContextReturn {
  const [enabled, setEnabled] = useState(false);
  const [context, setContext] = useState<PageContext | null>(null);
  const [loading, setLoading] = useState(false);

  /**
   * Fetch page context from active tab
   */
  const fetchContext = useCallback(async () => {
    setLoading(true);
    try {
      const pageContext = await requestPageContext();
      setContext(pageContext);
    } catch (error) {
      console.error('[usePageContext] Failed to fetch context:', error);
      setContext(null);
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Toggle enabled state
   */
  const toggleEnabled = useCallback(() => {
    setEnabled((prev) => !prev);
  }, []);

  /**
   * Fetch context when enabled is toggled on
   * Clear context when toggled off
   */
  useEffect(() => {
    if (enabled) {
      fetchContext();
    } else {
      setContext(null);
    }
  }, [enabled, fetchContext]);

  return {
    enabled,
    context,
    loading,
    toggleEnabled,
    fetchContext,
  };
}
