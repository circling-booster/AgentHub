/**
 * Tests for content messaging utilities
 * Phase 5 Part C - Content Script
 */
import { describe, it, expect } from 'vitest';
import {
  MessageType,
  createGetPageContext,
  isGetPageContextResponse,
  type GetPageContextMessage,
  type GetPageContextResponse,
} from './content-messaging';

describe('Content Script Messaging', () => {
  describe('createGetPageContext', () => {
    it('should create GET_PAGE_CONTEXT message', () => {
      // When
      const message = createGetPageContext();

      // Then
      expect(message.type).toBe(MessageType.GET_PAGE_CONTEXT);
    });
  });

  describe('isGetPageContextResponse', () => {
    it('should identify success response', () => {
      // Given
      const response: GetPageContextResponse = {
        success: true,
        context: {
          url: 'https://example.com',
          title: 'Test',
          selectedText: '',
          metaDescription: '',
          mainContent: '',
        },
      };

      // When
      const result = isGetPageContextResponse(response);

      // Then
      expect(result).toBe(true);
      expect(response.success).toBe(true);
      expect(response.context).toBeDefined();
    });

    it('should identify error response', () => {
      // Given
      const response: GetPageContextResponse = {
        success: false,
        error: 'Failed to extract',
      };

      // When
      const result = isGetPageContextResponse(response);

      // Then
      expect(result).toBe(true);
      expect(response.success).toBe(false);
      expect(response.error).toBeDefined();
    });

    it('should reject non-response objects', () => {
      // Given
      const notResponse = { type: 'SOME_OTHER_TYPE' };

      // When
      const result = isGetPageContextResponse(notResponse);

      // Then
      expect(result).toBe(false);
    });
  });
});
