# WXT Framework Patterns

WXT-specific patterns and configurations for AgentHub Chrome Extension development.

## WXT Configuration

### wxt.config.ts

```typescript
import { defineConfig } from 'wxt';

export default defineConfig({
  modules: ['@wxt-dev/module-react'], // or vue, svelte

  manifest: {
    name: 'AgentHub',
    version: '1.0.0',
    description: 'MCP + A2A 통합 AI Agent 인터페이스',

    permissions: [
      'activeTab',      // Current tab access
      'storage',        // chrome.storage API
      'sidePanel',      // Side Panel API
      'offscreen',      // Offscreen Document API (Chrome 109+)
      'alarms',         // Periodic tasks (health checks)
    ],

    host_permissions: [
      'http://localhost:8000/*',
      'http://127.0.0.1:8000/*',
    ],
  },

  // Development settings
  dev: {
    server: {
      port: 3000,
    },
  },

  // Build settings
  build: {
    target: 'chrome109', // Minimum Chrome version for Offscreen API
  },
});
```

## Entrypoint Patterns

### Background Service Worker

**File:** `entrypoints/background.ts`

WXT automatically registers this as the background service worker.

```typescript
export default defineBackground(() => {
  // Service worker logic
  console.log('Background service worker started');

  chrome.runtime.onInstalled.addListener(() => {
    console.log('Extension installed');
  });
});
```

### Popup

**Files:**
- `entrypoints/popup/index.html`
- `entrypoints/popup/App.tsx`
- `entrypoints/popup/main.tsx`

WXT auto-generates manifest entry for popup:

```json
{
  "action": {
    "default_popup": "popup/index.html"
  }
}
```

### Side Panel

**Files:**
- `entrypoints/sidepanel/index.html`
- `entrypoints/sidepanel/App.tsx`
- `entrypoints/sidepanel/main.tsx`

WXT auto-configures side_panel:

```json
{
  "side_panel": {
    "default_path": "sidepanel/index.html"
  }
}
```

### Offscreen Document

**Files:**
- `entrypoints/offscreen/index.html`
- `entrypoints/offscreen/main.ts`

**Note:** Offscreen Documents are NOT auto-configured in manifest. Create manually via chrome.offscreen API.

### Content Script

**File:** `entrypoints/content.ts`

For page-specific logic (optional for AgentHub):

```typescript
export default defineContentScript({
  matches: ['https://example.com/*'],
  main() {
    console.log('Content script loaded');
  },
});
```

## Development Workflow

### Start Dev Server

```bash
npm run dev
```

**Features:**
- HMR for UI components (React/Vue/Svelte)
- Fast reload for background/content scripts
- Auto-rebuild on file changes

### Load Extension

1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `.output/chrome-mv3/` directory

### View Console Logs

| Component | Console Location |
|-----------|-----------------|
| Background | chrome://extensions → Inspect views: service worker |
| Offscreen | chrome://extensions → Inspect views: offscreen.html |
| Popup | Right-click popup → Inspect |
| Sidepanel | Right-click sidepanel → Inspect |
| Content Script | Page DevTools console |

## Type Safety

### Auto-Generated Types

WXT generates TypeScript types for:
- `chrome.*` APIs
- Extension manifest
- Message passing

### Custom Types

```typescript
// types/messages.ts
export interface StreamChatMessage {
  type: 'STREAM_CHAT';
  payload: {
    conversationId: string;
    message: string;
  };
}

// Use in listener
chrome.runtime.onMessage.addListener((
  message: StreamChatMessage,
  sender,
  sendResponse
) => {
  // Type-safe message handling
});
```

## Shared Code

### lib/ Directory

Shared utilities accessible from all entrypoints:

```
lib/
├── api.ts          # API client
├── sse.ts          # SSE streaming
└── messaging.ts    # Message type definitions
```

Import in any entrypoint:

```typescript
import { streamChat } from '~/lib/sse';
import { authenticatedFetch } from '~/lib/api';
```

**Note:** `~` resolves to extension root.

## Build for Production

```bash
npm run build
```

**Output:** `.output/chrome-mv3.zip`

**Contents:**
- Minified JavaScript
- Optimized assets
- Complete manifest.json
- Ready for Chrome Web Store upload

## Testing

### E2E Testing

WXT integrates with Playwright:

```bash
npm install -D @playwright/test wxt/testing
```

```typescript
// tests/e2e/chat.spec.ts
import { test, expect } from '@playwright/test';
import { createExtensionContext } from 'wxt/testing';

test('chat streaming works', async () => {
  const { page } = await createExtensionContext();

  await page.goto('chrome-extension://YOUR_ID/sidepanel/index.html');
  await page.fill('input', 'Hello');
  await page.click('button[type="submit"]');

  await expect(page.locator('.message')).toContainText('Hello');
});
```

## Common Patterns

### Environment Variables

```typescript
// wxt.config.ts
export default defineConfig({
  manifest: {
    host_permissions: [
      import.meta.env.VITE_API_URL || 'http://localhost:8000/*',
    ],
  },
});
```

**.env:**
```
VITE_API_URL=http://localhost:8000/*
```

### Multi-Browser Support

```typescript
// wxt.config.ts
export default defineConfig({
  browser: process.env.BROWSER, // 'chrome' | 'firefox' | 'edge'

  manifest: {
    // Browser-specific overrides
    firefox: {
      browser_specific_settings: {
        gecko: {
          id: 'agenthub@example.com',
        },
      },
    },
  },
});
```

Build for different browsers:

```bash
BROWSER=chrome npm run build
BROWSER=firefox npm run build
```

## Migration from Plain Extension

### Before (Manual Setup)

```
extension/
├── manifest.json       # Manual configuration
├── background.js
├── popup.html
└── popup.js
```

### After (WXT)

```
entrypoints/
├── background.ts       # Auto-detected
├── popup/
│   ├── index.html
│   └── main.tsx
└── sidepanel/
    ├── index.html
    └── main.tsx

wxt.config.ts          # Replaces manifest.json
```

**Benefits:**
- TypeScript by default
- HMR for faster development
- Auto-manifest generation
- Framework support (React/Vue/Svelte)
- Built-in bundling (Vite)

## Troubleshooting

### Extension Not Loading

**Issue:** "Manifest file is missing or unreadable"

**Fix:** Run `npm run dev` or `npm run build` to generate manifest.

### HMR Not Working

**Issue:** Changes not reflecting

**Fix:**
1. Check dev server is running (`npm run dev`)
2. Reload extension in `chrome://extensions/`
3. Hard refresh extension page (Ctrl+Shift+R)

### Import Path Errors

**Issue:** Cannot find module `~/lib/api`

**Fix:** Use `~` prefix for extension root imports (WXT alias).

### Build Fails

**Issue:** Build errors after dependency update

**Fix:**
```bash
rm -rf node_modules .output
npm install
npm run build
```

## Performance Tips

### Code Splitting

WXT automatically code-splits by entrypoint. No manual configuration needed.

### Tree Shaking

Unused code automatically removed in production build.

### Asset Optimization

Images and static assets optimized automatically:

```typescript
import icon from '~/assets/icon.png';
// Optimized and fingerprinted in production
```

## References

- [WXT Documentation](https://wxt.dev/)
- [WXT GitHub](https://github.com/wxt-dev/wxt)
- [WXT Examples](https://github.com/wxt-dev/examples)
