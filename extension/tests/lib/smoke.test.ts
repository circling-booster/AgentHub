import { describe, it, expect } from 'vitest';
import { fakeBrowser } from 'wxt/testing';

describe('Vitest + WXT smoke test', () => {
  it('should have access to browser API via fakeBrowser', () => {
    expect(fakeBrowser).toBeDefined();
    expect(fakeBrowser.runtime).toBeDefined();
  });

  it('should support browser.storage.session', async () => {
    await fakeBrowser.storage.session.set({ key: 'value' });
    const result = await fakeBrowser.storage.session.get('key');
    expect(result).toEqual({ key: 'value' });
  });
});
