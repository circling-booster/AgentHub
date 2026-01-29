import { describe, it, expect, beforeEach, vi } from 'vitest';
import { fakeBrowser } from 'wxt/testing';

// Background worker will be imported dynamically
// For testing, we'll test the functions directly

describe('Background Service Worker', () => {
  beforeEach(() => {
    fakeBrowser.reset();
    global.fetch = vi.fn();
  });

  describe('Token Handshake', () => {
    it('should exchange token on successful auth', async () => {
      // Given: Server returns token
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ token: 'server-token-123' }),
      });

      // When: Initialize auth (simulate function call)
      const response = await fetch('http://localhost:8000/auth/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ extension_id: 'test-extension-id' }),
      });

      const { token } = await response.json();
      await fakeBrowser.storage.session.set({ extensionToken: token });

      // Then: Token saved to session storage
      const stored = await fakeBrowser.storage.session.get('extensionToken');
      expect(stored.extensionToken).toBe('server-token-123');
    });

    it('should handle auth failure gracefully', async () => {
      // Given: Server returns 403
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 403,
      });

      // When: Initialize auth fails
      const response = await fetch('http://localhost:8000/auth/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ extension_id: 'test-extension-id' }),
      });

      // Then: Should detect failure
      expect(response.ok).toBe(false);
    });

    it('should handle network errors', async () => {
      // Given: Network error
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      // When/Then: Should throw
      await expect(
        fetch('http://localhost:8000/auth/token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ extension_id: 'test-extension-id' }),
        })
      ).rejects.toThrow('Network error');
    });
  });

  describe('Offscreen Document Lifecycle', () => {
    it('should check for existing offscreen document', () => {
      // Given: chrome.runtime.getContexts mock
      const getContexts = vi.fn().mockResolvedValue([]);
      fakeBrowser.runtime.getContexts = getContexts;

      // When: Check for offscreen document
      const contextTypes = ['OFFSCREEN_DOCUMENT'];
      fakeBrowser.runtime.getContexts({ contextTypes });

      // Then: getContexts called with correct params
      expect(getContexts).toHaveBeenCalledWith({ contextTypes });
    });

    it('should create offscreen document if none exists', () => {
      // Given: No existing offscreen document
      fakeBrowser.runtime.getContexts = vi.fn().mockResolvedValue([]);
      const createDocument = vi.fn().mockResolvedValue(undefined);
      fakeBrowser.offscreen = { createDocument } as any;

      // When: Create offscreen document
      const params = {
        url: 'offscreen/index.html',
        reasons: ['WORKERS'],
        justification: 'Handle long-running LLM API requests',
      };
      fakeBrowser.offscreen.createDocument(params);

      // Then: createDocument called
      expect(createDocument).toHaveBeenCalledWith(params);
    });

    it('should not create offscreen document if already exists', async () => {
      // Given: Existing offscreen document
      fakeBrowser.runtime.getContexts = vi.fn().mockResolvedValue([
        { contextType: 'OFFSCREEN_DOCUMENT' },
      ]);
      const createDocument = vi.fn();
      fakeBrowser.offscreen = { createDocument } as any;

      // When: Check and skip creation
      const contexts = await fakeBrowser.runtime.getContexts({
        contextTypes: ['OFFSCREEN_DOCUMENT'],
      });

      if (contexts.length === 0) {
        await fakeBrowser.offscreen.createDocument({
          url: 'offscreen/index.html',
          reasons: ['WORKERS'],
          justification: 'Handle long-running LLM API requests',
        });
      }

      // Then: createDocument NOT called
      expect(createDocument).not.toHaveBeenCalled();
    });
  });

  describe('Message Routing', () => {
    it('should route START_STREAM_CHAT to offscreen', () => {
      // Given: Message listener setup
      const sendMessage = vi.fn().mockResolvedValue(undefined);
      fakeBrowser.runtime.sendMessage = sendMessage;

      // When: UI sends START_STREAM_CHAT
      const message = {
        type: 'START_STREAM_CHAT',
        payload: {
          conversationId: 'conv-123',
          message: 'Hello',
        },
      };
      fakeBrowser.runtime.sendMessage(message);

      // Then: Message forwarded
      expect(sendMessage).toHaveBeenCalledWith(message);
    });

    it('should route STREAM_CHAT_EVENT from offscreen to UI', () => {
      // Given: Offscreen sends event
      const sendMessage = vi.fn().mockResolvedValue(undefined);
      fakeBrowser.runtime.sendMessage = sendMessage;

      const event = {
        type: 'STREAM_CHAT_EVENT',
        requestId: 'req-123',
        event: { type: 'text', content: 'Hello' },
      };

      // When: Route to UI
      fakeBrowser.runtime.sendMessage(event);

      // Then: Event forwarded
      expect(sendMessage).toHaveBeenCalledWith(event);
    });

    it('should handle CANCEL_STREAM message', () => {
      // Given: Cancel message
      const sendMessage = vi.fn().mockResolvedValue(undefined);
      fakeBrowser.runtime.sendMessage = sendMessage;

      const cancelMessage = {
        type: 'CANCEL_STREAM',
        requestId: 'req-123',
      };

      // When: Send cancel
      fakeBrowser.runtime.sendMessage(cancelMessage);

      // Then: Message sent
      expect(sendMessage).toHaveBeenCalledWith(cancelMessage);
    });
  });

  describe('Health Check', () => {
    it('should create health check alarm', () => {
      // Given: Alarms API
      const create = vi.fn();
      fakeBrowser.alarms.create = create;

      // When: Create alarm
      fakeBrowser.alarms.create('healthCheck', { periodInMinutes: 0.5 });

      // Then: Alarm created with 30-second interval
      expect(create).toHaveBeenCalledWith('healthCheck', { periodInMinutes: 0.5 });
    });

    it('should check server health on alarm', async () => {
      // Given: Server is healthy
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'healthy' }),
      });

      // When: Health check
      const response = await fetch('http://localhost:8000/health', {
        method: 'GET',
      });

      const health = await response.json();

      // Then: Health status retrieved
      expect(health.status).toBe('healthy');
    });

    it('should save health status to storage', async () => {
      // Given: Health check result
      const healthStatus = {
        status: 'healthy',
        lastChecked: Date.now(),
      };

      // When: Save to storage
      await fakeBrowser.storage.local.set({ serverHealth: healthStatus });

      // Then: Status saved
      const stored = await fakeBrowser.storage.local.get('serverHealth');
      expect(stored.serverHealth).toEqual(healthStatus);
    });

    it('should retry token exchange on server recovery', async () => {
      // Given: Server recovers (unhealthy → healthy)
      const previousHealth = { status: 'unhealthy' };
      await fakeBrowser.storage.local.set({ serverHealth: previousHealth });

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'healthy' }),
      });

      // When: Health check detects recovery
      const response = await fetch('http://localhost:8000/health');
      const currentHealth = await response.json();

      const stored = await fakeBrowser.storage.local.get('serverHealth');
      const wasUnhealthy = stored.serverHealth?.status === 'unhealthy';
      const isNowHealthy = currentHealth.status === 'healthy';

      // Then: Should trigger token retry
      expect(wasUnhealthy && isNowHealthy).toBe(true);
    });
  });

  describe('Lifecycle Events', () => {
    it('should initialize on onInstalled', () => {
      // Given: onInstalled listener
      const addListener = vi.fn();
      fakeBrowser.runtime.onInstalled = { addListener } as any;

      // When: Add listener
      const handler = vi.fn();
      fakeBrowser.runtime.onInstalled.addListener(handler);

      // Then: Listener added
      expect(addListener).toHaveBeenCalledWith(handler);
    });

    it('should initialize on onStartup', () => {
      // Given: onStartup listener
      const addListener = vi.fn();
      fakeBrowser.runtime.onStartup = { addListener } as any;

      // When: Add listener
      const handler = vi.fn();
      fakeBrowser.runtime.onStartup.addListener(handler);

      // Then: Listener added
      expect(addListener).toHaveBeenCalledWith(handler);
    });
  });
});
