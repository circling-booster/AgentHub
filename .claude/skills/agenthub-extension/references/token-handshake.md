# Token Handshake Security Pattern

Complete implementation guide for securing localhost API communication between Chrome Extension and AgentHub server.

## Problem: Drive-by RCE Attack

Malicious websites can send requests to `localhost:8000`:

```javascript
// Malicious website's script
fetch('http://localhost:8000/api/tools/call', {
  method: 'POST',
  body: JSON.stringify({ tool: 'delete_file', args: { path: '/' } })
});
```

If AgentHub server accepts all localhost requests, any website can execute dangerous MCP tools.

## Solution: Token Handshake

### Architecture

1. Server generates random token at startup
2. Extension requests token via `/auth/token` endpoint
3. Server validates origin (`chrome-extension://`)
4. Extension stores token in `chrome.storage.session`
5. All API requests include `X-Extension-Token` header
6. Server validates token before processing

### Server Implementation (FastAPI)

#### 1. Token Generation

```python
# src/adapters/inbound/http/security.py
import secrets

# Generate token at server startup
EXTENSION_TOKEN: str = secrets.token_urlsafe(32)

def get_extension_token() -> str:
    return EXTENSION_TOKEN
```

#### 2. Auth Middleware

```python
# src/adapters/inbound/http/security.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class ExtensionAuthMiddleware(BaseHTTPMiddleware):
    EXCLUDED_PATHS = {"/health", "/auth/token", "/docs", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in self.EXCLUDED_PATHS:
            return await call_next(request)

        if path.startswith("/api/"):
            token = request.headers.get("X-Extension-Token")
            if token != EXTENSION_TOKEN:
                return JSONResponse(
                    status_code=403,
                    content={"error": "Unauthorized", "message": "Invalid extension token"}
                )

        return await call_next(request)
```

#### 3. Token Exchange Endpoint

```python
# src/adapters/inbound/http/routes/auth.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Auth"])

_token_issued = False

class TokenRequest(BaseModel):
    extension_id: str

class TokenResponse(BaseModel):
    token: str

@router.post("/token", response_model=TokenResponse)
async def exchange_token(request: Request, body: TokenRequest):
    global _token_issued

    # Origin validation
    origin = request.headers.get("Origin", "")
    if not origin.startswith("chrome-extension://"):
        raise HTTPException(status_code=403, detail="Invalid origin")

    # Prevent token re-issuance (optional)
    if _token_issued:
        raise HTTPException(status_code=403, detail="Token already issued")

    _token_issued = True
    return TokenResponse(token=get_extension_token())
```

#### 4. CORS Configuration

```python
# src/adapters/inbound/http/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# IMPORTANT: Middleware order matters (LIFO)
# Add ExtensionAuthMiddleware first (innermost)
app.add_middleware(ExtensionAuthMiddleware)

# Add CORSMiddleware second (outermost)
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["chrome-extension://*"] DOES NOT WORK!
    # Use allow_origin_regex instead
    allow_origin_regex=r"^chrome-extension://[a-zA-Z0-9_-]+$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["X-Extension-Token", "Content-Type"],
)
```

### Extension Implementation (TypeScript)

#### 1. Token Exchange on Startup

```typescript
// entrypoints/background.ts
let extensionToken: string | null = null;

async function initializeAuth(): Promise<boolean> {
  try {
    const response = await fetch('http://localhost:8000/auth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ extension_id: chrome.runtime.id }),
    });

    if (!response.ok) {
      console.error('[Background] Token exchange failed');
      return false;
    }

    const { token } = await response.json();
    extensionToken = token;

    // Store in session storage (cleared on browser close)
    await chrome.storage.session.set({ extensionToken: token });
    console.log('[Background] Token exchange successful');
    return true;
  } catch (error) {
    console.error('[Background] Token exchange error:', error);
    return false;
  }
}

// Run on extension startup
chrome.runtime.onStartup.addListener(async () => {
  const isHealthy = await checkServerHealth();
  if (isHealthy) {
    await initializeAuth();
  }
});

// Run on extension installation
chrome.runtime.onInstalled.addListener(async () => {
  const isHealthy = await checkServerHealth();
  if (isHealthy) {
    await initializeAuth();
  }
});
```

#### 2. Authenticated API Client

```typescript
// lib/api.ts
const API_BASE = 'http://localhost:8000';

async function getExtensionToken(): Promise<string | null> {
  const stored = await chrome.storage.session.get('extensionToken');
  return stored.extensionToken || null;
}

export async function authenticatedFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = await getExtensionToken();

  if (!token) {
    throw new Error('Not authenticated. Server may not be running.');
  }

  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...options.headers,
      'X-Extension-Token': token,
      'Content-Type': 'application/json',
    },
  });
}

// Example usage
export async function registerMcpServer(url: string): Promise<McpServer> {
  const response = await authenticatedFetch('/api/mcp/servers', {
    method: 'POST',
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to register MCP server');
  }

  return response.json();
}
```

#### 3. SSE Streaming with Token

```typescript
// lib/sse.ts
export async function streamChat(
  conversationId: string,
  message: string,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const token = await getExtensionToken();

  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch('http://localhost:8000/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Extension-Token': token,
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      message: message,
    }),
  });

  // ... SSE parsing logic
}
```

## Security Best Practices

### 1. Use chrome.storage.session (NOT local)

```typescript
// ✅ CORRECT: Token cleared on browser close
await chrome.storage.session.set({ extensionToken: token });

// ❌ WRONG: Token persists across browser restarts
await chrome.storage.local.set({ extensionToken: token });
```

### 2. Never Log Tokens

```typescript
// ❌ WRONG: Token leaked to console
console.log('Token:', token);

// ✅ CORRECT: Generic log
console.log('[Background] Token exchange successful');
```

### 3. Validate Origin Server-Side

```python
# Server must validate Origin header
origin = request.headers.get("Origin", "")
if not origin.startswith("chrome-extension://"):
    raise HTTPException(status_code=403, detail="Invalid origin")
```

### 4. Token Re-Issuance Policy

**Option A: Single Token Per Server Lifetime (Recommended for MVP)**

```python
_token_issued = False

@router.post("/token")
async def exchange_token(...):
    global _token_issued
    if _token_issued:
        raise HTTPException(status_code=403, detail="Token already issued")
    _token_issued = True
    return TokenResponse(token=get_extension_token())
```

**Option B: Allow Re-Issuance (Development Friendly)**

```python
# No re-issuance check, always return token
# Useful during development when reloading extension frequently
```

## Testing Checklist

- [ ] Token exchange returns 403 for non-chrome-extension origin
- [ ] `/api/*` requests without token return 403
- [ ] `/api/*` requests with invalid token return 403
- [ ] `/api/*` requests with valid token succeed
- [ ] Token stored in `chrome.storage.session` (not `local`)
- [ ] Token cleared after browser restart
- [ ] CORS headers allow `chrome-extension://<ID>`
- [ ] CORS headers reject `http://malicious.com`

## Common Issues

### Token Exchange Fails (403)

**Cause:** Origin header not sent or invalid.

**Fix:** Ensure request comes from Extension (not DevTools console).

### API Requests Return 403 Despite Valid Token

**Cause:** Middleware order incorrect.

**Fix:** Add `ExtensionAuthMiddleware` BEFORE `CORSMiddleware` in FastAPI app setup.

### Token Not Persisting

**Cause:** Using `chrome.storage.local` instead of `session`.

**Fix:** Change to `chrome.storage.session.set()`.

### CORS Errors Despite Configuration

**Cause:** Using `allow_origins=["chrome-extension://*"]` (doesn't work).

**Fix:** Use `allow_origin_regex=r"^chrome-extension://[a-zA-Z0-9_-]+$"`.
