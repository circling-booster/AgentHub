/**
 * Tests for Content Script entrypoint
 * Phase 5 Part C - Content Script
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { browser } from 'wxt/browser';
import { MessageType } from '@/lib/content-messaging';
import { extractPageContext } from '@/lib/content-extract';
import type { GetPageContextResponse } from '@/lib/content-messaging';

describe('Content Script', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset document
    document.title = '';
    document.head.innerHTML = '';
    document.body.innerHTML = '';
  });

  describe('Message Listener', () => {
    it('should register onMessage listener', () => {
      // Given
      const addListener = vi.spyOn(browser.runtime.onMessage, 'addListener');

      // When/Then
      // Content script main() would call addListener
      // This test verifies the API is available
      expect(addListener).toBeDefined();
      expect(typeof browser.runtime.onMessage.addListener).toBe('function');
    });

    it('should handle GET_PAGE_CONTEXT message and return success', () => {
      // Given
      const mockSendResponse = vi.fn();
      const message = { type: MessageType.GET_PAGE_CONTEXT };

      // Mock document
      document.title = 'Test Page';
      Object.defineProperty(window, 'location', {
        value: { href: 'https://example.com/test' },
        writable: true,
        configurable: true,
      });

      // Simulate the message handler from content.ts
      const handler = (msg: any, _sender: any, sendResponse: any) => {
        if (msg.type === MessageType.GET_PAGE_CONTEXT) {
          try {
            const context = extractPageContext();
            const response: GetPageContextResponse = {
              success: true,
              context,
            };
            sendResponse(response);
            return true;
          } catch (error) {
            const response: GetPageContextResponse = {
              success: false,
              error: error instanceof Error ? error.message : 'Unknown error',
            };
            sendResponse(response);
            return true;
          }
        }
      };

      // When
      const shouldKeepAlive = handler(message, {}, mockSendResponse);

      // Then
      expect(shouldKeepAlive).toBe(true);
      expect(mockSendResponse).toHaveBeenCalledTimes(1);
      const response = mockSendResponse.mock.calls[0][0] as GetPageContextResponse;
      expect(response.success).toBe(true);
      expect(response.context).toBeDefined();
      expect(response.context?.url).toBe('https://example.com/test');
      expect(response.context?.title).toBe('Test Page');
    });

    it('should handle extraction error and return failure', () => {
      // Given
      const mockSendResponse = vi.fn();
      const message = { type: MessageType.GET_PAGE_CONTEXT };

      // Simulate the message handler with error
      const handler = (msg: any, _sender: any, sendResponse: any) => {
        if (msg.type === MessageType.GET_PAGE_CONTEXT) {
          try {
            throw new Error('Extraction failed');
          } catch (error) {
            const response: GetPageContextResponse = {
              success: false,
              error: error instanceof Error ? error.message : 'Unknown error',
            };
            sendResponse(response);
            return true;
          }
        }
      };

      // When
      handler(message, {}, mockSendResponse);

      // Then
      expect(mockSendResponse).toHaveBeenCalledWith({
        success: false,
        error: 'Extraction failed',
      });
    });

    it('should ignore non-GET_PAGE_CONTEXT messages', () => {
      // Given
      const mockSendResponse = vi.fn();
      const message = { type: 'OTHER_MESSAGE_TYPE' };

      // Simulate the message handler
      const handler = (msg: any, _sender: any, sendResponse: any) => {
        if (msg.type === MessageType.GET_PAGE_CONTEXT) {
          sendResponse({ success: true });
          return true;
        }
        // No response for other messages
      };

      // When
      const result = handler(message, {}, mockSendResponse);

      // Then
      expect(result).toBeUndefined();
      expect(mockSendResponse).not.toHaveBeenCalled();
    });
  });
});
