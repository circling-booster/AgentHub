# Phase 1: Domain Entities

## 개요

Dynamic Configuration System에 필요한 Domain Entity를 정의합니다. 순수 Python으로 작성하며 외부 라이브러리에 의존하지 않습니다.

**TDD Required:** ✅ 각 엔티티 작성 전 테스트 먼저 작성

---

## Step 1.1: LlmProvider Enum 추가

**파일:** `src/domain/entities/enums.py` (기존 파일 확장)

**테스트 먼저 작성:** `tests/unit/domain/entities/test_enums.py` (확장)

### 테스트 시나리오

```python
# tests/unit/domain/entities/test_enums.py (확장)

from src.domain.entities.enums import LlmProvider

class TestLlmProvider:
    def test_openai_provider(self):
        """OpenAI provider enum"""
        assert LlmProvider.OPENAI == "openai"
        assert LlmProvider.OPENAI.value == "openai"

    def test_anthropic_provider(self):
        """Anthropic provider enum"""
        assert LlmProvider.ANTHROPIC == "anthropic"

    def test_google_provider(self):
        """Google provider enum"""
        assert LlmProvider.GOOGLE == "google"

    def test_provider_from_string(self):
        """문자열에서 enum 생성"""
        provider = LlmProvider("openai")
        assert provider == LlmProvider.OPENAI

    def test_all_providers_listed(self):
        """모든 provider가 enum에 정의됨"""
        providers = [p.value for p in LlmProvider]
        assert "openai" in providers
        assert "anthropic" in providers
        assert "google" in providers
```

### 구현

```python
# src/domain/entities/enums.py (기존 파일에 추가)

class LlmProvider(str, Enum):
    """LLM Provider"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
```

---

## Step 1.2: ApiKeyConfig 엔티티

**파일:** `src/domain/entities/api_key_config.py`

**테스트 먼저 작성:** `tests/unit/domain/entities/test_api_key_config.py`

### 테스트 시나리오

```python
# tests/unit/domain/entities/test_api_key_config.py

from datetime import datetime, timezone
from src.domain.entities.api_key_config import ApiKeyConfig
from src.domain.entities.enums import LlmProvider

class TestApiKeyConfig:
    def test_create_with_required_fields(self):
        """필수 필드만으로 생성"""
        config = ApiKeyConfig(
            id="key-1",
            provider=LlmProvider.OPENAI,
            encrypted_key="encrypted-data-here",
        )
        assert config.id == "key-1"
        assert config.provider == LlmProvider.OPENAI
        assert config.encrypted_key == "encrypted-data-here"
        assert config.name == ""
        assert config.is_active is True

    def test_create_with_all_fields(self):
        """모든 필드 포함 생성"""
        now = datetime.now(timezone.utc)
        config = ApiKeyConfig(
            id="key-1",
            provider=LlmProvider.ANTHROPIC,
            encrypted_key="encrypted-data",
            name="My Anthropic Key",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        assert config.name == "My Anthropic Key"
        assert config.is_active is True
        assert config.created_at == now

    def test_datetime_uses_timezone_aware(self):
        """datetime이 timezone-aware인지 확인"""
        config = ApiKeyConfig(
            id="key-1",
            provider=LlmProvider.OPENAI,
            encrypted_key="encrypted",
        )
        assert config.created_at.tzinfo is not None
        assert config.updated_at.tzinfo is not None

    def test_default_is_active_true(self):
        """기본값 is_active=True"""
        config = ApiKeyConfig(
            id="key-1",
            provider=LlmProvider.GOOGLE,
            encrypted_key="encrypted",
        )
        assert config.is_active is True

    def test_provider_is_enum(self):
        """provider가 LlmProvider enum인지 확인"""
        config = ApiKeyConfig(
            id="key-1",
            provider=LlmProvider.OPENAI,
            encrypted_key="encrypted",
        )
        assert isinstance(config.provider, LlmProvider)

    def test_encrypted_key_not_empty(self):
        """encrypted_key가 빈 문자열이 아님"""
        config = ApiKeyConfig(
            id="key-1",
            provider=LlmProvider.OPENAI,
            encrypted_key="some-encrypted-data",
        )
        assert len(config.encrypted_key) > 0

    def test_name_defaults_to_empty_string(self):
        """name이 기본값으로 빈 문자열"""
        config = ApiKeyConfig(
            id="key-1",
            provider=LlmProvider.OPENAI,
            encrypted_key="encrypted",
        )
        assert config.name == ""

    def test_created_at_and_updated_at_same_on_creation(self):
        """생성 시 created_at과 updated_at이 거의 동일"""
        config = ApiKeyConfig(
            id="key-1",
            provider=LlmProvider.OPENAI,
            encrypted_key="encrypted",
        )
        # Tolerance: 1 second
        delta = (config.updated_at - config.created_at).total_seconds()
        assert delta < 1.0

    def test_multiple_providers_distinct(self):
        """서로 다른 provider가 구별됨"""
        openai_config = ApiKeyConfig(
            id="key-1",
            provider=LlmProvider.OPENAI,
            encrypted_key="encrypted-1",
        )
        anthropic_config = ApiKeyConfig(
            id="key-2",
            provider=LlmProvider.ANTHROPIC,
            encrypted_key="encrypted-2",
        )
        assert openai_config.provider != anthropic_config.provider

    def test_is_active_can_be_false(self):
        """is_active를 False로 설정 가능"""
        config = ApiKeyConfig(
            id="key-1",
            provider=LlmProvider.OPENAI,
            encrypted_key="encrypted",
            is_active=False,
        )
        assert config.is_active is False

    def test_get_masked_key_returns_masked_string(self):
        """get_masked_key()가 마스킹된 키 반환"""
        config = ApiKeyConfig(
            id="key-1",
            provider=LlmProvider.OPENAI,
            encrypted_key="gAAAAABl1234567890abcdefghij",
        )
        masked = config.get_masked_key()
        assert masked.startswith("gAA")
        assert "***" in masked
        assert masked.endswith("ghij")
        assert "1234567890abcdef" not in masked

    def test_get_masked_key_handles_short_keys(self):
        """짧은 키도 마스킹 처리"""
        config = ApiKeyConfig(
            id="key-1",
            provider=LlmProvider.OPENAI,
            encrypted_key="short",
        )
        masked = config.get_masked_key()
        assert masked == "***"
```

### 구현

```python
# src/domain/entities/api_key_config.py

"""ApiKeyConfig 엔티티

API Key 설정을 표현합니다. 순수 Python으로 작성됩니다.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.domain.entities.enums import LlmProvider


@dataclass
class ApiKeyConfig:
    """
    API Key 설정

    LLM Provider별 API Key를 암호화하여 저장합니다.

    Attributes:
        id: 설정 ID (UUID)
        provider: LLM Provider (openai, anthropic, google)
        encrypted_key: 암호화된 API Key (Fernet)
        name: API Key 이름 (선택, 사용자 지정)
        is_active: 활성 상태 (기본: True)
        created_at: 생성 시각 (UTC, timezone-aware)
        updated_at: 수정 시각 (UTC, timezone-aware)
    """

    id: str
    provider: LlmProvider
    encrypted_key: str
    name: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_masked_key(self) -> str:
        """암호화된 키를 마스킹하여 반환 (보안)

        암호화된 키를 base64 디코딩한 후 중간 부분을 ***로 마스킹합니다.
        예: "gAAAAABl..." → "gAA***..."

        Returns:
            마스킹된 키 문자열
        """
        if len(self.encrypted_key) <= 10:
            return "***"

        # 앞 3글자 + *** + 뒤 4글자
        return f"{self.encrypted_key[:3]}***{self.encrypted_key[-4:]}"
```

---

## Step 1.3: ModelConfig 엔티티

**파일:** `src/domain/entities/model_config.py`

**테스트 먼저 작성:** `tests/unit/domain/entities/test_model_config.py`

### 테스트 시나리오

```python
# tests/unit/domain/entities/test_model_config.py

from datetime import datetime, timezone
from src.domain.entities.model_config import ModelConfig
from src.domain.entities.enums import LlmProvider

class TestModelConfig:
    def test_create_with_required_fields(self):
        """필수 필드만으로 생성"""
        config = ModelConfig(
            id="model-1",
            provider=LlmProvider.OPENAI,
            model_id="gpt-4o-mini",
        )
        assert config.id == "model-1"
        assert config.provider == LlmProvider.OPENAI
        assert config.model_id == "gpt-4o-mini"
        assert config.name == ""
        assert config.is_default is False
        assert config.parameters == {}

    def test_create_with_all_fields(self):
        """모든 필드 포함 생성"""
        params = {"temperature": 0.7, "max_tokens": 2048}
        now = datetime.now(timezone.utc)
        config = ModelConfig(
            id="model-1",
            provider=LlmProvider.ANTHROPIC,
            model_id="claude-sonnet-4.5",
            name="Claude Sonnet 4.5 (Default)",
            is_default=True,
            parameters=params,
            created_at=now,
            updated_at=now,
        )
        assert config.name == "Claude Sonnet 4.5 (Default)"
        assert config.is_default is True
        assert config.parameters == params

    def test_datetime_uses_timezone_aware(self):
        """datetime이 timezone-aware인지 확인"""
        config = ModelConfig(
            id="model-1",
            provider=LlmProvider.OPENAI,
            model_id="gpt-4o",
        )
        assert config.created_at.tzinfo is not None
        assert config.updated_at.tzinfo is not None

    def test_default_is_default_false(self):
        """기본값 is_default=False"""
        config = ModelConfig(
            id="model-1",
            provider=LlmProvider.GOOGLE,
            model_id="gemini-2.0-flash-exp",
        )
        assert config.is_default is False

    def test_provider_is_enum(self):
        """provider가 LlmProvider enum인지 확인"""
        config = ModelConfig(
            id="model-1",
            provider=LlmProvider.OPENAI,
            model_id="gpt-4o",
        )
        assert isinstance(config.provider, LlmProvider)

    def test_parameters_defaults_to_empty_dict(self):
        """parameters가 기본값으로 빈 딕셔너리"""
        config = ModelConfig(
            id="model-1",
            provider=LlmProvider.OPENAI,
            model_id="gpt-4o",
        )
        assert config.parameters == {}

    def test_parameters_are_mutable(self):
        """parameters가 dict 타입"""
        params = {"temperature": 0.5}
        config = ModelConfig(
            id="model-1",
            provider=LlmProvider.OPENAI,
            model_id="gpt-4o",
            parameters=params,
        )
        assert isinstance(config.parameters, dict)
        assert config.parameters["temperature"] == 0.5

    def test_model_id_format(self):
        """model_id가 문자열"""
        config = ModelConfig(
            id="model-1",
            provider=LlmProvider.OPENAI,
            model_id="gpt-4o-mini",
        )
        assert isinstance(config.model_id, str)
        assert len(config.model_id) > 0

    def test_is_default_can_be_true(self):
        """is_default를 True로 설정 가능"""
        config = ModelConfig(
            id="model-1",
            provider=LlmProvider.ANTHROPIC,
            model_id="claude-sonnet-4.5",
            is_default=True,
        )
        assert config.is_default is True

    def test_name_defaults_to_empty_string(self):
        """name이 기본값으로 빈 문자열"""
        config = ModelConfig(
            id="model-1",
            provider=LlmProvider.GOOGLE,
            model_id="gemini-1.5-pro",
        )
        assert config.name == ""
```

### 구현

```python
# src/domain/entities/model_config.py

"""ModelConfig 엔티티

LLM 모델 설정을 표현합니다. 순수 Python으로 작성됩니다.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.domain.entities.enums import LlmProvider


@dataclass
class ModelConfig:
    """
    LLM 모델 설정

    사용자가 선택 가능한 LLM 모델을 표현합니다.

    Attributes:
        id: 설정 ID (UUID)
        provider: LLM Provider (openai, anthropic, google)
        model_id: 모델 ID (예: "gpt-4o-mini", "claude-sonnet-4.5")
        name: 모델 이름 (선택, 사용자 지정)
        is_default: 기본 모델 여부 (기본: False)
        parameters: 모델 파라미터 (temperature, max_tokens 등, JSON)
        created_at: 생성 시각 (UTC, timezone-aware)
        updated_at: 수정 시각 (UTC, timezone-aware)
    """

    id: str
    provider: LlmProvider
    model_id: str
    name: str = ""
    is_default: bool = False
    parameters: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

---

## Step 1.4: Configuration Exceptions 추가

**파일:** `src/domain/exceptions.py` (기존 파일 확장)
**파일:** `src/domain/constants.py` (ErrorCode 추가)

**테스트 먼저 작성:** `tests/unit/domain/test_exceptions.py` (확장)

### ErrorCode 추가

```python
# src/domain/constants.py의 ErrorCode 클래스에 추가

class ErrorCode:
    # ... 기존 코드 ...

    # Configuration 관련 에러
    CONFIGURATION_NOT_FOUND = "ConfigurationNotFoundError"
    CONFIGURATION_VALIDATION = "ConfigurationValidationError"
    INVALID_PROVIDER = "InvalidProviderError"
    ENCRYPTION_ERROR = "EncryptionError"
    DECRYPTION_ERROR = "DecryptionError"
    MIGRATION_ERROR = "MigrationError"
```

### Exception 클래스 추가

```python
# src/domain/exceptions.py에 추가

# ============================================================
# Configuration 관련 예외
# ============================================================


class ConfigurationNotFoundError(DomainException):
    """설정을 찾을 수 없음"""

    def __init__(self, message: str):
        super().__init__(message, code=ErrorCode.CONFIGURATION_NOT_FOUND)


class ConfigurationValidationError(DomainException):
    """설정 검증 실패

    Note: 현재 사용되지 않지만 향후 다음 용도로 사용 예정:
    - API Key 형식 검증 (예: OpenAI key는 "sk-"로 시작)
    - Model ID 검증 (Provider별 유효한 모델 ID 확인)
    - Parameters 검증 (temperature 범위, max_tokens 제한 등)
    """

    def __init__(self, message: str):
        super().__init__(message, code=ErrorCode.CONFIGURATION_VALIDATION)


class InvalidProviderError(DomainException):
    """잘못된 Provider"""

    def __init__(self, message: str):
        super().__init__(message, code=ErrorCode.INVALID_PROVIDER)


class EncryptionError(DomainException):
    """암호화 실패"""

    def __init__(self, message: str):
        super().__init__(message, code=ErrorCode.ENCRYPTION_ERROR)


class DecryptionError(DomainException):
    """복호화 실패"""

    def __init__(self, message: str):
        super().__init__(message, code=ErrorCode.DECRYPTION_ERROR)


class MigrationError(DomainException):
    """마이그레이션 실패"""

    def __init__(self, message: str):
        super().__init__(message, code=ErrorCode.MIGRATION_ERROR)
```

### 테스트 시나리오

```python
# tests/unit/domain/test_exceptions.py (기존 파일 확장)

from src.domain.exceptions import (
    ConfigurationNotFoundError,
    ConfigurationValidationError,
    InvalidProviderError,
    EncryptionError,
    DecryptionError,
    MigrationError,
)
from src.domain.constants import ErrorCode

class TestConfigurationExceptions:
    def test_configuration_not_found_error(self):
        """설정 미발견 에러"""
        error = ConfigurationNotFoundError("API Key not found")
        assert error.message == "API Key not found"
        assert error.code == ErrorCode.CONFIGURATION_NOT_FOUND

    def test_configuration_validation_error(self):
        """설정 검증 실패 에러"""
        error = ConfigurationValidationError("Invalid provider")
        assert error.message == "Invalid provider"
        assert error.code == ErrorCode.CONFIGURATION_VALIDATION

    def test_invalid_provider_error(self):
        """잘못된 Provider 에러"""
        error = InvalidProviderError("Provider 'invalid' not supported")
        assert error.message == "Provider 'invalid' not supported"
        assert error.code == ErrorCode.INVALID_PROVIDER

    def test_encryption_error(self):
        """암호화 실패 에러"""
        error = EncryptionError("Failed to encrypt API key")
        assert error.message == "Failed to encrypt API key"
        assert error.code == ErrorCode.ENCRYPTION_ERROR

    def test_decryption_error(self):
        """복호화 실패 에러"""
        error = DecryptionError("Failed to decrypt API key")
        assert error.message == "Failed to decrypt API key"
        assert error.code == ErrorCode.DECRYPTION_ERROR

    def test_migration_error(self):
        """마이그레이션 실패 에러"""
        error = MigrationError("Migration rollback")
        assert error.message == "Migration rollback"
        assert error.code == ErrorCode.MIGRATION_ERROR
```

---

## Step 1.5: __init__.py Export 업데이트

**파일:** `src/domain/entities/__init__.py` (기존 파일 확장)

### 수정

```python
# src/domain/entities/__init__.py (기존 export에 추가)

"""Domain Entities - 비즈니스 개념 모델"""

from .api_key_config import ApiKeyConfig
from .elicitation_request import ElicitationRequest, ElicitationAction, ElicitationStatus
from .enums import LlmProvider  # 추가
from .model_config import ModelConfig
from .prompt_template import PromptTemplate, PromptArgument
from .resource import Resource, ResourceContent
from .sampling_request import SamplingRequest, SamplingStatus
from .stream_chunk import StreamChunk

__all__ = [
    "ApiKeyConfig",
    "ElicitationRequest",
    "ElicitationAction",
    "ElicitationStatus",
    "LlmProvider",  # 추가
    "ModelConfig",
    "PromptArgument",
    "PromptTemplate",
    "Resource",
    "ResourceContent",
    "SamplingRequest",
    "SamplingStatus",
    "StreamChunk",
]
```

**Note:** 이 Step은 테스트가 필요 없습니다 (import 구조 변경).

---

## Verification

```bash
# 모든 엔티티 테스트
pytest tests/unit/domain/entities/test_enums.py::TestLlmProvider -v
pytest tests/unit/domain/entities/test_api_key_config.py -v
pytest tests/unit/domain/entities/test_model_config.py -v

# 예외 테스트
pytest tests/unit/domain/test_exceptions.py::TestConfigurationExceptions -v

# 전체 Domain 엔티티 테스트
pytest tests/unit/domain/entities/ -v
```

---

## Step 1.6: Documentation Update

**목표:** Phase 1에서 추가된 Domain Entity 문서화

**문서화 항목:**

| 작업 | 대상 파일 | 유형 | 내용 |
|------|----------|------|------|
| Modify | docs/developers/architecture/layer/core/README.md | Architecture | Configuration 엔티티 섹션 추가 (ApiKeyConfig, ModelConfig, LlmProvider) |
| Modify | tests/docs/STRUCTURE.md | Test Documentation | Configuration 엔티티 테스트 전략 추가 (암호화 키 검증, datetime 일관성) |

**주의사항:**
- 엔티티 다이어그램은 포함하지 않음 (코드 우선 접근)
- Fernet 암호화는 Phase 4 Adapter 문서화 시 상세 설명

---

## Step 1.7: Git Commit

**목표:** Phase 1 완료 커밋

**절차:**

1. **Phase 시작 전 회귀 테스트 베이스라인 기록**
   ```bash
   pytest -q --tb=line -x
   # 결과: N개 통과, M개 실패 (있다면 기존 이슈)
   ```

2. **Phase 완료 후 전체 테스트 실행**
   ```bash
   # 모든 엔티티 테스트
   pytest tests/unit/domain/entities/test_enums.py::TestLlmProvider -v
   pytest tests/unit/domain/entities/test_api_key_config.py -v
   pytest tests/unit/domain/entities/test_model_config.py -v

   # 예외 테스트
   pytest tests/unit/domain/test_exceptions.py::TestConfigurationExceptions -v

   # 전체 회귀 테스트
   pytest -q --tb=line -x
   ```

3. **커버리지 확인**
   ```bash
   pytest --cov=src --cov-fail-under=80 -q
   ```

4. **커밋 수행**
   ```bash
   git add src/domain/entities/api_key_config.py \
           src/domain/entities/model_config.py \
           src/domain/entities/enums.py \
           src/domain/entities/__init__.py \
           src/domain/constants.py \
           src/domain/exceptions.py \
           tests/unit/domain/entities/test_api_key_config.py \
           tests/unit/domain/entities/test_model_config.py \
           tests/unit/domain/entities/test_enums.py \
           tests/unit/domain/test_exceptions.py \
           docs/developers/architecture/layer/core/README.md \
           tests/docs/STRUCTURE.md

   git commit -m "$(cat <<'EOF'
   feat: implement Phase 1 - Domain Entities for Configuration System

   - Add ApiKeyConfig entity with Fernet encryption support
   - Add ModelConfig entity with LLM model configuration
   - Add LlmProvider enum (OPENAI, ANTHROPIC, GOOGLE)
   - Add Configuration-related exceptions (ConfigurationNotFoundError, etc.)
   - Update entity exports in __init__.py

   Test Coverage:
   - All entities have unit tests with TDD approach (~10 tests each)
   - Exception tests for Configuration error scenarios (~5 tests)
   - datetime.now(timezone.utc) used for timezone-aware timestamps

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
   EOF
   )"
   ```

5. **Phase Status 업데이트**
   - `docs/project/planning/planned/09_dynamic_configuration/README.md`에서 Phase 1 Status를 ✅로 변경

---

## Checklist

- [ ] **Phase 시작**: Status 변경 (⏸️ → 🔄)
- [ ] Step 1.1: LlmProvider enum 추가 (TDD)
- [ ] Step 1.2: ApiKeyConfig 엔티티 (TDD, ~10 tests, datetime.now(timezone.utc) 사용)
- [ ] Step 1.3: ModelConfig 엔티티 (TDD, ~10 tests, datetime.now(timezone.utc) 사용)
- [ ] Step 1.4: Configuration Exceptions 추가 (TDD, ~5 tests)
- [ ] Step 1.5: __init__.py Export 업데이트
- [ ] Step 1.6: Documentation Update (Architecture + Test Docs)
- [ ] 전체 테스트 통과 확인
- [ ] **Phase 완료**: Status 변경 (🔄 → ✅)
- [ ] Git 커밋: `feat: implement Phase 1 - Domain Entities for Configuration System`

---

*Last Updated: 2026-02-07*
*Principle: TDD (Red → Green → Refactor), Domain Purity (순수 Python), datetime.now(timezone.utc) 사용*
