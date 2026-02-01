/**
 * Content Script Entrypoint
 * Phase 5 Part C - Content Script
 *
 * Runs in the context of web pages to extract page context information.
 */
import { defineContentScript } from 'wxt/sandbox';
import { extractPageContext } from '@/lib/content-extract';
import { MessageType } from '@/lib/content-messaging';
import type { GetPageContextResponse } from '@/lib/content-messaging';

export default defineContentScript({
  matches: ['<all_urls>'],
  runAt: 'document_idle',

  main() {
    // Listen for page context requests from background script
    browser.runtime.onMessage.addListener((message, _sender, sendResponse) => {
      if (message.type === MessageType.GET_PAGE_CONTEXT) {
        try {
          const context = extractPageContext();
          const response: GetPageContextResponse = {
            success: true,
            context,
          };
          sendResponse(response);
        } catch (error) {
          console.error('[Content Script] Failed to extract page context:', error);
          const response: GetPageContextResponse = {
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error',
          };
          sendResponse(response);
        }
        return true; // Keep channel open for async response
      }
    });

    console.log('[Content Script] AgentHub content script loaded');
  },
});
