import { describe, it, expect, beforeEach, vi } from 'vitest';
import { fakeBrowser } from 'wxt/testing';
import {
  initializeAuth,
  authenticatedFetch,
  getServerHealth,
  listConversations,
  createConversation,
  registerMcpServer,
  listMcpServers,
  removeMcpServer,
  getServerTools,
  registerA2aAgent,
  listA2aAgents,
  getA2aAgent,
  removeA2aAgent,
} from '../../lib/api';
import { STORAGE_KEYS } from '../../lib/constants';

describe('API Client', () => {
  beforeEach(() => {
    // Reset fakeBrowser state
    fakeBrowser.reset();
    // Reset fetch mock
    global.fetch = vi.fn();
  });

  describe('initializeAuth', () => {
    it('should exchange token successfully', async () => {
      // Given: Server returns token
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ token: 'server-token-123' }),
      });

      // When: Call initializeAuth
      const result = await initializeAuth();

      // Then: Token exchanged and saved
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/auth/token',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('extension_id'),
        })
      );
      expect(result).toBe(true);

      // Verify token saved to session storage
      const stored = await fakeBrowser.storage.session.get(STORAGE_KEYS.EXTENSION_TOKEN);
      expect(stored[STORAGE_KEYS.EXTENSION_TOKEN]).toBe('server-token-123');
    });

    it('should return false on server error', async () => {
      // Given: Server returns 403
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 403,
      });

      // When: Call initializeAuth
      const result = await initializeAuth();

      // Then: Returns false
      expect(result).toBe(false);
    });

    it('should return false on network error', async () => {
      // Given: Network error
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      // When: Call initializeAuth
      const result = await initializeAuth();

      // Then: Returns false
      expect(result).toBe(false);
    });
  });

  describe('authenticatedFetch', () => {
    it('should include X-Extension-Token header from session storage', async () => {
      // Given: Token stored in session
      await fakeBrowser.storage.session.set({ [STORAGE_KEYS.EXTENSION_TOKEN]: 'stored-token' });
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ([]),
      });

      // When: Call authenticatedFetch
      await authenticatedFetch('/api/conversations');

      // Then: Fetch called with token header
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/conversations',
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-Extension-Token': 'stored-token',
          }),
        })
      );
    });

    it('should throw error if no token available', async () => {
      // Given: No token in session storage
      // When/Then: Should throw
      await expect(authenticatedFetch('/api/test')).rejects.toThrow('Not authenticated');
    });

    it('should use provided options', async () => {
      // Given: Token available
      await fakeBrowser.storage.session.set({ [STORAGE_KEYS.EXTENSION_TOKEN]: 'token' });
      (global.fetch as any).mockResolvedValueOnce({ ok: true });

      // When: Call with POST method
      await authenticatedFetch('/api/test', {
        method: 'POST',
        body: JSON.stringify({ data: 'test' }),
      });

      // Then: Options merged correctly
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/test',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ data: 'test' }),
        })
      );
    });
  });

  describe('getServerHealth', () => {
    it('should call /health endpoint without auth', async () => {
      // Given: Server is healthy
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'healthy' }),
      });

      // When: Call getServerHealth
      const result = await getServerHealth();

      // Then: Returns healthy status
      expect(result.status).toBe('healthy');
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/health',
        expect.objectContaining({
          method: 'GET',
        })
      );
    });

    it('should return unhealthy on server error', async () => {
      // Given: Server error
      (global.fetch as any).mockResolvedValueOnce({ ok: false });

      // When: Call getServerHealth
      const result = await getServerHealth();

      // Then: Returns unhealthy
      expect(result.status).toBe('unhealthy');
    });

    it('should return unhealthy on network error', async () => {
      // Given: Network error
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      // When: Call getServerHealth
      const result = await getServerHealth();

      // Then: Returns unhealthy
      expect(result.status).toBe('unhealthy');
    });
  });

  describe('listConversations', () => {
    it('should call GET /api/conversations with auth', async () => {
      // Given: Token available, server returns conversations
      await fakeBrowser.storage.session.set({ [STORAGE_KEYS.EXTENSION_TOKEN]: 'token' });
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ([
          { id: 'conv-1', title: 'Test', created_at: '2026-01-30T00:00:00Z' },
        ]),
      });

      // When: Call listConversations
      const result = await listConversations();

      // Then: Returns conversations
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('conv-1');
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/conversations?limit=20',
        expect.any(Object)
      );
    });

    it('should support custom limit parameter', async () => {
      // Given: Token available
      await fakeBrowser.storage.session.set({ [STORAGE_KEYS.EXTENSION_TOKEN]: 'token' });
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ([]),
      });

      // When: Call with limit=10
      await listConversations(10);

      // Then: URL includes limit=10
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/conversations?limit=10',
        expect.any(Object)
      );
    });
  });

  describe('createConversation', () => {
    it('should call POST /api/conversations with auth', async () => {
      // Given: Token available
      await fakeBrowser.storage.session.set({ [STORAGE_KEYS.EXTENSION_TOKEN]: 'token' });
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 'new-conv', title: 'New', created_at: '2026-01-30T00:00:00Z' }),
      });

      // When: Create conversation
      const result = await createConversation('New Conversation');

      // Then: POST with title
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/conversations',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ title: 'New Conversation' }),
        })
      );
      expect(result.id).toBe('new-conv');
    });
  });

  describe('MCP Server Management', () => {
    beforeEach(async () => {
      await fakeBrowser.storage.session.set({ [STORAGE_KEYS.EXTENSION_TOKEN]: 'token' });
    });

    it('registerMcpServer should POST to /api/mcp/servers', async () => {
      // Given: Server accepts registration
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 'mcp-1',
          url: 'http://localhost:9000/mcp',
          name: 'Test MCP',
          enabled: true,
          registered_at: '2026-01-30T00:00:00Z',
        }),
      });

      // When: Register MCP server
      const result = await registerMcpServer('http://localhost:9000/mcp', 'Test MCP');

      // Then: Correct endpoint called
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/mcp/servers',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ url: 'http://localhost:9000/mcp', name: 'Test MCP', auth: undefined }),
        })
      );
      expect(result.id).toBe('mcp-1');
    });

    it('registerMcpServer should send API Key auth config (Phase 5-B Step 7)', async () => {
      // Given: Server accepts registration with auth
      const authConfig = {
        auth_type: 'api_key' as const,
        api_key: 'test-key-1',
        api_key_header: 'X-API-Key',
        api_key_prefix: '',
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 'mcp-2',
          url: 'http://localhost:9001/mcp',
          name: 'Auth MCP Server',
          enabled: true,
          registered_at: '2026-02-01T00:00:00Z',
        }),
      });

      // When: Register MCP server with API Key auth
      const result = await registerMcpServer('http://localhost:9001/mcp', 'Auth MCP Server', authConfig);

      // Then: Auth config sent to server
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/mcp/servers',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            url: 'http://localhost:9001/mcp',
            name: 'Auth MCP Server',
            auth: authConfig,
          }),
        })
      );
      expect(result.id).toBe('mcp-2');
    });

    it('registerMcpServer should send custom headers auth config (Phase 5-B Step 7)', async () => {
      // Given: Server accepts registration with custom headers
      const authConfig = {
        auth_type: 'header' as const,
        headers: {
          'X-Custom-Auth': 'custom-token',
          'X-User-Id': 'user-123',
        },
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 'mcp-3',
          url: 'http://localhost:9000/mcp',
          name: 'Custom Header MCP',
          enabled: true,
          registered_at: '2026-02-01T00:00:00Z',
        }),
      });

      // When: Register MCP server with custom headers
      const result = await registerMcpServer('http://localhost:9000/mcp', 'Custom Header MCP', authConfig);

      // Then: Auth config sent to server
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/mcp/servers',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            url: 'http://localhost:9000/mcp',
            name: 'Custom Header MCP',
            auth: authConfig,
          }),
        })
      );
      expect(result.id).toBe('mcp-3');
    });

    it('listMcpServers should GET /api/mcp/servers', async () => {
      // Given: Server returns MCP servers
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ([{ id: 'mcp-1', url: 'http://localhost:9000/mcp' }]),
      });

      // When: List servers
      const result = await listMcpServers();

      // Then: Returns servers
      expect(result).toHaveLength(1);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/mcp/servers',
        expect.any(Object)
      );
    });

    it('removeMcpServer should DELETE /api/mcp/servers/:id', async () => {
      // Given: Server accepts deletion
      (global.fetch as any).mockResolvedValueOnce({ ok: true });

      // When: Remove server
      await removeMcpServer('mcp-1');

      // Then: DELETE called
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/mcp/servers/mcp-1',
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });

    it('getServerTools should GET /api/mcp/servers/:id/tools', async () => {
      // Given: Server returns tools for a specific server
      const mockTools = [
        {
          name: 'echo',
          description: 'Echo tool',
          input_schema: { type: 'object', properties: {} },
        },
        {
          name: 'search',
          description: 'Search tool',
          input_schema: { type: 'object', properties: { query: { type: 'string' } } },
        },
      ];
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockTools,
      });

      // When: Get tools for server mcp-1
      const result = await getServerTools('mcp-1');

      // Then: Returns tools array
      expect(result).toHaveLength(2);
      expect(result[0].name).toBe('echo');
      expect(result[1].name).toBe('search');
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/mcp/servers/mcp-1/tools',
        expect.any(Object)
      );
    });

    it('getServerTools should throw on HTTP error', async () => {
      // Given: Server returns error
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      });

      // When/Then: Should throw
      await expect(getServerTools('invalid-id')).rejects.toThrow('Failed to get server tools');
    });
  });

  describe('A2A Agent API', () => {
    beforeEach(async () => {
      await fakeBrowser.storage.session.set({ [STORAGE_KEYS.EXTENSION_TOKEN]: 'token' });
    });

    it('registerA2aAgent should POST to /api/a2a/agents', async () => {
      // Given: Server accepts registration
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 'a2a-1',
          url: 'http://localhost:9001',
          name: 'Test A2A Agent',
          type: 'a2a',
          enabled: true,
          agent_card: null,
          registered_at: '2026-01-30T00:00:00Z',
        }),
      });

      // When: Register A2A agent
      const result = await registerA2aAgent('http://localhost:9001', 'Test A2A Agent');

      // Then: Correct endpoint called
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/a2a/agents',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ url: 'http://localhost:9001', name: 'Test A2A Agent' }),
        })
      );
      expect(result.id).toBe('a2a-1');
    });

    it('listA2aAgents should GET /api/a2a/agents', async () => {
      // Given: Server returns A2A agents
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ([
          { id: 'a2a-1', url: 'http://localhost:9001', type: 'a2a' },
        ]),
      });

      // When: List agents
      const result = await listA2aAgents();

      // Then: Returns agents
      expect(result).toHaveLength(1);
      expect(result[0].type).toBe('a2a');
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/a2a/agents',
        expect.any(Object)
      );
    });

    it('getA2aAgent should GET /api/a2a/agents/:id', async () => {
      // Given: Server returns agent
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 'a2a-1',
          url: 'http://localhost:9001',
          name: 'Test Agent',
          type: 'a2a',
          enabled: true,
          agent_card: { name: 'TestAgent' },
          registered_at: '2026-01-30T00:00:00Z',
        }),
      });

      // When: Get agent
      const result = await getA2aAgent('a2a-1');

      // Then: Returns agent details
      expect(result.id).toBe('a2a-1');
      expect(result.agent_card).toEqual({ name: 'TestAgent' });
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/a2a/agents/a2a-1',
        expect.any(Object)
      );
    });

    it('removeA2aAgent should DELETE /api/a2a/agents/:id', async () => {
      // Given: Server accepts deletion
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
      });

      // When: Remove agent
      await removeA2aAgent('a2a-1');

      // Then: DELETE called
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/a2a/agents/a2a-1',
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });

    it('registerA2aAgent should throw on HTTP error', async () => {
      // Given: Server returns error
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 502,
        statusText: 'Bad Gateway',
      });

      // When/Then: Should throw
      await expect(registerA2aAgent('http://invalid-agent')).rejects.toThrow('Failed to register A2A agent');
    });
  });

  describe('Error Handling', () => {
    beforeEach(async () => {
      await fakeBrowser.storage.session.set({ [STORAGE_KEYS.EXTENSION_TOKEN]: 'token' });
    });

    it('should throw on HTTP error responses', async () => {
      // Given: Server returns 500
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      // When/Then: Should throw
      await expect(listConversations()).rejects.toThrow();
    });

    it('should throw on network errors', async () => {
      // Given: Network error
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      // When/Then: Should throw
      await expect(listConversations()).rejects.toThrow('Network error');
    });
  });
});
