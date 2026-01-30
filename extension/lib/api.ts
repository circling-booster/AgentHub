/**
 * REST API client with Token Handshake authentication
 *
 * Security: All /api/* requests include X-Extension-Token header
 */

import { API_BASE, STORAGE_KEYS } from './constants';
import type { Conversation, McpServer, HealthStatus } from './types';

/**
 * Initialize authentication with server (Token Handshake)
 *
 * @returns true if successful, false otherwise
 */
export async function initializeAuth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ extension_id: chrome.runtime.id }),
    });

    if (!response.ok) {
      return false;
    }

    const { token } = await response.json();
    await chrome.storage.session.set({ [STORAGE_KEYS.EXTENSION_TOKEN]: token });
    return true;
  } catch {
    return false;
  }
}

/**
 * Authenticated fetch wrapper
 *
 * Automatically injects X-Extension-Token header from session storage
 *
 * @param path - API path (e.g., "/api/conversations")
 * @param options - Fetch options
 * @throws Error if not authenticated
 */
export async function authenticatedFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  // Load token from session storage
  const stored = await chrome.storage.session.get(STORAGE_KEYS.EXTENSION_TOKEN);
  const token = stored[STORAGE_KEYS.EXTENSION_TOKEN];

  if (!token) {
    throw new Error('Not authenticated. Server may not be running.');
  }

  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...options.headers,
      'X-Extension-Token': token,
      'Content-Type': 'application/json',
    },
  });
}

/**
 * Get server health status (no auth required)
 */
export async function getServerHealth(): Promise<HealthStatus> {
  try {
    const response = await fetch(`${API_BASE}/health`, {
      method: 'GET',
    });

    if (response.ok) {
      return await response.json();
    }

    return { status: 'unhealthy' };
  } catch {
    return { status: 'unhealthy' };
  }
}

/**
 * List conversations (authenticated)
 */
export async function listConversations(limit: number = 20): Promise<Conversation[]> {
  const response = await authenticatedFetch(`/api/conversations?limit=${limit}`);

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Create conversation (authenticated)
 */
export async function createConversation(title: string = ''): Promise<Conversation> {
  const response = await authenticatedFetch('/api/conversations', {
    method: 'POST',
    body: JSON.stringify({ title }),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Register MCP server (authenticated)
 */
export async function registerMcpServer(url: string, name?: string): Promise<McpServer> {
  const response = await authenticatedFetch('/api/mcp/servers', {
    method: 'POST',
    body: JSON.stringify({ url, name }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to register MCP server');
  }

  return response.json();
}

/**
 * List MCP servers (authenticated)
 */
export async function listMcpServers(): Promise<McpServer[]> {
  const response = await authenticatedFetch('/api/mcp/servers');

  if (!response.ok) {
    throw new Error('Failed to list MCP servers');
  }

  return response.json();
}

/**
 * Remove MCP server (authenticated)
 */
export async function removeMcpServer(serverId: string): Promise<void> {
  const response = await authenticatedFetch(`/api/mcp/servers/${serverId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to remove MCP server');
  }
}

/**
 * Get tools from a specific MCP server (authenticated)
 */
export async function getServerTools(serverId: string): Promise<import('./types').Tool[]> {
  const response = await authenticatedFetch(`/api/mcp/servers/${serverId}/tools`);

  if (!response.ok) {
    throw new Error('Failed to get server tools');
  }

  return response.json();
}

/**
 * Register A2A agent (authenticated)
 */
export async function registerA2aAgent(url: string, name?: string): Promise<import('./types').A2aAgent> {
  const response = await authenticatedFetch('/api/a2a/agents', {
    method: 'POST',
    body: JSON.stringify({ url, name }),
  });

  if (!response.ok) {
    throw new Error('Failed to register A2A agent');
  }

  return response.json();
}

/**
 * List all registered A2A agents (authenticated)
 */
export async function listA2aAgents(): Promise<import('./types').A2aAgent[]> {
  const response = await authenticatedFetch('/api/a2a/agents');

  if (!response.ok) {
    throw new Error('Failed to list A2A agents');
  }

  return response.json();
}

/**
 * Get a specific A2A agent by ID (authenticated)
 */
export async function getA2aAgent(agentId: string): Promise<import('./types').A2aAgent> {
  const response = await authenticatedFetch(`/api/a2a/agents/${agentId}`);

  if (!response.ok) {
    throw new Error('Failed to get A2A agent');
  }

  return response.json();
}

/**
 * Remove A2A agent (authenticated)
 */
export async function removeA2aAgent(agentId: string): Promise<void> {
  const response = await authenticatedFetch(`/api/a2a/agents/${agentId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to remove A2A agent');
  }
}
