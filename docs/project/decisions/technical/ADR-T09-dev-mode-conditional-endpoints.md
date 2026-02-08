# ADR-T09: DEV_MODE Conditional Endpoints

**Status:** Accepted
**Date:** 2026-02-07
**Context:** Plan 04.4 - DEV_MODE Implementation

---

## Context

E2E 테스트를 위해 `/test/state`, `/test/reset-data` 같은 테스트 유틸리티 엔드포인트가 필요합니다. 하지만 이러한 엔드포인트를 프로덕션에 노출하면 심각한 보안 위험이 있습니다:

- `/test/reset-data`: 모든 MCP 서버, A2A 에이전트, 대화 데이터를 삭제하는 파괴적 작업
- `/test/state`: 내부 시스템 상태를 노출하여 공격 벡터 제공

동시에, Playwright E2E 테스트에서는 테스트 격리(clean state)를 위해 이러한 엔드포인트가 필수적입니다.

---

## Decision

**`DEV_MODE` 환경변수를 사용하여 test utilities 라우터를 조건부로 등록합니다.**

### Implementation

```python
# src/adapters/inbound/http/app.py

def create_app() -> FastAPI:
    # ... 기본 라우터 등록 ...

    # DEV_MODE: Conditional test utilities
    settings = container.settings()
    if settings.dev_mode:
        from .routes import test_utils
        app.include_router(test_utils.router)
        logger.warning("Test utilities enabled (/test/*) - DEV_MODE only")

    return app
```

### Configuration

```python
# src/config/settings.py

class Settings(BaseSettings):
    dev_mode: bool = Field(
        default=False,
        alias="DEV_MODE",
        description="Enable development mode (localhost auth bypass, test utilities)"
    )

    @field_validator('dev_mode')
    @classmethod
    def warn_dev_mode(cls, v: bool) -> bool:
        """Warn when DEV_MODE is enabled (security risk)"""
        if v:
            warnings.warn(
                "DEV_MODE is enabled. This bypasses security for localhost requests. "
                "DO NOT use in production!",
                UserWarning,
                stacklevel=2
            )
        return v
```

### Behavior

| DEV_MODE | `/test/*` Endpoints | Security Impact |
|----------|---------------------|-----------------|
| `false` (default) | 404 Not Found | ✅ Safe - No test endpoints exposed |
| `true` | 200 OK (registered) | ⚠️ Risk - Destructive operations available |

---

## Consequences

### Positive

1. **Production Safety**: 기본값(`DEV_MODE=false`)에서 test endpoints가 완전히 제거되어 프로덕션 보안 강화
2. **E2E Testing**: Playwright E2E 테스트에서 `/test/reset-data`로 테스트 격리 달성
3. **명시적 활성화**: UserWarning으로 개발자가 DEV_MODE 활성화를 명확히 인지
4. **단일 진실 원천**: Settings.dev_mode가 CORS 설정, 인증 우회, test endpoints를 통합 제어

### Negative

1. **Configuration Complexity**: 로컬 개발 시 `DEV_MODE=true` 환경변수 설정 필요
2. **Accidental Production Exposure**: 실수로 프로덕션에서 `DEV_MODE=true` 설정 시 위험
   - **Mitigation**: pydantic field_validator의 UserWarning으로 경고
   - **Mitigation**: Deployment Guide에 환경변수 체크리스트 추가

### Trade-offs

| Aspect | Choice | Alternative | Rationale |
|--------|--------|-------------|-----------|
| **Endpoint Registration** | FastAPI 라우터 조건부 등록 | 라우터는 등록하되 엔드포인트에서 거부 | 404가 403보다 보안상 유리 (엔드포인트 존재 여부 노출 차단) |
| **Configuration Method** | 환경변수 (`DEV_MODE`) | Separate test server | E2E 테스트 복잡도 감소, 단일 서버로 모든 테스트 가능 |
| **Default Value** | `false` (안전) | `true` (편의) | Security-first 원칙, 프로덕션 사고 방지 |

---

## Alternatives Considered

### Alternative 1: Always-on Test Endpoints

**Rejected**: 프로덕션 보안 위험이 너무 높음. `/test/reset-data`는 모든 데이터를 삭제하므로 악의적 호출 시 치명적.

### Alternative 2: Separate Test Server

**Rejected**: E2E 테스트 복잡도가 크게 증가. 서버 2개 관리 부담, 포트 충돌 가능성.

### Alternative 3: Endpoint-level Authorization

**Rejected**: Authorization 로직 복잡도 증가. 404(라우터 미등록)가 403(권한 거부)보다 보안상 유리.

---

## Related ADRs

- **ADR-T08**: Drive-by RCE Protection (ExtensionAuthMiddleware와 함께 DEV_MODE는 localhost 인증 우회 제공)

---

## References

- [Security Guide: DEV_MODE Impact](../../../operators/security/README.md)
- [Deployment Guide: Environment Variables](../../../operators/deployment/README.md)
- [Test Documentation: E2E Clean State](../../../../tests/docs/WritingGuide.md)

---

*Last Updated: 2026-02-07*
