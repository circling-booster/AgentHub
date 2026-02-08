# Plan 09: Dynamic Configuration & Model Management

## Overview

**목표:** API Key와 LLM 모델을 런타임에 동적으로 관리하는 Configuration System 구현

**현재 상태:**
- 제한사항: API Key와 모델이 `.env`/`configs/default.yaml`에 하드코딩
- 문제점: 사용자가 런타임에 변경 불가, 컨테이너 재시작 필요

**핵심 원칙:**
- TDD (테스트 먼저 작성 - Red → Green → Refactor)
- 헥사고날 아키텍처 (Domain 레이어는 순수 Python)
- **DB-First Configuration**: SQLite가 단일 진실 공급원 (DB > .env 우선순위)
- **Playground-First Testing** (Phase 6-7: HTTP API와 Playground UI를 함께 구현)
- **Security by Design**: Fernet 대칭 암호화 (AES-128-CBC + HMAC)

---

## Foundational Concepts

### DB-First Configuration

**우선순위 정책:**
```
DB (api_keys 테이블) > .env (OPENAI_API_KEY 등)
```

- **단일 진실 공급원**: DB에 저장된 설정이 최우선
- **Fallback**: DB에 없으면 .env 사용 + Warning 로그
- **Migration**: 최초 실행 시 .env → DB 자동 마이그레이션
- **Deprecation**: Migration 후 .env는 Deprecated (DB만 사용)

### Fernet Encryption

**암호화 방식:**
- **알고리즘**: AES-128-CBC + HMAC (authenticated encryption)
- **키 관리**: 환경변수 `ENCRYPTION_KEY` (32-byte URL-safe base64)
- **키 저장**: 미설정 시 자동 생성 + 환경변수 export 경고
- **키 손실**: 복구 불가 (백업 필수)

**보안 원칙:**
- API Key 원문은 절대 로그/API 응답에 포함하지 않음
- ENCRYPTION_KEY는 로그에 기록하지 않음
- 마스킹된 형태만 노출 (예: "sk-***1234")

### Migration Strategy

**멱등성 보장:**
- `migration_versions` 테이블로 중복 실행 방지
- Migration 이름: `plan_09_api_keys`
- 이미 마이그레이션된 경우 skip

**실패 처리:**
- Migration 실패 시 Transaction Rollback
- 애플리케이션 시작 차단 + 로그에 상세 오류 기록

**Migration 대상:**
1. `.env`의 `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY` → `api_keys` 테이블
2. `configs/default.yaml`의 `llm.default_model` → `model_configs` 테이블

---

## Implementation Phases

각 Phase의 상세 내용은 아래 링크를 참조하세요:

| Phase | 설명 | Playground | Status | 문서 |
|-------|------|------------|--------|------|
| **Phase 1** | Domain Entities (ApiKeyConfig, ModelConfig) | - | ⏸️ | [01_domain_entities.md](01_domain_entities.md) |
| **Phase 2** | Port Interface + Fake | - | ⏸️ | [02_port_interface.md](02_port_interface.md) |
| **Phase 3** | Domain Services (ConfigurationService) | - | ⏸️ | [03_domain_services.md](03_domain_services.md) |
| **Phase 4** | Adapter Implementation (Storage + Encryption + Migration) | - | ⏸️ | [04_adapter_implementation.md](04_adapter_implementation.md) |
| **Phase 5** | Integration (DI Container + Settings + Lifespan) | - | ⏸️ | [05_integration.md](05_integration.md) |
| **Phase 6** | HTTP Routes + Playground UI | ✅ | ⏸️ | [06_http_routes_playground.md](06_http_routes_playground.md) |
| **Phase 7** | Validation & E2E Tests | ✅ | ⏸️ | [07_validation_e2e.md](07_validation_e2e.md) |

**Playground Column:**
- ✅ - Playground UI/테스트를 백엔드와 함께 구현
- - (dash) - 해당 없음 (Domain layer)

**Status Icons:**
- ⏸️ **Pending** - 대기 중
- 🔄 **In Progress** - 진행 중 (항상 1개만)
- ✅ **Done** - 완료

**Phase Update Workflow:**
1. Phase 시작: Status를 ⏸️ → 🔄로 변경
2. Phase 완료: Status를 🔄 → ✅로 변경, Git 커밋: `docs: complete phase N - {phase_name}`

**제외 (Extension → Production Preparation Phase):**
- extension/lib/types.ts, api.ts (Configuration 타입/API)
- Settings Page 컴포넌트

---

## Verification

### Unit Tests
```bash
pytest tests/unit/ -q --tb=line -x
```

### Integration Tests
```bash
# Storage Adapter (SQLite)
pytest tests/integration/adapters/test_sqlite_configuration_storage.py -v

# Encryption Adapter (Fernet)
pytest tests/integration/adapters/test_fernet_encryption_adapter.py -v

# Configuration Migrator
pytest tests/integration/adapters/test_configuration_migrator.py -v

# Container Configuration
pytest tests/integration/test_container_configuration.py -v

# HTTP Routes
pytest tests/integration/test_config_routes.py -v

# 모든 Integration 테스트
pytest tests/integration/ -q --tb=line
```

### Coverage
```bash
pytest --cov=src --cov-fail-under=80 -q
```

### Playground Tests (Phase 6-7)
```bash
# Playground E2E Tests
pytest tests/e2e/test_playground_settings.py -v -m e2e_playwright

# Specific feature tests
pytest tests/e2e/test_playground_settings.py -v -k "api_key or model_selection"

# JavaScript Unit Tests
cd tests/manual/playground && npm test
```

### Manual Playground Test
```bash
# Terminal 1: Backend (DEV_MODE)
DEV_MODE=true uvicorn src.main:app --reload

# Terminal 2: Playground
python -m http.server 3000 --directory tests/manual/playground

# Browser: http://localhost:3000
# Navigate to "Settings" tab
```

---

## Critical Files Summary

| 구분 | 신규/수정 | 파일 |
|------|----------|------|
| Entity (신규) | 신규 | `src/domain/entities/api_key_config.py` |
| Entity (신규) | 신규 | `src/domain/entities/model_config.py` |
| Enum (수정) | 수정 | `src/domain/entities/enums.py` (+LlmProvider) |
| Exception (수정) | 수정 | `src/domain/exceptions.py` (+ConfigurationError 계열) |
| Constant (수정) | 수정 | `src/domain/constants.py` (+ERROR_CODES) |
| Port (신규) | 신규 | `src/domain/ports/outbound/configuration_storage_port.py` |
| Port (신규) | 신규 | `src/domain/ports/outbound/encryption_port.py` |
| Service (신규) | 신규 | `src/domain/services/configuration_service.py` |
| Adapter (신규) | 신규 | `src/adapters/outbound/storage/sqlite_configuration_storage.py` |
| Adapter (신규) | 신규 | `src/adapters/outbound/encryption/fernet_encryption_adapter.py` |
| Adapter (신규) | 신규 | `src/adapters/outbound/storage/configuration_migrator.py` |
| Schema (신규) | 신규 | `src/adapters/inbound/http/schemas/config.py` (Pydantic Response Models) |
| Route (신규) | 신규 | `src/adapters/inbound/http/routes/config.py` |
| Exception (수정) | 수정 | `src/adapters/inbound/http/exceptions.py` (+Exception Handlers) |
| Settings (수정) | 수정 | `src/config/settings.py` (+encryption_key 필드) |
| Container (수정) | 수정 | `src/config/container.py` (+Encryption/Storage/Configuration Providers) |
| Lifespan (수정) | 수정 | `src/adapters/inbound/http/app.py` (DB init, migration, key export) |
| OrchestratorAdapter (수정) | 수정 | `src/adapters/outbound/adk/orchestrator_adapter.py` (+set_model 메서드) |
| Fake (신규) | 신규 | `tests/unit/fakes/fake_configuration_storage.py` |
| Fake (신규) | 신규 | `tests/unit/fakes/fake_encryption.py` |
| Playground (수정) | 수정 | `tests/manual/playground/index.html` (Settings 탭) |
| Playground (신규) | 신규 | `tests/manual/playground/js/settings-handler.js` |
| Dependencies (수정) | 수정 | `pyproject.toml` (+cryptography>=42.0.0,<48.0.0) |

---

## Design Decisions

### 1. DB-First Configuration (DB > .env)

**결정:** SQLite를 단일 진실 공급원으로 사용, .env는 Fallback

**이유:**
- 런타임 변경 가능 (컨테이너 재시작 불필요)
- Migration으로 기존 설정 자동 이전
- 사용자 친화적 (Playground/Extension UI)

**트레이드오프:**
- DB 파일 백업 필요
- .env보다 복잡한 관리

**ADR:** [ADR-C01: DB-First Configuration](../../decisions/configuration/ADR-C01-db-first-configuration.md)

### 2. Fernet 대칭 암호화

**결정:** Fernet (AES-128-CBC + HMAC) 사용

**이유:**
- Python `cryptography` 표준 라이브러리
- Authenticated encryption (무결성 보장)
- 단순한 API (`encrypt()`/`decrypt()`)

**트레이드오프:**
- 키 손실 시 복구 불가 (백업 필수)
- 키 회전 미구현 (수동 재입력 필요)

**ADR:** [ADR-C02: Fernet Encryption](../../decisions/configuration/ADR-C02-fernet-encryption.md)

### 3. Route 레벨 Model 조율 (OrchestratorAdapter.set_model)

**결정:** OrchestratorService 리팩토링 최소화, Route에서 model 전환

**이유:**
- 순환 참조 방지 (ConfigurationService ↔ OrchestratorService)
- 헥사고날 아키텍처 준수 (Route → Adapter)
- 간단한 구현 (`OrchestratorAdapter.set_model()` 메서드 추가)

**트레이드오프:**
- Route가 model 전환 책임 (약간의 비즈니스 로직 노출)
- 미래 확장 시 Service로 리팩토링 가능

**구현:**
```python
# Route (Phase 6)
@router.post("/models/{model_id}/select")
async def select_model(model_id: str, orchestrator: OrchestratorAdapter):
    model_config = await config_service.get_model_config(model_id)
    orchestrator.set_model(model_config.model_id)  # 다음 generate_response()에서 반영
    return {"status": "ok"}

# OrchestratorAdapter (Phase 5)
class OrchestratorAdapter:
    def set_model(self, model_name: str):
        """Set model for next generate_response() call. No agent rebuild."""
        self._model_name = model_name
```

**ADR:** [ADR-C03: Route-Level Model Coordination](../../decisions/configuration/ADR-C03-route-level-model-coordination.md)

### 4. LiteLLM Model List Fallback Strategy

**결정:** Static JSON model list를 Fallback으로 준비

**이유:**
- LiteLLM Python SDK에 직접 `model_list()` API 없음 ([Issue #5894](https://github.com/BerriAI/litellm/issues/5894))
- Proxy Server 사용 시 `/v1/models` 엔드포인트 제공하나 AgentHub는 Direct Python SDK 사용
- API 장애 시에도 UI 정상 작동 필요

**구현:**
```json
{
  "openai": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
  "anthropic": ["claude-sonnet-4.5", "claude-opus-4.6", "claude-haiku-4.5"],
  "google": ["gemini-2.0-flash-exp", "gemini-1.5-pro"]
}
```

**트레이드오프:**
- Static list 유지보수 필요
- 새 모델 출시 시 수동 업데이트

**ADR:** [ADR-C04: LiteLLM Model List Fallback](../../decisions/configuration/ADR-C04-litellm-model-list-fallback.md)

### 5. Migration Rollback on Failure

**결정:** Migration 실패 시 Transaction Rollback + 애플리케이션 시작 차단

**이유:**
- 부분 마이그레이션 방지 (데이터 일관성)
- 명확한 실패 피드백 (로그 + 시작 차단)
- 사용자가 문제 해결 후 재시작

**구현:**
```python
# ConfigurationMigrator (Phase 4)
async def run_migrations(self):
    try:
        async with self.storage._get_connection() as conn:
            # Check migration_versions
            # Apply pending migrations
            await conn.commit()
    except Exception as e:
        await conn.rollback()
        logger.error(f"Migration failed: {e}")
        raise
```

**ADR:** [ADR-C05: Migration Rollback Strategy](../../decisions/configuration/ADR-C05-migration-rollback-strategy.md)

---

## Test Strategy Matrix

| Phase | 테스트 유형 | 파일 | 마커 |
|-------|------------|------|------|
| 1 | Unit | `tests/unit/domain/entities/test_api_key_config.py` | (default) |
| 1 | Unit | `tests/unit/domain/entities/test_model_config.py` | (default) |
| 1 | Unit | `tests/unit/domain/entities/test_enums.py` | (default) |
| 2 | Unit | `tests/unit/fakes/test_fake_configuration_storage.py` | (default) |
| 2 | Unit | `tests/unit/fakes/test_fake_encryption.py` | (default) |
| 3 | Unit | `tests/unit/domain/services/test_configuration_service.py` | (default) |
| 4 | Integration | `tests/integration/adapters/test_sqlite_configuration_storage.py` | (default) |
| 4 | Integration | `tests/integration/adapters/test_fernet_encryption_adapter.py` | (default) |
| 4 | Integration | `tests/integration/adapters/test_configuration_migrator.py` | (default) |
| 5 | Integration | `tests/integration/test_container_configuration.py` | (default) |
| 6 | Integration | `tests/integration/test_config_routes.py` | (default) |
| 6 | E2E | `tests/e2e/test_playground_settings.py` | `e2e_playwright` |
| 7 | E2E | `tests/e2e/test_playground_settings.py::TestModelSwitching` | `e2e_playwright` |
| 7 | Integration | `tests/integration/test_api_key_connection.py` | `llm` |

**Coverage Target:** >= 80% (CI 강제)

**주의사항:**
- Phase 4 테스트는 Integration (외부 라이브러리 사용)
- Phase 7 API Key test-connection은 `llm` 마커 (실제 LiteLLM API 호출)

---

## Risk Mitigation

| 위험 | 심각도 | 대응 |
|------|:------:|------|
| API Key 유출 | 🔴 | Fernet 암호화 + ENCRYPTION_KEY 환경변수 + 로그 마스킹 |
| ENCRYPTION_KEY 손실 | 🟠 | 환경변수 export 경고 + 백업 가이드 문서화 |
| LiteLLM API 변경 | 🟡 | Static JSON Fallback + 버전 고정 (`litellm^1.25.0`) |
| Cryptography API 변경 | 🟡 | 버전 범위 고정 (`cryptography>=42.0.0,<48.0.0`) |
| Migration 실패 | 🟠 | Transaction Rollback + 시작 차단 + 상세 로그 |
| DB 파일 손상 | 🟡 | WAL 모드 + 백업 전략 (미래: 자동 백업) |
| Extension ↔ Backend 동기화 | 🟡 | LocalStorage 읽기 전용, Backend가 단일 진실 공급원 |

**심각도:**
- 🔴 Critical - 즉시 대응 필수
- 🟠 High - 명확한 대응 전략 필요
- 🟡 Medium - 모니터링 + 점진적 개선

---

## Review Notes

### 검토 완료 항목
- [x] 프로젝트 원칙 준수 (TDD, Hexagonal, Playground-First)
- [x] Plan 07 패턴 일치 (README 구조, Phase 문서 형식)
- [x] 웹 검색으로 최신 표준 확인 (LiteLLM, Cryptography, SQLite)
- [x] Phase 4.1/4.2 통합 → 단일 Phase 4 (Step 4.1~4.7)
- [x] provider: str → LlmProvider enum 사용
- [x] EncryptionPort에서 generate_key() 제거 (Adapter 정적 메서드로 이동)
- [x] SecuritySettings 중첩 제거 → 플랫 encryption_key 필드
- [x] Route 레벨 조율 패턴 (OrchestratorAdapter.set_model)
- [x] LiteLLM model_list Fallback 전략 명시
- [x] cryptography 의존성 추가 (>=42.0.0,<48.0.0)
- [x] datetime.now(timezone.utc) 사용 원칙
- [x] Migration Rollback on Failure 명시
- [x] WAL 모드 PRAGMA 순서 (journal_mode → busy_timeout)
- [x] DB 파일명 명확화 ({data_dir}/config.db)
- [x] Model 전환 시 Agent 재빌드 불필요 (set_model만)
- [x] API Key test-connection 구체화 (litellm.completion 최소 호출)
- [x] Model parameter JSON TEXT 저장
- [x] Port __init__.py Export Step 명시
- [x] Fake Adapter 테스트 명시
- [x] Coverage threshold 검증 명시 (--cov-fail-under=80)

### 주요 변경사항
1. **Phase 구조 개선**: Phase 4.1/4.2 분리 제거 → 단일 Phase 4 (Step 4.1~4.7)
2. **타입 안정성 강화**: provider: str → LlmProvider enum
3. **Port 단순화**: EncryptionPort.generate_key() 제거 (Adapter 내부 관심사)
4. **설정 구조 단순화**: SecuritySettings 중첩 제거 → 플랫 encryption_key 필드
5. **아키텍처 단순화**: OrchestratorService 리팩토링 최소화 → Route 레벨 조율
6. **Fallback 전략 추가**: LiteLLM model_list API 없음 → Static JSON 준비
7. **의존성 명확화**: cryptography>=42.0.0,<48.0.0 추가
8. **보안 강화**: ENCRYPTION_KEY 파일 저장 제거 → 환경변수 전용 + 자동생성 경고
9. **Migration 안정성**: Rollback on Failure + Transaction 명시
10. **테스트 전략 명확화**: Coverage threshold, API Key test-connection 구체화

### 주의사항
1. **Phase 순서대로 구현**: Phase 2에서 Fake를 함께 작성하여 Phase 3 테스트에서 사용
2. **Phase 4 테스트는 Integration**: 외부 라이브러리 사용하므로 `tests/integration/`에 위치
3. **LiteLLM Fallback 필수**: Python SDK에 직접 model_list() 없음
4. **ENCRYPTION_KEY 백업**: 손실 시 복구 불가 → 문서화 필수
5. **Migration 멱등성**: migration_versions 테이블로 중복 실행 방지
6. **datetime 일관성**: 모든 datetime 생성에 datetime.now(timezone.utc) 사용
7. **WAL 모드 주의**: PRAGMA 순서 (journal_mode → busy_timeout)
8. **Coverage 검증**: Phase 7에서 --cov-fail-under=80 실행

---

## Standards Verification Protocol

**CRITICAL:** LiteLLM과 Cryptography는 빠르게 진화하는 라이브러리입니다. 구현 전 최신 API 검증 필수.

### Phase 1 시작 전 (Plan Phase)

**Web Search 필수:**
- Query: "LiteLLM Python SDK 2026", "LiteLLM model list API"
- 검증 항목:
  - `model_list` API 존재 여부 및 반환 형식
  - 지원 Provider 목록 (openai, anthropic, google 등)
  - 모델 ID 형식 ("openai/gpt-4o-mini" vs "gpt-4o-mini")
- **확인된 사실 (2026-02-07)**:
  - Python SDK에 직접 model_list() 없음 ([Issue #5894](https://github.com/BerriAI/litellm/issues/5894))
  - Proxy Server 사용 시 `/v1/models` 엔드포인트 제공
  - **Fallback 전략 필수**: Static JSON model list 준비

### Phase 4 시작 전 (Implementation Phase)

**Web Search 재검증:**
- Query: "Cryptography Fernet Python 2026", "Fernet encryption API"
- 검증 항목:
  - `Fernet.generate_key()` 메서드 시그니처
  - `encrypt()`, `decrypt()` 메서드 시그니처
  - 키 길이 요구사항 (32-byte URL-safe base64)
  - 암호화 알고리즘 (AES-128-CBC + HMAC 확인)
- **확인된 사실 (2026-02-07)**:
  - 최신 버전: v47.0.0.dev1 (2026년 기준)
  - API: `Fernet.generate_key()`, `encrypt()`, `decrypt()`
  - 암호화: AES-128-CBC + HMAC (authenticated encryption)
  - 키 길이: 32-byte (URL-safe base64)

### 의존성 버전 (pyproject.toml)

```toml
[tool.poetry.dependencies]
litellm = "^1.25.0"  # Minor 버전 고정
cryptography = ">=42.0.0,<48.0.0"  # 2026 최신: v47.0.0
```

---

*Last Updated: 2026-02-07*
*Structure: Plan 07 Pattern (Phase-based, 7 Phases)*
*Reviewed: TDD, Hexagonal Architecture, DB-First Configuration, Fernet Encryption, Playground-First Testing*
