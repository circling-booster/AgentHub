# Phase 2: Port Interface + Fake

## 개요

Port Interface와 테스트용 Fake를 함께 작성합니다. Phase 3에서 Domain Services 테스트 시 필요하므로 여기서 함께 구현합니다.

**TDD Required:** ✅ Fake 구현 전 테스트 먼저 작성

---

## Step 2.1: ConfigurationStoragePort

**파일:** `src/domain/ports/outbound/configuration_storage_port.py`

### Port Interface

```python
# src/domain/ports/outbound/configuration_storage_port.py

"""ConfigurationStoragePort - Configuration 저장소 포트

API Key와 Model 설정을 SQLite에 저장하는 포트입니다.
"""

from abc import ABC, abstractmethod
from src.domain.entities.api_key_config import ApiKeyConfig
from src.domain.entities.model_config import ModelConfig
from src.domain.entities.enums import LlmProvider


class ConfigurationStoragePort(ABC):
    """Configuration 저장소 포트 (API Key + Model)

    DB-First Configuration 원칙에 따라 SQLite를 단일 진실 공급원으로 사용합니다.
    """

    # ============================================================
    # API Key 관리 (5 methods)
    # ============================================================

    @abstractmethod
    async def create_api_key(self, config: ApiKeyConfig) -> None:
        """API Key 생성"""
        pass

    @abstractmethod
    async def get_api_key(self, key_id: str) -> ApiKeyConfig:
        """API Key 조회 (ID로)"""
        pass

    @abstractmethod
    async def get_api_key_by_provider(self, provider: LlmProvider) -> ApiKeyConfig:
        """API Key 조회 (Provider로)

        활성화된 키 중 가장 최근에 생성된 키 반환
        """
        pass

    @abstractmethod
    async def update_api_key(self, config: ApiKeyConfig) -> None:
        """API Key 수정"""
        pass

    @abstractmethod
    async def delete_api_key(self, key_id: str) -> None:
        """API Key 삭제"""
        pass

    @abstractmethod
    async def list_api_keys(
        self, provider: LlmProvider | None = None
    ) -> list[ApiKeyConfig]:
        """API Key 목록 조회

        Args:
            provider: Provider 필터 (None이면 전체)
        """
        pass

    # ============================================================
    # Model 관리 (6 methods)
    # ============================================================

    @abstractmethod
    async def create_model(self, config: ModelConfig) -> None:
        """Model 생성"""
        pass

    @abstractmethod
    async def get_model(self, model_id: str) -> ModelConfig:
        """Model 조회 (ID로)"""
        pass

    @abstractmethod
    async def update_model(self, config: ModelConfig) -> None:
        """Model 수정"""
        pass

    @abstractmethod
    async def delete_model(self, model_id: str) -> None:
        """Model 삭제"""
        pass

    @abstractmethod
    async def list_models(
        self, provider: LlmProvider | None = None
    ) -> list[ModelConfig]:
        """Model 목록 조회

        Args:
            provider: Provider 필터 (None이면 전체)
        """
        pass

    @abstractmethod
    async def get_default_model(self) -> ModelConfig:
        """기본 모델 조회 (is_default=True인 모델)"""
        pass

    @abstractmethod
    async def set_default_model(self, model_id: str) -> None:
        """기본 모델 설정 (다른 모델들의 is_default=False로 변경)"""
        pass

    # ============================================================
    # Migration 관리 (2 methods)
    # ============================================================

    @abstractmethod
    async def is_migration_applied(self, migration_id: str) -> bool:
        """마이그레이션 적용 여부 확인

        Args:
            migration_id: Migration ID (예: "001_env_to_db")

        Returns:
            True if already applied, False otherwise
        """
        pass

    @abstractmethod
    async def mark_migration_applied(self, migration_id: str) -> None:
        """마이그레이션 적용 기록

        Args:
            migration_id: Migration ID
        """
        pass
```

**Note:** Port는 ABC이므로 테스트가 필요 없습니다. Fake에서 동작을 검증합니다.

---

## Step 2.2: EncryptionPort

**파일:** `src/domain/ports/outbound/encryption_port.py`

### Port Interface

```python
# src/domain/ports/outbound/encryption_port.py

"""EncryptionPort - 암호화/복호화 포트

Fernet 대칭 암호화를 추상화합니다.
"""

from abc import ABC, abstractmethod


class EncryptionPort(ABC):
    """암호화/복호화 포트

    Fernet 대칭 암호화를 사용합니다.
    키 생성(generate_key)은 Adapter 내부 관심사이므로 Port에 포함하지 않습니다.
    """

    @abstractmethod
    async def encrypt(self, plaintext: str) -> str:
        """평문 암호화

        Args:
            plaintext: 암호화할 평문 (API Key 등)

        Returns:
            암호화된 문자열 (Fernet token)
        """
        pass

    @abstractmethod
    async def decrypt(self, ciphertext: str) -> str:
        """암호문 복호화

        Args:
            ciphertext: 복호화할 암호문 (Fernet token)

        Returns:
            복호화된 평문

        Raises:
            DecryptionError: 복호화 실패 시
        """
        pass
```

**Note:**
- `generate_key()` 메서드는 **Port에 포함하지 않습니다** (Plan 파일의 수정사항 #4)
- 키 생성은 Adapter 내부 관심사이므로 FernetEncryptionAdapter의 정적 메서드로 구현 (Phase 4)

---

## Step 2.3: Port __init__.py Export 업데이트

**파일:** `src/domain/ports/outbound/__init__.py` (기존 파일 확장)

### 수정

```python
# src/domain/ports/outbound/__init__.py (기존 export에 추가)

"""Outbound Ports - 외부 시스템에 대한 추상화"""

from .configuration_storage_port import ConfigurationStoragePort
from .encryption_port import EncryptionPort
from .orchestrator_port import OrchestratorPort
from .storage_port import StoragePort

__all__ = [
    "ConfigurationStoragePort",
    "EncryptionPort",
    "OrchestratorPort",
    "StoragePort",
]
```

**Note:** 이 Step은 테스트가 필요 없습니다 (import 구조 변경).

---

## Step 2.4: FakeConfigurationStorage

**테스트 먼저:** `tests/unit/fakes/test_fake_configuration_storage.py`
**구현:** `tests/unit/fakes/fake_configuration_storage.py`

### 테스트 시나리오

```python
# tests/unit/fakes/test_fake_configuration_storage.py

import pytest
from src.domain.entities.api_key_config import ApiKeyConfig
from src.domain.entities.model_config import ModelConfig
from src.domain.entities.enums import LlmProvider
from src.domain.exceptions import (
    ConfigurationNotFoundError,
    ConfigurationValidationError,
)
from tests.unit.fakes.fake_configuration_storage import FakeConfigurationStorage


class TestFakeConfigurationStorage:
    """FakeConfigurationStorage 자체 테스트"""

    @pytest.fixture
    def storage(self):
        return FakeConfigurationStorage()

    # ============================================================
    # API Key 테스트 (~8 tests)
    # ============================================================

    async def test_create_api_key_stores_config(self, storage):
        """API Key 생성 후 조회 가능"""
        config = ApiKeyConfig(
            id="key-1",
            provider=LlmProvider.OPENAI,
            encrypted_key="encrypted-data",
            key_hint="sk-...data",
        )

        await storage.create_api_key(config)
        result = await storage.get_api_key("key-1")

        assert result.id == "key-1"
        assert result.provider == LlmProvider.OPENAI

    async def test_get_api_key_raises_when_not_found(self, storage):
        """존재하지 않는 API Key 조회 시 예외"""
        with pytest.raises(ConfigurationNotFoundError):
            await storage.get_api_key("nonexistent")

    async def test_get_api_key_by_provider_returns_active_key(self, storage):
        """Provider로 API Key 조회 (활성화된 키 중 최신)"""
        config1 = ApiKeyConfig(
            id="key-1",
            provider=LlmProvider.OPENAI,
            encrypted_key="old-key",
            key_hint="sk-...old1",
            is_active=True,
        )
        config2 = ApiKeyConfig(
            id="key-2",
            provider=LlmProvider.OPENAI,
            encrypted_key="new-key",
            key_hint="sk-...new2",
            is_active=True,
        )

        await storage.create_api_key(config1)
        await storage.create_api_key(config2)

        result = await storage.get_api_key_by_provider(LlmProvider.OPENAI)
        assert result.id == "key-2"  # 최신 키

    async def test_update_api_key_modifies_config(self, storage):
        """API Key 수정"""
        config = ApiKeyConfig(
            id="key-1",
            provider=LlmProvider.OPENAI,
            encrypted_key="old",
            key_hint="sk-...old0",
            name="Old Name",
        )
        await storage.create_api_key(config)

        updated = ApiKeyConfig(
            id="key-1",
            provider=LlmProvider.OPENAI,
            encrypted_key="new",
            key_hint="sk-...new0",
            name="New Name",
        )
        await storage.update_api_key(updated)

        result = await storage.get_api_key("key-1")
        assert result.name == "New Name"

    async def test_delete_api_key_removes_config(self, storage):
        """API Key 삭제"""
        config = ApiKeyConfig(
            id="key-1",
            provider=LlmProvider.OPENAI,
            encrypted_key="data",
            key_hint="sk-...data",
        )
        await storage.create_api_key(config)

        await storage.delete_api_key("key-1")

        with pytest.raises(ConfigurationNotFoundError):
            await storage.get_api_key("key-1")

    async def test_list_api_keys_returns_all(self, storage):
        """모든 API Key 조회"""
        config1 = ApiKeyConfig(
            id="key-1", provider=LlmProvider.OPENAI, encrypted_key="data1", key_hint="sk-...ata1"
        )
        config2 = ApiKeyConfig(
            id="key-2", provider=LlmProvider.ANTHROPIC, encrypted_key="data2", key_hint="sk-...ata2"
        )

        await storage.create_api_key(config1)
        await storage.create_api_key(config2)

        result = await storage.list_api_keys()
        assert len(result) == 2

    async def test_list_api_keys_filters_by_provider(self, storage):
        """Provider 필터로 API Key 조회"""
        config1 = ApiKeyConfig(
            id="key-1", provider=LlmProvider.OPENAI, encrypted_key="data1", key_hint="sk-...ata1"
        )
        config2 = ApiKeyConfig(
            id="key-2", provider=LlmProvider.ANTHROPIC, encrypted_key="data2", key_hint="sk-...ata2"
        )

        await storage.create_api_key(config1)
        await storage.create_api_key(config2)

        result = await storage.list_api_keys(provider=LlmProvider.OPENAI)
        assert len(result) == 1
        assert result[0].provider == LlmProvider.OPENAI

    async def test_list_api_keys_empty_when_no_keys(self, storage):
        """API Key가 없을 때 빈 리스트 반환"""
        result = await storage.list_api_keys()
        assert result == []

    # ============================================================
    # Model 테스트 (~7 tests)
    # ============================================================

    async def test_create_model_stores_config(self, storage):
        """Model 생성 후 조회 가능"""
        config = ModelConfig(
            id="model-1",
            provider=LlmProvider.OPENAI,
            model_id="gpt-4o-mini",
        )

        await storage.create_model(config)
        result = await storage.get_model("model-1")

        assert result.id == "model-1"
        assert result.model_id == "gpt-4o-mini"

    async def test_get_model_raises_when_not_found(self, storage):
        """존재하지 않는 Model 조회 시 예외"""
        with pytest.raises(ConfigurationNotFoundError):
            await storage.get_model("nonexistent")

    async def test_list_models_filters_by_provider(self, storage):
        """Provider 필터로 Model 조회"""
        config1 = ModelConfig(
            id="model-1",
            provider=LlmProvider.OPENAI,
            model_id="gpt-4o-mini",
        )
        config2 = ModelConfig(
            id="model-2",
            provider=LlmProvider.ANTHROPIC,
            model_id="claude-sonnet-4.5",
        )

        await storage.create_model(config1)
        await storage.create_model(config2)

        result = await storage.list_models(provider=LlmProvider.ANTHROPIC)
        assert len(result) == 1
        assert result[0].provider == LlmProvider.ANTHROPIC

    async def test_get_default_model_returns_default(self, storage):
        """기본 모델 조회 (is_default=True)"""
        config = ModelConfig(
            id="model-1",
            provider=LlmProvider.OPENAI,
            model_id="gpt-4o-mini",
            is_default=True,
        )

        await storage.create_model(config)
        result = await storage.get_default_model()

        assert result.id == "model-1"
        assert result.is_default is True

    async def test_get_default_model_raises_when_no_default(self, storage):
        """기본 모델이 없을 때 예외"""
        with pytest.raises(ConfigurationNotFoundError):
            await storage.get_default_model()

    async def test_set_default_model_updates_flags(self, storage):
        """기본 모델 설정 (다른 모델의 is_default=False)"""
        config1 = ModelConfig(
            id="model-1",
            provider=LlmProvider.OPENAI,
            model_id="gpt-4o-mini",
            is_default=True,
        )
        config2 = ModelConfig(
            id="model-2",
            provider=LlmProvider.ANTHROPIC,
            model_id="claude-sonnet-4.5",
            is_default=False,
        )

        await storage.create_model(config1)
        await storage.create_model(config2)

        await storage.set_default_model("model-2")

        model1 = await storage.get_model("model-1")
        model2 = await storage.get_model("model-2")

        assert model1.is_default is False
        assert model2.is_default is True

    async def test_delete_model_removes_config(self, storage):
        """Model 삭제"""
        config = ModelConfig(
            id="model-1",
            provider=LlmProvider.OPENAI,
            model_id="gpt-4o",
        )
        await storage.create_model(config)

        await storage.delete_model("model-1")

        with pytest.raises(ConfigurationNotFoundError):
            await storage.get_model("model-1")
```

### Fake 구현

```python
# tests/unit/fakes/fake_configuration_storage.py

"""FakeConfigurationStorage - 테스트용 Configuration 저장소 Fake

메모리 기반 저장소로 테스트 시 사용됩니다.
"""

from src.domain.ports.outbound.configuration_storage_port import (
    ConfigurationStoragePort,
)
from src.domain.entities.api_key_config import ApiKeyConfig
from src.domain.entities.model_config import ModelConfig
from src.domain.entities.enums import LlmProvider
from src.domain.exceptions import ConfigurationNotFoundError


class FakeConfigurationStorage(ConfigurationStoragePort):
    """테스트용 Configuration 저장소 Fake

    메모리 기반 저장소로 API Key와 Model 설정을 저장합니다.
    """

    def __init__(self) -> None:
        self._api_keys: dict[str, ApiKeyConfig] = {}
        self._models: dict[str, ModelConfig] = {}
        self._migrations: set[str] = set()  # Migration tracking

    # ============================================================
    # API Key 관리
    # ============================================================

    async def create_api_key(self, config: ApiKeyConfig) -> None:
        """API Key 생성"""
        self._api_keys[config.id] = config

    async def get_api_key(self, key_id: str) -> ApiKeyConfig:
        """API Key 조회 (ID로)"""
        if key_id not in self._api_keys:
            raise ConfigurationNotFoundError(f"API Key not found: {key_id}")
        return self._api_keys[key_id]

    async def get_api_key_by_provider(self, provider: LlmProvider) -> ApiKeyConfig:
        """API Key 조회 (Provider로)

        활성화된 키 중 가장 최근에 생성된 키 반환
        """
        active_keys = [
            k
            for k in self._api_keys.values()
            if k.provider == provider and k.is_active
        ]
        if not active_keys:
            raise ConfigurationNotFoundError(
                f"No active API Key for provider: {provider}"
            )
        # 최신 키 반환 (created_at 기준 내림차순)
        return sorted(active_keys, key=lambda k: k.created_at, reverse=True)[0]

    async def update_api_key(self, config: ApiKeyConfig) -> None:
        """API Key 수정"""
        if config.id not in self._api_keys:
            raise ConfigurationNotFoundError(f"API Key not found: {config.id}")
        self._api_keys[config.id] = config

    async def delete_api_key(self, key_id: str) -> None:
        """API Key 삭제"""
        if key_id not in self._api_keys:
            raise ConfigurationNotFoundError(f"API Key not found: {key_id}")
        del self._api_keys[key_id]

    async def list_api_keys(
        self, provider: LlmProvider | None = None
    ) -> list[ApiKeyConfig]:
        """API Key 목록 조회"""
        if provider is None:
            return list(self._api_keys.values())
        return [k for k in self._api_keys.values() if k.provider == provider]

    # ============================================================
    # Model 관리
    # ============================================================

    async def create_model(self, config: ModelConfig) -> None:
        """Model 생성"""
        self._models[config.id] = config

    async def get_model(self, model_id: str) -> ModelConfig:
        """Model 조회 (ID로)"""
        if model_id not in self._models:
            raise ConfigurationNotFoundError(f"Model not found: {model_id}")
        return self._models[model_id]

    async def update_model(self, config: ModelConfig) -> None:
        """Model 수정"""
        if config.id not in self._models:
            raise ConfigurationNotFoundError(f"Model not found: {config.id}")
        self._models[config.id] = config

    async def delete_model(self, model_id: str) -> None:
        """Model 삭제"""
        if model_id not in self._models:
            raise ConfigurationNotFoundError(f"Model not found: {model_id}")
        del self._models[model_id]

    async def list_models(
        self, provider: LlmProvider | None = None
    ) -> list[ModelConfig]:
        """Model 목록 조회"""
        if provider is None:
            return list(self._models.values())
        return [m for m in self._models.values() if m.provider == provider]

    async def get_default_model(self) -> ModelConfig:
        """기본 모델 조회 (is_default=True인 모델)"""
        defaults = [m for m in self._models.values() if m.is_default]
        if not defaults:
            raise ConfigurationNotFoundError("No default model configured")
        return defaults[0]

    async def set_default_model(self, model_id: str) -> None:
        """기본 모델 설정 (다른 모델들의 is_default=False로 변경)"""
        if model_id not in self._models:
            raise ConfigurationNotFoundError(f"Model not found: {model_id}")

        # 모든 모델의 is_default를 False로 변경
        for model in self._models.values():
            updated = ModelConfig(
                id=model.id,
                provider=model.provider,
                model_id=model.model_id,
                name=model.name,
                is_default=(model.id == model_id),
                parameters=model.parameters,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )
            self._models[model.id] = updated

    # ============================================================
    # Migration 관리
    # ============================================================

    async def is_migration_applied(self, migration_id: str) -> bool:
        """마이그레이션 적용 여부 확인"""
        return migration_id in self._migrations

    async def mark_migration_applied(self, migration_id: str) -> None:
        """마이그레이션 적용 기록"""
        self._migrations.add(migration_id)

    # ============================================================
    # 테스트 유틸리티
    # ============================================================

    def reset(self) -> None:
        """모든 데이터 초기화 (테스트 간 격리)"""
        self._api_keys.clear()
        self._models.clear()
        self._migrations.clear()
```

---

## Step 2.5: FakeEncryptionAdapter

**테스트 먼저:** `tests/unit/fakes/test_fake_encryption.py`
**구현:** `tests/unit/fakes/fake_encryption.py`

### 테스트 시나리오

```python
# tests/unit/fakes/test_fake_encryption.py

import pytest
from tests.unit.fakes.fake_encryption import FakeEncryption


class TestFakeEncryption:
    """FakeEncryption 자체 테스트"""

    @pytest.fixture
    def encryption(self):
        return FakeEncryption()

    async def test_encrypt_returns_base64(self, encryption):
        """encrypt가 base64로 인코딩된 문자열 반환"""
        plaintext = "test-api-key"
        ciphertext = await encryption.encrypt(plaintext)

        # base64로 디코딩 가능
        import base64

        decoded = base64.b64decode(ciphertext).decode()
        assert decoded == plaintext

    async def test_decrypt_returns_original(self, encryption):
        """decrypt가 원본 평문 반환"""
        plaintext = "sk-1234567890abcdef"
        ciphertext = await encryption.encrypt(plaintext)
        decrypted = await encryption.decrypt(ciphertext)

        assert decrypted == plaintext

    async def test_roundtrip_preserves_data(self, encryption):
        """encrypt → decrypt 라운드트립 테스트"""
        original = "my-secret-api-key"
        encrypted = await encryption.encrypt(original)
        decrypted = await encryption.decrypt(encrypted)

        assert decrypted == original

    async def test_encrypt_different_inputs_produce_different_outputs(self, encryption):
        """서로 다른 입력은 서로 다른 출력 생성"""
        plaintext1 = "key-1"
        plaintext2 = "key-2"

        ciphertext1 = await encryption.encrypt(plaintext1)
        ciphertext2 = await encryption.encrypt(plaintext2)

        assert ciphertext1 != ciphertext2

    async def test_empty_string_encryption(self, encryption):
        """빈 문자열 암호화"""
        plaintext = ""
        ciphertext = await encryption.encrypt(plaintext)
        decrypted = await encryption.decrypt(ciphertext)

        assert decrypted == ""
```

### Fake 구현

```python
# tests/unit/fakes/fake_encryption.py

"""FakeEncryption - 테스트용 암호화 Fake

Base64 인코딩/디코딩을 사용합니다 (실제 암호화 아님).
"""

import base64
from src.domain.ports.outbound.encryption_port import EncryptionPort


class FakeEncryption(EncryptionPort):
    """테스트용 암호화 Fake

    실제 Fernet 암호화 대신 base64 인코딩/디코딩을 사용합니다.
    테스트에서 암호화 로직을 검증하지 않고 비즈니스 로직만 검증합니다.
    """

    async def encrypt(self, plaintext: str) -> str:
        """평문을 base64로 인코딩"""
        return base64.b64encode(plaintext.encode()).decode()

    async def decrypt(self, ciphertext: str) -> str:
        """base64 디코딩"""
        return base64.b64decode(ciphertext.encode()).decode()
```

**Note:**
- FakeEncryption은 **base64 roundtrip**만 수행 (Plan 파일의 요구사항)
- 실제 Fernet 암호화는 Phase 4 FernetEncryptionAdapter에서 구현
- Domain Service 테스트에서는 암호화 로직이 아닌 비즈니스 로직만 검증

---

## Verification

```bash
# Phase 2 테스트
pytest tests/unit/fakes/test_fake_configuration_storage.py -v
pytest tests/unit/fakes/test_fake_encryption.py -v

# 전체 Fake 테스트
pytest tests/unit/fakes/ -v
```

---

## Step 2.6: Documentation Update

**목표:** Phase 2에서 추가된 Port 및 Fake Adapter 문서화

**문서화 항목:**

| 작업 | 대상 파일 | 유형 | 내용 |
|------|----------|------|------|
| Modify | docs/developers/architecture/layer/ports/README.md | Architecture | ConfigurationStoragePort 섹션 추가 (12 methods) |
| Modify | docs/developers/architecture/layer/ports/README.md | Architecture | EncryptionPort 섹션 추가 (encrypt/decrypt only, generate_key 제외 이유 명시) |
| Modify | tests/docs/STRATEGY.md | Test Documentation | Fake Adapter 작성 패턴 섹션에 FakeConfigurationStorage 예시 추가 |
| Modify | tests/docs/WritingGuide.md | Test Documentation | base64 Fake Encryption 패턴 추가 (실제 암호화 vs Fake) |

**주의사항:**
- `generate_key()` 메서드가 Port에 없는 이유 명시 (Adapter 내부 관심사)
- FakeEncryption은 base64 roundtrip만 수행 (실제 Fernet은 Phase 4)
- DB-First Configuration 원칙 강조

---

## Step 2.7: Git Commit

**목표:** Phase 2 완료 커밋

**절차:**

1. **Phase 시작 전 회귀 테스트 베이스라인 기록**
   ```bash
   pytest -q --tb=line -x
   # 결과: N개 통과, M개 실패 (있다면 기존 이슈)
   ```

2. **Phase 완료 후 전체 테스트 실행**
   ```bash
   # Fake 테스트
   pytest tests/unit/fakes/test_fake_configuration_storage.py -v
   pytest tests/unit/fakes/test_fake_encryption.py -v

   # 전체 회귀 테스트
   pytest -q --tb=line -x
   ```

3. **커버리지 확인**
   ```bash
   pytest --cov=src --cov-fail-under=80 -q
   ```

4. **커밋 수행**
   ```bash
   git add src/domain/ports/outbound/configuration_storage_port.py \
           src/domain/ports/outbound/encryption_port.py \
           src/domain/ports/outbound/__init__.py \
           tests/unit/fakes/fake_configuration_storage.py \
           tests/unit/fakes/fake_encryption.py \
           tests/unit/fakes/test_fake_configuration_storage.py \
           tests/unit/fakes/test_fake_encryption.py \
           docs/developers/architecture/layer/ports/README.md \
           tests/docs/STRATEGY.md \
           tests/docs/WritingGuide.md

   git commit -m "$(cat <<'EOF'
   feat: implement Phase 2 - Port Interface + Fake for Configuration

   - Add ConfigurationStoragePort (12 methods: API Key + Model CRUD)
   - Add EncryptionPort (encrypt/decrypt only, no generate_key)
   - Add FakeConfigurationStorage with in-memory storage (~15 tests)
   - Add FakeEncryption with base64 roundtrip (~5 tests)
   - Update Port exports in __init__.py

   Test Coverage:
   - All Fakes have unit tests with TDD approach
   - FakeEncryption uses base64 (not real Fernet) for testing
   - DB-First Configuration principle (DB > .env priority)

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
   EOF
   )"
   ```

5. **Phase Status 업데이트**
   - `docs/project/planning/planned/09_dynamic_configuration/README.md`에서 Phase 2 Status를 ✅로 변경

---

## Checklist

- [ ] **Baseline 회귀 테스트**: `pytest -q --tb=line` (Phase 시작 전 Green 상태 확인)
- [ ] **Phase 시작**: Status 변경 (⏸️ → 🔄)
- [ ] Step 2.1: ConfigurationStoragePort 생성 (12 methods)
- [ ] Step 2.2: EncryptionPort 생성 (encrypt/decrypt only, no generate_key)
- [ ] Step 2.3: Port __init__.py Export 업데이트
- [ ] Step 2.4: FakeConfigurationStorage (TDD, ~15 tests)
- [ ] Step 2.5: FakeEncryptionAdapter (TDD, ~5 tests, base64 roundtrip)
- [ ] Step 2.6: Documentation Update (Ports + Test Docs)
- [ ] **회귀 테스트**: `pytest --cov=src --cov-fail-under=80 -q` (Phase 완료 후 검증)
- [ ] **Phase 완료**: Status 변경 (🔄 → ✅)
- [ ] Git 커밋: `feat: implement Phase 2 - Port Interface + Fake for Configuration`

---

*Last Updated: 2026-02-07*
*Principle: TDD (Red → Green → Refactor), Fake Adapters (no mocking), DB-First Configuration*
