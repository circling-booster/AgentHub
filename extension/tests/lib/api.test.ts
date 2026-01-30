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
          body: JSON.stringify({ url: 'http://localhost:9000/mcp', name: 'Test MCP' }),
        })
      );
      expect(result.id).toBe('mcp-1');
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
