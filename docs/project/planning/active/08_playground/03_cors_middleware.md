# Phase 3: CORS Middleware (조건부 확장)

## Overview

**목표:** DEV_MODE=true 시 localhost Origin 허용하도록 CORS 확장

**TDD 원칙:** Red → Green → Refactor 순서 엄수

**전제 조건:** Phase 1-2 완료 (Settings.dev_mode, Auth 우회)

---

## Implementation Steps (TDD)

### Step 3.1: Red - DEV_MODE CORS 테스트 작성

**목표:** DEV_MODE 시 localhost에서 CORS 에러 없이 요청 가능

**테스트 파일:** `tests/integration/adapters/test_dev_mode_cors.py`

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

class TestDevModeCors:
    """Integration Test: DEV_MODE CORS 확장"""

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

    def test_localhost_cors_allowed_in_dev_mode(self, client_dev_mode):
        """Red: DEV_MODE 시 localhost CORS 허용"""
        # Given: localhost Origin
        headers = {"Origin": "http://localhost:3000"}

        # When: Preflight 요청
        response = client_dev_mode.options("/api/health", headers=headers)

        # Then: CORS 헤더 포함
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_localhost_cors_blocked_in_prod_mode(self, client_prod_mode):
        """Red: 프로덕션 모드에서는 localhost CORS 차단"""
        # Given: localhost Origin
        headers = {"Origin": "http://localhost:3000"}

        # When: Preflight 요청
        response = client_prod_mode.options("/api/health", headers=headers)

        # Then: CORS 헤더 없음
        assert "access-control-allow-origin" not in response.headers

    def test_chrome_extension_cors_always_allowed(self, client_dev_mode, client_prod_mode):
        """Red: Extension Origin은 항상 허용"""
        # Given: Chrome Extension Origin
        headers = {"Origin": "chrome-extension://abc123"}

        # When: DEV/Prod 모두 테스트
        dev_response = client_dev_mode.options("/api/health", headers=headers)
        prod_response = client_prod_mode.options("/api/health", headers=headers)

        # Then: 둘 다 CORS 허용
        assert "access-control-allow-origin" in dev_response.headers
        assert "access-control-allow-origin" in prod_response.headers
```

**실행 결과:** ❌ 실패 (CORS 조건부 로직 없음)

```bash
pytest tests/integration/adapters/test_dev_mode_cors.py -v
# FAILED: AssertionError: assert 'access-control-allow-origin' in response.headers
```

---

### Step 3.2: Green - app.py에 조건부 CORS 추가

**목표:** 최소 구현으로 테스트 통과

**파일:** `src/adapters/inbound/http/app.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import Settings

settings = Settings()

def create_app() -> FastAPI:
    """FastAPI 앱 생성"""
    app = FastAPI(title="AgentHub API")

    # Phase 3: 조건부 CORS 설정
    if settings.dev_mode:
        # DEV_MODE: localhost 허용
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
            allow_origin_regex=r"^chrome-extension://[a-zA-Z0-9_-]+$",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        # 프로덕션: Extension만 허용
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"^chrome-extension://[a-zA-Z0-9_-]+$",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # ... 라우터 등록 ...
    return app

app = create_app()
```

**실행 결과:** ✅ 통과

```bash
pytest tests/integration/adapters/test_dev_mode_cors.py -v
# PASSED: 3 tests
```

---

### Step 3.3: Refactor - CORS 설정 함수 분리

**목표:** 가독성 및 유지보수성 향상

**파일:** `src/adapters/inbound/http/app.py` (Refactored)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import Settings

settings = Settings()

def get_cors_origins() -> dict:
    """CORS 설정 반환 (DEV_MODE에 따라 조건부)"""
    base_config = {
        "allow_origin_regex": r"^chrome-extension://[a-zA-Z0-9_-]+$",
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }

    if settings.dev_mode:
        # DEV_MODE: localhost 허용
        base_config["allow_origins"] = [
            "http://localhost:*",
            "http://127.0.0.1:*"
        ]

    return base_config

def create_app() -> FastAPI:
    """FastAPI 앱 생성"""
    app = FastAPI(title="AgentHub API")

    # CORS Middleware
    cors_config = get_cors_origins()
    app.add_middleware(CORSMiddleware, **cors_config)

    # ... 라우터 등록 ...
    return app

app = create_app()
```

**테스트 추가:**

```python
# tests/integration/adapters/test_dev_mode_cors.py

from src.adapters.inbound.http.app import get_cors_origins

def test_get_cors_origins_dev_mode(monkeypatch):
    """Refactor: DEV_MODE 시 CORS 설정 확인"""
    monkeypatch.setenv("DEV_MODE", "true")
    config = get_cors_origins()

    assert "allow_origins" in config
    assert "http://localhost:*" in config["allow_origins"]
    assert config["allow_origin_regex"] == r"^chrome-extension://[a-zA-Z0-9_-]+$"

def test_get_cors_origins_prod_mode(monkeypatch):
    """Refactor: 프로덕션 모드 시 CORS 설정 확인"""
    monkeypatch.setenv("DEV_MODE", "false")
    config = get_cors_origins()

    assert "allow_origins" not in config
    assert config["allow_origin_regex"] == r"^chrome-extension://[a-zA-Z0-9_-]+$"
```

**실행 결과:** ✅ 모든 테스트 통과 (리팩토링 성공)

```bash
pytest tests/integration/adapters/test_dev_mode_cors.py -v
# PASSED: 5 tests
```

---

## Verification

### 로컬 테스트
```bash
# DEV_MODE=true (localhost 허용)
DEV_MODE=true uvicorn src.main:app --reload

# 브라우저 Console (http://localhost:3000):
fetch("http://localhost:8000/api/health", {
    method: "GET",
    headers: {"Origin": "http://localhost:3000"}
})
// 응답: 200 OK (CORS 허용)
```

### 통합 테스트
```bash
pytest tests/integration/adapters/test_dev_mode_cors.py -v
# PASSED: 5 tests
```

---

## Critical Files

| 파일 | 변경 사항 |
|------|----------|
| `src/adapters/inbound/http/app.py` | 조건부 CORS, get_cors_origins 함수 추가 |
| `tests/integration/adapters/test_dev_mode_cors.py` | 통합 테스트 추가 |

---

## Next Steps

**Phase 4로 이동**: Playground Static Files (HTML/CSS/JS)

**Rollback 조건**: CORS 테스트 실패 시 조건부 로직 제거 후 재시도

---

## TDD 검증 체크리스트

- [x] **Red**: 테스트 작성 → 실행 → 실패 확인
- [x] **Green**: 최소 구현 → 테스트 통과
- [x] **Refactor**: get_cors_origins 함수 분리 → 테스트 여전히 통과

---

*Last Updated: 2026-02-05*
*TDD: Red-Green-Refactor*
*Layer: Middleware (CORS)*
