/**
 * Server health status hook
 *
 * Subscribes to chrome.storage.local changes for real-time health updates.
 * Background Service Worker writes health data via checkServerHealth().
 */

import { useState, useEffect } from 'react';
import { STORAGE_KEYS } from '../lib/constants';

interface ServerHealthState {
  status: 'healthy' | 'unhealthy' | 'unknown';
  lastChecked: number | null;
  isHealthy: boolean;
}

export function useServerHealth(): ServerHealthState {
  const [status, setStatus] = useState<'healthy' | 'unhealthy' | 'unknown'>('unknown');
  const [lastChecked, setLastChecked] = useState<number | null>(null);

  useEffect(() => {
    // Load initial state from storage
    browser.storage.local.get(STORAGE_KEYS.SERVER_HEALTH).then((stored) => {
      const health = stored[STORAGE_KEYS.SERVER_HEALTH];
      if (health) {
        setStatus(health.status);
        setLastChecked(health.lastChecked);
      }
    });

    // Subscribe to storage changes
    const listener = (
      changes: Record<string, { oldValue?: unknown; newValue?: unknown }>,
      areaName: string
    ) => {
      if (areaName === 'local' && changes[STORAGE_KEYS.SERVER_HEALTH]) {
        const newValue = changes[STORAGE_KEYS.SERVER_HEALTH].newValue as {
          status: 'healthy' | 'unhealthy';
          lastChecked: number;
        } | undefined;

        if (newValue) {
          setStatus(newValue.status);
          setLastChecked(newValue.lastChecked);
        }
      }
    };

    browser.storage.onChanged.addListener(listener);

    return () => {
      browser.storage.onChanged.removeListener(listener);
    };
  }, []);

  return {
    status,
    lastChecked,
    isHealthy: status === 'healthy',
  };
}
