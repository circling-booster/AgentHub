/**
 * Background Service Worker handler functions
 *
 * Separated for testability (unit tests can import and test these directly)
 */

import { STORAGE_KEYS } from './constants';
import { createGetPageContext, isGetPageContextResponse } from './content-messaging';
import type { PageContext } from './types';

// ==================== Token Handshake ====================

export async function initializeAuth(extensionId: string): Promise<boolean> {
  try {
    const response = await fetch('http://localhost:8000/auth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ extension_id: extensionId }),
    });

    if (!response.ok) {
      return false;
    }

    const { token } = await response.json();

    // Save to session storage
    await browser.storage.session.set({ [STORAGE_KEYS.EXTENSION_TOKEN]: token });

    return true;
  } catch (error) {
    return false;
  }
}

// ==================== Offscreen Document Lifecycle ====================

export async function ensureOffscreenDocument(documentPath: string): Promise<void> {
  // Check for existing offscreen document
  const existingContexts = await browser.runtime.getContexts({
    contextTypes: ['OFFSCREEN_DOCUMENT' as any],
  });

  if (existingContexts.length > 0) {
    return; // Already exists
  }

  // Create new offscreen document
  await browser.offscreen.createDocument({
    url: documentPath,
    reasons: ['WORKERS' as any],
    justification: 'Handle long-running LLM API requests that exceed Service Worker timeout',
  });

  // Wait for document to load and register its message listener
  await new Promise((resolve) => setTimeout(resolve, 200));
}

// ==================== Health Check ====================

export async function checkServerHealth(): Promise<{
  isHealthy: boolean;
  shouldRetryAuth: boolean;
}> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch('http://localhost:8000/health', {
      method: 'GET',
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    const isHealthy = response.ok;

    // Get previous health status
    const stored = await browser.storage.local.get(STORAGE_KEYS.SERVER_HEALTH);
    const previousHealth = stored[STORAGE_KEYS.SERVER_HEALTH] as
      | { status: string; lastChecked: number }
      | undefined;

    // Save current status
    await browser.storage.local.set({
      [STORAGE_KEYS.SERVER_HEALTH]: {
        status: isHealthy ? 'healthy' : 'unhealthy',
        lastChecked: Date.now(),
      },
    });

    // Determine if should retry auth (server recovered)
    const shouldRetryAuth = previousHealth?.status === 'unhealthy' && isHealthy;

    return { isHealthy, shouldRetryAuth };
  } catch (error) {
    await browser.storage.local.set({
      [STORAGE_KEYS.SERVER_HEALTH]: {
        status: 'unhealthy',
        lastChecked: Date.now(),
      },
    });
    return { isHealthy: false, shouldRetryAuth: false };
  }
}

// ==================== Page Context Request ====================

/**
 * Request page context from the active tab's content script
 *
 * Returns null if:
 * - No active tab found
 * - Content script not loaded
 * - Content script returns error
 */
export async function requestPageContext(): Promise<PageContext | null> {
  try {
    // Get active tab
    const tabs = await browser.tabs.query({ active: true, currentWindow: true });
    if (tabs.length === 0 || !tabs[0].id) {
      return null;
    }

    const tabId = tabs[0].id;

    // Send message to content script
    const response = await browser.tabs.sendMessage(tabId, createGetPageContext());

    // Validate response
    if (!isGetPageContextResponse(response)) {
      return null;
    }

    if (!response.success || !response.context) {
      return null;
    }

    return response.context;
  } catch (error) {
    // Content script not loaded or tab closed
    console.warn('[Background] Failed to request page context:', error);
    return null;
  }
}
