# 플랜 검증 보고서: Phase 6 Part A - MCP Gateway + Cost Tracking + Chaos Tests

**검증 대상:** `docs/plans/phase6/partA.md`
**플랜 타입:** Part Plan (Part A)
**검증 일시:** 2026-02-02
**검증 기준:** AgentHub CLAUDE.md, roadmap.md, STATUS.md, 기존 플랜 문서
**보고서 저장 위치:** `docs/validations/phase6-partA-validation-20260202.md`

---

## 1. 요약 (Executive Summary)

**결과:** PASS WITH CONDITIONS

Phase 6 Part A 플랜은 전반적으로 잘 구성되어 있으며, 헥사고날 아키텍처 원칙을 준수하고 TDD 전략이 명확합니다. 다만 Master Plan과의 일부 불일치, 상세도 부족, 그리고 일부 위험 요소에 대한 추가 명확화가 필요합니다.

**주요 강점:**
- Circuit Breaker를 순수 Python 도메인 엔티티로 설계 (헥사고날 원칙 준수)
- TDD 순서가 명확하게 기재됨
- Gateway 패턴으로 DynamicToolset 래핑 (Adapter Layer 적절)
- Chaos Engineering 도입으로 신뢰성 검증 강화

**주요 개선 필요 사항:**
- Master Plan과의 Step 번호 불일치 (Cost Tracking)
- API 엔드포인트 보안 검증 누락
- Fallback 서버 전환 메커니즘 상세도 부족
- Budget Alert 알림 방식 미정의

---

## 2. 아키텍처 정합성

| 항목 | 상태 | 비고 |
|------|:----:|------|
| Domain Layer 순수성 | ✅ | CircuitBreaker, Usage 엔티티가 순수 Python (`time` 모듈만 사용) |
| Port 인터페이스 정의 | ✅ | UsageStoragePort 신규 정의 계획됨 |
| Adapter 격리 | ✅ | GatewayToolset이 DynamicToolset 래핑 (ADK BaseToolset 상속) |
| DI Container 반영 | ⚠️ | Container 수정 계획 없음 (GatewayService, GatewayToolset 주입 필요) |

### 상세 분석

**강점:**
1. **Domain Layer 순수성 유지:** CircuitBreaker와 Usage 엔티티가 순수 Python으로 설계되어 있음. `time.time()` 사용은 표준 라이브러리이므로 허용 가능.
2. **Port 인터페이스:** UsageStoragePort가 Outbound Port로 명확히 정의됨.
3. **Adapter 격리:** GatewayToolset이 BaseToolset을 상속하여 ADK와 통합되며, DynamicToolset을 내부적으로 래핑하는 구조가 명확함.

**우려 사항:**
1. **DI Container 누락:** `src/config/container.py`의 수정 계획이 Step 2 파일 목록에 없음. GatewayService와 GatewayToolset을 Container에 등록해야 하는데, 이 부분이 누락됨.
   - **권장 조치:** Step 2 수정 파일에 `src/config/container.py` 추가 필요.

---

## 3. 기존 플랜 양식 비교

### 3.1 Master Plan 정합성

| 검증 항목 | 상태 | 비고 |
|-----------|:----:|------|
| Master Plan에 명시된 목표와 일치 | ✅ | "Circuit Breaker + Rate Limiting + Fallback, 비용 추적/예산 관리, Chaos Engineering" 일치 |
| Master Plan의 Part 설명과 일치 | ✅ | Part A 목표가 Master Plan과 일치 |
| Master Plan의 우선순위 반영 | ✅ | Part A가 Phase 6 첫 번째 Part로 명시됨 |
| Steps 범위가 Master Plan과 일치 | ⚠️ | Master Plan: Steps 1-4, Part A: Steps 1-4 (일치하나 Step 번호 내용 불일치) |

### Master Plan과의 불일치 상세

**문제점:**
1. **Step 번호 내용 불일치:**
   - Master Plan Step 3: "Cost Tracking & Budget Alert"
   - Part A Step 3: "Cost Tracking & Budget Alert"
   - ✅ 일치함 (이전 검증에서 착오 발견)

2. **Circuit Breaker 세부 설계 확장:**
   - Master Plan은 Circuit Breaker 언급만 있음
   - Part A는 상태 전이 (CLOSED → OPEN → HALF_OPEN) 상세 설계 포함
   - ✅ 이는 Part Plan의 역할로 적절함

**결론:** Master Plan과의 정합성은 양호함. Step 번호와 내용이 일치함.

### 3.2 기존 Part Plan 양식 비교

| 비교 항목 | Phase 5 Part A | Phase 4 Part A | Phase 6 Part A | 차이점 |
|-----------|----------------|----------------|----------------|--------|
| Progress Checklist | ✅ 있음 | ✅ 있음 | ✅ 있음 | 일치 |
| Prerequisites 섹션 | ✅ 있음 | ✅ 있음 | ❌ 없음 | 누락 |
| Step별 의존성 명시 | ✅ 명확 | ✅ 명확 | ⚠️ Step 4만 명시 | 부분 누락 |
| TDD 순서 기재 | ✅ 있음 | ✅ 있음 | ✅ 있음 | 일치 |
| DoD 체크리스트 | ✅ 구체적 | ✅ 구체적 | ✅ 구체적 | 일치 |
| Skill/Agent 활용 계획 | ✅ 있음 | ✅ 있음 | ❌ 없음 | 누락 |
| 커밋 정책 | ✅ 있음 | ✅ 있음 | ❌ 없음 | 누락 |
| 리스크 테이블 | ✅ 있음 | ✅ 있음 | ❌ 없음 | 누락 |
| Deferred Features | ✅ 있음 | ❌ 없음 | ❌ 없음 | 선택적 |

### 누락된 섹션 상세

1. **Prerequisites 섹션 누락:**
   - Phase 4/5 Part A에는 "선행 조건", "Step별 검증 게이트" 포함
   - Phase 6 Part A에는 없음
   - **권장 조치:** Prerequisites 섹션 추가 필요 (예: Phase 5 Complete, Coverage >= 90%, 브랜치: `feature/phase-6`)

2. **Skill/Agent 활용 계획 누락:**
   - Phase 4/5에는 "시점 | 호출 | 목적" 테이블 있음
   - Phase 6 Part A에는 없음
   - **권장 조치:** Web search (Circuit Breaker 패턴), `/tdd` skill, `code-reviewer` agent 활용 계획 추가

3. **커밋 정책 누락:**
   - Phase 4/5에는 커밋 메시지 예시 있음
   - Phase 6 Part A에는 없음
   - **권장 조치:** 커밋 정책 섹션 추가 (예: `feat(phase6): Step 1 - Circuit Breaker entity`)

4. **리스크 테이블 누락:**
   - Phase 4/5에는 "리스크 | 심각도 | 대응" 테이블 있음
   - Phase 6 Part A에는 없음
   - Master Plan에만 리스크 존재
   - **권장 조치:** Part A 특정 리스크 추가 (예: Circuit Breaker 상태 전이 버그, Rate Limiting Token Bucket 정확도)

---

## 4. 완전성 검증

### 충족된 항목 ✅

1. **도메인 엔티티 명시:**
   - CircuitBreaker (상태 머신)
   - Usage (비용 추적)
   - 필드, 메서드, 상태 전이 로직 포함

2. **테스트 파일 명시:**
   - Step별 테스트 파일 계획됨
   - TDD 순서 명확 (RED-GREEN-REFACTOR)

3. **DoD (Definition of Done) 구체적:**
   - 기능별 체크리스트
   - 품질 기준 (Coverage >= 90%, 21+ 테스트)

4. **통합 테스트 계획:**
   - Step 3: `test_cost_tracking.py` (통합 테스트)
   - Step 4: Chaos Engineering 테스트 (3개 시나리오)

5. **Fake Adapter 계획:**
   - 명시되지 않았으나, 기존 FakeOrchestrator, FakeStorage 패턴 활용 예상

### 누락/부족한 항목 ⚠️

1. **API 엔드포인트 보안:**
   - Step 3에 4개 API 엔드포인트 추가됨:
     - `GET /api/usage/summary`
     - `GET /api/usage/by-model`
     - `GET /api/usage/budget`
     - `PUT /api/usage/budget`
   - ExtensionAuthMiddleware 적용 여부 미명시
   - **권장 조치:** Step 3 DoD에 "모든 `/api/*` 엔드포인트에 X-Extension-Token 검증" 추가

2. **Rate Limiting 구현 상세:**
   - Step 2에서 "Rate Limiting 동작" 언급만 있음
   - Token Bucket 알고리즘 상세 설계 없음
   - 설정값 (requests/second, burst size) 미정의
   - **권장 조치:** Step 2에 Rate Limiting 설계 추가 (GatewaySettings에 rate_limit_rps, burst_size 필드)

3. **Fallback 서버 전환 메커니즘:**
   - Step 2 DoD에 "Fallback 서버 전환 동작" 있음
   - 실제 전환 로직, 우선순위, 설정 방법 미명시
   - **권장 조치:** Fallback 서버 목록 관리 방법, 자동 전환 조건 추가

4. **Budget Alert 알림 방식:**
   - Step 3에서 "예산 초과 시 경고" 언급
   - 알림 방법 (로그? API 응답? Extension UI?) 미정의
   - **권장 조치:** BudgetStatus 반환 타입, Extension 연동 방법 명시

5. **Chaos Tests CI 통합:**
   - Step 4에서 `@pytest.mark.chaos` 마커 추가
   - CI에서 선택적 실행 가능 언급
   - `.github/workflows/` 수정 계획 없음
   - **권장 조치:** CI 통합 계획 추가 또는 "Phase 6 완료 후 CI 통합" 명시

6. **테스트 개수 추정:**
   - "예상 테스트: ~21 신규" (상단)
   - Step별 테스트: Step 1(DoD 미명시) + Step 2(DoD 미명시) + Step 3(10개) + Step 4(3개 시나리오)
   - **권장 조치:** Step 1, 2의 예상 테스트 개수 명시 (예: Step 1: 5개, Step 2: 6개)

---

## 5. 모호성 및 위험 요소

| # | 위험 요소 | 심각도 | 설명 | 권장 조치 |
|---|----------|:------:|------|----------|
| 1 | Circuit Breaker recovery_timeout 구현 방식 | 중간 | `time.time()` 기반 타임아웃 체크가 정확하지 않을 수 있음 (서버 재시작 시 타임스탬프 리셋) | 영속적 상태 저장 (SQLite) 또는 재시작 시 CLOSED 상태로 초기화 정책 명시 |
| 2 | GatewayToolset과 DynamicToolset 이중 등록 | 높음 | OrchestratorAdapter에 GatewayToolset을 주입하면, DynamicToolset의 기존 통합이 깨질 수 있음 | Container에서 DynamicToolset → GatewayToolset 교체 계획 명시 필요 |
| 3 | Rate Limiting 동시성 안전성 | 중간 | 여러 요청이 동시에 Token Bucket을 업데이트하면 경쟁 조건 발생 가능 | asyncio.Lock 사용 계획 명시 또는 Domain Service에 동시성 처리 로직 추가 |
| 4 | Cost Tracking LiteLLM 콜백 중복 | 낮음 | Phase 4 Part B에서 이미 CustomLogger 추가됨. Step 3에서 "확장" 계획인데, 기존 콜백과 충돌 가능성 | 기존 CustomLogger 수정 vs 새 콜백 추가 명확히 구분 |
| 5 | Chaos Tests 재현성 | 중간 | MCP 서버 "돌발 중단" 시뮬레이션 방법 불명확 (subprocess kill? mock?) | Chaos fixture 구현 방법 명시 (예: conftest.py에서 MCP 서버 강제 종료 함수 제공) |
| 6 | Budget 초과 시 행동 정의 | 높음 | 예산 초과 시 "경고"만 표시하는지, API 호출 차단하는지 불명확 | Step 3에 정책 명시 (예: 예산 90% 경고, 100% soft limit, 110% hard limit - 호출 차단) |
| 7 | API 엔드포인트 인증 누락 | 높음 | `/api/usage/*` 엔드포인트가 ExtensionAuthMiddleware 적용 여부 불명확 | Step 3 DoD에 보안 검증 항목 추가 |

---

## 6. 프로젝트 방향성 일치도

### roadmap.md 일치 여부

| roadmap.md 항목 | Phase 6 Part A 반영 | 상태 |
|----------------|---------------------|:----:|
| Phase 6 Part A: MCP Gateway + Cost Tracking + Chaos Tests | ✅ 제목 일치 | ✅ |
| Steps 1-4: Circuit Breaker, Gateway, Cost, Chaos | ✅ 4개 Step 계획됨 | ✅ |
| TDD Red-Green-Refactor 필수 | ✅ TDD 순서 기재됨 | ✅ |
| Coverage >= 90% | ✅ DoD에 명시 | ✅ |
| Phase 5 Complete 선행 조건 | ⚠️ Prerequisites 섹션 없음 | ⚠️ |

### STATUS.md 일치 여부

- STATUS.md: "Phase 5 Complete (2026-02-01)"
- Phase 6 Part A: "선행 조건: Phase 5 Complete" ✅
- 현재 Phase 5까지 완료되었으므로 Phase 6 Part A 시작 가능 ✅

### ADR 일치 여부

| ADR | 관련성 | Phase 6 Part A 반영 |
|-----|--------|---------------------|
| ADR-9: LangGraph=A2A, Plugin=개별 도구만 | 낮음 | 해당 없음 (Plugin은 Part C) |
| ADR-10: ADK Workflow Agents | 낮음 | 해당 없음 (Phase 5 Part E 완료) |
| ADR-11: Workflow Agents Spike Results | 낮음 | 해당 없음 |

**결론:** 기존 ADR과 충돌 없음. Phase 6 Part A는 새로운 도메인 (Gateway, Cost) 도입이므로 ADR 추가 필요할 수 있음.

**권장 조치:** Circuit Breaker 패턴 채택 결정 시 ADR-012 작성 고려 (선택적)

---

## 7. 개선 필요 사항 (Action Items)

### 필수 (Must Fix Before Implementation)

1. **Container.py 수정 계획 추가:**
   - Step 2 수정 파일에 `src/config/container.py` 추가
   - GatewayService, GatewayToolset, CostService 주입 계획 명시

2. **Prerequisites 섹션 추가:**
   - Phase 4/5 Part A 양식 참고하여 추가
   - 선행 조건: Phase 5 Complete, Coverage >= 90%, 브랜치: `feature/phase-6`
   - Step별 검증 게이트 명시 (Web search 시점)

3. **Budget Alert 정책 명확화:**
   - Step 3에 예산 초과 시 행동 정의
   - 경고 수준 (90%, 100%) vs 차단 수준 (110%?)
   - Extension UI 알림 방법 명시

4. **API 보안 검증:**
   - Step 3 DoD에 "모든 `/api/usage/*` 엔드포인트에 ExtensionAuthMiddleware 적용" 추가

5. **GatewayToolset 통합 계획:**
   - Container에서 DynamicToolset을 GatewayToolset으로 교체하는 계획 명시
   - OrchestratorAdapter 주입 변경 영향 분석

### 권장 (Should Fix)

1. **Rate Limiting 설계 상세화:**
   - Token Bucket 알고리즘 파라미터 (rps, burst_size) 명시
   - GatewaySettings에 필드 추가 계획
   - 동시성 안전성 (asyncio.Lock) 명시

2. **Fallback 서버 전환 메커니즘 상세화:**
   - Endpoint 엔티티에 fallback_url 필드 추가 계획
   - 자동 전환 조건, 우선순위 로직 명시

3. **Chaos Tests 재현성 보장:**
   - Step 4에 Chaos fixture 구현 방법 추가
   - MCP 서버 강제 종료 시뮬레이션 방법 (subprocess, mock 등)

4. **Skill/Agent 활용 계획 추가:**
   - Web search: Circuit Breaker 패턴 best practices
   - `/tdd` skill: TDD Red-Green-Refactor
   - `code-reviewer` agent: Part A 완료 후 검토

5. **커밋 정책 추가:**
   - Phase 4/5 Part A 참고하여 커밋 메시지 예시 추가

6. **리스크 테이블 추가:**
   - Part A 특정 리스크 명시 (위 5번 표 참조)

### 제안 (Nice to Have)

1. **Circuit Breaker 영속성:**
   - 서버 재시작 시 Circuit Breaker 상태 복원 계획
   - SQLite 저장 또는 재시작 시 CLOSED 초기화 정책 명시

2. **Cost Tracking 집계 단위:**
   - 시간별, 일별, 월별 집계 여부 명시
   - `/api/usage/summary`의 기간 파라미터 설계

3. **Chaos Tests CI 통합:**
   - `.github/workflows/ci.yml` 수정 계획 추가
   - `pytest -m chaos` 선택적 실행 설정

4. **Step별 테스트 개수 명시:**
   - Step 1: 5개, Step 2: 6개 등 구체적 추정
   - 전체 21개 테스트와 Step별 합계 일치 검증

---

## 8. 기타 제안

### 긍정적 측면

1. **Circuit Breaker 도메인 엔티티 설계:**
   - 순수 Python으로 상태 전이 로직 구현 (헥사고날 원칙 준수)
   - `@property`로 자동 상태 전이 (OPEN → HALF_OPEN) 우아함

2. **Gateway 패턴 도입:**
   - DynamicToolset을 래핑하여 Circuit Breaker + Rate Limiting 추가
   - 기존 코드 변경 최소화 (Adapter Layer만 수정)

3. **Chaos Engineering 도입:**
   - MCP 서버 장애, LLM Rate Limit, 동시 호출 경합 시나리오
   - 프로덕션 신뢰성 검증에 필수적

4. **Cost Tracking SQLite 저장:**
   - Usage 엔티티 + UsageStoragePort로 헥사고날 아키텍처 준수
   - 기존 SQLite WAL 모드 활용으로 동시성 안전

### 개선 제안

1. **Circuit Breaker 설정 동적 변경:**
   - 현재 `failure_threshold`, `recovery_timeout`이 생성자 파라미터
   - Runtime에 설정 변경 가능하도록 API 추가 고려 (예: `PUT /api/gateway/circuit-breaker/{endpoint_id}/config`)

2. **Cost 대시보드 Extension UI:**
   - Step 3에서 Backend API만 추가됨
   - Extension UI 추가는 Phase 7 Part A로 연기된 것으로 보임
   - 연기 이유 명시 권장

3. **Chaos Tests 결과 리포트:**
   - Step 4에서 3개 시나리오 통과 여부만 확인
   - 장애 복구 시간, 데이터 손실 여부 등 메트릭 수집 고려

4. **Gateway Metrics 수집:**
   - Circuit Breaker 상태 전이 횟수, Rate Limit 거부 횟수 등
   - Observability 강화를 위해 Phase 4 Part B의 Logging과 통합 고려

---

## 검증 결과

**결과:** PASS WITH CONDITIONS

**조건:**
1. **필수 수정 (Must Fix):**
   - Container.py 수정 계획 추가
   - Prerequisites 섹션 추가
   - Budget Alert 정책 명확화
   - API 보안 검증 추가
   - GatewayToolset 통합 계획 명시

2. **권장 수정 (Should Fix):**
   - Rate Limiting 설계 상세화
   - Fallback 서버 전환 메커니즘 상세화
   - Chaos Tests 재현성 보장
   - Skill/Agent 활용 계획, 커밋 정책, 리스크 테이블 추가

3. **구현 전 웹 검색 필수:**
   - Circuit Breaker 패턴 best practices
   - Token Bucket 알고리즘 구현
   - Chaos Engineering pytest fixture 패턴

---

**검증자:** Claude Sonnet 4.5 (Plan Validator Agent)
**검증 완료일:** 2026-02-02
