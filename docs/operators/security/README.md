# Security Guide

AgentHub 보안 설정 가이드입니다.

---

## Overview

AgentHub는 **Zero-Trust** 보안 원칙을 따릅니다:

1. **Token Handshake**: 서버 시작 시 난수 토큰 생성
2. **Middleware 검증**: 모든 `/api/*` 요청에 헤더 필수
3. **CORS 제한**: 허용된 Origin만 접근

---

## Token Authentication

### How It Works

```
┌─────────────────┐         ┌─────────────────┐
│ Chrome Extension│         │  AgentHub API   │
└────────┬────────┘         └────────┬────────┘
         │                           │
         │  GET /auth/token          │
         │ ─────────────────────────>│
         │                           │
         │  { token: "abc123..." }   │
         │ <─────────────────────────│
         │                           │
         │  GET /api/* + Header      │
         │  X-Extension-Token: abc123│
         │ ─────────────────────────>│
         │                           │
         │  Response (200 OK)        │
         │ <─────────────────────────│
```

### Token Generation

서버 시작 시 `secrets.token_urlsafe(32)`로 32바이트 난수 토큰 생성:

```python
# src/adapters/inbound/http/security.py
import secrets

class TokenProvider:
    def get_token(self) -> str:
        if self._token is None:
            self._token = secrets.token_urlsafe(32)
        return self._token
```

### Protected Endpoints

| Path Pattern | Authentication |
|--------------|----------------|
| `/api/*` | Token 필수 |
| `/health` | Public |
| `/auth/token` | Public |
| `/docs`, `/redoc`, `/openapi.json` | Public |

### Header Format

```http
GET /api/conversations HTTP/1.1
Host: localhost:8000
X-Extension-Token: <token>
```

### Error Response

토큰 불일치 시:

```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing extension token"
}
```

HTTP Status: `403 Forbidden`

---

## CORS Configuration

### Default Settings

```python
# 기본 허용 Origins
origins = [
    "chrome-extension://*",
    "http://localhost:*",
    "http://127.0.0.1:*"
]
```

### Production Override

프로덕션에서는 특정 Extension ID만 허용:

```python
origins = [
    "chrome-extension://abcdefghijklmnop..."
]
```

### CORS Headers

```http
Access-Control-Allow-Origin: chrome-extension://...
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: X-Extension-Token, Content-Type
Access-Control-Allow-Credentials: true
```

---

## OAuth 2.0

MCP 서버 인증용 OAuth 2.0 지원입니다.

### Supported Flows

| Flow | Use Case |
|------|----------|
| **Client Credentials** | 서버 간 인증 |
| **Authorization Code** | 사용자 동의 필요 시 |

### Configuration

MCP 서버별 OAuth 설정:

```python
# src/domain/entities/auth_config.py
@dataclass
class AuthConfig:
    auth_type: str = "oauth2"

    # OAuth 2.0 설정
    oauth2_client_id: str = ""
    oauth2_client_secret: str = ""
    oauth2_token_url: str = ""
    oauth2_authorize_url: str = ""
    oauth2_scope: str = ""
```

### Supported Auth Types

| Type | Description | Use Case |
|------|-------------|----------|
| `none` | 인증 없음 | 로컬 테스트 |
| `header` | 커스텀 헤더 | 레거시 시스템 |
| `api_key` | API Key | 단순 인증 |
| `oauth2` | OAuth 2.0 | 표준 인증 |

### Auth Header Generation

```python
def get_auth_headers(self) -> dict[str, str]:
    if self.auth_type == "oauth2" and self.oauth2_access_token:
        return {"Authorization": f"Bearer {self.oauth2_access_token}"}
    return {}
```

---

## Security Best Practices

### 1. API Key Management

- API 키는 `.env` 파일에만 저장
- `.env`는 `.gitignore`에 등록
- 프로덕션에서는 환경변수 또는 Secret Manager 사용

### 2. HTTPS (Production)

프로덕션 환경에서는 반드시 HTTPS 적용:

```bash
# Reverse Proxy (nginx) 예시
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
    }
}
```

### 3. Token Rotation

서버 재시작 시 토큰 자동 갱신:
- Extension은 재연결 시 새 토큰 교환
- 세션 하이재킹 방지

### 4. Rate Limiting

```yaml
# configs/default.yaml
gateway:
  rate_limit_rps: 5.0   # 초당 요청 수
  burst_size: 10        # 버스트 허용량
```

### 5. Circuit Breaker

외부 서비스 장애 격리:

```yaml
gateway:
  circuit_failure_threshold: 5    # 실패 임계값
  circuit_recovery_timeout: 60.0  # 복구 대기 (초)
```

---

## Drive-by RCE Protection

AgentHub의 Token 인증은 **Drive-by RCE** 공격을 방지합니다:

| Threat | Protection |
|--------|------------|
| 악성 웹페이지의 localhost 호출 | Token 없으면 403 |
| CORS 우회 시도 | Origin 검증 |
| Token 추측 | 32바이트 난수 (256비트 엔트로피) |

---

## Security Checklist

### Development

- [ ] `.env` 파일 생성 및 API 키 설정
- [ ] `.gitignore`에 `.env` 포함 확인
- [ ] Token 인증 테스트

### Production

- [ ] HTTPS 적용
- [ ] CORS Origin 제한 (특정 Extension ID)
- [ ] Rate Limiting 활성화
- [ ] 로그에서 민감 정보 필터링
- [ ] API 키 Secret Manager 사용

---

## Related

- [../](../) - Operators Hub
- [../deployment/](../deployment/) - 배포 가이드
- [../observability/](../observability/) - 모니터링 및 로깅
- [../../developers/guides/](../../developers/guides/) - 보안 패턴 구현
