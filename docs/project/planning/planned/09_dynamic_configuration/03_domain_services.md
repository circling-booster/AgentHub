# Phase 3: Domain Services (TDD)

## 개요

ConfigurationService를 TDD 방식으로 구현합니다. API Key와 Model 설정을 관리하며, DB-First Configuration 원칙을 따릅니다.

**핵심 원칙:**
- **DB-First Configuration**: DB > .env 우선순위
- **TDD Required**: 모든 메서드 구현 전 테스트 먼저 작성
- **Fake Adapter 사용**: Phase 2에서 작성한 FakeConfigurationStorage, FakeEncryption 사용

---

## Step 3.1: ConfigurationService — API Key CRUD

**파일:** `src/domain/services/configuration_service.py`
**테스트:** `tests/unit/domain/services/test_configuration_service.py`

### TDD Required

```python
# tests/unit/domain/services/test_configuration_service.py

import pytest
from datetime import datetime, timezone
from src.domain.services.configuration_service import ConfigurationService
from src.domain.entities.api_key_config import ApiKeyConfig
from src.domain.entities.enums import LlmProvider
from src.domain.exceptions import ConfigurationNotFoundError
from tests.unit.fakes.fake_configuration_storage import FakeConfigurationStorage
from tests.unit.fakes.fake_encryption import FakeEncryption


@pytest.fixture
def storage():
    return FakeConfigurationStorage()


@pytest.fixture
def encryption():
    return FakeEncryption()


@pytest.fixture
def service(storage, encryption):
    # env_api_keys는 테스트에서 직접 주입 (Domain Layer 순수성 유지)
    return ConfigurationService(
        storage=storage,
        encryption=encryption,
        env_api_keys={},  # 테스트에서는 빈 dict (환경변수 Fallback 테스트 시 변경)
    )


class TestApiKeyCRUD:
    """API Key CRUD 테스트 (~10 tests)"""

    async def test_create_api_key_encrypts_and_stores(self, service, storage, encryption):
        """API Key 생성 시 암호화 후 저장"""
        plaintext_key = "sk-1234567890abcdef"

        config = await service.create_api_key(
            provider=LlmProvider.OPENAI,
            api_key=plaintext_key,
            name="My OpenAI Key",
        )

        assert config.provider == LlmProvider.OPENAI
        assert config.name == "My OpenAI Key"
        assert config.encrypted_key != plaintext_key  # 암호화됨
        assert config.is_active is True

        # 저장소에 저장됨
        stored = await storage.get_api_key(config.id)
        assert stored.encrypted_key == config.encrypted_key

    async def test_get_api_key_decrypts_key(self, service, storage, encryption):
        """API Key 조회 시 복호화"""
        plaintext_key = "sk-test-key"
        config = await service.create_api_key(
            provider=LlmProvider.ANTHROPIC,
            api_key=plaintext_key,
        )

        # 복호화된 키 조회
        result = await service.get_api_key(config.id)

        assert result.id == config.id
        assert result.provider == LlmProvider.ANTHROPIC
        # FakeEncryption은 base64이므로 복호화 가능
        decrypted = await encryption.decrypt(result.encrypted_key)
        assert decrypted == plaintext_key

    async def test_get_api_key_not_found_raises_error(self, service):
        """존재하지 않는 API Key 조회 시 예외"""
        with pytest.raises(ConfigurationNotFoundError):
            await service.get_api_key("nonexistent-id")

    async def test_update_api_key_re_encrypts(self, service, storage):
        """API Key 수정 시 재암호화"""
        config = await service.create_api_key(
            provider=LlmProvider.OPENAI,
            api_key="old-key",
            name="Old Name",
        )

        updated = await service.update_api_key(
            key_id=config.id,
            api_key="new-key",
            name="New Name",
        )

        assert updated.id == config.id
        assert updated.name == "New Name"
        assert updated.encrypted_key != config.encrypted_key  # 재암호화됨

    async def test_update_api_key_partial_update(self, service):
        """API Key 부분 수정 (name만 변경)"""
        config = await service.create_api_key(
            provider=LlmProvider.OPENAI,
            api_key="test-key",
            name="Old Name",
        )

        updated = await service.update_api_key(
            key_id=config.id,
            name="New Name",
            # api_key와 is_active는 변경하지 않음
        )

        assert updated.name == "New Name"
        assert updated.encrypted_key == config.encrypted_key  # 변경 없음
        assert updated.is_active is True  # 변경 없음

    async def test_update_api_key_with_is_active(self, service):
        """API Key 활성화 상태 변경"""
        config = await service.create_api_key(
            provider=LlmProvider.OPENAI,
            api_key="test-key",
        )

        updated = await service.update_api_key(
            key_id=config.id,
            is_active=False,
        )

        assert updated.is_active is False

    async def test_delete_api_key_removes_from_storage(self, service, storage):
        """API Key 삭제"""
        config = await service.create_api_key(
            provider=LlmProvider.GOOGLE,
            api_key="test-key",
        )

        await service.delete_api_key(config.id)

        with pytest.raises(ConfigurationNotFoundError):
            await storage.get_api_key(config.id)

    async def test_list_api_keys_returns_all(self, service):
        """모든 API Key 조회"""
        await service.create_api_key(
            provider=LlmProvider.OPENAI,
            api_key="key-1",
        )
        await service.create_api_key(
            provider=LlmProvider.ANTHROPIC,
            api_key="key-2",
        )

        keys = await service.list_api_keys()

        assert len(keys) == 2

    async def test_list_api_keys_filters_by_provider(self, service):
        """Provider 필터로 API Key 조회"""
        await service.create_api_key(
            provider=LlmProvider.OPENAI,
            api_key="key-1",
        )
        await service.create_api_key(
            provider=LlmProvider.ANTHROPIC,
            api_key="key-2",
        )

        keys = await service.list_api_keys(provider=LlmProvider.OPENAI)

        assert len(keys) == 1
        assert keys[0].provider == LlmProvider.OPENAI

    async def test_deactivate_api_key(self, service):
        """API Key 비활성화"""
        config = await service.create_api_key(
            provider=LlmProvider.OPENAI,
            api_key="test-key",
        )

        await service.deactivate_api_key(config.id)

        result = await service.get_api_key(config.id)
        assert result.is_active is False

    async def test_activate_api_key(self, service):
        """API Key 활성화"""
        config = await service.create_api_key(
            provider=LlmProvider.OPENAI,
            api_key="test-key",
        )
        await service.deactivate_api_key(config.id)

        await service.activate_api_key(config.id)

        result = await service.get_api_key(config.id)
        assert result.is_active is True
```

### 구현

```python
# src/domain/services/configuration_service.py

"""ConfigurationService - API Key & Model 설정 관리

DB-First Configuration 원칙을 따릅니다.
"""

from datetime import datetime, timezone
from uuid import uuid4

from src.domain.ports.outbound.configuration_storage_port import (
    ConfigurationStoragePort,
)
from src.domain.ports.outbound.encryption_port import EncryptionPort
from src.domain.entities.api_key_config import ApiKeyConfig
from src.domain.entities.model_config import ModelConfig
from src.domain.entities.enums import LlmProvider
from src.domain.exceptions import ConfigurationNotFoundError

# Note: os.getenv() 제거 - Domain Layer 순수성 유지
# env_api_keys는 Service 생성 시 DI로 주입받음


class ConfigurationService:
    """Configuration 관리 서비스

    API Key와 Model 설정을 관리합니다.
    """

    def __init__(
        self,
        storage: ConfigurationStoragePort,
        encryption: EncryptionPort,
        env_api_keys: dict[LlmProvider, str] | None = None,
    ) -> None:
        """
        Args:
            storage: Configuration 저장소
            encryption: 암호화 Adapter
            env_api_keys: 환경변수 API Key 맵 (선택, .env Fallback용)
        """
        self._storage = storage
        self._encryption = encryption
        self._env_api_keys = env_api_keys or {}

    # ============================================================
    # API Key CRUD
    # ============================================================

    async def create_api_key(
        self,
        provider: LlmProvider,
        api_key: str,
        name: str = "",
    ) -> ApiKeyConfig:
        """API Key 생성 (C1 이슈: key_hint 생성 추가)

        Args:
            provider: LLM Provider (enum)
            api_key: 평문 API Key
            name: API Key 이름 (선택)

        Returns:
            생성된 ApiKeyConfig
        """
        # key_hint 생성 (원본 키 기반)
        key_hint = self._generate_key_hint(api_key)

        # 암호화
        encrypted_key = await self._encryption.encrypt(api_key)

        # 엔티티 생성
        config = ApiKeyConfig(
            id=str(uuid4()),
            provider=provider,
            encrypted_key=encrypted_key,
            key_hint=key_hint,
            name=name,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # 저장
        await self._storage.create_api_key(config)

        return config

    def _generate_key_hint(self, api_key: str) -> str:
        """원본 API Key에서 힌트 생성 (C1 이슈)

        Args:
            api_key: 평문 API Key

        Returns:
            key_hint (예: "sk-...cdef")
        """
        if len(api_key) <= 10:
            return "***"

        # Provider별 prefix 길이 고려
        if api_key.startswith("sk-ant-"):
            prefix = api_key[:7]  # "sk-ant-"
        elif api_key.startswith("sk-"):
            prefix = api_key[:3]  # "sk-"
        elif api_key.startswith("AIza"):
            prefix = api_key[:4]  # "AIza"
        else:
            prefix = api_key[:3]  # 기타

        suffix = api_key[-4:]
        return f"{prefix}...{suffix}"

    async def get_api_key(self, key_id: str) -> ApiKeyConfig:
        """API Key 조회

        Args:
            key_id: API Key ID

        Returns:
            ApiKeyConfig

        Raises:
            ConfigurationNotFoundError: 존재하지 않는 키
        """
        return await self._storage.get_api_key(key_id)

    async def update_api_key(
        self,
        key_id: str,
        api_key: str | None = None,
        name: str | None = None,
        is_active: bool | None = None,
    ) -> ApiKeyConfig:
        """API Key 수정 (C1 이슈: key_hint 업데이트 추가)

        Args:
            key_id: API Key ID
            api_key: 새 API Key (None이면 변경 안 함)
            name: 새 이름 (None이면 변경 안 함)
            is_active: 활성화 상태 (None이면 변경 안 함)

        Returns:
            수정된 ApiKeyConfig

        Raises:
            ConfigurationNotFoundError: 존재하지 않는 키
        """
        # 기존 설정 조회
        existing = await self._storage.get_api_key(key_id)

        # 변경사항 적용
        encrypted_key = existing.encrypted_key
        key_hint = existing.key_hint
        if api_key is not None:
            encrypted_key = await self._encryption.encrypt(api_key)
            key_hint = self._generate_key_hint(api_key)  # C1: key_hint 업데이트

        updated_name = name if name is not None else existing.name
        updated_is_active = is_active if is_active is not None else existing.is_active

        # 새 엔티티 생성
        updated = ApiKeyConfig(
            id=existing.id,
            provider=existing.provider,
            encrypted_key=encrypted_key,
            key_hint=key_hint,
            name=updated_name,
            is_active=updated_is_active,
            created_at=existing.created_at,
            updated_at=datetime.now(timezone.utc),
        )

        # 저장
        await self._storage.update_api_key(updated)

        return updated

    async def delete_api_key(self, key_id: str) -> None:
        """API Key 삭제

        Args:
            key_id: API Key ID

        Raises:
            ConfigurationNotFoundError: 존재하지 않는 키
        """
        await self._storage.delete_api_key(key_id)

    async def list_api_keys(
        self, provider: LlmProvider | None = None
    ) -> list[ApiKeyConfig]:
        """API Key 목록 조회

        Args:
            provider: Provider 필터 (None이면 전체)

        Returns:
            ApiKeyConfig 목록
        """
        return await self._storage.list_api_keys(provider)

    async def activate_api_key(self, key_id: str) -> None:
        """API Key 활성화

        Args:
            key_id: API Key ID

        Raises:
            ConfigurationNotFoundError: 존재하지 않는 키
        """
        existing = await self._storage.get_api_key(key_id)

        updated = ApiKeyConfig(
            id=existing.id,
            provider=existing.provider,
            encrypted_key=existing.encrypted_key,
            name=existing.name,
            is_active=True,
            created_at=existing.created_at,
            updated_at=datetime.now(timezone.utc),
        )

        await self._storage.update_api_key(updated)

    async def deactivate_api_key(self, key_id: str) -> None:
        """API Key 비활성화

        Args:
            key_id: API Key ID

        Raises:
            ConfigurationNotFoundError: 존재하지 않는 키
        """
        existing = await self._storage.get_api_key(key_id)

        updated = ApiKeyConfig(
            id=existing.id,
            provider=existing.provider,
            encrypted_key=existing.encrypted_key,
            name=existing.name,
            is_active=False,
            created_at=existing.created_at,
            updated_at=datetime.now(timezone.utc),
        )

        await self._storage.update_api_key(updated)
```

---

## Step 3.2: ConfigurationService — Model 관리

**파일:** `src/domain/services/configuration_service.py` (확장)
**테스트:** `tests/unit/domain/services/test_configuration_service.py` (확장)

### TDD Required

```python
# tests/unit/domain/services/test_configuration_service.py (확장)

class TestModelManagement:
    """Model 관리 테스트 (~8 tests)"""

    async def test_create_model_stores_config(self, service, storage):
        """Model 생성"""
        config = await service.create_model(
            provider=LlmProvider.OPENAI,
            model_id="gpt-4o-mini",
            name="GPT-4o Mini",
            parameters={"temperature": 0.7},
        )

        assert config.provider == LlmProvider.OPENAI
        assert config.model_id == "gpt-4o-mini"
        assert config.parameters["temperature"] == 0.7

        # 저장소에 저장됨
        stored = await storage.get_model(config.id)
        assert stored.model_id == "gpt-4o-mini"

    async def test_get_model_returns_config(self, service):
        """Model 조회"""
        config = await service.create_model(
            provider=LlmProvider.ANTHROPIC,
            model_id="claude-sonnet-4.5",
        )

        result = await service.get_model(config.id)

        assert result.id == config.id
        assert result.model_id == "claude-sonnet-4.5"

    async def test_update_model_modifies_config(self, service):
        """Model 수정"""
        config = await service.create_model(
            provider=LlmProvider.OPENAI,
            model_id="gpt-4o",
            name="Old Name",
        )

        updated = await service.update_model(
            model_id=config.id,
            name="New Name",
            parameters={"max_tokens": 2048},
        )

        assert updated.name == "New Name"
        assert updated.parameters["max_tokens"] == 2048

    async def test_delete_model_removes_config(self, service, storage):
        """Model 삭제"""
        config = await service.create_model(
            provider=LlmProvider.GOOGLE,
            model_id="gemini-2.0-flash-exp",
        )

        await service.delete_model(config.id)

        with pytest.raises(ConfigurationNotFoundError):
            await storage.get_model(config.id)

    async def test_list_models_filters_by_provider(self, service):
        """Provider 필터로 Model 조회"""
        await service.create_model(
            provider=LlmProvider.OPENAI,
            model_id="gpt-4o",
        )
        await service.create_model(
            provider=LlmProvider.ANTHROPIC,
            model_id="claude-sonnet-4.5",
        )

        models = await service.list_models(provider=LlmProvider.ANTHROPIC)

        assert len(models) == 1
        assert models[0].provider == LlmProvider.ANTHROPIC

    async def test_get_default_model_returns_default(self, service):
        """기본 모델 조회"""
        config = await service.create_model(
            provider=LlmProvider.OPENAI,
            model_id="gpt-4o-mini",
            is_default=True,
        )

        default = await service.get_default_model()

        assert default.id == config.id
        assert default.is_default is True

    async def test_set_default_model_updates_flags(self, service):
        """기본 모델 설정 (다른 모델의 is_default=False)"""
        model1 = await service.create_model(
            provider=LlmProvider.OPENAI,
            model_id="gpt-4o-mini",
            is_default=True,
        )
        model2 = await service.create_model(
            provider=LlmProvider.ANTHROPIC,
            model_id="claude-sonnet-4.5",
        )

        result = await service.set_default_model(model2.id)

        result1 = await service.get_model(model1.id)
        result2 = await service.get_model(model2.id)

        assert result.id == model2.id
        assert result.is_default is True
        assert result1.is_default is False
        assert result2.is_default is True

    async def test_create_model_with_default_flag(self, service):
        """is_default=True로 Model 생성"""
        config = await service.create_model(
            provider=LlmProvider.OPENAI,
            model_id="gpt-4o",
            is_default=True,
        )

        assert config.is_default is True

        default = await service.get_default_model()
        assert default.id == config.id
```

### 구현 (ConfigurationService 확장)

```python
# src/domain/services/configuration_service.py (Model 관리 메서드 추가)

class ConfigurationService:
    # ... (기존 API Key CRUD 메서드)

    # ============================================================
    # Model 관리
    # ============================================================

    async def create_model(
        self,
        provider: LlmProvider,
        model_id: str,
        name: str = "",
        is_default: bool = False,
        parameters: dict | None = None,
    ) -> ModelConfig:
        """Model 생성

        Args:
            provider: LLM Provider
            model_id: 모델 ID (예: "gpt-4o-mini")
            name: 모델 이름 (선택)
            is_default: 기본 모델 여부
            parameters: 모델 파라미터 (temperature 등)

        Returns:
            생성된 ModelConfig
        """
        config = ModelConfig(
            id=str(uuid4()),
            provider=provider,
            model_id=model_id,
            name=name,
            is_default=is_default,
            parameters=parameters or {},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await self._storage.create_model(config)

        return config

    async def get_model(self, model_id: str) -> ModelConfig:
        """Model 조회

        Args:
            model_id: Model ID

        Returns:
            ModelConfig

        Raises:
            ConfigurationNotFoundError: 존재하지 않는 모델
        """
        return await self._storage.get_model(model_id)

    async def update_model(
        self,
        model_id: str,
        name: str | None = None,
        parameters: dict | None = None,
        is_default: bool | None = None,
    ) -> ModelConfig:
        """Model 수정 (H1 이슈: is_default 파라미터 추가)

        Args:
            model_id: Model ID
            name: 새 이름 (None이면 변경 안 함)
            parameters: 새 파라미터 (None이면 변경 안 함)
            is_default: 기본 모델 여부 (None이면 변경 안 함)

        Returns:
            수정된 ModelConfig

        Raises:
            ConfigurationNotFoundError: 존재하지 않는 모델
        """
        existing = await self._storage.get_model(model_id)

        updated_name = name if name is not None else existing.name
        updated_params = parameters if parameters is not None else existing.parameters
        updated_is_default = is_default if is_default is not None else existing.is_default

        updated = ModelConfig(
            id=existing.id,
            provider=existing.provider,
            model_id=existing.model_id,
            name=updated_name,
            is_default=updated_is_default,
            parameters=updated_params,
            created_at=existing.created_at,
            updated_at=datetime.now(timezone.utc),
        )

        await self._storage.update_model(updated)

        return updated

    async def delete_model(self, model_id: str) -> None:
        """Model 삭제

        Args:
            model_id: Model ID

        Raises:
            ConfigurationNotFoundError: 존재하지 않는 모델
        """
        await self._storage.delete_model(model_id)

    async def list_models(
        self, provider: LlmProvider | None = None
    ) -> list[ModelConfig]:
        """Model 목록 조회

        Args:
            provider: Provider 필터 (None이면 전체)

        Returns:
            ModelConfig 목록
        """
        return await self._storage.list_models(provider)

    async def get_default_model(self) -> ModelConfig:
        """기본 모델 조회

        Returns:
            기본 모델 (is_default=True)

        Raises:
            ConfigurationNotFoundError: 기본 모델이 설정되지 않음
        """
        return await self._storage.get_default_model()

    async def set_default_model(self, model_id: str) -> ModelConfig:
        """기본 모델 설정

        다른 모델들의 is_default를 False로 변경합니다.

        Args:
            model_id: Model ID

        Returns:
            업데이트된 ModelConfig (is_default=True)

        Raises:
            ConfigurationNotFoundError: 존재하지 않는 모델
        """
        await self._storage.set_default_model(model_id)
        return await self._storage.get_model(model_id)
```

---

## Step 3.3: ConfigurationService — API Key Resolution (DB > env)

**파일:** `src/domain/services/configuration_service.py` (확장)
**테스트:** `tests/unit/domain/services/test_configuration_service.py` (확장)

### DB-First Configuration 원칙

```
우선순위: DB (api_keys 테이블) > .env (OPENAI_API_KEY 등)

1. resolve_api_key(provider) → DB에서 활성 키 조회
2. DB에 없으면 → .env에서 조회 (Fallback)
3. .env에도 없으면 → ConfigurationNotFoundError
```

### TDD Required

```python
# tests/unit/domain/services/test_configuration_service.py (확장)

class TestApiKeyResolution:
    """API Key Resolution 테스트 (DB > env) (~5 tests)"""

    async def test_resolve_api_key_returns_db_key(self, service):
        """DB에 API Key가 있으면 DB 우선 반환"""
        db_key = await service.create_api_key(
            provider=LlmProvider.OPENAI,
            api_key="db-api-key",
        )

        # .env는 무시됨 (DB 우선)
        resolved = await service.resolve_api_key(LlmProvider.OPENAI)

        assert resolved.id == db_key.id
        assert resolved.provider == LlmProvider.OPENAI

    async def test_resolve_api_key_fallback_to_env(self, storage, encryption):
        """DB에 없으면 .env에서 조회"""
        # env_api_keys를 주입한 Service 생성
        service = ConfigurationService(
            storage=storage,
            encryption=encryption,
            env_api_keys={LlmProvider.OPENAI: "env-api-key"},
        )
        # DB에 API Key 없음

        resolved = await service.resolve_api_key(LlmProvider.OPENAI, env_fallback=True)

        assert resolved is not None
        assert resolved.provider == LlmProvider.OPENAI
        assert resolved.id == "env-openai"
        # .env에서 가져온 키는 임시 엔티티 (DB 저장 안 됨)

    async def test_resolve_api_key_not_found_raises_error(self, service):
        """DB와 .env 모두 없으면 예외"""
        with pytest.raises(ConfigurationNotFoundError):
            await service.resolve_api_key(LlmProvider.GOOGLE)

    async def test_resolve_api_key_only_active_keys(self, service):
        """비활성 키는 무시하고 활성 키만 반환"""
        inactive_key = await service.create_api_key(
            provider=LlmProvider.ANTHROPIC,
            api_key="inactive-key",
        )
        await service.deactivate_api_key(inactive_key.id)

        active_key = await service.create_api_key(
            provider=LlmProvider.ANTHROPIC,
            api_key="active-key",
        )

        resolved = await service.resolve_api_key(LlmProvider.ANTHROPIC)

        assert resolved.id == active_key.id
        assert resolved.is_active is True

    async def test_get_decrypted_api_key_returns_plaintext(self, service, encryption):
        """API Key 복호화하여 평문 반환"""
        plaintext = "sk-secret-key-12345"
        config = await service.create_api_key(
            provider=LlmProvider.OPENAI,
            api_key=plaintext,
        )

        decrypted = await service.get_decrypted_api_key(config.id)

        # FakeEncryption은 base64이므로 복호화 가능
        assert decrypted == plaintext
```

### 구현 (ConfigurationService 확장)

```python
# src/domain/services/configuration_service.py (API Key Resolution 메서드 추가)

import os

class ConfigurationService:
    # ... (기존 메서드)

    # ============================================================
    # API Key Resolution (DB > env)
    # ============================================================

    async def resolve_api_key(
        self,
        provider: LlmProvider,
        env_fallback: bool = True,
    ) -> ApiKeyConfig:
        """API Key 해결 (DB > .env 우선순위)

        Args:
            provider: LLM Provider
            env_fallback: .env Fallback 활성화 (기본: True)

        Returns:
            ApiKeyConfig (활성화된 키)

        Raises:
            ConfigurationNotFoundError: DB와 .env 모두 없음
        """
        # 1. DB에서 활성 키 조회
        try:
            return await self._storage.get_api_key_by_provider(provider)
        except ConfigurationNotFoundError:
            pass

        # 2. .env Fallback
        if env_fallback:
            env_key = self._env_api_keys.get(provider)
            if env_key:
                # 임시 엔티티 생성 (DB 저장 안 함)
                return await self._create_temporary_api_key_config(provider, env_key)

        # 3. 없으면 예외
        raise ConfigurationNotFoundError(
            f"No API Key found for provider: {provider} (DB and .env)"
        )

    async def get_decrypted_api_key(self, key_id: str) -> str:
        """API Key 복호화하여 평문 반환

        Args:
            key_id: API Key ID

        Returns:
            복호화된 평문 API Key

        Raises:
            ConfigurationNotFoundError: 존재하지 않는 키
            DecryptionError: 복호화 실패
        """
        config = await self._storage.get_api_key(key_id)
        return await self._encryption.decrypt(config.encrypted_key)

    # ============================================================
    # 내부 헬퍼 메서드
    # ============================================================

    async def _create_temporary_api_key_config(
        self, provider: LlmProvider, api_key: str
    ) -> ApiKeyConfig:
        """임시 API Key Config 생성 (.env에서 가져온 키용)

        Args:
            provider: LLM Provider
            api_key: 평문 API Key

        Returns:
            임시 ApiKeyConfig (DB 저장 안 됨)
        """
        encrypted_key = await self._encryption.encrypt(api_key)

        return ApiKeyConfig(
            id=f"env-{provider.value}",
            provider=provider,
            encrypted_key=encrypted_key,
            name=f"[.env] {provider.value.upper()}_API_KEY",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
```

---

## Verification

```bash
# ConfigurationService 테스트
pytest tests/unit/domain/services/test_configuration_service.py -v

# 전체 Domain Services 테스트
pytest tests/unit/domain/services/ -v
```

---

## Step 3.4: Documentation Update

**목표:** Phase 3에서 추가된 Domain Service 문서화

**문서화 항목:**

| 작업 | 대상 파일 | 유형 | 내용 |
|------|----------|------|------|
| Modify | docs/developers/architecture/layer/core/README.md | Architecture | ConfigurationService 섹션 추가 (DB-First Configuration 원칙, API Key Resolution) |
| Modify | tests/docs/STRATEGY.md | Test Documentation | Service 테스트 전략 추가 (Fake Adapter 사용, TDD 사이클) |
| Modify | tests/docs/WritingGuide.md | Test Documentation | monkeypatch 사용 예시 추가 (.env 시뮬레이션) |

**주의사항:**
- DB-First Configuration 원칙 강조 (DB > .env 우선순위)
- Fake Adapter 사용 이유 (Mocking 대신 Fake)
- datetime.now(timezone.utc) 일관성

---

## Step 3.5: Git Commit

**목표:** Phase 3 완료 커밋

**절차:**

1. **Phase 시작 전 회귀 테스트 베이스라인 기록**
   ```bash
   pytest -q --tb=line -x
   # 결과: N개 통과, M개 실패 (있다면 기존 이슈)
   ```

2. **Phase 완료 후 전체 테스트 실행**
   ```bash
   # ConfigurationService 테스트
   pytest tests/unit/domain/services/test_configuration_service.py -v

   # 전체 회귀 테스트
   pytest -q --tb=line -x
   ```

3. **커버리지 확인**
   ```bash
   pytest --cov=src --cov-fail-under=80 -q
   ```

4. **커밋 수행**
   ```bash
   git add src/domain/services/configuration_service.py \
           tests/unit/domain/services/test_configuration_service.py \
           docs/developers/architecture/layer/core/README.md \
           tests/docs/STRATEGY.md \
           tests/docs/WritingGuide.md

   git commit -m "$(cat <<'EOF'
   feat: implement Phase 3 - Domain Services for Configuration

   - Add ConfigurationService with TDD approach
   - API Key CRUD (create, get, update, delete, list) (~10 tests)
   - Model management (create, get, update, delete, list, default) (~8 tests)
   - API Key resolution (DB > .env fallback) (~5 tests)
   - Encryption/Decryption integration with EncryptionPort
   - datetime.now(timezone.utc) for timezone-aware timestamps

   Test Coverage:
   - All methods have unit tests with Fake Adapters (no mocking)
   - DB-First Configuration principle enforced
   - monkeypatch for .env simulation

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
   EOF
   )"
   ```

5. **Phase Status 업데이트**
   - `docs/project/planning/planned/09_dynamic_configuration/README.md`에서 Phase 3 Status를 ✅로 변경

---

## Checklist

- [ ] **Baseline 회귀 테스트**: `pytest -q --tb=line` (Phase 시작 전 Green 상태 확인)
- [ ] **Phase 시작**: Status 변경 (⏸️ → 🔄)
- [ ] Step 3.1: ConfigurationService — API Key CRUD (TDD, ~10 tests)
- [ ] Step 3.2: ConfigurationService — Model 관리 (TDD, ~8 tests)
- [ ] Step 3.3: ConfigurationService — API Key Resolution (TDD, ~5 tests, DB > env)
- [ ] Step 3.4: Documentation Update (Architecture + Test Docs)
- [ ] **회귀 테스트**: `pytest --cov=src --cov-fail-under=80 -q` (Phase 완료 후 검증)
- [ ] **Phase 완료**: Status 변경 (🔄 → ✅)
- [ ] Git 커밋: `feat: implement Phase 3 - Domain Services for Configuration`

---

*Last Updated: 2026-02-07*
*Principle: TDD (Red → Green → Refactor), DB-First Configuration (DB > .env), Fake Adapters (no mocking)*
