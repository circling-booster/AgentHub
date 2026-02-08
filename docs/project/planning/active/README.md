# Active Planning

현재 진행 중인 계획 문서입니다.

---

## Current Work

| 항목 | 상태 |
|------|------|
| **Plan** | 09 - dynamic_configuration |
| **Branch** | `feature/plan-09-dynamic-configuration` |
| **목표** | Dynamic Configuration & Model Management (API Key, LLM Model 런타임 관리) |
| **Current Phase** | Phase 1 - Domain Entities |

---

## Active Plans

### Plan 09: Dynamic Configuration & Model Management

API Key와 LLM 모델을 런타임에 동적으로 관리하는 Configuration System을 구현합니다.

**주요 특징:**
- DB-First Configuration (SQLite 단일 진실 공급원)
- Fernet 대칭 암호화 (API Key 보안)
- Runtime Model Switching (컨테이너 재시작 불필요)
- Playground-First Testing (Phase 6-7)

---

## Quick Navigation

**현재 작업의 상세 계획 (Phases):**
- [01_domain_entities.md](09_dynamic_configuration/01_domain_entities.md) - Phase 1: Domain Entities
- [02_port_interface.md](09_dynamic_configuration/02_port_interface.md) - Phase 2: Port Interface + Fake
- [03_domain_services.md](09_dynamic_configuration/03_domain_services.md) - Phase 3: Domain Services
- [04_adapter_implementation.md](09_dynamic_configuration/04_adapter_implementation.md) - Phase 4: Adapter Implementation
- [05_integration.md](09_dynamic_configuration/05_integration.md) - Phase 5: Integration
- [06_http_routes_playground.md](09_dynamic_configuration/06_http_routes_playground.md) - Phase 6: HTTP Routes + Playground
- [07_validation_e2e.md](09_dynamic_configuration/07_validation_e2e.md) - Phase 7: Validation & E2E Tests

---

## Planning Structure

이 프로젝트는 **Plan > Phase > Step** 계층 구조를 따릅니다:

```
09_dynamic_configuration/ (Plan)
├─ README.md                        # Plan 개요 + Phase 목록
├─ 01_domain_entities.md            # Phase 1 (Steps 1.1~1.5)
├─ 02_port_interface.md             # Phase 2 (Steps 2.1~2.4)
├─ 03_domain_services.md            # Phase 3 (Steps 3.1~3.6)
├─ 04_adapter_implementation.md     # Phase 4 (Steps 4.1~4.7)
├─ 05_integration.md                # Phase 5 (Steps 5.1~5.5)
├─ 06_http_routes_playground.md     # Phase 6 (Steps 6.1~6.4) + Playground UI
└─ 07_validation_e2e.md             # Phase 7 (Steps 7.1~7.3)
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

*Last Updated: 2026-02-08*
