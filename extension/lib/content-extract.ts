/**
 * Content extraction utilities
 * Phase 5 Part C - Content Script
 *
 * Extracts page context information from the current web page.
 */
import type { PageContext } from './types';

const MAX_CONTENT_LENGTH = 2000;

/**
 * Extract main content from the page
 * Priority: <main> > <article> > <body>
 */
function extractMainContent(): string {
  let element = document.querySelector('main');
  if (!element) {
    element = document.querySelector('article');
  }
  if (!element) {
    element = document.body;
  }

  const text = element?.textContent || '';
  // Strip excessive whitespace
  const normalized = text.replace(/\s+/g, ' ').trim();
  // Limit to max length
  return normalized.slice(0, MAX_CONTENT_LENGTH);
}

/**
 * Extract page context information
 *
 * Extracts:
 * - URL and title
 * - Selected text (if any)
 * - Meta description
 * - Main content (simplified, max 2000 chars)
 */
export function extractPageContext(): PageContext {
  const selection = window.getSelection();
  const selectedText = selection?.toString() || '';

  const metaDescription =
    document.querySelector('meta[name="description"]')?.getAttribute('content') || '';

  return {
    url: window.location.href,
    title: document.title,
    selectedText,
    metaDescription,
    mainContent: extractMainContent(),
  };
}
