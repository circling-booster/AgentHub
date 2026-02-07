# Plan 09: Dynamic Configuration & Model Management (Draft)

> **상태:** 📋 Draft
> **선행 조건:** Plan 07 Complete
> **목표:** API Key 관리 + LLM 모델 동적 선택 (Playground + Extension)

---

## Overview

**핵심 문제:**
- 현재: API Key와 모델이 `.env`와 `configs/default.yaml`에 하드코딩
- 필요: 사용자가 Playground/Extension UI에서 직접 추가/선택

**구현 범위:**
1. **API Key Management**: CRUD 작업 (추가, 조회, 삭제)
2. **Model Selection**: LiteLLM 지원 모델 목록 + 선택
3. **Playground UI**: Settings 탭 (Phase 6+)
4. **Extension UI**: Settings 페이지 (Production Phase로 연기)

**저장소:**
- Backend: SQLite (새 테이블 `api_keys`, `model_configs`)
- Extension: LocalStorage (미래: Backend와 동기화)

---

## Key Features

### 1. API Key Management

**Domain Entities:**
```python
@dataclass
class ApiKeyConfig:
    id: str
    provider: str  # "openai", "anthropic", "google", etc.
    key_name: str  # User-friendly name (e.g., "My OpenAI Key")
    encrypted_key: str  # 암호화된 API Key
    created_at: datetime
    last_used_at: datetime | None
    is_active: bool
```

**Operations:**
- POST `/api/config/api-keys` - Add new API key
- GET `/api/config/api-keys` - List API keys (masked)
- DELETE `/api/config/api-keys/{id}` - Remove API key
- POST `/api/config/api-keys/{id}/test` - Test validity

### 2. Model Selection

**Domain Entities:**
```python
@dataclass
class ModelConfig:
    id: str
    provider: str  # "openai", "anthropic", etc.
    model_id: str  # "gpt-4o-mini", "claude-sonnet-4.5", etc.
    display_name: str  # "GPT-4o Mini"
    is_default: bool
    parameters: dict[str, Any]  # temperature, max_tokens, etc.
```

**Operations:**
- GET `/api/config/models` - List available models (from LiteLLM)
- GET `/api/config/models/selected` - Get current default model
- POST `/api/config/models/{id}/select` - Set default model
- PUT `/api/config/models/{id}/parameters` - Update model parameters

### 3. Playground UI (Phase 6)

**Settings Tab:**
- API Key 섹션:
  - Provider 선택 드롭다운 (OpenAI, Anthropic, Google, etc.)
  - Key Name 입력 (선택적)
  - API Key 입력 (masked)
  - Add/Delete 버튼
  - Test Connection 버튼

- Model 섹션:
  - Provider 필터 드롭다운
  - Model 선택 Radio Buttons (display_name + model_id)
  - Parameters 조정 슬라이더 (temperature, max_tokens)
  - Save 버튼

### 4. Extension UI (추후)

**Settings Page:**
- Playground와 동일한 UI
- LocalStorage에 저장 → Backend API 호출로 동기화

---

## Phases (Preliminary)

| Phase | 설명 | Playground | Status |
|-------|------|------------|--------|
| **1** | Domain Entities (ApiKeyConfig, ModelConfig) | - | ⏸️ |
| **2** | Port Interface (ConfigurationStoragePort, EncryptionPort) + Fake | - | ⏸️ |
| **3** | Domain Services (ConfigurationService) + Custom Exceptions | - | ⏸️ |
| **4.1** | Storage Adapter (SQLite + Tables) | - | ⏸️ |
| **4.2** | Encryption Adapter + Migration Logic | - | ⏸️ |
| **5** | Integration (DI Container + OrchestratorService 리팩토링) | - | ⏸️ |
| **6** | HTTP Routes + Playground UI + Error Handlers | ✅ | ⏸️ |
| **7** | Validation & E2E Tests | ✅ | ⏸️ |

**Phase 4 세분화 이유:** Storage와 Encryption은 독립적인 TDD 사이클. Phase 4.2의 Migration은 4.1의 Storage에 의존.

**Phase 상세는 Plan 승인 후 작성 예정**

---

## Standards Verification Protocol

**CRITICAL:** LiteLLM과 Cryptography는 빠르게 진화하는 라이브러리입니다. 구현 전 최신 API 검증 필수.

### Phase 1 시작 전 (Plan Phase)

**Web Search 필수:**
- Query: "LiteLLM 1.x API 2026", "LiteLLM model list Python"
- 검증 항목:
  - `model_list` API 존재 여부 및 반환 형식
  - 지원 Provider 목록 (openai, anthropic, google 등)
  - 모델 ID 형식 ("openai/gpt-4o-mini" vs "gpt-4o-mini")

### Phase 4 시작 전 (Implementation Phase)

**Web Search 재검증:**
- Query: "Cryptography Fernet Python 2026", "Fernet encryption key size"
- 검증 항목:
  - `Fernet.generate_key()` 메서드
  - `encrypt()`, `decrypt()` 메서드 시그니처
  - 키 길이 요구사항 (32-byte)

**의존성 버전:**
```toml
[tool.poetry.dependencies]
litellm = "^1.25.0"  # Minor 버전 고정
cryptography = ">=42.0.0,<43.0.0"  # 최신 안정 버전
```

---

## Design Considerations

### Port Interfaces (Phase 2)

**ConfigurationStoragePort:**
- API Key CRUD: `add_api_key()`, `get_api_keys()`, `delete_api_key()`
- Model Config: `get_model_configs()`, `set_default_model()`, `update_model_parameters()`
- Migration: `get_migration_version()`, `set_migration_version()` (멱등성 보장)

**EncryptionPort:**
- `encrypt(plaintext: str) -> str`: API Key 암호화
- `decrypt(ciphertext: str) -> str`: API Key 복호화
- `generate_key() -> str`: 최초 실행 시 키 생성

### Security

**API Key 암호화:**
- Fernet (symmetric encryption) 사용
- 암호화 키는 환경변수 `ENCRYPTION_KEY`로 관리
- **키 영구 저장:** 최초 생성 시 `data/.encryption_key` 파일로 저장 (컨테이너 재시작 시에도 유지)
- **키 손실 방지:** 백업 필수 (손실 시 모든 API Key 복호화 불가)
- **로그 노출 금지:** ENCRYPTION_KEY는 로그/API 응답에 절대 포함하지 않음

**Settings.py 확장 (Phase 5):**
```python
class SecuritySettings(BaseModel):
    encryption_key: str = Field(default="", alias="ENCRYPTION_KEY")

class Settings(BaseSettings):
    # ...기존 설정...
    security: SecuritySettings = Field(default_factory=SecuritySettings)
```

**저장소:**
```sql
CREATE TABLE api_keys (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    key_name TEXT NOT NULL,
    encrypted_key TEXT NOT NULL,  -- Fernet encrypted
    created_at TEXT NOT NULL,
    last_used_at TEXT,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE model_configs (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    model_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    is_default INTEGER DEFAULT 0,
    parameters TEXT NOT NULL,  -- JSON
    UNIQUE(provider, model_id)
);

CREATE TABLE migration_versions (
    name TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    applied_at TEXT NOT NULL
);
```

### Error Handling (Phase 3, 6)

**Custom Exceptions (Phase 3):**
- `ConfigurationError`: 베이스 예외
- `ApiKeyNotFoundError`: API Key 조회 실패
- `InvalidEncryptionKeyError`: 복호화 실패 (잘못된 ENCRYPTION_KEY)
- `ModelNotFoundError`: 모델 조회 실패

**Error Handlers (Phase 6):**
- API Key 복호화 실패 → 500 응답 + 로그
- API Key 유효성 테스트 실패 → Provider API 호출 결과 반환
- LiteLLM model_list 실패 → Fallback to static JSON model list

### Audit Logging (Phase 3+)

**로깅 대상:**
- API Key 추가/삭제: `logger.info(f"API Key added: provider={provider}")`
- 모델 전환: `logger.info(f"Default model changed: {model_id}")`
- API Key 사용: `last_used_at` 컬럼 업데이트

**보안 고려:**
- API Key 원문은 절대 로그에 기록하지 않음
- 마스킹된 형태만 로그 (예: "sk-***1234")

### LiteLLM Integration

**모델 목록 가져오기:**
- LiteLLM의 `model_list` API 사용 (Phase 1 전 Web Search로 검증)
- Provider별 필터링 (API Key가 설정된 Provider만)
- 캐싱 (5분)
- **Fallback:** LiteLLM API 실패 시 static JSON model list 사용

**모델 전환 (Phase 5):**
- **OrchestratorService 리팩토링 필요:**
  - 현재: `__init__(default_model: str, ...)`
  - 변경: `__init__(config_service: ConfigurationService, ...)`
  - 실시간 모델 조회: `await config_service.get_default_model()`
- `model_configs` 테이블의 `is_default=1` 모델 조회

**DI Container 확장 (Phase 5):**
- `encryption_adapter`: FernetEncryptionAdapter Provider
- `configuration_storage`: SqliteConfigurationStorage Provider
- `configuration_service`: ConfigurationService Provider
- `orchestrator_service`: ConfigurationService 의존성 추가

### Playground-First Testing

**Phase 6:**
- Settings 탭 구현 (HTML/JS)
- API Key CRUD 테스트 (Playwright E2E)
- Model Selection 테스트 (Playwright E2E)

**Phase 7:**
- API Key 유효성 검증 (LLM 호출 테스트)
- 모델 전환 후 대화 테스트

---

## Dependencies

**Python Packages:**
- `cryptography` (Fernet encryption)
- 기존: `litellm`, `sqlalchemy`

**External APIs:**
- LiteLLM model list (로컬 캐시 가능)
- Provider APIs (테스트 연결용)

---

## Migration Strategy

**기존 설정 마이그레이션 (Phase 4.2):**
1. `.env`의 `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY` → `api_keys` 테이블
2. `configs/default.yaml`의 `llm.default_model` → `model_configs` 테이블
3. 최초 실행 시 자동 마이그레이션 (`@app.on_event("startup")` hook)

**멱등성 보장:**
- `migration_versions` 테이블로 중복 실행 방지
- Migration 이름: `"plan_09_api_keys"`
- 이미 마이그레이션된 경우 skip

**실패 처리:**
- Migration 실패 시 Rollback + 애플리케이션 시작 차단
- 로그에 상세 오류 기록

**API Key 우선순위 (Phase 3 Service 로직):**
```
우선순위: DB > .env (단일 진실 공급원 = DB)
```
1. **DB 우선:** `api_keys` 테이블에 활성 키가 있으면 사용
2. **Fallback to .env:** DB에 없으면 .env 사용 + Warning 로그 ("Migrate via Playground")
3. **오류:** 둘 다 없으면 `ApiKeyNotFoundError` 발생

**Migration 후:**
- .env의 API Key는 Deprecated (DB가 단일 진실 공급원)
- Playground UI에서 DB에 추가하면 .env는 무시됨

---

## Risks

| 위험 | 심각도 | 대응 |
|------|:------:|------|
| API Key 유출 | 🔴 | Fernet 암호화 + ENCRYPTION_KEY 환경변수 |
| LiteLLM model_list API 변경 | 🟡 | 버전 고정 + 웹 검색 검증 |
| Extension ↔ Backend 동기화 | 🟡 | LocalStorage는 읽기 전용, Backend가 단일 진실 공급원 |
| 암호화 키 손실 | 🟠 | 키 손실 시 재설정 필요 (복구 불가) |

---

## Definition of Done

### Functionality
- [ ] API Key CRUD 동작 (Playground UI)
- [ ] API Key 유효성 테스트 동작
- [ ] Model Selection 동작 (Playground UI)
- [ ] 선택된 모델로 대화 동작
- [ ] 암호화/복호화 정상 동작
- [ ] 기존 `.env` 설정 마이그레이션

### Quality
- [ ] Backend coverage >= 80%
- [ ] Playground E2E 테스트 통과
- [ ] TDD Red-Green-Refactor 사이클 준수

### Documentation
- [ ] **`docs/operators/security/encryption.md`** 작성 (ENCRYPTION_KEY 관리 가이드)
  - 최초 설정 (자동 생성 vs 수동 설정)
  - 백업 절차 (`data/.encryption_key` 파일 백업)
  - 손실 시 복구 불가 경고
  - 키 회전 (미구현, 수동 재입력 필요)
- [ ] `docs/operators/deployment/configuration.md` 업데이트 (Settings 환경변수 추가)
- [ ] `extension/README.md` 업데이트 (Settings 기능 추가)
- [ ] ADR 작성:
  - ADR-XX: API Key 암호화 방식 (Fernet 선택 이유)
  - ADR-XX: 설정 저장소 (SQLite 선택 이유)
  - ADR-XX: API Key 우선순위 (DB > .env)

---

## Related Plans

- **Plan 07**: Hybrid-Dual Architecture (선행 조건)
- **Plan 10**: stdio Transport (독립적, 병렬 가능)
- **Plan 11**: MCP App UI Rendering (독립적, 병렬 가능)

---

## Implementation Notes

### Critical Requirements (P0)

1. **Standards Verification:** Phase 1/4 시작 전 LiteLLM/Cryptography API 웹 검색 필수
2. **Port Interface 명세:** Phase 2에서 모든 메서드 시그니처 명확히 정의
3. **Migration 멱등성:** `migration_versions` 테이블로 중복 실행 방지
4. **Settings.py 확장:** `SecuritySettings` 클래스 추가 (ENCRYPTION_KEY)
5. **DI Container 확장:** encryption/storage/configuration service Provider 추가
6. **API Key 우선순위:** DB > .env (단일 진실 공급원 = DB)

### Recommended (P1)

7. **Phase 4 세분화:** Storage (4.1) + Encryption/Migration (4.2) 분리
8. **Error Handling:** Custom Exceptions (Phase 3) + Error Handlers (Phase 6)
9. **Audit Logging:** API Key 추가/삭제/사용 로그 (보안: 원문 제외)
10. **ENCRYPTION_KEY 문서:** 백업/복구 절차 문서화 (`docs/operators/security/encryption.md`)

### Phase 5 주의사항

**OrchestratorService 리팩토링 영향:**
- 의존성 변경: `default_model: str` → `config_service: ConfigurationService`
- **기존 테스트 깨짐 가능:** Mock ConfigurationService 필요
- DI Container 업데이트 필수

---

*Draft Created: 2026-02-07*
*Updated: 2026-02-07 (P0/P1 권장사항 반영)*
*Next: Plan 승인 후 Phase 상세 계획 작성*
