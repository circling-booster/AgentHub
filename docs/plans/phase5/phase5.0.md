# Phase 5: Verification + Core Connectivity

> **상태:** 📋 Planned
> **선행 조건:** Phase 4 Part A-D Complete (91% coverage, 389 backend tests, 197 extension tests)
> **목표:** A2A 에이전트 작동 검증, MCP 서버 인증(Headers + OAuth 2.1), Content Script, 테스트 인프라 강화
> **분할:** Part A-E (개별 파일)
> **예상 테스트:** ~77 신규 (backend + extension)

---

## 확정된 의사결정 (ADR)

### ADR-5: Phase 구조 → 우선순위 기반 재구성

**문제:** 기존 Phase 5/6/7 경계가 논리적 의존성과 맞지 않음
**결정:** 우선순위 기반으로 Phase 재배치. A2A 검증(P0) → MCP Auth(P1) → Content Script(P2) 순
**이유:** A2A 작동 검증이 최우선 (현재 LLM이 A2A 에이전트를 인식 못하는 문제)

### ADR-6: OAuth 2.1 Flow → Hybrid (Backend Callback + chrome.identity)

**문제:** MCP 서버가 OAuth 2.1 인증을 요구하는 경우 redirect URI 처리 필요
**결정:** Backend `localhost:8000/oauth/callback`이 기본, `chrome.identity.launchWebAuthFlow()` 보조
**이유:** 플랫폼 독립성 확보 (Backend callback), Chrome 환경 최적화 (chrome.identity)

### ADR-7: Plugin System → Option 2 (독립 Port Interface), 독립 인프라

**문제:** DynamicToolset 인프라를 공유할지, 별도 구현할지
**결정:** PluginToolset에 retry, cache, circuit breaker 독립 구현
**이유:** 결합도 최소화. DynamicToolset 변경이 Plugin에 영향 주지 않음

### ADR-8: stdio Transport → 전체 크로스플랫폼 동등 지원

**결정:** Windows/macOS/Linux 3-OS 동등 지원, CI 매트릭스 포함
**이유:** 사용자 환경 다양성 대응

---

## Phase 구조

| Part | 파일 | Steps | 초점 | 우선순위 |
|:----:|------|:-----:|------|:--------:|
| A | [partA.md](partA.md) | 1-4 | A2A Verification & Test Agents | P0 (최우선) |
| B | [partB.md](partB.md) | 5-8 | MCP Server Authentication | P1 |
| C | [partC.md](partC.md) | 9-10 | Content Script (Page Context) | P2 |
| D | [partD.md](partD.md) | 11-12 | Test Infrastructure Enhancement | Support |
| E | [partE.md](partE.md) | 13-16 | ADK Workflow Agents (SequentialAgent, ParallelAgent) | P2 |

---

## Step 번호 매핑

| Step | Title | Part |
|:----:|-------|:----:|
| 1 | A2A Wiring Diagnostic | A |
| 2 | Enhanced Echo Agent | A |
| 3 | LangGraph Chat Agent | A |
| 4 | A2A Full Flow Integration Test | A |
| 5 | AuthConfig Domain Entity | B |
| 6 | Authenticated MCP Connection | B |
| 7 | MCP Registration API with Auth | B |
| 8 | OAuth 2.1 Flow (Hybrid) | B |
| 9 | Content Script Implementation | C |
| 10 | Sidepanel Toggle + Context Injection | C |
| 11 | Server Startup Validation | D |
| 12 | Dynamic Test Port Configuration | D |
| 13 | ADK Workflow Agent API 검증 (Spike Test) | E |
| 14 | WorkflowAgent 도메인 엔티티 + Orchestrator 확장 | E |
| 15 | Workflow API Endpoint + Extension UI | E |
| 16 | ParallelAgent 지원 + E2E 시나리오 | E |

---

## 전체 실행 순서 및 의존성

```
Part A (A2A Verification) ─── 최우선, 단독 시작
  ↓
Part B (MCP Auth) ─── Part A 이후 (A2A 작동 확인 후)
Part C (Content Script) ─── Part A 이후 (Part B와 병렬 가능)
Part D (Test Infra) ─── Part A 이후 (Part B/C와 병렬 가능)
  ↓
Part E (Workflow Agents) ─── Part A 이후 (B-D와 병렬 가능, 순서상 마지막)
```

**병렬화 옵션:**
- Part A 완료 후: Part B + C + D + E 모두 병렬 실행 가능 (상호 독립)
- Part E는 A2A 에이전트(Part A) 결과에 의존하므로 Part A 완료 필수

---

## Phase 시작 전 체크리스트

### 선행 조건

- [ ] 기존 테스트 전체 통과: `pytest tests/ -q --tb=line -x`
- [ ] Coverage >= 90%: `pytest --cov=src --cov-fail-under=90 -q` (현재 91%)
- [ ] 브랜치: `feature/phase-5` 생성
- [ ] Extension 테스트 통과: `cd extension && npm run test`

---

## Phase 5 Definition of Done

### 기능

- [ ] A2A sub_agents wiring 검증 완료 (진단 테스트 통과)
- [ ] Echo + LangGraph Chat 에이전트가 A2A sub-agent로 작동
- [ ] LLM이 A2A 에이전트에 태스크 위임 확인
- [ ] MCP 서버 API Key / Header 인증으로 등록 가능
- [ ] OAuth 2.1 플로우 동작 (mock 프로바이더 + melon MCP 서버)
- [ ] Content Script: 페이지 컨텍스트 추출 동작
- [ ] Sidepanel에서 페이지 컨텍스트 토글 ON/OFF 동작
- [ ] 서버 시작 검증 테스트 통과
- [ ] SequentialAgent로 2+ 에이전트 순차 실행
- [ ] ParallelAgent로 2+ 에이전트 병렬 실행
- [ ] Workflow CRUD API + Extension UI 동작

### 품질

- [ ] Backend coverage >= 90%
- [ ] Extension tests updated (Vitest)
- [ ] 기존 테스트 전체 통과 (regression-free)
- [ ] TDD Red-Green-Refactor 사이클 준수

### 문서

- [ ] `docs/STATUS.md` 업데이트
- [ ] `docs/roadmap.md` Phase 5 상태 반영
- [ ] Phase 5 Part A-E 완료 상태 체크

---

## Phase 4E 항목 처리

| 기존 Phase 4E 항목 | 이관 위치 | 사유 |
|---|---|---|
| MCP Gateway (Step 12) | Phase 6 Part A | 테스트 인프라 의존 |
| Cost Tracking (Step 13) | Phase 6 Part A | Gateway와 함께 |
| Semantic Tool Routing (Step 14) | Phase 6 Part D | MCP Client 의존 |
| Chaos Engineering (Step 15) | Phase 6 Part A | Gateway 테스트 |
| Plugin System Mock (Step 16) | Phase 6 Part C | 전체 구현으로 확장 |
| Event-Driven Architecture | 보류 유지 | 단일 사용자 앱에서 불필요 |

---

## 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|--------|:------:|------|
| A2A가 근본적 ADK 이슈인 경우 | 🔴 | ADK GitHub Issues 검색, 필요시 workaround |
| ADK StreamableHTTPConnectionParams에 headers 미지원 | 🟡 | httpx 커스텀 transport 또는 MCP Python SDK 직접 사용 |
| OAuth melon MCP 서버 접근 불가 | 🟡 | Mock OAuth provider로 대체 테스트 |
| LangGraph 의존성 추가 영향 | 🟢 | test fixture에만 한정, 프로덕션 코드에 영향 없음 |
| SequentialAgent + RemoteA2aAgent 비호환 | 🔴 | Step 13 Spike로 조기 발견. 대안: LlmAgent wrapper |
| ADK Workflow Agent API 변경 | 🟡 | 구현 전 웹 검색으로 최신 API 확인 |

---

*Phase 5 계획 작성일: 2026-01-31*
