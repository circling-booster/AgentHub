# Phase 6: MCP Advanced + Plugin System + Production Hardening

> **상태:** 📋 Planned
> **선행 조건:** Phase 5 Complete
> **목표:** MCP Gateway/Cost Tracking, MCP Resources/Prompts/Apps, Plugin System, Sampling/Elicitation, Vector Search
> **분할:** Part A-D (개별 파일)
> **예상 테스트:** ~75 신규 (backend + extension)

---

## Phase 구조

| Part | 파일 | Steps | 초점 |
|:----:|------|:-----:|------|
| A | [phase6.0-partA.md](phase6.0-partA.md) | 1-4 | MCP Gateway + Cost Tracking + Chaos Tests |
| B | [phase6.0-partB.md](phase6.0-partB.md) | 5-8 | MCP Resources, Prompts, Apps |
| C | [phase6.0-partC.md](phase6.0-partC.md) | 9-12 | Plugin System (Independent Port) |
| D | [phase6.0-partD.md](phase6.0-partD.md) | 13-15 | Sampling, Elicitation, Vector Search |

---

## Step 번호 매핑

| Step | Title | Part |
|:----:|-------|:----:|
| 1 | Circuit Breaker Entity | A |
| 2 | Gateway Service + MCP Integration | A |
| 3 | Cost Tracking & Budget Alert | A |
| 4 | Chaos Engineering Tests | A |
| 5 | MCP Python SDK Client Port | B |
| 6 | Resources API + Extension UI | B |
| 7 | Prompts API + Extension UI | B |
| 8 | MCP Apps Metadata | B |
| 9 | PluginPort Interface | C |
| 10 | PluginToolset (ADK BaseToolset) | C |
| 11 | Echo + Chat Test Plugins | C |
| 12 | Plugin Management API + Extension UI | C |
| 13 | MCP Sampling | D |
| 14 | MCP Elicitation | D |
| 15 | Vector Search (Semantic Tool Routing) | D |

---

## 전체 실행 순서 및 의존성

```
Part A (Gateway + Cost) ─── Phase 6 첫 번째
  ↓
Part B (MCP Resources/Prompts/Apps) ─── Part A 이후
Part C (Plugin System) ─── Part A와 병렬 가능 (독립)
  ↓
Part D (Sampling + Elicitation + Vector) ─── Part B Step 5 이후
```

**병렬화 옵션:**
- Part B + Part C: Part A 완료 후 병렬 실행 가능
- Part D: Part B Step 5 (McpClientPort) 완료 후 시작

---

## Phase 6 Definition of Done

### 기능

- [ ] Circuit Breaker 상태 전이 (CLOSED → OPEN → HALF_OPEN → CLOSED)
- [ ] Rate Limiting (Token Bucket) 동작
- [ ] Cost Tracking + Budget Alert 동작 ($100/month default)
- [ ] Chaos Engineering 3개 시나리오 통과
- [ ] MCP Resources API + Extension UI 동작
- [ ] MCP Prompts API + Extension UI 동작
- [ ] MCP Apps 메타데이터 표시
- [ ] PluginPort + PluginToolset 동작
- [ ] Echo + LangChain 테스트 플러그인 동작
- [ ] Plugin Management API + Extension UI 동작
- [ ] MCP Sampling handler 동작
- [ ] MCP Elicitation 동적 폼 렌더링
- [ ] Vector Search: 50+ 도구 시 자동 활성화

### 품질

- [ ] Backend coverage >= 90%
- [ ] Extension tests updated
- [ ] Chaos tests 별도 마커 (`@pytest.mark.chaos`)
- [ ] TDD Red-Green-Refactor 사이클 준수

### 문서

- [ ] `docs/STATUS.md` 업데이트
- [ ] `docs/roadmap.md` Phase 6 상태 반영

---

## 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|--------|:------:|------|
| MCP Python SDK 호환성 이슈 | 🟡 | 버전 고정, 웹 검색으로 최신 API 확인 |
| Synapse가 MCP Apps 미지원 | 🟡 | 외부 테스트 서버 찾거나 간단 구현 |
| ChromaDB 의존성 크기 | 🟡 | 선택적 의존성 (`pip install agenthub[vector]`) |
| Elicitation 동적 폼 복잡도 | 🟡 | JSON Schema 서브셋만 지원 (string, number, boolean, enum) |
| LangChain 버전 변동 | 🟢 | 테스트 플러그인에만 한정 |

---

*Phase 6 계획 작성일: 2026-01-31*
