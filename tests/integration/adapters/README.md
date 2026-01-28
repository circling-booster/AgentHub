# Adapter Integration Tests

Phase 1.5 Security Layer 통합 테스트

## 테스트 구조

### 1. test_security.py (Unit Tests - 15개)
**TokenProvider 테스트 (5개)**
- 첫 접근 시 토큰 자동 생성
- 암호학적으로 안전한 길이 (43+ chars)
- 세션 중 일관된 토큰 반환
- reset() 메서드로 테스트 토큰 주입
- reset() 인자 없이 새 토큰 생성

**ExtensionAuthMiddleware 테스트 (10개)**
- 토큰 없이 /api/* 요청 시 403
- 잘못된 토큰으로 /api/* 요청 시 403
- 올바른 토큰으로 /api/* 요청 통과
- 제외 경로 토큰 검증 생략 (/health, /auth/token, /docs, /redoc, /openapi.json)
- /api/* 아닌 경로 토큰 검증 생략
- 403 응답 JSON 구조 검증

### 2. test_auth_routes.py (Integration Tests - 8개)
**POST /auth/token 엔드포인트**
- chrome-extension:// Origin으로 토큰 반환
- 웹 Origin (https://) 403 반환
- Origin 헤더 누락 시 403
- 빈 Origin 헤더 403
- 토큰 형식 검증 (URL-safe base64)
- 여러 chrome-extension Origin 허용
- extension_id 누락 시 422
- 동일 서버는 동일 토큰 반환

### 3. test_health_routes.py (Integration Tests - 5개)
**GET /health 엔드포인트**
- 200 OK 반환
- status 및 version 포함
- 토큰 없이 접근 가능
- 잘못된 토큰이 있어도 동작
- 올바른 JSON 형식

### 4. test_http_app.py (Integration Tests - 9개)
**CORS 설정 (5개)**
- chrome-extension:// Origin 허용
- 웹 Origin 차단
- OPTIONS preflight 처리
- 필요한 HTTP 메서드 허용 (GET, POST, DELETE)
- 필요한 헤더 허용 (X-Extension-Token, Content-Type)

**Middleware 순서 (1개)**
- CORS 미들웨어가 Auth보다 먼저 실행

**API 보호 (3개)**
- /api/* 엔드포인트 토큰 필수
- 올바른 토큰으로 /api/* 접근 가능
- 공개 엔드포인트 (/health, /auth/token) 토큰 불필요

## 실행 방법

```bash
# 전체 Phase 1.5 테스트
pytest tests/unit/adapters/test_security.py tests/integration/adapters/test_auth_routes.py tests/integration/adapters/test_health_routes.py tests/integration/adapters/test_http_app.py -v

# Unit 테스트만
pytest tests/unit/adapters/test_security.py -v

# Integration 테스트만
pytest tests/integration/adapters/test_auth_routes.py tests/integration/adapters/test_health_routes.py tests/integration/adapters/test_http_app.py -v
```

## TDD 상태

현재 **RED 단계** - 모든 테스트가 예상대로 실패함 (구현 전)

다음 단계: Green 단계 - 테스트를 통과하는 최소한의 구현 작성
