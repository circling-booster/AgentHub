/**
 * Tests for content-extract.ts
 * Phase 5 Part C - Content Script
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { extractPageContext } from './content-extract';

describe('extractPageContext', () => {
  beforeEach(() => {
    // Reset DOM for each test
    document.body.innerHTML = '';
    document.head.innerHTML = '';
    document.title = '';

    // Mock window.location
    delete (window as any).location;
    (window as any).location = { href: 'https://example.com' };

    // Mock window.getSelection
    window.getSelection = vi.fn();
  });

  it('should extract URL and title', () => {
    // Given
    document.title = 'Test Page Title';
    (window as any).location.href = 'https://example.com/test';

    // When
    const context = extractPageContext();

    // Then
    expect(context.url).toBe('https://example.com/test');
    expect(context.title).toBe('Test Page Title');
  });

  it('should extract selected text when available', () => {
    // Given
    const mockSelection = {
      toString: () => 'Selected text here',
    };
    (window.getSelection as any).mockReturnValue(mockSelection);

    // When
    const context = extractPageContext();

    // Then
    expect(context.selectedText).toBe('Selected text here');
  });

  it('should return empty string when no text selected', () => {
    // Given
    const mockSelection = {
      toString: () => '',
    };
    (window.getSelection as any).mockReturnValue(mockSelection);

    // When
    const context = extractPageContext();

    // Then
    expect(context.selectedText).toBe('');
  });

  it('should extract meta description when present', () => {
    // Given
    const meta = document.createElement('meta');
    meta.setAttribute('name', 'description');
    meta.setAttribute('content', 'This is a test description');
    document.head.appendChild(meta);

    // When
    const context = extractPageContext();

    // Then
    expect(context.metaDescription).toBe('This is a test description');
  });

  it('should return empty string when meta description absent', () => {
    // Given - no meta tag

    // When
    const context = extractPageContext();

    // Then
    expect(context.metaDescription).toBe('');
  });

  it('should extract main content with max 2000 chars', () => {
    // Given
    const longContent = 'A'.repeat(3000);
    const mainElement = document.createElement('main');
    mainElement.textContent = longContent;
    document.body.appendChild(mainElement);

    // When
    const context = extractPageContext();

    // Then
    expect(context.mainContent).toHaveLength(2000);
    expect(context.mainContent).toBe('A'.repeat(2000));
  });

  it('should extract from article if no main element', () => {
    // Given
    const article = document.createElement('article');
    article.textContent = 'Article content here';
    document.body.appendChild(article);

    // When
    const context = extractPageContext();

    // Then
    expect(context.mainContent).toContain('Article content here');
  });

  it('should extract from body if no main or article', () => {
    // Given
    document.body.innerHTML = '<p>Body paragraph 1</p><p>Body paragraph 2</p>';

    // When
    const context = extractPageContext();

    // Then
    expect(context.mainContent).toContain('Body paragraph 1');
    expect(context.mainContent).toContain('Body paragraph 2');
  });

  it('should strip excessive whitespace from content', () => {
    // Given
    document.body.innerHTML = '<p>Text   with    multiple     spaces</p>';

    // When
    const context = extractPageContext();

    // Then
    expect(context.mainContent).toBe('Text with multiple spaces');
  });

  it('should handle null selection gracefully', () => {
    // Given
    (window.getSelection as any).mockReturnValue(null);

    // When
    const context = extractPageContext();

    // Then
    expect(context.selectedText).toBe('');
  });
});
