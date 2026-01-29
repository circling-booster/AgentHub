/**
 * MCP server management hook
 *
 * Provides CRUD operations for MCP servers via authenticated API calls.
 */

import { useState, useCallback } from 'react';
import type { McpServer } from '../lib/types';
import { listMcpServers, registerMcpServer, removeMcpServer } from '../lib/api';

interface McpServersState {
  servers: McpServer[];
  loading: boolean;
  error: string | null;
  loadServers: () => Promise<void>;
  addServer: (url: string, name?: string) => Promise<void>;
  removeServer: (serverId: string) => Promise<void>;
}

export function useMcpServers(): McpServersState {
  const [servers, setServers] = useState<McpServer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadServers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listMcpServers();
      setServers(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load servers');
      setServers([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const addServer = useCallback(async (url: string, name?: string) => {
    setError(null);
    try {
      await registerMcpServer(url, name);
      await loadServers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add server');
    }
  }, [loadServers]);

  const removeServer = useCallback(async (serverId: string) => {
    setError(null);
    try {
      await removeMcpServer(serverId);
      await loadServers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove server');
    }
  }, [loadServers]);

  return {
    servers,
    loading,
    error,
    loadServers,
    addServer,
    removeServer,
  };
}
