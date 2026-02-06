# Phase 1: Settings Layer (Config)

## Overview

**목표:** DEV_MODE 환경변수를 지원하도록 Settings 레이어 확장

**TDD 원칙:** Red → Green → Refactor 순서 엄수

**전제 조건:** 없음 (첫 번째 Phase)

---

## Implementation Steps (TDD)

### Step 1.1: Red - dev_mode 필드 테스트 작성

**목표:** Settings에 dev_mode 필드가 있고 환경변수에서 로드되는지 검증

**테스트 파일:** `tests/integration/adapters/test_dev_mode_settings.py`

```python
import pytest
import os
from src.config.settings import Settings

class TestDevModeSettings:
    """Integration Test: DEV_MODE 환경변수 로드"""

    def test_dev_mode_false_by_default(self):
        """Red: dev_mode 기본값은 False"""
        # Given: 환경변수 없음
        if "DEV_MODE" in os.environ:
            del os.environ["DEV_MODE"]

        # When: Settings 로드
        settings = Settings()

        # Then: dev_mode는 False
        assert settings.dev_mode is False

    def test_dev_mode_true_from_env(self):
        """Red: DEV_MODE=true 시 dev_mode가 True"""
        # Given: 환경변수 설정
        os.environ["DEV_MODE"] = "true"

        # When: Settings 로드
        settings = Settings()

        # Then: dev_mode는 True
        assert settings.dev_mode is True

    def test_dev_mode_validation(self):
        """Red: DEV_MODE는 bool 타입"""
        # Given: 잘못된 값
        os.environ["DEV_MODE"] = "invalid"

        # When: Settings 로드
        # Then: ValidationError 발생
        with pytest.raises(ValueError):
            Settings()
```

**실행 결과:** ❌ 실패 (dev_mode 필드 없음)

```bash
pytest tests/integration/adapters/test_dev_mode_settings.py -v
# FAILED: AttributeError: 'Settings' object has no attribute 'dev_mode'
```

---

### Step 1.2: Green - Settings에 dev_mode 추가

**목표:** 최소 구현으로 테스트 통과

**파일:** `src/config/settings.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""

    # Existing fields...
    host: str = "localhost"
    port: int = 8000

    # Phase 1: DEV_MODE support
    dev_mode: bool = False  # DEV_MODE=true 시 개발 모드 활성화

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # 대소문자 구분 없이 환경변수 매칭
        case_sensitive = False
```

**실행 결과:** ✅ 통과

```bash
pytest tests/integration/adapters/test_dev_mode_settings.py -v
# PASSED: 3 tests
```

---

### Step 1.3: Refactor - 환경변수 검증 추가

**목표:** 프로덕션 환경에서 실수로 DEV_MODE가 활성화되지 않도록 검증 추가

**파일:** `src/config/settings.py` (Refactored)

```python
from pydantic_settings import BaseSettings
from pydantic import field_validator
import warnings

class Settings(BaseSettings):
    """Application settings"""

    dev_mode: bool = False

    @field_validator("dev_mode")
    def warn_if_dev_mode_enabled(cls, v):
        """DEV_MODE 활성화 시 경고"""
        if v:
            warnings.warn(
                "DEV_MODE is enabled. This should ONLY be used in local development. "
                "NEVER deploy with DEV_MODE=true to production!",
                UserWarning
            )
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
```

**테스트 추가:**

```python
# tests/integration/adapters/test_dev_mode_settings.py

def test_dev_mode_warns_when_enabled(caplog):
    """Refactor: DEV_MODE=true 시 경고 메시지 출력"""
    # Given
    os.environ["DEV_MODE"] = "true"

    # When
    with pytest.warns(UserWarning, match="DEV_MODE is enabled"):
        settings = Settings()

    # Then
    assert settings.dev_mode is True
```

**실행 결과:** ✅ 모든 테스트 통과 (리팩토링 성공)

```bash
pytest tests/integration/adapters/test_dev_mode_settings.py -v
# PASSED: 4 tests
```

---

## Verification

### 로컬 테스트
```bash
# DEV_MODE=false (기본값)
python -c "from src.config.settings import Settings; print(Settings().dev_mode)"
# Output: False

# DEV_MODE=true
DEV_MODE=true python -c "from src.config.settings import Settings; print(Settings().dev_mode)"
# Output: True (경고 메시지 표시)
```

### 통합 테스트
```bash
pytest tests/integration/adapters/test_dev_mode_settings.py -v
# PASSED: 4 tests
```

---

## Critical Files

| 파일 | 변경 사항 |
|------|----------|
| `src/config/settings.py` | dev_mode 필드 추가, 검증 추가 |
| `tests/integration/adapters/test_dev_mode_settings.py` | 통합 테스트 추가 |

---

## Next Steps

**Phase 2로 이동**: Security Layer (Auth 우회 로직 추가)

**Rollback 조건**: 테스트 실패 시 dev_mode 필드 제거 후 재시도

---

## TDD 검증 체크리스트

- [x] **Red**: 테스트 작성 → 실행 → 실패 확인
- [x] **Green**: 최소 구현 → 테스트 통과
- [x] **Refactor**: 검증 로직 추가 → 테스트 여전히 통과

---

*Last Updated: 2026-02-05*
*TDD: Red-Green-Refactor*
*Layer: Config (헥사고날 최상위)*
