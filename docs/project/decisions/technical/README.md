# Technical Decisions

기술 스택 관련 ADR(Architecture Decision Record) 인덱스.

---

## ADR 목록

### 채택된 결정

| ID | 제목 | 상태 | 결정일 |
|----|------|------|--------|
| ADR-T01 | Google ADK 채택 | Accepted | 2025-12 |
| ADR-T02 | LiteLLM 통합 | Accepted | 2025-12 |
| ADR-T03 | SQLite WAL 모드 | Accepted | 2025-12 |
| ADR-T04 | WXT 프레임워크 | Accepted | 2025-12 |
| ADR-T05 | dependency-injector 채택 | Accepted | 2026-01 |
| ADR-T06 | pydantic-settings 설정 관리 | Accepted | 2026-01 |
| ADR-T07 | Playground-First Testing | Accepted | 2026-02 |
| ADR-T08 | Drive-by RCE Protection | Accepted | 2026-02 |
| ADR-T09 | DEV_MODE Conditional Endpoints | Accepted | 2026-02-07 |
| ADR-T10 | AnyIO Pytest Plugin Migration | Accepted | 2026-02-07 |

---

## 주요 결정 요약

### Google ADK

**컨텍스트:** Agent 프레임워크 선택 필요. LangGraph, AutoGen, CrewAI 등 대안 존재.

**결정:** Google ADK 1.23.0+ 채택.

**이유:**
- MCP 네이티브 지원 (DynamicToolset)
- A2A 프로토콜 지원
- LiteLLM 통합으로 다중 LLM 지원

---

### LiteLLM

**컨텍스트:** 다양한 LLM Provider(OpenAI, Anthropic, Google 등) 지원 필요.

**결정:** LiteLLM을 통한 LLM 통합.

**이유:**
- 100+ LLM 통합 지원
- 통일된 API 인터페이스
- Provider 전환 시 코드 변경 최소화

**기본 모델:** `openai/gpt-4o-mini`

---

### SQLite WAL 모드

**컨텍스트:** 로컬 데스크톱 환경에서 데이터 저장 필요. 설치 간소화 중요.

**결정:** SQLite with WAL(Write-Ahead Logging) 모드 채택.

**이유:**
- 별도 DB 서버 불필요
- 동시 읽기/쓰기 성능 향상
- 단일 파일 백업 용이

---

### WXT 프레임워크

**컨텍스트:** Chrome Extension 개발 프레임워크 선택 필요.

**결정:** WXT + TypeScript 채택.

**이유:**
- Hot Reload 지원
- Manifest V3 최적화
- TypeScript 기본 지원
- 엔트리포인트 자동 구성

---

### dependency-injector

**컨텍스트:** 헥사고날 아키텍처의 의존성 주입 필요.

**결정:** dependency-injector 라이브러리 채택.

**이유:**
- Python 네이티브 DI 컨테이너
- Provider 패턴 지원
- 테스트 시 의존성 오버라이드 용이

---

### pydantic-settings

**컨텍스트:** 환경변수 및 설정 파일 관리 필요.

**결정:** pydantic-settings + YAML 설정 파일 조합.

**이유:**
- 타입 안전한 설정 로딩
- 환경변수 자동 바인딩
- YAML 파일을 통한 복잡한 설정 지원

---

### Playground-First Testing

**컨텍스트:** HTTP API/SSE 구현 시 Extension UI를 기다리지 않고 즉시 테스트할 필요.

**결정:** Phase 6-7에서 Backend + Playground UI + E2E 테스트를 함께 구현.

**이유:**
- 즉각적인 피드백 (Extension 빌드 불필요)
- 빠른 회귀 테스트 (Playwright E2E < 10초)
- API 계약 조기 검증
- Extension UI는 Production Phase로 연기

**적용:** Resources, Prompts, Sampling, Elicitation API (Plan 07 Phase 6-7)

---

### DEV_MODE Conditional Endpoints

**컨텍스트:** E2E 테스트를 위한 `/test/*` 엔드포인트 필요, 프로덕션 노출 시 보안 위험.

**결정:** `DEV_MODE` 환경변수로 test utilities 라우터를 조건부 등록.

**이유:**
- Production Safety: 기본값 `false`로 test endpoints 완전 제거
- E2E Testing: Playwright 테스트에서 `/test/reset-data`로 clean state 달성
- 명시적 활성화: pydantic validator로 UserWarning 발생

**Behavior:**
- `DEV_MODE=false` (default): `/test/*` → 404 (라우터 미등록)
- `DEV_MODE=true`: `/test/*` → 200 (라우터 등록, UserWarning)

**Trade-off:** Configuration 복잡도 증가 vs 프로덕션 보안 강화

**참고:** [ADR-T09](ADR-T09-dev-mode-conditional-endpoints.md)

---

*Last Updated: 2026-02-07*
