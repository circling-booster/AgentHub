# 보안 위반 사례 및 올바른 패턴

## Token Handshake 위반

```python
# BAD: 하드코딩된 토큰
EXTENSION_TOKEN = "my-secret-token"

# BAD: 파일에 토큰 저장
with open("token.txt", "w") as f:
    f.write(token)

# BAD: 토큰 없이 API 허용
if not token:
    pass  # 무시하고 진행

# GOOD: secrets 모듈로 생성, 메모리 전용
self._token = secrets.token_urlsafe(32)
```

## CORS 위반

```python
# BAD: allow_origins 와일드카드 (작동 안 함)
allow_origins=["chrome-extension://*"]

# BAD: 모든 Origin 허용 (Drive-by RCE 취약)
allow_origins=["*"]

# BAD: 미들웨어 순서 역전 (403에 CORS 헤더 누락)
app.add_middleware(CORSMiddleware, ...)       # innermost
app.add_middleware(ExtensionAuthMiddleware)   # outermost
# -> 403 응답에 CORS 헤더 없음 -> 브라우저에서 CORS 에러로 표시

# GOOD: allow_origin_regex + 올바른 순서
app.add_middleware(ExtensionAuthMiddleware)   # innermost (나중 실행)
app.add_middleware(                           # outermost (먼저 실행)
    CORSMiddleware,
    allow_origin_regex=r"^chrome-extension://[a-zA-Z0-9_-]+$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["X-Extension-Token", "Content-Type"],
)
```

## Extension Client 위반

```typescript
// BAD: Local Storage에 토큰 저장 (브라우저 종료 후에도 유지)
await chrome.storage.local.set({ extensionToken: token });
localStorage.setItem('token', token);

// BAD: Content Script에서 직접 API 호출 (Mixed Content 위험)
// content.ts
fetch('http://localhost:8000/api/...');

// GOOD: Session Storage + Background 경유
await chrome.storage.session.set({ extensionToken: token });

// GOOD: Content Script -> Background -> API
// content.ts
chrome.runtime.sendMessage({ type: 'API_REQUEST', ... });
// background.ts
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'API_REQUEST') {
    fetch('http://localhost:8000/api/...', {
      headers: { 'X-Extension-Token': token }
    });
  }
});
```

## 인증 제외 경로 위반

```python
# BAD: 과도한 경로 제외
EXCLUDED_PATHS = {"/health", "/auth/token", "/api/public", "/api/tools"}

# BAD: OPTIONS 메서드 미처리 (CORS preflight 실패)
async def dispatch(self, request, call_next):
    # OPTIONS 검증 생략 코드 없음
    if path.startswith("/api/"):
        token = request.headers.get("X-Extension-Token")
        ...

# GOOD: 최소한의 제외 + OPTIONS 처리
EXCLUDED_PATHS = {"/health", "/auth/token", "/docs", "/openapi.json", "/redoc"}

async def dispatch(self, request, call_next):
    if method == "OPTIONS":
        return await call_next(request)  # CORS 미들웨어가 처리
    if path in self.EXCLUDED_PATHS:
        return await call_next(request)
    if path.startswith("/api/"):
        ...
```
