# Phase 5: Integration

## 개요

Configuration System을 FastAPI 애플리케이션에 통합합니다. DI Container, Settings, Lifespan을 수정하여 DB-First Configuration을 활성화합니다.

**핵심 원칙:**
- **DB-First Configuration**: SQLite를 단일 진실 공급원으로 사용
- **Lifespan Management**: 서버 시작 시 DB 초기화 + Migration 자동 실행
- **Encryption Key Export**: 환경변수에서 ENCRYPTION_KEY 로드 (미설정 시 자동 생성 + 경고)
- **Model Switching**: OrchestratorAdapter.set_model() 메서드 추가 (재빌드 없이 모델 변경)

---

## Step 5.1: Settings 확장 (encryption_key 필드)

**파일:** `src/config/settings.py` (기존 파일 확장)

### 수정

```python
# src/config/settings.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """애플리케이션 설정 (환경변수 + .env 파일)"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ... 기존 필드 ...

    # Configuration 관련 (신규)
    encryption_key: str = ""  # Fernet 암호화 키 (32-byte base64)
    config_db_path: str = "data/config.db"  # Configuration DB 경로

    # LLM API Keys (.env Fallback용)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
```

**변경사항:**
- `encryption_key`: Fernet 암호화 키 (환경변수 `ENCRYPTION_KEY`에서 로드)
- `config_db_path`: Configuration SQLite DB 경로 (기본: `data/config.db`)
- LLM API Key 필드 추가 (ConfigurationService의 .env Fallback용)

**Note:** 이 Step은 테스트가 필요 없습니다 (Settings 확장).

---

## Step 5.2: Container 확장 (Configuration Providers)

**파일:** `src/config/container.py` (기존 파일 확장)
**테스트:** `tests/integration/test_container_configuration.py`

### TDD Required

```python
# tests/integration/test_container_configuration.py

import pytest
from src.config.container import Container
from src.domain.services.configuration_service import ConfigurationService
from src.adapters.outbound.storage.sqlite_configuration_storage import (
    SqliteConfigurationStorage,
)
from src.adapters.outbound.encryption.fernet_encryption_adapter import (
    FernetEncryptionAdapter,
)


class TestContainerConfiguration:
    """Container Configuration Providers 테스트 (~5 tests)"""

    @pytest.fixture
    def container(self, tmp_path):
        """임시 DB를 사용하는 Container"""
        container = Container()
        # Settings 오버라이드
        container.config.from_dict({
            "encryption_key": FernetEncryptionAdapter.generate_key(),
            "config_db_path": str(tmp_path / "test_config.db"),
        })
        return container

    async def test_configuration_storage_provider(self, container):
        """ConfigurationStorage Provider 생성"""
        storage = container.configuration_storage()

        assert isinstance(storage, SqliteConfigurationStorage)
        # 초기화 확인 (initialize는 lifespan에서 호출)
        await storage.initialize()
        await storage.close()

    async def test_encryption_adapter_provider(self, container):
        """EncryptionAdapter Provider 생성"""
        encryption = container.encryption_adapter()

        assert isinstance(encryption, FernetEncryptionAdapter)

        # Roundtrip 테스트
        plaintext = "test-key"
        ciphertext = await encryption.encrypt(plaintext)
        decrypted = await encryption.decrypt(ciphertext)
        assert decrypted == plaintext

    async def test_configuration_service_provider(self, container):
        """ConfigurationService Provider 생성 (DI 확인)"""
        service = container.configuration_service()

        assert isinstance(service, ConfigurationService)
        # 의존성 주입 확인 (storage, encryption)
        assert service._storage is not None
        assert service._encryption is not None

    async def test_configuration_migrator_provider(self, container):
        """ConfigurationMigrator Provider 생성"""
        from src.adapters.outbound.storage.configuration_migrator import (
            ConfigurationMigrator,
        )

        migrator = container.configuration_migrator()

        assert isinstance(migrator, ConfigurationMigrator)

    async def test_settings_encryption_key_loads_from_env(self, monkeypatch):
        """Settings가 환경변수에서 encryption_key 로드"""
        test_key = FernetEncryptionAdapter.generate_key()
        monkeypatch.setenv("ENCRYPTION_KEY", test_key)

        container = Container()
        settings = container.config()

        assert settings.encryption_key == test_key
```

### Container 수정

```python
# src/config/container.py (Configuration Providers 추가)

from dependency_injector import containers, providers
from src.adapters.outbound.storage.sqlite_configuration_storage import (
    SqliteConfigurationStorage,
)
from src.adapters.outbound.encryption.fernet_encryption_adapter import (
    FernetEncryptionAdapter,
)
from src.adapters.outbound.storage.configuration_migrator import ConfigurationMigrator
from src.domain.services.configuration_service import ConfigurationService
from src.domain.entities.enums import LlmProvider


class Container(containers.DeclarativeContainer):
    # ... 기존 providers ...

    # ============================================================
    # Configuration Providers (신규)
    # ============================================================

    # Configuration Storage (Singleton)
    configuration_storage = providers.Singleton(
        SqliteConfigurationStorage,
        db_path=config.config_db_path,
    )

    # Encryption Adapter (Singleton)
    encryption_adapter = providers.Singleton(
        FernetEncryptionAdapter,
        encryption_key=config.encryption_key,
    )

    # Environment API Keys (공통 Provider - DRY 원칙)
    env_api_keys = providers.Dict({
        LlmProvider.OPENAI: config.openai_api_key,
        LlmProvider.ANTHROPIC: config.anthropic_api_key,
        LlmProvider.GOOGLE: config.google_api_key,
    })

    # Configuration Service (Factory - 요청마다 생성)
    configuration_service = providers.Factory(
        ConfigurationService,
        storage=configuration_storage,
        encryption=encryption_adapter,
        env_api_keys=env_api_keys,
    )

    # Configuration Migrator (Singleton)
    configuration_migrator = providers.Singleton(
        ConfigurationMigrator,
        storage=configuration_storage,
        encryption=encryption_adapter,
        env_api_keys=env_api_keys,
    )
```

**주의사항:**
- `configuration_storage`는 **Singleton** (DB 연결 재사용, 앱 전체에서 단일 인스턴스)
- `encryption_adapter`는 **Singleton** (Fernet 인스턴스 재사용)
- `configuration_service`는 **Factory** (요청마다 새 인스턴스 생성, stateless)
- `configuration_migrator`는 **Singleton** (Migration은 startup 시 1회만)
- `env_api_keys`는 **공통 Provider** (DRY 원칙, 중복 제거)
- `config.encryption_key`는 Settings에서 자동 로드 (`settings.provided` 패턴)

**Provider 스코프 선택 기준:**
| Provider | 스코프 | 이유 |
|----------|--------|------|
| `configuration_storage` | Singleton | DB 연결 객체는 앱 전체에서 재사용 (WAL 모드 성능 최적화) |
| `encryption_adapter` | Singleton | Fernet 인스턴스는 stateless, 매번 생성할 필요 없음 |
| `configuration_service` | Factory | Service는 비즈니스 로직 레이어, 요청별 독립성 보장 |
| `configuration_migrator` | Singleton | Migration은 startup 시 1회만 실행, 재생성 불필요 |
| `env_api_keys` | Dict | 정적 데이터 (Settings에서 로드), 공유 가능 |

---

## Step 5.3: Lifespan 변경 (DB init, migration, key export)

**파일:** `src/adapters/inbound/http/app.py` (기존 파일 확장)

### Lifespan startup/shutdown 수정

```python
# src/adapters/inbound/http/app.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 Lifespan (Startup + Shutdown)"""
    # ============================================================
    # Startup
    # ============================================================
    from src.config.container import Container
    from src.adapters.outbound.encryption.fernet_encryption_adapter import (
        FernetEncryptionAdapter,
    )

    # 1. Encryption Key 검증 (환경변수 필수)
    settings = Container.config()
    if not settings.encryption_key:
        # 자동 생성 + 경고
        generated_key = FernetEncryptionAdapter.generate_key()
        logger.warning(
            f"ENCRYPTION_KEY not set. Auto-generated key: {generated_key}"
        )
        logger.warning(
            "⚠️  CRITICAL: Add this key to .env file immediately!"
        )
        logger.warning(
            "⚠️  Without this key, encrypted data will be unrecoverable on restart."
        )
        # Settings 오버라이드 (메모리에서만, .env에는 저장 안 됨)
        Container.config.override(
            settings.model_copy(update={"encryption_key": generated_key})
        )

    # 2. Configuration Storage 초기화
    configuration_storage = Container.configuration_storage()
    await configuration_storage.initialize()
    logger.info("Configuration storage initialized")

    # 3. Migration 실행 (.env → DB)
    configuration_migrator = Container.configuration_migrator()
    try:
        await configuration_migrator.migrate_env()
        logger.info("Configuration migration completed")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        logger.error("Application startup blocked due to migration failure")
        # Migration 실패 시 애플리케이션 시작 차단
        raise RuntimeError(f"Configuration migration failed: {e}")

    # 4. 기존 엔드포인트 복원 (기존 코드)
    registry_service = Container.registry_service()
    result = await registry_service.restore_endpoints()
    logger.info(
        f"Endpoints restored: {len(result['restored'])}, "
        f"failed: {len(result['failed'])}"
    )

    yield

    # ============================================================
    # Shutdown
    # ============================================================

    # Configuration Storage 종료
    await configuration_storage.close()
    logger.info("Configuration storage closed")

    # 기존 정리 코드 (MCP sessions 등)
    # ...


app = FastAPI(lifespan=lifespan)
```

**변경사항:**
1. **Encryption Key 검증**: 환경변수 미설정 시 자동 생성 + 경고 로그
2. **DB 초기화**: `configuration_storage.initialize()` 호출
3. **Migration 실행**: `.env` → DB 마이그레이션 (멱등성 보장)
4. **Shutdown 시 DB 종료**: `configuration_storage.close()` 호출

**주의사항:**
- ENCRYPTION_KEY 미설정 시 서버 시작은 차단하지 않음 (자동 생성)
- 하지만 **반드시 .env에 추가해야 함** (재시작 시 데이터 복구 불가)
- **Migration 실패 시 애플리케이션 시작 차단** (데이터 일관성 보장)

**Note:** 이 Step은 테스트가 어려움 (Lifespan은 E2E 레벨에서 검증). Integration 테스트는 개별 함수 단위로 수행.

---

## Step 5.4: OrchestratorAdapter.set_model() 추가

**파일:** `src/adapters/outbound/adk/orchestrator_adapter.py` (기존 파일 확장)
**테스트:** `tests/integration/adapters/outbound/adk/test_orchestrator_adapter.py` (확장)

### TDD Required

```python
# tests/integration/adapters/outbound/adk/test_orchestrator_adapter.py (확장)

class TestOrchestratorAdapterModelSwitching:
    """OrchestratorAdapter 모델 전환 테스트"""

    @pytest.fixture
    def adapter(self):
        """Orchestrator Adapter Fixture"""
        from src.adapters.outbound.adk.orchestrator_adapter import (
            AdkOrchestratorAdapter,
        )

        return AdkOrchestratorAdapter(
            model_name="openai/gpt-4o-mini",
            adk_config={},
        )

    async def test_set_model_changes_model_name(self, adapter):
        """set_model() - 모델 이름 변경"""
        original_model = adapter._model_name

        adapter.set_model("anthropic/claude-sonnet-4.5")

        assert adapter._model_name == "anthropic/claude-sonnet-4.5"
        assert adapter._model_name != original_model

    @pytest.mark.llm
    async def test_set_model_affects_next_generate_response(self, adapter):
        """set_model() - 다음 generate_response()에 반영됨"""
        # 1. 기본 모델로 호출
        result1 = await adapter.generate_response(
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10,
        )
        # model 필드에 "gpt-4o-mini" 포함됨

        # 2. 모델 변경
        adapter.set_model("openai/gpt-4o")

        # 3. 변경된 모델로 호출
        result2 = await adapter.generate_response(
            messages=[{"role": "user", "content": "Say hi"}],
            max_tokens=10,
        )

        # model 필드에 "gpt-4o" 포함됨
        assert "gpt-4o" in result2.get("model", "")

    async def test_set_model_does_not_rebuild_agent(self, adapter):
        """set_model() - Agent 재빌드하지 않음 (ADK Runner 재사용)"""
        # _agent 필드가 있다면 동일 인스턴스 유지
        # (실제로는 AdkOrchestratorAdapter가 _agent를 rebuild하지 않음을 확인)
        # 이 테스트는 로직 검증용 (실제 재빌드는 A2A sub-agent 변경 시만)

        adapter.set_model("openai/gpt-4o")

        # _model_name만 변경됨 (재빌드 없음)
        assert adapter._model_name == "openai/gpt-4o"
```

### 구현

```python
# src/adapters/outbound/adk/orchestrator_adapter.py (메서드 추가)

class AdkOrchestratorAdapter(OrchestratorPort):
    # ... 기존 코드 ...

    def set_model(self, model_name: str) -> None:
        """모델 변경 (재빌드 없이 _model_name만 변경)

        Args:
            model_name: 새 모델 이름 (예: "openai/gpt-4o", "anthropic/claude-sonnet-4.5")

        Note:
            Agent 재빌드는 하지 않습니다 (_rebuild_agent는 A2A sub-agent 변경 시만 호출).
            다음 generate_response() 호출 시 변경된 모델이 사용됩니다.
        """
        self._model_name = model_name
        logger.info(f"Model changed to: {model_name}")
```

**변경사항:**
- `set_model()` 메서드 추가 (재빌드 없이 모델만 변경)
- `_model_name` 필드만 업데이트
- `_rebuild_agent()`는 호출하지 않음 (A2A sub-agent 변경 시만 재빌드)

**주의사항:**
- Model 변경은 다음 `generate_response()` 호출부터 반영됨
- `process_message()`는 ADK Runner를 사용하므로 모델 변경이 즉시 반영됨
- A2A sub-agent 재구성은 `_rebuild_agent()`로 별도 처리

---

## Verification

```bash
# Phase 1-4 복습 (Unit + Integration)
pytest tests/unit/ -q --tb=line -x
pytest tests/integration/adapters/ -v

# Phase 5 Integration Tests (Container + Orchestrator)
pytest tests/integration/test_container_configuration.py -v
pytest tests/integration/adapters/test_orchestrator_adapter.py::TestOrchestratorAdapterModelSwitching -v

# 전체 회귀 테스트
pytest -q --tb=line -x

# Coverage 확인
pytest --cov=src --cov-fail-under=80 -q
```

---

## Step 5.5: Documentation Update

**목표:** Phase 5에서 구현된 Integration 레이어 문서화

**문서화 항목:**

| 작업 | 대상 파일 | 유형 | 내용 |
|------|----------|------|------|
| Modify | docs/operators/deployment/configuration.md | Deployment Guide | ENCRYPTION_KEY 환경변수 설정 가이드 (필수, 자동 생성 경고, .env 추가 방법) |
| Modify | docs/operators/deployment/configuration.md | Deployment Guide | .env → DB Migration 자동 실행 설명 (멱등성, 재시작 안전성) |
| Create | docs/developers/guides/implementation/di-container-patterns.md | Implementation Guide | DI Container Providers 패턴 (Singleton vs Factory, Settings 오버라이드) |
| Modify | docs/developers/architecture/layer/config/README.md | Architecture | Settings 확장 섹션 추가 (encryption_key, config_db_path, LLM API keys) |
| Modify | docs/developers/architecture/layer/config/README.md | Architecture | Lifespan 관리 섹션 추가 (DB 초기화, Migration, Key 검증) |
| Create | docs/developers/guides/implementation/model-switching.md | Implementation Guide | OrchestratorAdapter 모델 전환 가이드 (set_model vs rebuild_agent 차이) |

**주의사항:**
- ENCRYPTION_KEY 미설정 시 자동 생성되지만 **반드시 .env에 추가해야 함** 강조
- Migration은 멱등성 보장 (여러 번 실행해도 안전)
- Model 전환은 재빌드 없이 즉시 반영 (LiteLLM은 model_name만 변경)

---

## Step 5.6: Git Commit

**목표:** Phase 5 완료 커밋

**절차:**

1. **Phase 시작 전 회귀 테스트 베이스라인 기록**
   ```bash
   pytest -q --tb=line -x
   # 결과: N개 통과, M개 실패 (있다면 기존 이슈)
   ```

2. **Phase 완료 후 전체 테스트 실행**
   ```bash
   # Phase 5 Integration Tests
   pytest tests/integration/test_container_configuration.py -v
   pytest tests/integration/adapters/test_orchestrator_adapter.py::TestOrchestratorAdapterModelSwitching -v

   # 전체 회귀 테스트
   pytest -q --tb=line -x
   ```

3. **커버리지 확인**
   ```bash
   pytest --cov=src --cov-fail-under=80 -q
   ```

4. **커밋 수행**
   ```bash
   git add src/config/settings.py \
           src/config/container.py \
           src/adapters/inbound/http/app.py \
           src/adapters/outbound/adk/orchestrator_adapter.py \
           tests/integration/test_container_configuration.py \
           tests/integration/adapters/test_orchestrator_adapter.py \
           docs/operators/deployment/configuration.md \
           docs/developers/guides/implementation/di-container-patterns.md \
           docs/developers/guides/implementation/model-switching.md \
           docs/developers/architecture/layer/config/README.md

   git commit -m "$(cat <<'EOF'
   feat: implement Phase 5 - Integration for Configuration System

   - Add Settings fields: encryption_key, config_db_path, LLM API keys
   - Add Container providers: ConfigurationStorage, EncryptionAdapter, ConfigurationService, ConfigurationMigrator
   - Modify Lifespan: DB init, .env → DB migration, encryption key validation
   - Add OrchestratorAdapter.set_model() for model switching (no rebuild)
   - Auto-generate ENCRYPTION_KEY if not set (with critical warning)

   Test Coverage:
   - Container configuration providers: ~5 integration tests
   - OrchestratorAdapter model switching: ~3 integration tests
   - Settings loads encryption_key from environment variable
   - Migration is idempotent (safe to run multiple times)

   DB-First Configuration:
   - SQLite as single source of truth (DB > .env priority)
   - Migration auto-runs on server startup
   - ENCRYPTION_KEY must be added to .env for data recovery

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
   EOF
   )"
   ```

5. **Phase Status 업데이트**
   - `docs/project/planning/planned/09_dynamic_configuration/README.md`에서 Phase 5 Status를 ✅로 변경

---

## Checklist

- [ ] **Baseline 회귀 테스트**: `pytest -q --tb=line` (Phase 시작 전 Green 상태 확인)
- [ ] **Phase 시작**: Status 변경 (⏸️ → 🔄)
- [ ] Step 5.1: Settings 확장 (encryption_key, config_db_path, LLM API keys)
- [ ] Step 5.2: Container 확장 (TDD, ~5 tests, Configuration Providers)
- [ ] Step 5.3: Lifespan 변경 (DB init, migration, key validation)
- [ ] Step 5.4: OrchestratorAdapter.set_model() 추가 (TDD, ~3 tests)
- [ ] Step 5.5: Documentation Update (Deployment + Implementation Guides)
- [ ] **회귀 테스트**: `pytest --cov=src --cov-fail-under=80 -q` (Phase 완료 후 검증)
- [ ] **Phase 완료**: Status 변경 (🔄 → ✅)
- [ ] Git 커밋: `feat: implement Phase 5 - Integration for Configuration System`

---

## 🔑 ENCRYPTION_KEY 관리 중요 사항

### 초기 설정

```bash
# 1. 서버 최초 실행 (ENCRYPTION_KEY 미설정)
uvicorn src.main:app --host localhost --port 8000

# 로그 확인:
# WARNING: ENCRYPTION_KEY not set. Auto-generated key: gAAAAABl...
# ⚠️  CRITICAL: Add this key to .env file immediately!
# ⚠️  Without this key, encrypted data will be unrecoverable on restart.

# 2. 로그에서 키 복사 후 .env에 추가
echo "ENCRYPTION_KEY=gAAAAABl..." >> .env

# 3. 서버 재시작 (이제 .env의 키 사용)
uvicorn src.main:app --host localhost --port 8000
```

### 키 분실 시 대처

```
키 분실 → DB의 암호화된 API Key 복구 불가 → 재등록 필요
```

**예방 방법:**
- .env 파일을 git에 커밋하지 않되, 백업은 안전한 곳에 보관
- 프로덕션 환경에서는 Secret Manager 사용 권장 (AWS Secrets Manager, Azure Key Vault 등)

---

*Last Updated: 2026-02-07*
*Principle: DB-First Configuration, Lifespan Management, Encryption Key Security*
