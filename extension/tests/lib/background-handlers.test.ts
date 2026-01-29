import { describe, it, expect, beforeEach, vi } from 'vitest';
import { fakeBrowser } from 'wxt/testing';
import { initializeAuth, ensureOffscreenDocument, checkServerHealth } from '../../lib/background-handlers';
import { STORAGE_KEYS } from '../../lib/constants';

describe('Background Handlers', () => {
  beforeEach(() => {
    fakeBrowser.reset();
    global.fetch = vi.fn();
  });

  describe('initializeAuth', () => {
    it('should exchange token successfully', async () => {
      // Given: Server returns token
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ token: 'server-token-123' }),
      });

      // When: Initialize auth
      const result = await initializeAuth('test-extension-id');

      // Then: Token exchanged and saved
      expect(result).toBe(true);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/auth/token',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ extension_id: 'test-extension-id' }),
        })
      );

      const stored = await fakeBrowser.storage.session.get(STORAGE_KEYS.EXTENSION_TOKEN);
      expect(stored[STORAGE_KEYS.EXTENSION_TOKEN]).toBe('server-token-123');
    });

    it('should return false on HTTP error', async () => {
      // Given: Server returns 403
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 403,
      });

      // When: Initialize auth
      const result = await initializeAuth('test-extension-id');

      // Then: Returns false
      expect(result).toBe(false);
    });

    it('should return false on network error', async () => {
      // Given: Network error
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      // When: Initialize auth
      const result = await initializeAuth('test-extension-id');

      // Then: Returns false
      expect(result).toBe(false);
    });
  });

  describe('ensureOffscreenDocument', () => {
    it('should create offscreen document if none exists', async () => {
      // Given: No existing offscreen document
      fakeBrowser.runtime.getContexts = vi.fn().mockResolvedValue([]);
      const createDocument = vi.fn().mockResolvedValue(undefined);
      fakeBrowser.offscreen = { createDocument } as any;

      // When: Ensure offscreen document
      await ensureOffscreenDocument('offscreen/index.html');

      // Then: Document created
      expect(createDocument).toHaveBeenCalledWith({
        url: 'offscreen/index.html',
        reasons: ['WORKERS'],
        justification: 'Handle long-running LLM API requests that exceed Service Worker timeout',
      });
    });

    it('should not create if already exists', async () => {
      // Given: Existing offscreen document
      fakeBrowser.runtime.getContexts = vi.fn().mockResolvedValue([
        { contextType: 'OFFSCREEN_DOCUMENT' },
      ]);
      const createDocument = vi.fn();
      fakeBrowser.offscreen = { createDocument } as any;

      // When: Ensure offscreen document
      await ensureOffscreenDocument('offscreen/index.html');

      // Then: Document NOT created
      expect(createDocument).not.toHaveBeenCalled();
    });
  });

  describe('checkServerHealth', () => {
    it('should detect healthy server', async () => {
      // Given: Server is healthy
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'healthy' }),
      });

      // When: Check health
      const result = await checkServerHealth();

      // Then: Returns healthy status
      expect(result.isHealthy).toBe(true);
      expect(result.shouldRetryAuth).toBe(false);

      const stored = await fakeBrowser.storage.local.get(STORAGE_KEYS.SERVER_HEALTH);
      expect(stored[STORAGE_KEYS.SERVER_HEALTH].status).toBe('healthy');
    });

    it('should detect unhealthy server', async () => {
      // Given: Server error
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      // When: Check health
      const result = await checkServerHealth();

      // Then: Returns unhealthy status
      expect(result.isHealthy).toBe(false);
      expect(result.shouldRetryAuth).toBe(false);

      const stored = await fakeBrowser.storage.local.get(STORAGE_KEYS.SERVER_HEALTH);
      expect(stored[STORAGE_KEYS.SERVER_HEALTH].status).toBe('unhealthy');
    });

    it('should detect server recovery and signal auth retry', async () => {
      // Given: Previous unhealthy status
      await fakeBrowser.storage.local.set({
        [STORAGE_KEYS.SERVER_HEALTH]: { status: 'unhealthy', lastChecked: Date.now() },
      });

      // Server now healthy
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'healthy' }),
      });

      // When: Check health
      const result = await checkServerHealth();

      // Then: Signals auth retry needed
      expect(result.isHealthy).toBe(true);
      expect(result.shouldRetryAuth).toBe(true);
    });

    it('should timeout after 5 seconds', async () => {
      // Given: Fetch that rejects on abort
      (global.fetch as any).mockImplementationOnce(
        (_url: string, options: any) => {
          return new Promise((_resolve, reject) => {
            options.signal?.addEventListener('abort', () => {
              reject(new Error('AbortError'));
            });
          });
        }
      );

      // When: Check health (will abort after 5s)
      const result = await checkServerHealth();

      // Then: Returns unhealthy due to timeout
      expect(result.isHealthy).toBe(false);
      expect(result.shouldRetryAuth).toBe(false);
    }, 10000); // Extend test timeout to 10s
  });
});
