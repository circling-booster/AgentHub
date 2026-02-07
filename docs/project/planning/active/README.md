# Active Planning

현재 진행 중인 계획 문서입니다.

---

## Current Work

| 항목 | 상태 |
|------|------|
| **Plan** | 07 - hybrid_dual |
| **Branch** | `feature/plan-07-hybrid-dual` |
| **목표** | SDK Track (Resources/Prompts/Sampling/Elicitation) + Playground Testing |
| **Current Phase** | Phase 1 - Domain Entities |

---

## Active Plans

### Plan 07: Hybrid-Dual Architecture

SDK Track(Resources/Prompts/Sampling/Elicitation)을 Playground-First Testing 원칙에 따라 구현합니다.

**주요 특징:**
- Phase 6+: HTTP API와 Playground UI를 함께 구현
- 즉시 회귀 테스트 (Playwright E2E)
- Extension UI는 Production Phase로 연기

---

## Quick Navigation

**현재 작업의 상세 계획 (Phases):**
- [01_domain_entities.md](07_hybrid_dual/01_domain_entities.md) - Phase 1: Domain Entities
- [02_port_interface.md](07_hybrid_dual/02_port_interface.md) - Phase 2: Port Interface + Fake
- [03_domain_services.md](07_hybrid_dual/03_domain_services.md) - Phase 3: Domain Services
- [04_adapter_implementation.md](07_hybrid_dual/04_adapter_implementation.md) - Phase 4: Adapter Implementation
- [05_integration.md](07_hybrid_dual/05_integration.md) - Phase 5: Integration
- [06_http_routes.md](07_hybrid_dual/06_http_routes.md) - Phase 6: HTTP Routes + Playground
- [07_sse_events_playground.md](07_hybrid_dual/07_sse_events_playground.md) - Phase 7: SSE Events + Playground

---

## Planning Structure

이 프로젝트는 **Plan > Phase > Step** 계층 구조를 따릅니다:

```
07_hybrid_dual/ (Plan)
├─ README.md                     # Plan 개요 + Phase 목록
├─ 01_domain_entities.md         # Phase 1 (Steps 1.1, 1.2, 1.3)
├─ 02_port_interface.md          # Phase 2 (Steps 2.1, 2.2)
├─ 03_domain_services.md         # Phase 3
├─ 04_adapter_implementation.md  # Phase 4
├─ 05_integration.md             # Phase 5
├─ 06_http_routes.md             # Phase 6 + Playground UI
└─ 07_sse_events_playground.md   # Phase 7 (Playground-focused)
```

**계층 설명:**
- **Plan**: 하나의 독립적인 개발 주기/마일스톤
- **Phase**: 헥사고날 아키텍처 레이어 단위 (1 Phase = 1 File)
- **Step**: Phase 내부의 TDD 구현 단계 (예: Step 1.1, 1.2, 1.3)

**표준 문서:** [../README.md](../README.md) - Planning 구조 상세 설명

---

## Related

- [../completed/](../completed/) - 완료된 Plan 문서
- [../planned/](../planned/) - 예정된 Plan 문서
- [../README.md](../README.md) - Planning 구조 및 원칙
- [../../MAP.md](../../MAP.md) - 전체 문서 지도

---

*Last Updated: 2026-02-06*
