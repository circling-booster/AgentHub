# ADR-T07: Playground-First Testing

## Status

Accepted

## Context

Plan 07(Phase 6+)부터 HTTP API와 SSE 기능을 구현하면서 다음과 같은 문제에 직면했습니다:

1. **Extension UI 의존성**: 기존 방식은 Chrome Extension UI를 먼저 구현한 후 테스트하는 방식
2. **느린 피드백 루프**: Extension 빌드 + 재로드 시간으로 인한 개발 속도 저하
3. **회귀 테스트 부재**: API 변경 시 즉시 검증할 수 있는 자동화된 테스트 부재
4. **API 계약 검증 지연**: Extension UI 완성 전까지 백엔드 API의 실제 동작 확인 불가

HTTP API/SSE는 브라우저만으로도 테스트 가능한데, Extension을 기다려야 하는 것은 비효율적입니다.

## Decision

**Playground-First Testing 전략을 채택합니다.**

Phase 6-7에서 구현되는 HTTP API와 SSE 이벤트는 다음과 같이 처리:

### 적용 대상
- ✅ **적용**: HTTP Routes (Phase 6+), SSE Events (Phase 7+)
- ❌ **제외**: Domain 엔티티, Port, Service (단위/통합 테스트로 검증)
- ❌ **제외**: 순수 백엔드 기능 (chaos engineering, retry logic 등)
- ⏸️ **연기**: Chrome Extension UI → Production Preparation Phase로 연기

### 구현 방식

**Phase 6 (HTTP Routes + Playground):**
1. Backend Routes 구현 (TDD)
2. Playground UI Tabs 추가 (HTML/JS)
   - Resources, Prompts, Sampling, Elicitation 탭
3. Playwright E2E Tests 작성 (즉시 회귀 방지)

**Phase 7 (SSE Events + Playground):**
1. StreamChunk 확장 (Backend)
2. Playground SSE Verification UI
3. SSE E2E Tests (Playwright)

### 검증 방법
```bash
# Playground E2E Tests
pytest tests/e2e/test_playground.py -v -k "resources or prompts"

# JavaScript Unit Tests
cd tests/manual/playground && npm test

# Manual Test
# Terminal 1: Backend
DEV_MODE=true uvicorn src.main:app --reload

# Terminal 2: Playground
python -m http.server 3000 --directory tests/manual/playground

# Browser: http://localhost:3000
```

## Consequences

### Positive
- **즉각적인 피드백**: Extension 빌드 없이 브라우저 새로고침만으로 테스트
- **빠른 회귀 테스트**: Playwright E2E < 10초 (기존 Extension E2E는 30초+)
- **API 계약 조기 검증**: Backend 완성 즉시 실제 HTTP 요청/응답 확인 가능
- **병렬 개발 가능**: Playground로 검증하면서 Extension UI는 나중에 구현
- **테스트 자동화**: Playwright로 Playground를 자동 테스트 → CI/CD 통합 가능

### Negative
- **추가 구현 비용**: Playground UI + E2E 테스트 작성 시간 필요 (단, Extension UI 대비 간단)
- **유지보수 부담**: Playground도 API 변경 시 함께 업데이트 필요
- **임시 코드 인식**: Playground는 프로덕션 코드가 아니므로 추후 정리 필요할 수 있음

### Neutral
- Playground는 개발/테스트 환경에서만 사용 (프로덕션 배포 제외)
- Extension UI는 Production Preparation Phase에서 Playground를 참고하여 구현

## Alternatives Considered

### 1. Extension UI First (기존 방식)
Extension UI를 먼저 구현한 후 테스트

**장점:**
- Playground 구현 불필요
- 최종 사용자 UI와 동일한 환경에서 테스트

**단점:**
- 느린 피드백 루프 (빌드 + 재로드)
- 백엔드 완성 후에도 Extension UI 완성까지 대기
- 회귀 테스트 자동화 어려움

**채택 안 한 이유:** Phase 6-7에서 즉시 검증 불가, 개발 속도 저하

### 2. Postman/Thunder Client (API Client만 사용)
HTTP 클라이언트 도구만으로 테스트

**장점:**
- 도구 사용법이 간단
- API 테스트에 특화

**단점:**
- SSE 스트리밍 테스트 어려움
- UI 인터랙션 검증 불가 (예: 폼 입력, 버튼 클릭)
- E2E 자동화 어려움

**채택 안 한 이유:** SSE와 HITL 같은 복잡한 흐름 검증 불가

### 3. Cypress/Playwright만 사용 (UI 없이)
E2E 테스트만 작성 (Playground UI 없이)

**장점:**
- Playground UI 구현 불필요
- 자동화된 테스트만 유지

**단점:**
- 수동 테스트 불가 (개발자가 직접 확인하기 어려움)
- 디버깅 어려움 (실제 UI가 없으므로)

**채택 안 한 이유:** 개발 중 수동 검증이 필요할 때 불편

## References

- [Plan 07 README.md](../../planning/active/07_hybrid_dual/README.md) - Playground-First Testing 원칙 설명
- [Phase 6: HTTP Routes + Playground](../../planning/active/07_hybrid_dual/06_http_routes.md)
- [Phase 7: SSE Events + Playground](../../planning/active/07_hybrid_dual/07_sse_events_playground.md)
- [CLAUDE.md](../../../../CLAUDE.md) - Quick Reference에 Playground-First Testing 언급
- [Planning README.md](../../planning/README.md) - Planning Principles 섹션

---

*Created: 2026-02-06*
