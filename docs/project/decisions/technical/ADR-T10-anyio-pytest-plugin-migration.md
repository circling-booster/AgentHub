# ADR-T10: AnyIO Pytest Plugin Migration

**Status:** Accepted
**Date:** 2026-02-07
**Decision Maker:** Development Team

---

## Context

pytest-asyncio는 비동기 테스트를 지원하지만 fixture setup/teardown을 서로 다른 async task에서 실행합니다. 이로 인해 MCP SDK 내부에서 사용하는 `anyio.CancelScope`와 충돌이 발생했습니다.

**문제:**
- `anyio.CancelScope`는 동일 task에서 진입(enter)과 탈출(exit)을 요구
- pytest-asyncio는 fixture의 setup과 teardown을 다른 task에서 실행
- Phase 4 McpClientAdapter 테스트에서 `RuntimeError: Attempted to exit cancel scope in a different task` 발생

**영향:**
- 테스트는 PASSED하지만 teardown 시 에러 로그 출력
- AsyncExitStack 기반 리소스 정리가 불안정
- 실제 서버 운영에는 영향 없음 (FastAPI lifespan에서는 정상 동작)

**관련 이슈:**
- [pytest-asyncio #1191](https://github.com/pytest-dev/pytest-asyncio/issues/1191)

---

## Decision

pytest-asyncio를 제거하고 **anyio pytest plugin**으로 전환합니다.

**변경 사항:**
- `pyproject.toml`: `asyncio_mode = "auto"` → `anyio_mode = "auto"`
- 전체 `@pytest.mark.asyncio` 마커 제거 (39개 파일, ~200개 마커)
- 2개 conftest.py에서 `@pytest_asyncio.fixture` → `@pytest.fixture`

**구현:**
```toml
# pyproject.toml
[tool.pytest.ini_options]
anyio_mode = "auto"  # async def test_*() 자동 감지
```

---

## Rationale

### anyio plugin의 장점

1. **Fixture Task 일관성**
   - anyio plugin은 fixture를 **단일 task** 내에서 실행
   - setup과 teardown이 동일 task에서 실행되어 `anyio.CancelScope` 정상 동작

2. **asyncio API 호환성**
   - anyio는 asyncio를 기본 backend로 사용
   - 기존 `asyncio.create_task`, `asyncio.gather` 등 그대로 사용 가능

3. **Auto Mode 지원**
   - `anyio_mode = "auto"`는 기존 `asyncio_mode = "auto"`와 동일한 동작
   - `async def test_*()` 형식의 테스트를 자동 감지
   - 마이그레이션 비용 최소화

4. **MCP SDK 호환성**
   - MCP SDK v1.25+가 anyio 기반으로 구현됨
   - anyio plugin 사용 시 task context 일치로 teardown 에러 해소

---

## Alternatives Considered

### Alternative 1: AsyncExitStack 제거

**아이디어:** AsyncExitStack 대신 manual cleanup 구현

**거부 이유:**
- 코드 복잡도 증가
- MCP SDK가 내부적으로 AsyncExitStack 사용 → 근본 해결 불가

### Alternative 2: MCP SDK 업데이트 대기

**아이디어:** MCP SDK에서 pytest-asyncio 호환성 수정 대기

**거부 이유:**
- 타임라인 불확실
- anyio plugin 도입이 더 간단하고 확실한 해결책

### Alternative 3: pytest-asyncio scope 변경

**아이디어:** `asyncio_default_fixture_loop_scope` 조정

**거부 이유:**
- pytest-asyncio 0.23+ 이후에도 teardown 에러 지속
- 근본적인 task 불일치 문제는 해결 불가

---

## Consequences

### Positive

- ✅ **Teardown 에러 해소**: 616개 테스트 전체 PASSED, teardown 에러 0건
- ✅ **테스트 안정성 향상**: MCP SDK와의 완벽한 호환성
- ✅ **코드 간소화**: `@pytest.mark.asyncio` 마커 ~195개 제거 (37 files)
- ✅ **호환성 유지**: 기존 asyncio API 그대로 사용 가능

### Negative

- ⚠️ **플러그인 변경**: pytest-asyncio에 의존하던 코드는 수정 필요
- ⚠️ **문서 업데이트**: tests/docs/ 전체 업데이트 필요

### Neutral

- 🔄 **학습 곡선**: anyio plugin은 pytest-asyncio와 사용법 동일 (auto mode)
- 🔄 **의존성 변경**: `pytest-asyncio` → `anyio` (둘 다 널리 사용됨)

---

## Implementation

**Phase 4.5에서 완료:**
- Step 4.5.2: pyproject.toml 수정 (1 file)
- Step 4.5.3: @pytest_asyncio.fixture 변경 (2 files)
- Step 4.5.4: @pytest.mark.asyncio 제거 (37 files)
- Step 4.5.4.1: authenticated_client 사용 테스트를 async로 변환 (9 files)
- Step 4.5.4.2: test_app_startup.py app fixture 동기화 (1 file)
- Step 4.5.5: 검증 (616 passed, coverage 86.84%)
- Step 4.5.6: 문서 업데이트 (7 files)

**문서 업데이트:**
- tests/docs/CONFIGURATION.md - anyio plugin 설명
- tests/docs/TROUBLESHOOTING.md - anyio 에러 가이드
- tests/docs/WritingGuide.md - asyncio_mode → anyio_mode
- tests/docs/RESOURCES.md - Known Issue 해결 표시
- src/adapters/outbound/mcp/README.md - Known Issue 해결 표시
- tests/README.md - Quick Reference 업데이트

---

## References

- [AnyIO Documentation](https://anyio.readthedocs.io/)
- [pytest-asyncio Issue #1191](https://github.com/pytest-dev/pytest-asyncio/issues/1191)
- [Phase 04.5 Document](../../planning/active/07_hybrid_dual/04.5_anyio_pytest_plugin_migration.md)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

---

*Last Updated: 2026-02-07*
