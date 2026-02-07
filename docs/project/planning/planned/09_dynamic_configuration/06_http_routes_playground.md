# Phase 6: HTTP Routes + Playground UI (Playground-First Testing)

## 개요

Configuration System의 HTTP API와 Playground UI를 함께 구현합니다.

**Playground-First Principle:**
- Backend API 구현 → Playground UI 추가 → E2E 테스트 작성 → 즉시 회귀 테스트
- Extension UI는 Production Preparation Phase로 연기

**핵심:**
- API Key CRUD API + Playground Settings Tab
- Model CRUD API + Playground Settings Tab
- Configuration Exception Handlers
- Playground E2E 테스트 (Playwright)

---

## Step 6.1: Pydantic Response Schemas

**파일:** `src/adapters/inbound/http/schemas/config.py` (신규)

**목표:** Configuration API의 Request/Response 스키마 정의

### Response Models

```python
# src/adapters/inbound/http/schemas/config.py
"""Configuration API Response Schemas"""

from datetime import datetime
from pydantic import BaseModel

from src.domain.entities.api_key_config import ApiKeyConfig
from src.domain.entities.model_config import ModelConfig
from src.domain.entities.enums import LlmProvider


class ApiKeySchema(BaseModel):
    """API Key 응답 스키마 (암호화된 키는 마스킹)"""

    id: str
    provider: str  # LlmProvider enum value
    masked_key: str  # "sk-***1234" 형태
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, api_key: ApiKeyConfig) -> "ApiKeySchema":
        """Domain Entity → HTTP Response Schema"""
        return cls(
            id=api_key.id,
            provider=api_key.provider.value,
            masked_key=api_key.get_masked_key(),
            name=api_key.name,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at,
        )


class ApiKeyCreateRequest(BaseModel):
    """API Key 생성 요청"""

    provider: str  # "openai", "anthropic", "google"
    api_key: str  # Raw API key (평문, 암호화 전)
    name: str = ""


class ApiKeyUpdateRequest(BaseModel):
    """API Key 업데이트 요청"""

    api_key: str | None = None  # 새 키 (None이면 변경 안 함)
    name: str | None = None
    is_active: bool | None = None


class ApiKeyListResponse(BaseModel):
    """API Key 목록 응답"""

    api_keys: list[ApiKeySchema]


class ModelConfigSchema(BaseModel):
    """Model Config 응답 스키마"""

    id: str
    provider: str  # LlmProvider enum value
    model_id: str  # "openai/gpt-4o-mini"
    name: str
    parameters: dict | None = None
    is_default: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, model: ModelConfig) -> "ModelConfigSchema":
        """Domain Entity → HTTP Response Schema"""
        return cls(
            id=model.id,
            provider=model.provider.value,
            model_id=model.model_id,
            name=model.name,
            parameters=model.parameters,
            is_default=model.is_default,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class ModelConfigCreateRequest(BaseModel):
    """Model Config 생성 요청"""

    provider: str  # "openai", "anthropic", "google"
    model_id: str  # "openai/gpt-4o-mini"
    name: str
    parameters: dict | None = None


class ModelConfigUpdateRequest(BaseModel):
    """Model Config 업데이트 요청"""

    name: str | None = None
    parameters: dict | None = None
    is_default: bool | None = None


class ModelConfigListResponse(BaseModel):
    """Model Config 목록 응답"""

    models: list[ModelConfigSchema]


class ConnectionTestRequest(BaseModel):
    """API Key 연결 테스트 요청"""

    provider: str  # "openai", "anthropic", "google"
    api_key: str  # 테스트할 키 (평문)


class ConnectionTestResponse(BaseModel):
    """API Key 연결 테스트 응답"""

    status: str  # "success" or "failed"
    message: str  # 성공: "Connection successful", 실패: 오류 메시지
    model_used: str | None = None  # 테스트에 사용된 모델 (성공 시)
```

**주의사항:**
- `ApiKeySchema`는 암호화된 키를 포함하지 않음 (마스킹된 형태만)
- `ApiKeyCreateRequest`, `ConnectionTestRequest`는 평문 키 포함 (HTTPS 필수)
- `datetime` 필드는 `timezone.utc` 사용 (Entity에서 보장)

**Note:** 이 Step은 테스트가 필요 없습니다 (Pydantic 스키마 정의).

---

## Step 6.2: Config Routes (API Key CRUD)

**파일:** `src/adapters/inbound/http/routes/config.py` (신규)
**테스트:** `tests/integration/test_config_routes.py`

### TDD Required

```python
# tests/integration/test_config_routes.py

import pytest
from httpx import AsyncClient
from src.adapters.inbound.http.app import app
from src.config.container import Container
from src.adapters.outbound.encryption.fernet_encryption_adapter import (
    FernetEncryptionAdapter,
)


@pytest.fixture(scope="module")
async def test_container(tmp_path_factory):
    """테스트용 Container (임시 DB)"""
    tmp_path = tmp_path_factory.mktemp("config_test")
    container = Container()
    container.config.from_dict({
        "encryption_key": FernetEncryptionAdapter.generate_key(),
        "config_db_path": str(tmp_path / "test_config.db"),
    })
    # Initialize storage
    storage = container.configuration_storage()
    await storage.initialize()
    yield container
    await storage.close()


@pytest.fixture
async def client(test_container):
    """Test HTTP Client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


class TestApiKeyRoutes:
    """API Key CRUD Routes 테스트 (~8 tests)"""

    async def test_create_api_key_returns_masked_key(self, client):
        """API Key 생성 - 마스킹된 키 반환"""
        response = await client.post("/api/config/api-keys", json={
            "provider": "openai",
            "api_key": "sk-test1234567890abcdef",
            "name": "Test OpenAI Key",
        })

        assert response.status_code == 201
        data = response.json()
        assert data["provider"] == "openai"
        assert data["masked_key"].startswith("sk-***")
        assert "test1234567890abcdef" not in data["masked_key"]  # 원문 노출 안 됨
        assert data["name"] == "Test OpenAI Key"
        assert data["is_active"] is True

    async def test_create_api_key_invalid_provider(self, client):
        """API Key 생성 - 잘못된 provider → 400"""
        response = await client.post("/api/config/api-keys", json={
            "provider": "invalid_provider",
            "api_key": "sk-test",
            "name": "",
        })

        assert response.status_code == 400
        assert "invalid provider" in response.json()["detail"].lower()

    async def test_list_api_keys_returns_all_keys(self, client):
        """API Key 목록 조회"""
        # 2개 생성
        await client.post("/api/config/api-keys", json={
            "provider": "openai",
            "api_key": "sk-key1",
            "name": "Key 1",
        })
        await client.post("/api/config/api-keys", json={
            "provider": "anthropic",
            "api_key": "sk-key2",
            "name": "Key 2",
        })

        # 목록 조회
        response = await client.get("/api/config/api-keys")

        assert response.status_code == 200
        data = response.json()
        assert len(data["api_keys"]) >= 2
        # 모든 키는 마스킹됨
        for key in data["api_keys"]:
            assert "***" in key["masked_key"]

    async def test_get_api_key_by_id(self, client):
        """API Key 단일 조회"""
        # 생성
        create_resp = await client.post("/api/config/api-keys", json={
            "provider": "google",
            "api_key": "sk-google123",
            "name": "Google Key",
        })
        key_id = create_resp.json()["id"]

        # 조회
        response = await client.get(f"/api/config/api-keys/{key_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == key_id
        assert data["provider"] == "google"

    async def test_update_api_key_name(self, client):
        """API Key 이름 수정"""
        # 생성
        create_resp = await client.post("/api/config/api-keys", json={
            "provider": "openai",
            "api_key": "sk-update-test",
            "name": "Original",
        })
        key_id = create_resp.json()["id"]

        # 수정
        response = await client.patch(f"/api/config/api-keys/{key_id}", json={
            "name": "Updated Name",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    async def test_update_api_key_deactivate(self, client):
        """API Key 비활성화"""
        # 생성
        create_resp = await client.post("/api/config/api-keys", json={
            "provider": "openai",
            "api_key": "sk-deactivate",
            "name": "To deactivate",
        })
        key_id = create_resp.json()["id"]

        # 비활성화
        response = await client.patch(f"/api/config/api-keys/{key_id}", json={
            "is_active": False,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    async def test_delete_api_key(self, client):
        """API Key 삭제"""
        # 생성
        create_resp = await client.post("/api/config/api-keys", json={
            "provider": "openai",
            "api_key": "sk-delete-test",
            "name": "To delete",
        })
        key_id = create_resp.json()["id"]

        # 삭제
        response = await client.delete(f"/api/config/api-keys/{key_id}")

        assert response.status_code == 204

        # 조회 시 404
        get_resp = await client.get(f"/api/config/api-keys/{key_id}")
        assert get_resp.status_code == 404

    async def test_get_api_key_not_found(self, client):
        """존재하지 않는 API Key → 404"""
        response = await client.get("/api/config/api-keys/nonexistent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
```

### API 구현

```python
# src/adapters/inbound/http/routes/config.py
"""Configuration API Routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from dependency_injector.wiring import inject, Provide

from src.config.container import Container
from src.domain.services.configuration_service import ConfigurationService
from src.domain.exceptions import (
    ConfigurationNotFoundError,
    InvalidProviderError,
)
from src.adapters.inbound.http.schemas.config import (
    ApiKeySchema,
    ApiKeyCreateRequest,
    ApiKeyUpdateRequest,
    ApiKeyListResponse,
)

router = APIRouter(prefix="/api/config", tags=["configuration"])


# ============================================================
# API Key CRUD
# ============================================================


@router.post("/api-keys", response_model=ApiKeySchema, status_code=status.HTTP_201_CREATED)
@inject
async def create_api_key(
    request_body: ApiKeyCreateRequest,
    config_service: ConfigurationService = Depends(Provide[Container.configuration_service]),
):
    """API Key 생성"""
    try:
        api_key = await config_service.create_api_key(
            provider=request_body.provider,
            api_key=request_body.api_key,
            name=request_body.name,
        )
        return ApiKeySchema.from_entity(api_key)
    except InvalidProviderError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api-keys", response_model=ApiKeyListResponse)
@inject
async def list_api_keys(
    config_service: ConfigurationService = Depends(Provide[Container.configuration_service]),
):
    """API Key 목록 조회"""
    api_keys = await config_service.list_api_keys()
    return ApiKeyListResponse(
        api_keys=[ApiKeySchema.from_entity(key) for key in api_keys]
    )


@router.get("/api-keys/{key_id}", response_model=ApiKeySchema)
@inject
async def get_api_key(
    key_id: str,
    config_service: ConfigurationService = Depends(Provide[Container.configuration_service]),
):
    """API Key 단일 조회"""
    try:
        api_key = await config_service.get_api_key(key_id)
        return ApiKeySchema.from_entity(api_key)
    except ConfigurationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/api-keys/{key_id}", response_model=ApiKeySchema)
@inject
async def update_api_key(
    key_id: str,
    request_body: ApiKeyUpdateRequest,
    config_service: ConfigurationService = Depends(Provide[Container.configuration_service]),
):
    """API Key 업데이트 (이름, 활성화 상태, 키 교체)"""
    try:
        api_key = await config_service.update_api_key(
            key_id=key_id,
            api_key=request_body.api_key,
            name=request_body.name,
            is_active=request_body.is_active,
        )
        return ApiKeySchema.from_entity(api_key)
    except ConfigurationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_api_key(
    key_id: str,
    config_service: ConfigurationService = Depends(Provide[Container.configuration_service]),
):
    """API Key 삭제"""
    try:
        await config_service.delete_api_key(key_id)
    except ConfigurationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

**주의사항:**
- 생성 시 `status_code=201`
- 삭제 시 `status_code=204` (No Content)
- `InvalidProviderError` → 400 Bad Request
- `ConfigurationNotFoundError` → 404 Not Found

---

## Step 6.3: Config Routes (Model CRUD)

**파일:** `src/adapters/inbound/http/routes/config.py` (확장)
**테스트:** `tests/integration/test_config_routes.py` (확장)

### TDD Required

```python
# tests/integration/test_config_routes.py (확장)


class TestModelConfigRoutes:
    """Model Config CRUD Routes 테스트 (~7 tests)"""

    async def test_create_model(self, client):
        """Model Config 생성"""
        response = await client.post("/api/config/models", json={
            "provider": "openai",
            "model_id": "openai/gpt-4o",
            "name": "GPT-4o",
            "parameters": {"temperature": 0.7, "max_tokens": 2000},
        })

        assert response.status_code == 201
        data = response.json()
        assert data["provider"] == "openai"
        assert data["model_id"] == "openai/gpt-4o"
        assert data["name"] == "GPT-4o"
        assert data["parameters"]["temperature"] == 0.7

    async def test_list_models_returns_all(self, client):
        """Model Config 목록 조회"""
        # 2개 생성
        await client.post("/api/config/models", json={
            "provider": "openai",
            "model_id": "openai/gpt-4o-mini",
            "name": "GPT-4o Mini",
        })
        await client.post("/api/config/models", json={
            "provider": "anthropic",
            "model_id": "anthropic/claude-sonnet-4.5",
            "name": "Claude Sonnet 4.5",
        })

        # 목록 조회
        response = await client.get("/api/config/models")

        assert response.status_code == 200
        data = response.json()
        assert len(data["models"]) >= 2

    async def test_get_model_by_id(self, client):
        """Model Config 단일 조회"""
        # 생성
        create_resp = await client.post("/api/config/models", json={
            "provider": "google",
            "model_id": "google/gemini-2.0-flash-exp",
            "name": "Gemini 2.0 Flash",
        })
        model_id = create_resp.json()["id"]

        # 조회
        response = await client.get(f"/api/config/models/{model_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == model_id
        assert data["model_id"] == "google/gemini-2.0-flash-exp"

    async def test_update_model_name(self, client):
        """Model Config 이름 변경"""
        # 생성
        create_resp = await client.post("/api/config/models", json={
            "provider": "openai",
            "model_id": "openai/gpt-4o",
            "name": "Original Name",
        })
        model_id = create_resp.json()["id"]

        # 수정
        response = await client.patch(f"/api/config/models/{model_id}", json={
            "name": "Updated Name",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    async def test_set_default_model(self, client):
        """기본 모델 설정"""
        # 생성
        create_resp = await client.post("/api/config/models", json={
            "provider": "openai",
            "model_id": "openai/gpt-4o-mini",
            "name": "GPT-4o Mini",
        })
        model_id = create_resp.json()["id"]

        # 기본 모델 설정
        response = await client.post(f"/api/config/models/{model_id}/set-default")

        assert response.status_code == 200
        data = response.json()
        assert data["is_default"] is True

    async def test_select_model_for_orchestrator(self, client):
        """모델 선택 (OrchestratorAdapter.set_model 호출)"""
        # 생성
        create_resp = await client.post("/api/config/models", json={
            "provider": "anthropic",
            "model_id": "anthropic/claude-sonnet-4.5",
            "name": "Claude Sonnet 4.5",
        })
        model_id = create_resp.json()["id"]

        # 선택
        response = await client.post(f"/api/config/models/{model_id}/select")

        assert response.status_code == 200
        assert response.json()["status"] == "selected"

    async def test_delete_model(self, client):
        """Model Config 삭제"""
        # 생성
        create_resp = await client.post("/api/config/models", json={
            "provider": "openai",
            "model_id": "openai/gpt-3.5-turbo",
            "name": "GPT-3.5 Turbo",
        })
        model_id = create_resp.json()["id"]

        # 삭제
        response = await client.delete(f"/api/config/models/{model_id}")

        assert response.status_code == 204

        # 조회 시 404
        get_resp = await client.get(f"/api/config/models/{model_id}")
        assert get_resp.status_code == 404
```

### API 구현 (확장)

```python
# src/adapters/inbound/http/routes/config.py (Model CRUD 추가)

from src.adapters.inbound.http.schemas.config import (
    ModelConfigSchema,
    ModelConfigCreateRequest,
    ModelConfigUpdateRequest,
    ModelConfigListResponse,
)
from src.domain.ports.outbound.orchestrator_port import OrchestratorPort


# ============================================================
# Model CRUD
# ============================================================


@router.post("/models", response_model=ModelConfigSchema, status_code=status.HTTP_201_CREATED)
@inject
async def create_model(
    request_body: ModelConfigCreateRequest,
    config_service: ConfigurationService = Depends(Provide[Container.configuration_service]),
):
    """Model Config 생성"""
    try:
        model = await config_service.create_model(
            provider=request_body.provider,
            model_id=request_body.model_id,
            name=request_body.name,
            parameters=request_body.parameters,
        )
        return ModelConfigSchema.from_entity(model)
    except InvalidProviderError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/models", response_model=ModelConfigListResponse)
@inject
async def list_models(
    config_service: ConfigurationService = Depends(Provide[Container.configuration_service]),
):
    """Model Config 목록 조회"""
    models = await config_service.list_models()
    return ModelConfigListResponse(
        models=[ModelConfigSchema.from_entity(m) for m in models]
    )


@router.get("/models/{model_id}", response_model=ModelConfigSchema)
@inject
async def get_model(
    model_id: str,
    config_service: ConfigurationService = Depends(Provide[Container.configuration_service]),
):
    """Model Config 단일 조회"""
    try:
        model = await config_service.get_model(model_id)
        return ModelConfigSchema.from_entity(model)
    except ConfigurationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/models/{model_id}", response_model=ModelConfigSchema)
@inject
async def update_model(
    model_id: str,
    request_body: ModelConfigUpdateRequest,
    config_service: ConfigurationService = Depends(Provide[Container.configuration_service]),
):
    """Model Config 업데이트"""
    try:
        model = await config_service.update_model(
            model_id=model_id,
            name=request_body.name,
            parameters=request_body.parameters,
            is_default=request_body.is_default,
        )
        return ModelConfigSchema.from_entity(model)
    except ConfigurationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/models/{model_id}/set-default", response_model=ModelConfigSchema)
@inject
async def set_default_model(
    model_id: str,
    config_service: ConfigurationService = Depends(Provide[Container.configuration_service]),
):
    """기본 모델 설정 (다른 모델들의 is_default=False 자동 해제)"""
    try:
        model = await config_service.set_default_model(model_id)
        return ModelConfigSchema.from_entity(model)
    except ConfigurationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/models/{model_id}/select")
@inject
async def select_model(
    model_id: str,
    config_service: ConfigurationService = Depends(Provide[Container.configuration_service]),
    orchestrator: OrchestratorPort = Depends(Provide[Container.orchestrator_adapter]),
):
    """모델 선택 (OrchestratorAdapter.set_model 호출)

    1. ConfigurationService에서 Model Config 조회
    2. OrchestratorAdapter.set_model()로 모델 전환
    3. 다음 generate_response()부터 새 모델 사용
    """
    try:
        model = await config_service.get_model(model_id)
        orchestrator.set_model(model.model_id)
        return {"status": "selected", "model_id": model.model_id}
    except ConfigurationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_model(
    model_id: str,
    config_service: ConfigurationService = Depends(Provide[Container.configuration_service]),
):
    """Model Config 삭제"""
    try:
        await config_service.delete_model(model_id)
    except ConfigurationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

**핵심:**
- `POST /models/{model_id}/select` - Route 레벨 조율 패턴 (ADR-C03)
- `OrchestratorPort`를 직접 주입하여 model 전환 (헥사고날 위반 아님)
- `set_model()`은 재빌드 없이 모델만 변경

---

## Step 6.4: Exception Handler 등록

**파일:** `src/adapters/inbound/http/exceptions.py` (확장)

**목표:** Configuration 관련 Exception을 HTTP 에러로 변환

### 구현

```python
# src/adapters/inbound/http/exceptions.py (확장)

from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.domain.exceptions import (
    ConfigurationNotFoundError,
    InvalidProviderError,
    EncryptionError,
    DecryptionError,
)


async def configuration_not_found_exception_handler(
    request: Request, exc: ConfigurationNotFoundError
):
    """ConfigurationNotFoundError → 404"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


async def invalid_provider_exception_handler(request: Request, exc: InvalidProviderError):
    """InvalidProviderError → 400"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


async def encryption_error_exception_handler(request: Request, exc: EncryptionError):
    """EncryptionError → 500"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Encryption failed"},
    )


async def decryption_error_exception_handler(request: Request, exc: DecryptionError):
    """DecryptionError → 500"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Decryption failed"},
    )


# src/adapters/inbound/http/app.py (Exception Handler 등록)

from src.adapters.inbound.http import exceptions as custom_exceptions

app.add_exception_handler(
    ConfigurationNotFoundError,
    custom_exceptions.configuration_not_found_exception_handler,
)
app.add_exception_handler(
    InvalidProviderError,
    custom_exceptions.invalid_provider_exception_handler,
)
app.add_exception_handler(
    EncryptionError,
    custom_exceptions.encryption_error_exception_handler,
)
app.add_exception_handler(
    DecryptionError,
    custom_exceptions.decryption_error_exception_handler,
)
```

**Note:** 이 Step은 테스트가 필요 없습니다 (Exception Handler 등록).

---

## Step 6.5: Playground Settings Tab (HTML/JS)

**파일:**
- `tests/manual/playground/index.html` (확장)
- `tests/manual/playground/js/settings-handler.js` (신규)

**목표:** Playground에 Settings Tab 추가 (API Key CRUD, Model CRUD, Connection Test)

### HTML Tab

```html
<!-- tests/manual/playground/index.html (Settings Tab 추가) -->

<nav class="tabs">
  <!-- 기존 탭들... -->
  <button class="tab-btn" data-tab="settings" data-testid="tab-settings">Settings</button>
</nav>

<div id="settings-tab" class="tab-pane" style="display: none;">
  <h2>Configuration Settings</h2>

  <!-- API Key Management -->
  <section class="settings-section">
    <h3>API Keys</h3>
    <div class="form-group">
      <label>Provider:</label>
      <select data-testid="settings-api-key-provider">
        <option value="openai">OpenAI</option>
        <option value="anthropic">Anthropic</option>
        <option value="google">Google</option>
      </select>

      <label>API Key:</label>
      <input type="password" data-testid="settings-api-key-input" placeholder="sk-...">

      <label>Description:</label>
      <input type="text" data-testid="settings-api-key-description" placeholder="My API Key">

      <button data-testid="settings-api-key-create">Add API Key</button>
      <button data-testid="settings-api-key-test">Test Connection</button>
    </div>

    <div class="api-keys-list" data-testid="settings-api-keys-list">
      <!-- API Key 카드들 동적 렌더링 -->
    </div>
  </section>

  <!-- Model Management -->
  <section class="settings-section">
    <h3>Model Configurations</h3>
    <div class="form-group">
      <label>Provider:</label>
      <select data-testid="settings-model-provider">
        <option value="openai">OpenAI</option>
        <option value="anthropic">Anthropic</option>
        <option value="google">Google</option>
      </select>

      <label>Model ID:</label>
      <input type="text" data-testid="settings-model-id" placeholder="openai/gpt-4o-mini">

      <label>Display Name:</label>
      <input type="text" data-testid="settings-model-display-name" placeholder="GPT-4o Mini">

      <button data-testid="settings-model-create">Add Model</button>
    </div>

    <div class="models-list" data-testid="settings-models-list">
      <!-- Model 카드들 동적 렌더링 -->
    </div>
  </section>
</div>
```

### JavaScript Handler

```javascript
// tests/manual/playground/js/settings-handler.js
/**
 * Settings Tab Handler (API Key CRUD + Model CRUD)
 */

const API_BASE = "http://localhost:8000";

// ============================================================
// API Key Management
// ============================================================

async function loadApiKeys() {
  const response = await fetch(`${API_BASE}/api/config/api-keys`);
  const data = await response.json();
  renderApiKeysList(data.api_keys);
}

function renderApiKeysList(apiKeys) {
  const listEl = document.querySelector('[data-testid="settings-api-keys-list"]');
  listEl.innerHTML = apiKeys.map(key => `
    <div class="api-key-card" data-id="${key.id}">
      <div class="api-key-header">
        <span class="provider-badge">${key.provider}</span>
        <span class="masked-key">${key.masked_key}</span>
        ${key.is_active ? '<span class="active-badge">Active</span>' : '<span class="inactive-badge">Inactive</span>'}
      </div>
      <p class="description">${key.description || '(No description)'}</p>
      <div class="actions">
        <button onclick="toggleApiKeyStatus('${key.id}', ${!key.is_active})">
          ${key.is_active ? 'Deactivate' : 'Activate'}
        </button>
        <button onclick="deleteApiKey('${key.id}')">Delete</button>
      </div>
    </div>
  `).join('');
}

async function createApiKey() {
  const provider = document.querySelector('[data-testid="settings-api-key-provider"]').value;
  const apiKey = document.querySelector('[data-testid="settings-api-key-input"]').value;
  const description = document.querySelector('[data-testid="settings-api-key-description"]').value;

  const response = await fetch(`${API_BASE}/api/config/api-keys`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider, api_key: apiKey, description }),
  });

  if (response.ok) {
    showNotification('API Key added successfully');
    loadApiKeys();
    // 입력 필드 초기화
    document.querySelector('[data-testid="settings-api-key-input"]').value = '';
    document.querySelector('[data-testid="settings-api-key-description"]').value = '';
  } else {
    const error = await response.json();
    showNotification(`Error: ${error.detail}`, 'error');
  }
}

async function toggleApiKeyStatus(keyId, isActive) {
  const response = await fetch(`${API_BASE}/api/config/api-keys/${keyId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ is_active: isActive }),
  });

  if (response.ok) {
    showNotification(`API Key ${isActive ? 'activated' : 'deactivated'}`);
    loadApiKeys();
  }
}

async function deleteApiKey(keyId) {
  if (!confirm('Delete this API Key?')) return;

  const response = await fetch(`${API_BASE}/api/config/api-keys/${keyId}`, {
    method: 'DELETE',
  });

  if (response.ok) {
    showNotification('API Key deleted');
    loadApiKeys();
  }
}

async function testApiKeyConnection() {
  const provider = document.querySelector('[data-testid="settings-api-key-provider"]').value;
  const apiKey = document.querySelector('[data-testid="settings-api-key-input"]').value;

  const response = await fetch(`${API_BASE}/api/config/test-connection`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider, api_key: apiKey }),
  });

  const result = await response.json();
  if (result.status === 'success') {
    showNotification(`✅ ${result.message} (Model: ${result.model_used})`, 'success');
  } else {
    showNotification(`❌ ${result.message}`, 'error');
  }
}

// ============================================================
// Model Management
// ============================================================

async function loadModels() {
  const response = await fetch(`${API_BASE}/api/config/models`);
  const data = await response.json();
  renderModelsList(data.models);
}

function renderModelsList(models) {
  const listEl = document.querySelector('[data-testid="settings-models-list"]');
  listEl.innerHTML = models.map(model => `
    <div class="model-card" data-id="${model.id}">
      <div class="model-header">
        <span class="provider-badge">${model.provider}</span>
        <strong>${model.display_name}</strong>
        ${model.is_default ? '<span class="default-badge">Default</span>' : ''}
      </div>
      <p class="model-id">${model.model_id}</p>
      <div class="actions">
        <button onclick="selectModel('${model.id}')">Select</button>
        ${!model.is_default ? `<button onclick="setDefaultModel('${model.id}')">Set Default</button>` : ''}
        <button onclick="deleteModel('${model.id}')">Delete</button>
      </div>
    </div>
  `).join('');
}

async function createModel() {
  const provider = document.querySelector('[data-testid="settings-model-provider"]').value;
  const modelId = document.querySelector('[data-testid="settings-model-id"]').value;
  const displayName = document.querySelector('[data-testid="settings-model-display-name"]').value;

  const response = await fetch(`${API_BASE}/api/config/models`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider, model_id: modelId, display_name: displayName }),
  });

  if (response.ok) {
    showNotification('Model added successfully');
    loadModels();
    // 입력 필드 초기화
    document.querySelector('[data-testid="settings-model-id"]').value = '';
    document.querySelector('[data-testid="settings-model-display-name"]').value = '';
  } else {
    const error = await response.json();
    showNotification(`Error: ${error.detail}`, 'error');
  }
}

async function selectModel(modelId) {
  const response = await fetch(`${API_BASE}/api/config/models/${modelId}/select`, {
    method: 'POST',
  });

  if (response.ok) {
    showNotification('Model selected for next conversation');
  }
}

async function setDefaultModel(modelId) {
  const response = await fetch(`${API_BASE}/api/config/models/${modelId}/set-default`, {
    method: 'POST',
  });

  if (response.ok) {
    showNotification('Default model updated');
    loadModels();
  }
}

async function deleteModel(modelId) {
  if (!confirm('Delete this model configuration?')) return;

  const response = await fetch(`${API_BASE}/api/config/models/${modelId}`, {
    method: 'DELETE',
  });

  if (response.ok) {
    showNotification('Model deleted');
    loadModels();
  }
}

// ============================================================
// Initialization
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  // Event Listeners
  document.querySelector('[data-testid="settings-api-key-create"]').addEventListener('click', createApiKey);
  document.querySelector('[data-testid="settings-api-key-test"]').addEventListener('click', testApiKeyConnection);
  document.querySelector('[data-testid="settings-model-create"]').addEventListener('click', createModel);

  // Tab 전환 시 데이터 로드
  document.querySelector('[data-testid="tab-settings"]').addEventListener('click', () => {
    loadApiKeys();
    loadModels();
  });
});

function showNotification(message, type = 'info') {
  // 알림 UI 표시 (간단한 alert로 대체 가능)
  alert(message);
}
```

**주의사항:**
- API Key는 평문으로 입력받지만 HTTPS 필수 (프로덕션 환경)
- Playground는 로컬 테스트용 (http://localhost:3000)
- 입력 필드 초기화로 보안 강화 (입력 후 즉시 clear)

---

## Step 6.6: API Key Connection Test API

**파일:** `src/adapters/inbound/http/routes/config.py` (확장)
**테스트:** `tests/integration/test_config_routes.py` (확장, `llm` 마커)

### TDD Required

```python
# tests/integration/test_config_routes.py (확장)


class TestApiKeyConnectionTest:
    """API Key 연결 테스트 (~2 tests)"""

    @pytest.mark.llm
    async def test_connection_test_success(self, client):
        """유효한 API Key - 연결 성공"""
        # 실제 유효한 키 필요 (환경변수에서 로드)
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        response = await client.post("/api/config/test-connection", json={
            "provider": "openai",
            "api_key": api_key,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "model_used" in data

    async def test_connection_test_invalid_key(self, client):
        """잘못된 API Key - 연결 실패"""
        response = await client.post("/api/config/test-connection", json={
            "provider": "openai",
            "api_key": "sk-invalid-key",
        })

        # LiteLLM은 401/403 에러를 발생시킴 → 500 또는 400
        assert response.status_code in [400, 500]
        data = response.json()
        assert data["status"] == "failed"
```

### API 구현

```python
# src/adapters/inbound/http/routes/config.py (Connection Test API 추가)

import litellm
from src.adapters.inbound.http.schemas.config import (
    ConnectionTestRequest,
    ConnectionTestResponse,
)


@router.post("/test-connection", response_model=ConnectionTestResponse)
async def test_api_key_connection(request_body: ConnectionTestRequest):
    """API Key 연결 테스트 (LiteLLM 최소 호출)

    Provider별 기본 모델로 최소 토큰 호출:
    - openai: gpt-4o-mini
    - anthropic: claude-haiku-4.5
    - google: gemini-2.0-flash-exp
    """
    # Provider별 기본 모델
    default_models = {
        "openai": "openai/gpt-4o-mini",
        "anthropic": "anthropic/claude-haiku-4.5",
        "google": "google/gemini-2.0-flash-exp",
    }

    provider = request_body.provider
    if provider not in default_models:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    model = default_models[provider]

    try:
        # LiteLLM per-request API key 사용 (thread-safe)
        response = await litellm.acompletion(
            model=model,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1,
            api_key=request_body.api_key,  # per-request로 전달 (환경변수 사용 안 함)
        )

        return ConnectionTestResponse(
            status="success",
            message="Connection successful",
            model_used=model,
        )
    except Exception as e:
        return ConnectionTestResponse(
            status="failed",
            message=str(e),
        )
```

**주의사항:**
- `litellm.acompletion()` 사용 (비동기)
- **Thread-safe**: `api_key` 파라미터로 per-request 전달 (환경변수 사용 안 함)
- `max_tokens=1` - 최소 비용
- `@pytest.mark.llm` - 실제 LLM API 호출하는 테스트

---

## Step 6.7: Router 등록

**파일:** `src/adapters/inbound/http/app.py` (확장)

```python
# src/adapters/inbound/http/app.py (Router 등록)

from src.adapters.inbound.http.routes import config

app.include_router(config.router)
```

---

## Step 6.8: Playground Regression Tests (E2E)

**파일:** `tests/e2e/test_playground_settings.py` (신규)

### E2E 테스트

```python
# tests/e2e/test_playground_settings.py
"""Playground Settings Tab E2E Tests"""

import pytest
from playwright.async_api import async_playwright


@pytest.mark.e2e_playwright
class TestPlaygroundSettings:
    """Playground Settings Tab E2E 테스트 (~10 tests)"""

    @pytest.fixture
    async def page(self):
        """Playwright Page Fixture"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            yield page
            await browser.close()

    async def test_settings_tab_displays(self, page):
        """Settings 탭 클릭 시 표시"""
        await page.goto("http://localhost:3000")
        await page.click('[data-testid="tab-settings"]')

        # Settings 탭 표시됨
        settings_tab = await page.locator('#settings-tab').is_visible()
        assert settings_tab

    async def test_create_api_key_displays_in_list(self, page):
        """API Key 생성 후 목록에 표시"""
        await page.goto("http://localhost:3000")
        await page.click('[data-testid="tab-settings"]')

        # API Key 생성
        await page.select_option('[data-testid="settings-api-key-provider"]', 'openai')
        await page.fill('[data-testid="settings-api-key-input"]', 'sk-test-playground')
        await page.fill('[data-testid="settings-api-key-description"]', 'Playground Test Key')
        await page.click('[data-testid="settings-api-key-create"]')

        # 목록에 표시됨
        api_key_cards = await page.locator('.api-key-card').all()
        assert len(api_key_cards) > 0

        # 마스킹된 키 확인
        masked_key = await page.locator('.masked-key').first.text_content()
        assert '***' in masked_key

    async def test_api_key_shows_masked_key(self, page):
        """API Key 목록에서 마스킹된 키만 표시"""
        await page.goto("http://localhost:3000")
        await page.click('[data-testid="tab-settings"]')

        # 목록 로드 대기
        await page.wait_for_selector('.api-key-card')

        # 모든 카드에서 원문 키 노출 안 됨
        cards = await page.locator('.api-key-card').all()
        for card in cards:
            masked_key = await card.locator('.masked-key').text_content()
            assert '***' in masked_key
            assert 'sk-test-playground' not in masked_key

    async def test_deactivate_api_key(self, page):
        """API Key 비활성화"""
        await page.goto("http://localhost:3000")
        await page.click('[data-testid="tab-settings"]')

        # 첫 번째 카드 비활성화
        await page.wait_for_selector('.api-key-card')
        await page.locator('.api-key-card').first.locator('button:has-text("Deactivate")').click()

        # Inactive 뱃지 표시됨
        inactive_badge = await page.locator('.inactive-badge').first.is_visible()
        assert inactive_badge

    async def test_create_model_displays_in_list(self, page):
        """Model Config 생성 후 목록에 표시"""
        await page.goto("http://localhost:3000")
        await page.click('[data-testid="tab-settings"]')

        # Model 생성
        await page.select_option('[data-testid="settings-model-provider"]', 'openai')
        await page.fill('[data-testid="settings-model-id"]', 'openai/gpt-4o')
        await page.fill('[data-testid="settings-model-display-name"]', 'GPT-4o Playground')
        await page.click('[data-testid="settings-model-create"]')

        # 목록에 표시됨
        model_cards = await page.locator('.model-card').all()
        assert len(model_cards) > 0

    async def test_select_model_shows_notification(self, page):
        """모델 선택 시 알림 표시"""
        await page.goto("http://localhost:3000")
        await page.click('[data-testid="tab-settings"]')

        # 첫 번째 모델 선택
        await page.wait_for_selector('.model-card')
        await page.locator('.model-card').first.locator('button:has-text("Select")').click()

        # 알림 확인 (alert 또는 notification UI)
        # (구현에 따라 수정)

    async def test_set_default_model(self, page):
        """기본 모델 설정"""
        await page.goto("http://localhost:3000")
        await page.click('[data-testid="tab-settings"]')

        # 두 번째 모델을 기본으로 설정
        await page.wait_for_selector('.model-card')
        cards = await page.locator('.model-card').all()
        if len(cards) > 1:
            await cards[1].locator('button:has-text("Set Default")').click()

            # Default 뱃지 표시됨
            default_badge = await cards[1].locator('.default-badge').is_visible()
            assert default_badge

    async def test_delete_api_key_removes_from_list(self, page):
        """API Key 삭제 후 목록에서 제거"""
        await page.goto("http://localhost:3000")
        await page.click('[data-testid="tab-settings"]')

        # 초기 카드 수
        await page.wait_for_selector('.api-key-card')
        initial_count = len(await page.locator('.api-key-card').all())

        # 첫 번째 카드 삭제
        page.on('dialog', lambda dialog: dialog.accept())  # confirm 자동 승인
        await page.locator('.api-key-card').first.locator('button:has-text("Delete")').click()

        # 카드 수 감소
        await page.wait_for_timeout(1000)  # API 호출 대기
        final_count = len(await page.locator('.api-key-card').all())
        assert final_count == initial_count - 1

    async def test_delete_model_removes_from_list(self, page):
        """Model Config 삭제 후 목록에서 제거"""
        await page.goto("http://localhost:3000")
        await page.click('[data-testid="tab-settings"]')

        # 초기 카드 수
        await page.wait_for_selector('.model-card')
        initial_count = len(await page.locator('.model-card').all())

        # 첫 번째 카드 삭제
        page.on('dialog', lambda dialog: dialog.accept())
        await page.locator('.model-card').first.locator('button:has-text("Delete")').click()

        # 카드 수 감소
        await page.wait_for_timeout(1000)
        final_count = len(await page.locator('.model-card').all())
        assert final_count == initial_count - 1
```

**실행:**
```bash
pytest tests/e2e/test_playground_settings.py -v -m e2e_playwright
```

---

## Verification

```bash
# Phase 1-5 복습
pytest tests/unit/ -q --tb=line -x
pytest tests/integration/adapters/ -v

# Phase 6 Integration Tests (Routes)
pytest tests/integration/test_config_routes.py -v

# Phase 6 E2E Tests (Playground)
pytest tests/e2e/test_playground_settings.py -v -m e2e_playwright

# Connection Test (실제 LLM API 호출)
pytest tests/integration/test_config_routes.py::TestApiKeyConnectionTest -v -m llm

# Coverage
pytest --cov=src --cov-fail-under=80 -q
```

---

## Step 6.9: Documentation Update

**목표:** Phase 6에서 구현된 HTTP API 및 Playground Testing 문서화

**문서화 항목:**

| 작업 | 대상 파일 | 유형 | 내용 |
|------|----------|------|------|
| Create | docs/developers/architecture/api/configuration.md | API Documentation | Configuration API 전체 엔드포인트 문서 (API Key CRUD, Model CRUD, Connection Test) |
| Modify | docs/developers/architecture/api/configuration.md | API Documentation | Request/Response Schema, Route 레벨 조율 패턴 (select 엔드포인트) 설명 |
| Modify | tests/manual/playground/README.md | Component README | Settings Tab 추가 (API Key/Model 관리 UI) |
| Modify | tests/docs/EXECUTION.md | Test Documentation | Playground E2E 테스트 실행 섹션 업데이트 (Settings Tab 테스트) |
| Modify | tests/docs/STRUCTURE.md | Test Documentation | tests/e2e/test_playground_settings.py 추가 |
| Modify | docs/MAP.md | Directory Structure | API 문서 파일 반영 (developers/architecture/api/configuration.md) |

**ADR 참조:**
- [ADR-T07 (Playground-First Testing)](../../decisions/technical/ADR-T07-playground-first-testing.md) — Phase 6+ 원칙
- [ADR-C03 (Route-Level Model Coordination)](../../decisions/configuration/ADR-C03-route-level-model-coordination.md) — Model 선택 API 패턴

**주의사항:**
- configuration.md는 전체 API 포함 (OpenAPI 스펙 아닌 개발자 문서 형식)
- Connection Test API는 `llm` 마커 필수 (실제 LLM API 호출)
- Playground README.md는 ToC + 빠른 시작, 상세 E2E 테스트 가이드는 tests/docs/에 작성

---

## Step 6.10: Git Commit

**목표:** Phase 6 완료 커밋

**절차:**

1. **Phase 시작 전 회귀 테스트 베이스라인 기록**
   ```bash
   pytest -q --tb=line -x
   ```

2. **Phase 완료 후 전체 테스트 실행**
   ```bash
   # Phase 6 Integration Tests
   pytest tests/integration/test_config_routes.py -v

   # Phase 6 E2E Tests
   pytest tests/e2e/test_playground_settings.py -v -m e2e_playwright

   # 전체 회귀 테스트
   pytest -q --tb=line -x
   ```

3. **커버리지 확인**
   ```bash
   pytest --cov=src --cov-fail-under=80 -q
   ```

4. **커밋 수행**
   ```bash
   git add src/adapters/inbound/http/schemas/config.py \
           src/adapters/inbound/http/routes/config.py \
           src/adapters/inbound/http/exceptions.py \
           src/adapters/inbound/http/app.py \
           tests/integration/test_config_routes.py \
           tests/e2e/test_playground_settings.py \
           tests/manual/playground/index.html \
           tests/manual/playground/js/settings-handler.js \
           docs/developers/architecture/api/configuration.md \
           docs/MAP.md

   git commit -m "$(cat <<'EOF'
   feat: implement Phase 6 - HTTP Routes + Playground UI for Configuration System

   - Add Pydantic Response Schemas: ApiKeySchema, ModelConfigSchema, ConnectionTestRequest/Response
   - Add Config Routes: API Key CRUD (create, list, get, update, delete)
   - Add Config Routes: Model CRUD (create, list, get, update, delete, set-default, select)
   - Add Connection Test API: litellm.acompletion minimal call (max_tokens=1)
   - Add Exception Handlers: ConfigurationNotFoundError → 404, InvalidProviderError → 400
   - Add Playground Settings Tab: API Key/Model management UI (HTML + JavaScript)
   - Add E2E Tests: Playwright tests for Settings Tab (~10 tests)

   Test Coverage:
   - API Key CRUD Routes: ~8 integration tests
   - Model CRUD Routes: ~7 integration tests
   - Connection Test: ~2 integration tests (llm marker)
   - Playground E2E: ~10 tests (e2e_playwright marker)

   Playground-First Testing:
   - Backend API + Playground UI implemented together
   - Immediate regression testing with E2E Playwright
   - Extension UI deferred to Production Preparation Phase

   Route-Level Model Coordination (ADR-C03):
   - POST /models/{model_id}/select calls OrchestratorAdapter.set_model()
   - No agent rebuild (model change only, next generate_response reflects)

   Security:
   - API Key masked in all responses (sk-***1234)
   - Plaintext keys only in create/update requests (HTTPS required)
   - Connection Test: API Key set to env var temporarily, removed after test

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
   EOF
   )"
   ```

5. **Phase Status 업데이트**
   - `docs/project/planning/planned/09_dynamic_configuration/README.md`에서 Phase 6 Status를 ✅로 변경

---

## Checklist

- [ ] **Baseline 회귀 테스트**: `pytest -q --tb=line` (Phase 시작 전 Green 상태 확인)
- [ ] **Phase 시작**: Status 변경 (⏸️ → 🔄)
- [ ] Step 6.1: Pydantic Response Schemas (ApiKeySchema, ModelConfigSchema, etc.)
- [ ] Step 6.2: Config Routes (API Key CRUD) - TDD, ~8 tests
- [ ] Step 6.3: Config Routes (Model CRUD) - TDD, ~7 tests
- [ ] Step 6.4: Exception Handler 등록
- [ ] Step 6.5: Playground Settings Tab (HTML/JS)
- [ ] Step 6.6: API Key Connection Test API - TDD, ~2 tests (llm marker)
- [ ] Step 6.7: Router 등록
- [ ] Step 6.8: Playground Regression Tests (E2E, ~10 tests)
- [ ] Step 6.9: Documentation Update (API Docs + Playground README + Test Docs + ADR References)
- [ ] **회귀 테스트**: `pytest --cov=src --cov-fail-under=80 -q` (Phase 완료 후 검증)
- [ ] **Phase 완료**: Status 변경 (🔄 → ✅)
- [ ] Step 6.10: Git 커밋: `feat: implement Phase 6 - HTTP Routes + Playground UI for Configuration System`

---

## 🔒 Security Notes

### API Key 노출 방지

```python
# ✅ GOOD - 마스킹된 키만 반환
class ApiKeySchema(BaseModel):
    masked_key: str  # "sk-***1234"

# ❌ BAD - 원문 키 노출
class ApiKeySchema(BaseModel):
    api_key: str  # "sk-1234567890abcdef"
```

### Connection Test 보안

```python
# API Key를 임시 환경변수로 설정 후 즉시 제거
os.environ[env_var_name] = request_body.api_key
try:
    await litellm.acompletion(...)
finally:
    os.environ.pop(env_var_name, None)  # 보안: 환경변수 제거
```

### HTTPS 필수 (Production)

```
Playground는 로컬 테스트용 (http://localhost:3000)
프로덕션 환경에서는 HTTPS 필수 (평문 API Key 전송)
```

---

*Last Updated: 2026-02-07*
*Playground-First: Backend + Playground UI + E2E Tests together*
