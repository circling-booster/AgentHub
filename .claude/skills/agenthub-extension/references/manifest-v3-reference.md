# Manifest V3 Reference

Chrome Extension Manifest V3 permissions and API reference for AgentHub.

## Essential Permissions

### storage

**Purpose:** Persist data locally (token, settings, cache)

**APIs:**
- `chrome.storage.local` - Local storage (persistent)
- `chrome.storage.session` - Session storage (cleared on browser close)
- `chrome.storage.sync` - Sync storage (across devices)

**AgentHub Usage:**
```typescript
// Store token in session (cleared on browser close)
await chrome.storage.session.set({ extensionToken: token });

// Get token
const { extensionToken } = await chrome.storage.session.get('extensionToken');
```

### activeTab

**Purpose:** Access current tab when user invokes extension

**Benefits:**
- No broad host permissions needed
- User grants access implicitly by clicking extension icon

**AgentHub Usage:**
```typescript
// Get current tab
const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
```

### sidePanel (Chrome 114+)

**Purpose:** Display UI in browser side panel

**APIs:**
- `chrome.sidePanel.open()`
- `chrome.sidePanel.setOptions()`

**AgentHub Usage:**
```typescript
// Open side panel
await chrome.sidePanel.open({ windowId: currentWindow.id });
```

### offscreen (Chrome 109+)

**Purpose:** Create hidden document for long-running tasks

**APIs:**
- `chrome.offscreen.createDocument()`
- `chrome.offscreen.closeDocument()`

**AgentHub Usage:**
```typescript
await chrome.offscreen.createDocument({
  url: 'offscreen/index.html',
  reasons: [chrome.offscreen.Reason.WORKERS],
  justification: 'Handle long-running LLM API requests',
});
```

**Reasons:**
- `AUDIO_PLAYBACK` - Audio playback
- `BLOBS` - Blob/ArrayBuffer operations
- `CLIPBOARD` - Clipboard access
- `DOM_PARSER` - DOMParser
- `DOM_SCRAPING` - DOM scraping
- `IFRAME_SCRIPTING` - iframe manipulation
- `LOCAL_STORAGE` - localStorage access
- `TESTING` - Testing purposes
- `USER_MEDIA` - getUserMedia
- `WORKERS` - Web Workers (AgentHub uses this)

### alarms

**Purpose:** Schedule periodic tasks

**APIs:**
- `chrome.alarms.create()`
- `chrome.alarms.onAlarm`

**AgentHub Usage:**
```typescript
// Health check every 30 seconds
chrome.alarms.create('healthCheck', { periodInMinutes: 0.5 });

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'healthCheck') {
    checkServerHealth();
  }
});
```

## Host Permissions

### localhost Access

```json
{
  "host_permissions": [
    "http://localhost:8000/*",
    "http://127.0.0.1:8000/*"
  ]
}
```

**Why Both:**
- Some systems resolve `localhost` to IPv6 `::1`
- Include both IPv4 (`127.0.0.1`) and hostname (`localhost`)

**Security:**
- localhost permissions don't trigger Chrome Web Store review
- Still need Token Handshake to prevent Drive-by RCE

## Optional Permissions

### tabs (Not Recommended)

**Alternative:** Use `activeTab` instead

**Difference:**
- `tabs`: Requires user approval, access to all tabs
- `activeTab`: Implicit approval, current tab only

### <all_urls> (Avoid)

**Issues:**
- Requires privacy policy
- Longer Chrome Web Store review
- Security concerns

**Alternative:** Use `activeTab` or specific host permissions

## API Reference

### chrome.runtime

**Message Passing:**
```typescript
// Send message
chrome.runtime.sendMessage({ type: 'ACTION', data: {...} });

// Listen for messages
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'ACTION') {
    sendResponse({ success: true });
  }
  return true; // Keep channel open for async
});
```

**Extension Lifecycle:**
```typescript
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    // First install
  } else if (details.reason === 'update') {
    // Extension updated
  }
});

chrome.runtime.onStartup.addListener(() => {
  // Browser started
});
```

### chrome.tabs

**Query Tabs:**
```typescript
// Get active tab
const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

// Get all tabs
const tabs = await chrome.tabs.query({});
```

**Send Message to Tab:**
```typescript
await chrome.tabs.sendMessage(tabId, { type: 'ACTION' });
```

### chrome.storage

**Local Storage:**
```typescript
// Set
await chrome.storage.local.set({ key: value });

// Get
const { key } = await chrome.storage.local.get('key');

// Remove
await chrome.storage.local.remove('key');

// Clear all
await chrome.storage.local.clear();
```

**Session Storage:**
```typescript
// Same API, but cleared on browser close
await chrome.storage.session.set({ token: 'secret' });
```

**Storage Limits:**
- `local`: 10 MB
- `sync`: 100 KB (8 KB per item)
- `session`: 10 MB

### chrome.offscreen

**Create Document:**
```typescript
await chrome.offscreen.createDocument({
  url: chrome.runtime.getURL('offscreen/index.html'),
  reasons: [chrome.offscreen.Reason.WORKERS],
  justification: 'Long-running API requests',
});
```

**Check Existence:**
```typescript
const contexts = await chrome.runtime.getContexts({
  contextTypes: [chrome.runtime.ContextType.OFFSCREEN_DOCUMENT],
});

const exists = contexts.length > 0;
```

**Close Document:**
```typescript
await chrome.offscreen.closeDocument();
```

### chrome.sidePanel

**Open Side Panel:**
```typescript
await chrome.sidePanel.open({ windowId });
```

**Set Options:**
```typescript
await chrome.sidePanel.setOptions({
  path: 'sidepanel/index.html',
  enabled: true,
});
```

### chrome.alarms

**Create Alarm:**
```typescript
// One-time alarm
chrome.alarms.create('taskName', { delayInMinutes: 1 });

// Periodic alarm
chrome.alarms.create('periodic', { periodInMinutes: 30 });
```

**Listen:**
```typescript
chrome.alarms.onAlarm.addListener((alarm) => {
  console.log('Alarm fired:', alarm.name);
});
```

**Clear Alarm:**
```typescript
await chrome.alarms.clear('taskName');
```

## Content Security Policy (CSP)

### Default CSP (Manifest V3)

```
script-src 'self'; object-src 'self'
```

**Restrictions:**
- ❌ No inline scripts (`<script>alert()</script>`)
- ❌ No inline event handlers (`<button onclick="...">`)
- ❌ No `eval()` or `new Function()`
- ❌ No external script URLs (except via `externally_connectable`)

### Custom CSP (Rarely Needed)

```json
{
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'"
  }
}
```

### CSP-Compliant Code

**✅ Good:**
```typescript
// External script reference
<script src="main.js"></script>

// Element creation
const button = document.createElement('button');
button.textContent = 'Click me';
button.addEventListener('click', handleClick);
```

**❌ Bad:**
```typescript
// Inline script (CSP violation)
<script>alert('hello')</script>

// Inline handler (CSP violation)
<button onclick="handleClick()">Click</button>

// eval (CSP violation)
eval('alert("hello")');
```

## Web Accessible Resources

**Purpose:** Allow web pages to access extension resources

```json
{
  "web_accessible_resources": [{
    "resources": ["images/*.png", "styles/*.css"],
    "matches": ["https://example.com/*"]
  }]
}
```

**AgentHub:** Not needed (extension doesn't inject resources into pages)

## Background Service Worker Restrictions

### No DOM Access

```typescript
// ❌ Error: document is not defined
const div = document.createElement('div');

// ✅ Use Offscreen Document for DOM operations
```

### 30-Second Timeout

```typescript
// ❌ Will terminate after 30s
setInterval(() => console.log('tick'), 1000);

// ✅ Use chrome.alarms for periodic tasks
chrome.alarms.create('tick', { periodInMinutes: 1/60 });
```

### No Persistent State

```typescript
// ❌ Will be lost on service worker restart
let counter = 0;

// ✅ Use chrome.storage
await chrome.storage.local.set({ counter });
```

## Cross-Browser Compatibility

### Chrome vs Firefox

| Feature | Chrome | Firefox |
|---------|--------|---------|
| Manifest V3 | ✅ Required | ✅ Supported |
| Offscreen API | ✅ Chrome 109+ | ❌ Not available |
| Side Panel | ✅ Chrome 114+ | ❌ Use sidebar_action |
| chrome.storage.session | ✅ Chrome 102+ | ❌ Use local storage |

### Polyfills

For cross-browser compatibility:

```typescript
// Use 'browser' instead of 'chrome'
import browser from 'webextension-polyfill';

await browser.storage.local.set({ key: value });
```

## Debugging Manifest Issues

### Validation

Chrome validates manifest on load:

```
chrome://extensions/ → Load unpacked
```

**Common Errors:**
- Invalid JSON syntax
- Missing required fields
- Unknown permissions
- Invalid host permissions format

### Check Permissions

```typescript
// Check if permission granted
const hasPermission = await chrome.permissions.contains({
  permissions: ['storage'],
});

// Request optional permission
const granted = await chrome.permissions.request({
  permissions: ['downloads'],
});
```

## Migration from V2 to V3

| V2 | V3 |
|----|-----|
| `background.page` | `background.service_worker` |
| `browser_action` | `action` |
| `page_action` | `action` |
| `webRequest` | `declarativeNetRequest` |
| Callback APIs | Promise-based APIs |

## Best Practices

1. **Minimal Permissions:** Only request what's needed
2. **activeTab over tabs:** Use when possible
3. **Session Storage for Tokens:** Auto-clear on browser close
4. **Offscreen for Long Tasks:** Avoid Service Worker timeout
5. **CSP Compliance:** No inline scripts/handlers

## References

- [Chrome Extensions Manifest V3](https://developer.chrome.com/docs/extensions/mv3/intro/)
- [Permissions Documentation](https://developer.chrome.com/docs/extensions/reference/api/permissions)
- [API Reference](https://developer.chrome.com/docs/extensions/reference/api)
- [Offscreen API](https://developer.chrome.com/docs/extensions/reference/api/offscreen)
- [Side Panel API](https://developer.chrome.com/docs/extensions/reference/api/sidePanel)
