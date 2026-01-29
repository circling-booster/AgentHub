/**
 * Background Service Worker
 *
 * Responsibilities:
 * 1. Token Handshake with server
 * 2. Offscreen Document lifecycle management
 * 3. Message routing (UI ↔ Background ↔ Offscreen)
 * 4. Health Check (30-second interval)
 */

import { STORAGE_KEYS, HEALTH_CHECK_INTERVAL_MINUTES, OFFSCREEN_DOCUMENT_PATH } from '../lib/constants';
import type { ExtensionMessage } from '../lib/messaging';
import { MessageType } from '../lib/messaging';
import { initializeAuth, ensureOffscreenDocument, checkServerHealth } from '../lib/background-handlers';

export default defineBackground(() => {
  // Active stream tracking
  const activeStreams = new Map<string, AbortController>();

  // ==================== Message Routing ====================

  browser.runtime.onMessage.addListener((message: ExtensionMessage, sender, sendResponse) => {
    // UI → Background → Offscreen: Start stream
    if (message.type === MessageType.START_STREAM_CHAT) {
      handleStartStreamChat(message.payload)
        .then(() => sendResponse({ received: true }))
        .catch((error) => sendResponse({ error: error.message }));
      return true; // Keep channel open for async
    }

    // Offscreen → Background → UI: Stream events
    if (
      message.type === MessageType.STREAM_CHAT_EVENT ||
      message.type === MessageType.STREAM_CHAT_DONE ||
      message.type === MessageType.STREAM_CHAT_ERROR
    ) {
      // Forward to UI (broadcast to all tabs)
      broadcastToUI(message);
      return false;
    }

    // UI → Background → Offscreen: Cancel stream
    if (message.type === MessageType.CANCEL_STREAM) {
      handleCancelStream(message.requestId);
      sendResponse({ cancelled: true });
      return false;
    }

    return false;
  });

  async function handleStartStreamChat(payload: { conversationId: string | null; message: string }) {
    const requestId = crypto.randomUUID();

    // Ensure offscreen document exists
    await ensureOffscreenDocument(OFFSCREEN_DOCUMENT_PATH);

    // Create abort controller for this stream
    const controller = new AbortController();
    activeStreams.set(requestId, controller);

    // Forward to offscreen document
    await browser.runtime.sendMessage({
      type: MessageType.STREAM_CHAT,
      payload: {
        ...payload,
        requestId,
      },
    });
  }

  function handleCancelStream(requestId: string) {
    const controller = activeStreams.get(requestId);
    if (controller) {
      controller.abort();
      activeStreams.delete(requestId);

      // Forward cancel to offscreen
      browser.runtime.sendMessage({
        type: MessageType.CANCEL_STREAM,
        requestId,
      });
    }
  }

  function broadcastToUI(message: ExtensionMessage) {
    // Send to all extension contexts (popup, sidepanel, etc.)
    browser.runtime.sendMessage(message).catch(() => {
      // UI may not be open, ignore error
    });
  }

  // ==================== Health Check Alarm ====================

  browser.alarms.create('healthCheck', {
    periodInMinutes: HEALTH_CHECK_INTERVAL_MINUTES,
  });

  browser.alarms.onAlarm.addListener(async (alarm) => {
    if (alarm.name === 'healthCheck') {
      const { isHealthy, shouldRetryAuth } = await checkServerHealth();

      if (shouldRetryAuth) {
        console.log('[Background] Server recovered, retrying token exchange');
        await initializeAuth(browser.runtime.id);
      }
    }
  });

  // ==================== Lifecycle Events ====================

  browser.runtime.onInstalled.addListener(async () => {
    console.log('[Background] Extension installed');
    await checkServerHealth();
    await initializeAuth(browser.runtime.id);
  });

  browser.runtime.onStartup.addListener(async () => {
    console.log('[Background] Extension startup');
    const { isHealthy } = await checkServerHealth();
    if (isHealthy) {
      await initializeAuth(browser.runtime.id);
    }
  });

  console.log('[Background] Service Worker initialized');
});
