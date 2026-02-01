/**
 * Tests for background handlers - page context functionality
 * Phase 5 Part C - Content Script
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { browser } from 'wxt/browser';
import { requestPageContext } from './background-handlers';
import type { PageContext } from './types';

describe('Background Handlers - Page Context', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('requestPageContext', () => {
    it('should send GET_PAGE_CONTEXT message to active tab', async () => {
      // Given
      const mockContext: PageContext = {
        url: 'https://example.com',
        title: 'Test Page',
        selectedText: 'selected',
        metaDescription: 'desc',
        mainContent: 'content',
      };

      vi.spyOn(browser.tabs, 'query').mockResolvedValue([{ id: 123 }] as any);
      vi.spyOn(browser.tabs, 'sendMessage').mockResolvedValue({
        success: true,
        context: mockContext,
      } as any);

      // When
      const result = await requestPageContext();

      // Then
      expect(browser.tabs.query).toHaveBeenCalledWith({ active: true, currentWindow: true });
      expect(browser.tabs.sendMessage).toHaveBeenCalledWith(123, { type: 'GET_PAGE_CONTEXT' });
      expect(result).toEqual(mockContext);
    });

    it('should return null when no active tab', async () => {
      // Given
      vi.spyOn(browser.tabs, 'query').mockResolvedValue([] as any);

      // When
      const result = await requestPageContext();

      // Then
      expect(result).toBeNull();
    });

    it('should return null when content script returns error', async () => {
      // Given
      vi.spyOn(browser.tabs, 'query').mockResolvedValue([{ id: 123 }] as any);
      vi.spyOn(browser.tabs, 'sendMessage').mockResolvedValue({
        success: false,
        error: 'Failed to extract',
      } as any);

      // When
      const result = await requestPageContext();

      // Then
      expect(result).toBeNull();
    });

    it('should return null when sendMessage throws', async () => {
      // Given
      vi.spyOn(browser.tabs, 'query').mockResolvedValue([{ id: 123 }] as any);
      vi.spyOn(browser.tabs, 'sendMessage').mockRejectedValue(new Error('Tab closed'));

      // When
      const result = await requestPageContext();

      // Then
      expect(result).toBeNull();
    });
  });
});
