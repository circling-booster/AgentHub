# Phase 1.5: Security Layer 구현 계획 (최종 검증판)

> Drive-by RCE 공격 방지를 위한 Zero-Trust localhost API 보안 레이어

**작성일:** 2026-01-29
**버전:** 2.0 (Critical Issues 수정 완료)

---

## 📋 목차

1. [현재 상태 및 목표](#1-현재-상태-및-목표)
2. [DoD (Definition of Done)](#2-dod-definition-of-done)
3. [구현 순서 (TDD 방식)](#3-구현-순서-tdd-방식)
4. [파일별 구현 상세](#4-파일별-구현-상세)
5. [테스트 전략 (TDD + 헥사고날)](#5-테스트-전략-tdd--헥사고날)
6. [검증 방법](#6-검증-방법)
7. [생성/수정 파일 목록](#7-생성수정-파일-목록)
8. [서브에이전트 호출 계획](#8-서브에이전트-호출-계획)
9. [참조 문서](#9-참조-문서)

---

## 1. 현재 상태 및 목표

### Phase 1 완료 확인 ✅

| 항목 | 상태 | 비고 |
|------|:----:|------|
| 테스트 커버리지 | **91%** | 목표 80% 초과 달성 |
| 테스트 수 | **136개** | 전체 통과 |
| Domain Layer | ✅ | 순수 Python, 외부 의존성 없음 검증 완료 |
| SQLite WAL 저장소 | ✅ | 동시성 처리 구현 완료 |
| 폴더 README | ✅ | src/, src/domain/, src/config/, tests/ 생성 완료 |

### Phase 1.5 목표

**Zero-Trust 보안 체계 확립**으로 다음 위협 차단:
- **Drive-by RCE Attack**: 악성 웹사이트가 localhost API 호출하여 MCP 도구 실행
- **CORS Bypass**: 웹 페이지에서 localhost API 접근
- **Token Spoofing**: 토큰 없이 API 우회

### 구현 필요 컴포넌트

| 컴포넌트 | 현재 상태 | 구현 범위 |
|---------|----------|----------|
| HTTP Adapter (FastAPI) | 없음 | **새로 생성** |
| Security Middleware | 없음 | **새로 생성 (핵심)** |
| Auth Routes | 없음 | **새로 생성** |
| CORS Configuration | 없음 | **새로 생성** |
| src/main.py | 없음 | **새로 생성** |

---

## 2. DoD (Definition of Done)

### 기능 검증

- [ ] curl로 토큰 없이 `/api/*` 호출 시 **403 Forbidden** 반환
- [ ] `/auth/token` 호출 시 유효한 토큰 반환
- [ ] 잘못된 Origin(`https://evil.com`)에서 요청 시 **CORS 에러** 발생
- [ ] Chrome Extension Origin에서 요청 시 CORS 통과

### 품질 검증

- [ ] **테스트 커버리지 80% 유지** (Phase 1 수준 유지)
- [ ] 모든 보안 테스트 케이스 통과 (15개 이상)
- [ ] ruff 린트/포맷 통과
- [ ] mypy 타입 체크 통과 (신규 코드)

### 문서화

- [ ] `src/README.md`에 **Security 섹션 업데이트** (신규 추가가 아닌 기존 문서 수정)
- [ ] 보안 패턴 설명 포함 (Token Handshake, CORS, Drive-by RCE 방지)

---

## 3. 구현 순서 (TDD 방식)

```
Step 1: 폴더 구조 생성
    └── src/adapters/inbound/http/, schemas/, routes/

Step 2: 보안 모듈 (핵심) - TDD ⭐
    ├── 🤖 tdd-agent 호출
    ├── tests/unit/adapters/test_security.py (테스트 먼저 작성)
    └── src/adapters/inbound/http/security.py

Step 3: Auth 라우트 - TDD ⭐
    ├── 🤖 tdd-agent 호출
    ├── tests/integration/adapters/test_auth_routes.py (테스트 먼저)
    ├── src/adapters/inbound/http/schemas/auth.py
    └── src/adapters/inbound/http/routes/auth.py

Step 4: Health 엔드포인트
    ├── tests/integration/adapters/test_health_routes.py
    └── src/adapters/inbound/http/routes/health.py

Step 5: FastAPI 앱 통합
    ├── tests/integration/adapters/test_http_app.py
    ├── src/adapters/inbound/http/app.py
    └── src/main.py

Step 6: 보안 검토
    └── 🤖 security-reviewer 호출

Step 7: 문서화
    ├── src/README.md Security 섹션 업데이트
    └── 🤖 code-reviewer 호출 (최종 검토)
```

> **⚠️ TDD 원칙 엄수**: Step 2와 Step 3에서 **반드시 테스트를 먼저 작성**한 후 구현

---

## 4. 파일별 구현 상세

### Step 1: 폴더 구조

```
src/adapters/inbound/http/
├── __init__.py
├── security.py          # Token Provider + Auth Middleware (핵심)
├── app.py               # FastAPI 앱 팩토리
├── schemas/
│   ├── __init__.py
│   └── auth.py          # TokenRequest, TokenResponse
└── routes/
    ├── __init__.py
    ├── auth.py          # POST /auth/token
    └── health.py        # GET /health
```

---

### Step 2: security.py (핵심 - 테스트 용이성 개선)

**파일**: `src/adapters/inbound/http/security.py`

```python
"""Localhost API 보안 (Drive-by RCE 방지)

Zero-Trust 보안 원칙:
1. Token Handshake: 서버 시작 시 난수 토큰 생성, Extension만 교환
2. Middleware 검증: 모든 /api/* 요청에 X-Extension-Token 헤더 필수
3. CORS 제한: chrome-extension:// Origin만 허용
"""
import secrets
from typing import ClassVar

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class TokenProvider:
    """
    토큰 관리 클래스 (테스트 용이성 개선)

    기존 모듈 레벨 전역 변수 대신 클래스로 래핑하여
    테스트에서 토큰 주입 가능
    """
    def __init__(self):
        self._token: str | None = None

    @property
    def token(self) -> str:
        """토큰 lazy 생성 (서버 시작 시 1회만)"""
        if self._token is None:
            self._token = secrets.token_urlsafe(32)
        return self._token

    def reset(self, new_token: str | None = None) -> None:
        """테스트용: 토큰 재설정"""
        self._token = new_token


# 싱글톤 인스턴스
token_provider = TokenProvider()


class ExtensionAuthMiddleware(BaseHTTPMiddleware):
    """
    Chrome Extension 인증 미들웨어

    모든 /api/* 요청에 X-Extension-Token 헤더 검증.
    토큰 불일치 시 403 Forbidden 반환하여 Drive-by RCE 공격 차단.
    """

    # 인증 제외 경로 (Public endpoints)
    EXCLUDED_PATHS: ClassVar[set[str]] = {
        "/health",
        "/auth/token",
        "/docs",
        "/openapi.json",
        "/redoc",  # ⭐ 추가 (FastAPI 문서)
    }

    async def dispatch(self, request: Request, call_next):
        """요청 처리 전 토큰 검증"""
        path = request.url.path

        # 제외 경로는 검증 생략
        if path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # API 경로는 토큰 검증 필수
        if path.startswith("/api/"):
            token = request.headers.get("X-Extension-Token")
            if token != token_provider.token:
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "Unauthorized",
                        "message": "Invalid or missing extension token"
                    }
                )

        return await call_next(request)


def get_extension_token() -> str:
    """Extension 초기화 시 토큰 반환"""
    return token_provider.token
```

**주요 개선점:**
- `TokenProvider` 클래스로 테스트 용이성 향상
- `EXCLUDED_PATHS`에 `/redoc` 추가
- 에러 메시지 명확화
- 타입 힌트 추가 (`ClassVar`)

---

### Step 3: Auth 라우트

**파일**: `src/adapters/inbound/http/schemas/auth.py`

```python
"""Auth API 스키마"""
from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    """토큰 교환 요청"""
    extension_id: str = Field(..., description="Chrome Extension ID")


class TokenResponse(BaseModel):
    """토큰 교환 응답"""
    token: str = Field(..., description="API access token")
```

**파일**: `src/adapters/inbound/http/routes/auth.py`

```python
"""토큰 교환 엔드포인트"""
from fastapi import APIRouter, Request, HTTPException

from ..schemas.auth import TokenRequest, TokenResponse
from ..security import get_extension_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/token", response_model=TokenResponse)
async def exchange_token(request: Request, body: TokenRequest):
    """
    Chrome Extension 토큰 교환

    Origin 검증:
    - chrome-extension:// Origin만 허용
    - 웹 페이지(https://)에서 호출 시 403 Forbidden

    보안:
    - 토큰 발급은 서버 세션당 1회 (재시작 시 리셋)
    - Extension ID는 로깅용, 검증은 Origin 헤더로 수행
    """
    # Origin 헤더 검증
    origin = request.headers.get("Origin", "")
    if not origin.startswith("chrome-extension://"):
        raise HTTPException(
            status_code=403,
            detail="Invalid origin. Only Chrome Extensions are allowed."
        )

    # 토큰 반환
    return TokenResponse(token=get_extension_token())
```

---

### Step 4: Health 엔드포인트

**파일**: `src/adapters/inbound/http/routes/health.py`

```python
"""Health Check 엔드포인트"""
from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    서버 상태 확인

    인증 불필요 (EXCLUDED_PATHS에 포함)
    Extension background.ts에서 30초 주기로 호출
    """
    return {
        "status": "healthy",
        "version": "0.1.0"
    }
```

---

### Step 5: FastAPI 앱 통합

**파일**: `src/adapters/inbound/http/app.py`

```python
"""FastAPI 앱 팩토리"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .security import ExtensionAuthMiddleware
from .routes import auth, health


def create_app() -> FastAPI:
    """
    FastAPI 앱 생성

    Middleware 순서 (중요):
    1. CORSMiddleware 먼저 추가 → outermost (요청을 먼저 처리)
    2. ExtensionAuthMiddleware 나중 추가 → innermost

    이유: CORS preflight (OPTIONS) 요청이 Auth 검증 전에 처리되어야 함.
    참조: https://medium.com/@saurabhbatham17/navigating-middleware-ordering-in-fastapi-a-cors-dilemma-8be88ab2ee7b
    """
    app = FastAPI(
        title="AgentHub API",
        version="0.1.0",
        description="MCP + A2A 통합 Agent System"
    )

    # CORS: Chrome Extension만 허용 (regex 패턴)
    # ⭐ Critical Fix: allow_origins=["chrome-extension://*"]는 작동하지 않음
    # FastAPI/Starlette는 allow_origin_regex를 사용해야 함
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^chrome-extension://[a-z]{32}$",  # Extension ID 형식
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["X-Extension-Token", "Content-Type"],
        allow_credentials=False,
    )

    # 보안 미들웨어 (Token 검증)
    app.add_middleware(ExtensionAuthMiddleware)

    # 라우터 등록
    app.include_router(auth.router)
    app.include_router(health.router)

    return app
```

**파일**: `src/main.py`

```python
"""AgentHub API 서버 엔트리포인트

실행 방법:
    uvicorn src.main:app --host localhost --port 8000
"""
from src.adapters.inbound.http.app import create_app

app = create_app()
```

**핵심 수정사항:**
- ✅ `allow_origins` → `allow_origin_regex` 변경 (Critical Fix)
- ✅ Middleware 순서 설명 추가
- ✅ CORS OPTIONS 메서드 명시적 추가

---

## 5. 테스트 전략 (TDD + 헥사고날)

### 테스트 커버리지 목표

| 레이어 | 목표 | 이유 |
|--------|:----:|------|
| **Security Module** | **90%+** | 보안 코드는 가장 높은 커버리지 필요 |
| **HTTP Adapter** | **80%** | Phase 1 수준 유지 |
| **전체 프로젝트** | **80%+** | CI/CD 통과 조건 (DoD) |

### 생성할 테스트 파일

| 파일 | 테스트 내용 | 개수 |
|------|-----------|:----:|
| `tests/unit/adapters/test_security.py` | TokenProvider, Middleware 단위 테스트 | 8+ |
| `tests/integration/adapters/test_auth_routes.py` | Origin 검증, 토큰 교환 API | 5+ |
| `tests/integration/adapters/test_health_routes.py` | Health 엔드포인트 | 2+ |
| `tests/integration/adapters/test_http_app.py` | 앱 통합, CORS 검증 | 5+ |

**총 테스트 케이스: 최소 20개 이상**

---

### 필수 테스트 케이스 (보안 관점)

#### tests/unit/adapters/test_security.py

```python
"""Security Module 단위 테스트"""
import pytest
from src.adapters.inbound.http.security import (
    TokenProvider,
    ExtensionAuthMiddleware,
    token_provider,
)


class TestTokenProvider:
    """토큰 생성/관리 테스트"""

    def test_token_is_generated_on_first_access(self):
        """첫 접근 시 토큰이 자동 생성되어야 함"""
        provider = TokenProvider()
        token = provider.token
        assert token is not None
        assert len(token) > 0

    def test_token_is_cryptographically_secure(self):
        """토큰이 충분히 랜덤해야 함 (32 bytes = 256 bits)"""
        provider = TokenProvider()
        token = provider.token
        assert len(token) >= 43  # urlsafe_b64encode(32 bytes) ≈ 43 chars

    def test_token_is_consistent_during_session(self):
        """같은 세션에서 토큰이 변경되지 않아야 함"""
        provider = TokenProvider()
        token1 = provider.token
        token2 = provider.token
        assert token1 == token2

    def test_reset_allows_token_injection(self):
        """테스트용 reset 메서드로 토큰 주입 가능"""
        provider = TokenProvider()
        provider.reset("test-token-123")
        assert provider.token == "test-token-123"


class TestExtensionAuthMiddleware:
    """인증 미들웨어 테스트"""

    @pytest.fixture
    def middleware(self):
        return ExtensionAuthMiddleware(app=None)

    def test_api_request_without_token_returns_403(self, middleware):
        """토큰 없이 /api/* 접근 시 403"""
        # Mock Request with path="/api/test"
        # Assert response.status_code == 403

    def test_api_request_with_invalid_token_returns_403(self, middleware):
        """잘못된 토큰으로 /api/* 접근 시 403"""
        # Mock Request with X-Extension-Token: "wrong-token"
        # Assert response.status_code == 403

    def test_api_request_with_valid_token_passes(self, middleware):
        """올바른 토큰으로 /api/* 접근 시 통과"""
        # Mock Request with valid token
        # Assert next handler is called

    def test_excluded_paths_bypass_auth(self, middleware):
        """/health, /auth/token 등은 토큰 없이 접근 가능"""
        excluded = ["/health", "/auth/token", "/docs", "/redoc"]
        for path in excluded:
            # Mock Request with path
            # Assert no 403 error

    def test_excluded_paths_complete(self):
        """모든 필수 제외 경로가 정의되어 있는지 확인"""
        assert "/health" in ExtensionAuthMiddleware.EXCLUDED_PATHS
        assert "/auth/token" in ExtensionAuthMiddleware.EXCLUDED_PATHS
        assert "/docs" in ExtensionAuthMiddleware.EXCLUDED_PATHS
        assert "/redoc" in ExtensionAuthMiddleware.EXCLUDED_PATHS
```

#### tests/integration/adapters/test_auth_routes.py

```python
"""Auth Routes 통합 테스트"""
import pytest
from fastapi.testclient import TestClient


class TestAuthTokenEndpoint:
    """토큰 교환 엔드포인트 테스트"""

    def test_valid_chrome_extension_origin_returns_token(self, http_client: TestClient):
        """chrome-extension:// Origin으로 요청 시 토큰 반환"""
        response = http_client.post(
            "/auth/token",
            json={"extension_id": "test"},
            headers={"Origin": "chrome-extension://abcdefghijklmnopqrstuvwxyz123456"}
        )
        assert response.status_code == 200
        assert "token" in response.json()

    def test_invalid_origin_returns_403(self, http_client: TestClient):
        """https://evil.com Origin으로 요청 시 403"""
        response = http_client.post(
            "/auth/token",
            json={"extension_id": "test"},
            headers={"Origin": "https://evil.com"}
        )
        assert response.status_code == 403
        assert "Invalid origin" in response.json()["detail"]

    def test_missing_origin_returns_403(self, http_client: TestClient):
        """Origin 헤더 없이 요청 시 403"""
        response = http_client.post(
            "/auth/token",
            json={"extension_id": "test"}
        )
        assert response.status_code == 403

    def test_token_format_is_valid(self, http_client: TestClient):
        """반환된 토큰이 올바른 형식인지 확인"""
        response = http_client.post(
            "/auth/token",
            json={"extension_id": "test"},
            headers={"Origin": "chrome-extension://test"}
        )
        token = response.json()["token"]
        assert len(token) >= 43  # urlsafe_b64encode(32 bytes)
        assert all(c.isalnum() or c in "-_" for c in token)  # URL-safe
```

#### tests/integration/adapters/test_http_app.py

```python
"""HTTP App 통합 테스트 (CORS 검증)"""
import pytest
from fastapi.testclient import TestClient


class TestCorsConfiguration:
    """CORS 설정 테스트"""

    def test_cors_allows_chrome_extension_origin(self, http_client: TestClient):
        """chrome-extension:// Origin CORS 허용"""
        response = http_client.options(
            "/auth/token",
            headers={
                "Origin": "chrome-extension://abcdefghijklmnopqrstuvwxyz123456",
                "Access-Control-Request-Method": "POST"
            }
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_cors_blocks_web_origin(self, http_client: TestClient):
        """https://example.com Origin CORS 차단"""
        response = http_client.options(
            "/auth/token",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "POST"
            }
        )
        # CORS 차단 시 Access-Control-Allow-Origin 헤더 없음
        assert "access-control-allow-origin" not in response.headers

    def test_preflight_options_handled(self, http_client: TestClient):
        """OPTIONS preflight 요청 정상 처리"""
        response = http_client.options(
            "/api/test",
            headers={
                "Origin": "chrome-extension://test",
                "Access-Control-Request-Method": "POST"
            }
        )
        assert response.status_code in (200, 204)
```

---

### conftest.py 수정

**파일**: `tests/integration/conftest.py` (기존 파일 **수정**)

```python
"""Integration Tests 공통 Fixtures"""
import pytest
from fastapi.testclient import TestClient

# ... 기존 fixtures ...


@pytest.fixture
def http_client():
    """
    FastAPI TestClient 픽스처

    실제 HTTP 요청 없이 FastAPI 앱 테스트
    """
    from src.adapters.inbound.http.app import create_app
    from src.adapters.inbound.http.security import token_provider

    # 테스트용 토큰 주입
    token_provider.reset("test-token-fixed")

    return TestClient(create_app())
```

---

## 6. 검증 방법

### 자동화 검증 (필수)

```bash
# 1. 전체 테스트 실행 (Phase 1 + 1.5)
pytest tests/ -v

# 2. 커버리지 검증 (80% 이상 필수)
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80

# 3. Security Module 커버리지 (90% 이상 권장)
pytest tests/unit/adapters/test_security.py \
    --cov=src/adapters/inbound/http/security \
    --cov-report=term-missing

# 4. 린트/포맷 검증
ruff check src/ tests/
ruff format src/ tests/ --check

# 5. 타입 체크
mypy src/adapters/inbound/http/
```

---

### 수동 검증 (curl) - 선택적

```bash
# 서버 시작
uvicorn src.main:app --host localhost --port 8000

# 테스트 1: 토큰 없이 API 호출 → 403
curl -i http://localhost:8000/api/test
# 예상: HTTP/1.1 403 Forbidden
# {"error":"Unauthorized","message":"Invalid or missing extension token"}

# 테스트 2: 토큰 교환 (chrome-extension Origin) → 토큰 반환
curl -i -X POST http://localhost:8000/auth/token \
  -H "Origin: chrome-extension://test" \
  -H "Content-Type: application/json" \
  -d '{"extension_id": "test"}'
# 예상: HTTP/1.1 200 OK
# {"token":"..."}

# 테스트 3: 잘못된 Origin → 403
curl -i -X POST http://localhost:8000/auth/token \
  -H "Origin: https://evil.com" \
  -H "Content-Type: application/json" \
  -d '{"extension_id": "test"}'
# 예상: HTTP/1.1 403 Forbidden
# {"detail":"Invalid origin..."}

# 테스트 4: Health 접근 (토큰 불필요) → 성공
curl -i http://localhost:8000/health
# 예상: HTTP/1.1 200 OK
# {"status":"healthy","version":"0.1.0"}

# 테스트 5: CORS Preflight (chrome-extension)
curl -i -X OPTIONS http://localhost:8000/auth/token \
  -H "Origin: chrome-extension://abcdefghijklmnopqrstuvwxyz123456" \
  -H "Access-Control-Request-Method: POST"
# 예상: access-control-allow-origin 헤더 포함
```

---

## 7. 생성/수정 파일 목록

### 새로 생성 (14개)

| 파일 | 역할 | 줄 수(예상) |
|------|------|:---------:|
| `src/adapters/inbound/http/__init__.py` | HTTP 어댑터 패키지 | 1 |
| `src/adapters/inbound/http/security.py` | **보안 미들웨어 (핵심)** | ~80 |
| `src/adapters/inbound/http/app.py` | FastAPI 앱 팩토리 | ~40 |
| `src/adapters/inbound/http/schemas/__init__.py` | 스키마 패키지 | 1 |
| `src/adapters/inbound/http/schemas/auth.py` | Auth 스키마 | ~15 |
| `src/adapters/inbound/http/routes/__init__.py` | 라우트 패키지 | 1 |
| `src/adapters/inbound/http/routes/auth.py` | Auth 라우트 | ~30 |
| `src/adapters/inbound/http/routes/health.py` | Health 라우트 | ~15 |
| `src/main.py` | 앱 엔트리포인트 | ~10 |
| `tests/unit/adapters/__init__.py` | 테스트 패키지 | 1 |
| `tests/unit/adapters/test_security.py` | **보안 단위 테스트** | ~120 |
| `tests/integration/adapters/test_auth_routes.py` | Auth 통합 테스트 | ~60 |
| `tests/integration/adapters/test_health_routes.py` | Health 통합 테스트 | ~20 |
| `tests/integration/adapters/test_http_app.py` | 앱 통합 + CORS 테스트 | ~50 |

**총 줄 수: 약 440줄**

### 수정 (2개)

| 파일 | 변경 내용 | 줄 수(추가) |
|------|----------|:--------:|
| `tests/integration/conftest.py` | `http_client` 픽스처 추가 | +10 |
| `src/README.md` | **Security 섹션 업데이트** | +30 |

---

## 8. 서브에이전트 호출 계획

### TDD + 보안 검토 워크플로우

| 시점 | 서브에이전트 | 목적 | 필수 여부 |
|------|-------------|------|:--------:|
| **Step 2 전** | `tdd-agent` | security.py **테스트 먼저 작성** (Red-Green-Refactor) | ✅ 필수 |
| **Step 3 전** | `tdd-agent` | auth routes **테스트 먼저 작성** | ✅ 필수 |
| **Step 6 (구현 완료 후)** | `security-reviewer` | 보안 취약점 검토 (Token, CORS, Origin 검증) | ✅ 필수 |
| **Step 7 (전체 완료 후)** | `code-reviewer` | 코드 품질 및 헥사고날 아키텍처 준수 검토 | 권장 |

### 호출 예시

```markdown
# Step 2 시작 시
"tdd-agent를 호출하여 security.py의 테스트를 먼저 작성해줘. TokenProvider와 ExtensionAuthMiddleware를 테스트해야 해."

# Step 3 시작 시
"tdd-agent를 호출하여 auth routes의 테스트를 먼저 작성해줘. Origin 검증과 토큰 교환 API를 테스트해야 해."

# Step 6 시작 시
"security-reviewer를 호출하여 구현된 보안 코드를 검토해줘. Drive-by RCE 방지 패턴이 올바르게 적용되었는지 확인해줘."
```

---

## 9. 참조 문서

### 프로젝트 문서

- [docs/guides/implementation-guide.md#9-보안-패턴](../guides/implementation-guide.md) - 상세 코드 예시 및 보안 패턴
- [docs/archive/risk-assessment.md#2-즉시-반영-항목](../archive/risk-assessment.md) - Drive-by RCE 완화책
- [docs/guides/architecture.md](../guides/architecture.md) - 헥사고날 아키텍처 설계
- [docs/roadmap.md](../roadmap.md) - Phase 1.5 목표 및 DoD

### 외부 참조

- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/) - `allow_origin_regex` 사용법
- [Starlette Middleware](https://www.starlette.io/middleware/) - Middleware 순서 및 동작 원리
- [FastAPI Middleware Order](https://medium.com/@saurabhbatham17/navigating-middleware-ordering-in-fastapi-a-cors-dilemma-8be88ab2ee7b) - CORS + Auth 순서
- [Chrome Extension Manifest V3 CORS](https://www.chromium.org/Home/chromium-security/extension-content-script-fetches/) - Extension CORS 동작

---

## 10. 의존성 확인

**확인 완료**: `pyproject.toml`에 이미 포함됨

```toml
[project]
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.25.0",  # TestClient 의존성
]
```

**추가 설치 불필요** ✅

---

## 11. 체크리스트 (구현 전 확인)

### 플랜 검증

- [x] Critical Issues 모두 수정 (CORS regex, EXCLUDED_PATHS)
- [x] Important Issues 모두 반영 (테스트 커버리지, 문서 표현, 토큰 테스트 용이성)
- [x] TDD 순서 명확화 (Step 2, 3에서 tdd-agent 호출)
- [x] 테스트 케이스 상세 명시 (20개 이상)
- [x] 서브에이전트 호출 시점 구체화
- [x] DoD에 커버리지 목표 추가

### 구현 준비

- [ ] Phase 1 완료 상태 확인 (91% 커버리지, 136 tests)
- [ ] `src/adapters/inbound/` 폴더 존재 확인
- [ ] `tests/integration/conftest.py` 백업 (기존 내용 보존)
- [ ] 서브에이전트 정의 확인 (`tdd-agent`, `security-reviewer`)

---

**플랜 승인 후 구현 시작 준비 완료** ✅

*최종 검증일: 2026-01-29*
