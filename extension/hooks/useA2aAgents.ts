/**
 * A2A agent management hook
 *
 * Provides CRUD operations for A2A agents via authenticated API calls.
 */

import { useState, useCallback } from 'react';
import type { A2aAgent } from '../lib/types';
import { listA2aAgents, registerA2aAgent, removeA2aAgent } from '../lib/api';

interface A2aAgentsState {
  agents: A2aAgent[];
  loading: boolean;
  error: string | null;
  loadAgents: () => Promise<void>;
  addAgent: (url: string, name?: string) => Promise<void>;
  removeAgent: (agentId: string) => Promise<void>;
}

export function useA2aAgents(): A2aAgentsState {
  const [agents, setAgents] = useState<A2aAgent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAgents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listA2aAgents();
      setAgents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load agents');
    } finally {
      setLoading(false);
    }
  }, []);

  const addAgent = useCallback(async (url: string, name?: string) => {
    setError(null);
    try {
      await registerA2aAgent(url, name);
      await loadAgents();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add agent');
    }
  }, [loadAgents]);

  const removeAgent = useCallback(async (agentId: string) => {
    setError(null);
    try {
      await removeA2aAgent(agentId);
      await loadAgents();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove agent');
    }
  }, [loadAgents]);

  return {
    agents,
    loading,
    error,
    loadAgents,
    addAgent,
    removeAgent,
  };
}
