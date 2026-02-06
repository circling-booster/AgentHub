# Phase 2: Security Layer (Auth 우회)

## Overview

**목표:** DEV_MODE=true + localhost Origin 시 토큰 검증 우회

**TDD 원칙:** Red → Green → Refactor 순서 엄수

**전제 조건:** Phase 1 완료 (Settings.dev_mode 필드)

---

## Implementation Steps (TDD)

### Step 2.1: Red - DEV_MODE Auth 우회 테스트 작성

**목표:** DEV_MODE 시 localhost Origin은 토큰 없이 접근 가능

**테스트 파일:** `tests/integration/adapters/test_dev_mode_security.py`

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

class TestDevModeAuthBypass:
    """Integration Test: DEV_MODE Auth 우회"""

    @pytest.fixture
    def client_dev_mode(self, monkeypatch):
        """DEV_MODE=true 클라이언트"""
        monkeypatch.setenv("DEV_MODE", "true")
        return TestClient(app)

    @pytest.fixture
    def client_prod_mode(self, monkeypatch):
        """DEV_MODE=false 클라이언트"""
        monkeypatch.setenv("DEV_MODE", "false")
        return TestClient(app)

    def test_localhost_bypasses_auth_in_dev_mode(self, client_dev_mode):
        """Red: DEV_MODE + localhost Origin은 토큰 검증 우회"""
        # Given: localhost Origin + 토큰 없음
        headers = {"Origin": "http://localhost:3000"}

        # When: 보호된 엔드포인트 호출
        response = client_dev_mode.get("/api/chat/stream", headers=headers)

        # Then: 401 반환되지 않음 (우회 성공)
        assert response.status_code != 401

    def test_localhost_requires_auth_in_prod_mode(self, client_prod_mode):
        """Red: 프로덕션 모드에서는 localhost도 인증 필요"""
        # Given: localhost Origin + 토큰 없음
        headers = {"Origin": "http://localhost:3000"}

        # When: 보호된 엔드포인트 호출
        response = client_prod_mode.get("/api/chat/stream", headers=headers)

        # Then: 401 Unauthorized
        assert response.status_code == 401

    def test_non_localhost_requires_auth_in_dev_mode(self, client_dev_mode):
        """Red: DEV_MODE이더라도 localhost 외 Origin은 인증 필요"""
        # Given: 외부 Origin + 토큰 없음
        headers = {"Origin": "https://malicious-site.com"}

        # When: 보호된 엔드포인트 호출
        response = client_dev_mode.get("/api/chat/stream", headers=headers)

        # Then: 401 Unauthorized
        assert response.status_code == 401
```

**실행 결과:** ❌ 실패 (Auth 우회 로직 없음)

```bash
pytest tests/integration/adapters/test_dev_mode_security.py -v
# FAILED: AssertionError: assert 401 != 401
```

---

### Step 2.2: Green - security.py에 우회 로직 추가

**목표:** 최소 구현으로 테스트 통과

**파일:** `src/adapters/inbound/http/security.py`

```python
from fastapi import Request, HTTPException, status
from src.config.settings import Settings

settings = Settings()

async def verify_token(request: Request):
    """토큰 검증 (DEV_MODE 시 localhost는 우회)"""

    # Phase 2: DEV_MODE + localhost Origin 시 우회
    if settings.dev_mode:
        origin = request.headers.get("origin", "")
        if origin.startswith(("http://localhost", "http://127.0.0.1")):
            return  # Skip auth

    # 기존 토큰 검증 로직
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = auth_header.split(" ")[1]
    # ... 토큰 검증 로직 ...
```

**실행 결과:** ✅ 통과

```bash
pytest tests/integration/adapters/test_dev_mode_security.py -v
# PASSED: 3 tests
```

---

### Step 2.3: Refactor - Origin 검증 함수 분리

**목표:** 가독성 및 테스트 용이성 향상

**파일:** `src/adapters/inbound/http/security.py` (Refactored)

```python
from fastapi import Request, HTTPException, status
from src.config.settings import Settings
from typing import Optional

settings = Settings()

def is_localhost_origin(origin: Optional[str]) -> bool:
    """Origin이 localhost인지 확인"""
    if not origin:
        return False
    return origin.startswith(("http://localhost", "http://127.0.0.1"))

async def verify_token(request: Request):
    """토큰 검증 (DEV_MODE 시 localhost는 우회)"""

    # DEV_MODE + localhost Origin 시 우회
    if settings.dev_mode and is_localhost_origin(request.headers.get("origin")):
        return  # Skip auth

    # 토큰 검증 (기존 로직)
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = auth_header.split(" ")[1]
    # ... 토큰 검증 로직 ...
```

**테스트 추가:**

```python
# tests/integration/adapters/test_dev_mode_security.py

from src.adapters.inbound.http.security import is_localhost_origin

def test_is_localhost_origin():
    """Refactor: is_localhost_origin 함수 검증"""
    assert is_localhost_origin("http://localhost:3000") is True
    assert is_localhost_origin("http://127.0.0.1:3000") is True
    assert is_localhost_origin("https://localhost:3000") is False  # HTTPS는 제외
    assert is_localhost_origin("https://example.com") is False
    assert is_localhost_origin(None) is False
```

**실행 결과:** ✅ 모든 테스트 통과 (리팩토링 성공)

```bash
pytest tests/integration/adapters/test_dev_mode_security.py -v
# PASSED: 4 tests
```

---

## Verification

### 로컬 테스트
```bash
# DEV_MODE=true (localhost 우회)
DEV_MODE=true uvicorn src.main:app --reload

# 브라우저 Console:
fetch("http://localhost:8000/api/chat/stream", {
    headers: {"Origin": "http://localhost:3000"}
})
// 응답: 200 OK (토큰 없이 성공)
```

### 통합 테스트
```bash
pytest tests/integration/adapters/test_dev_mode_security.py -v
# PASSED: 4 tests
```

---

## Critical Files

| 파일 | 변경 사항 |
|------|----------|
| `src/adapters/inbound/http/security.py` | DEV_MODE 우회 로직, is_localhost_origin 함수 추가 |
| `tests/integration/adapters/test_dev_mode_security.py` | 통합 테스트 추가 |

---

## Security Considerations

### ⚠️ 위험
- DEV_MODE가 프로덕션 환경에 유출되면 보안 취약점 발생

### ✅ 대응
1. **환경변수 검증**: Phase 1에서 경고 메시지 추가
2. **.env.example**: `DEV_MODE=false` 명시
3. **문서화**: Phase 7에서 "DEV_MODE는 로컬 개발 전용" 명시
4. **CI 검증**: 프로덕션 배포 시 DEV_MODE=false 강제

---

## Next Steps

**Phase 3로 이동**: CORS Middleware (조건부 확장)

**Rollback 조건**: 보안 테스트 실패 시 우회 로직 제거 후 재시도

---

## TDD 검증 체크리스트

- [x] **Red**: 테스트 작성 → 실행 → 실패 확인
- [x] **Green**: 최소 구현 → 테스트 통과
- [x] **Refactor**: is_localhost_origin 함수 분리 → 테스트 여전히 통과

---

*Last Updated: 2026-02-05*
*TDD: Red-Green-Refactor*
*Layer: Security (인증/인가)*
