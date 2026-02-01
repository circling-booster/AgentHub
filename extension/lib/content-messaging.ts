/**
 * Content Script messaging types and utilities
 * Phase 5 Part C - Content Script
 *
 * Message flow:
 *   Background → Content Script: GET_PAGE_CONTEXT
 *   Content Script → Background: PageContext data or error
 */

import type { PageContext } from './types';

/** Message type constants for content script */
export const MessageType = {
  GET_PAGE_CONTEXT: 'GET_PAGE_CONTEXT',
} as const;

/** Background → Content Script: request page context */
export interface GetPageContextMessage {
  type: typeof MessageType.GET_PAGE_CONTEXT;
}

/** Content Script → Background: page context response */
export interface GetPageContextResponse {
  success: boolean;
  context?: PageContext;
  error?: string;
}

// Factory functions

export function createGetPageContext(): GetPageContextMessage {
  return {
    type: MessageType.GET_PAGE_CONTEXT,
  };
}

// Type guards

export function isGetPageContextResponse(
  response: unknown,
): response is GetPageContextResponse {
  if (typeof response !== 'object' || response === null) {
    return false;
  }
  const r = response as any;
  return typeof r.success === 'boolean';
}
