# Documentation Map

> AgentHub 프로젝트의 문서 구조를 보여주는 "메타 지도"입니다.

---

## 🗺️ How to Navigate

이 지도는 **Hub-and-Spoke (허브-스포크) 구조**로 구성되어 있습니다:

- **Hub (이 문서)**: 주요 섹션 개요 및 진입점
- **Spokes (Section READMEs)**: 각 섹션의 상세 문서 목록

### 🔗 Linking Strategy

| 대상 | 전략 | 사용 시점 |
|------|------|----------|
| **같은 섹션 내** | 직접 상대 링크 | 같은 폴더 내 문서 참조 시 |
| **다른 섹션, 자주 참조** | 직접 절대 링크 | 핵심 문서 (CLAUDE.md, tests/README.md) |
| **다른 섹션, 가끔 참조** | MAP 참조 | 다른 도메인 참고 문서 |

---

## 📚 Main Sections

### [developers/](developers/) - 개발자 가이드
코드베이스 이해, 기여, 확장을 위한 문서

- **architecture/** - 시스템 아키텍처 (헥사고날, 도메인 모델, Extension 구조, Dual-Track 통합, API 문서)
- **testing/** - 테스트 전략 (TDD, Fake Adapter 패턴, Playground-First Testing)
- **workflows/** - 개발 워크플로우 (Git, CI/CD, 자동화)
- **guides/** - 구현 가이드 (Entity/Service/Adapter 작성, 표준 통합, Lifecycle 관리)

### [operators/](operators/) - 운영자 가이드
배포, 운영, 모니터링을 위한 문서

- **deployment/** - 설치, 설정, 실행
- **observability/** - 로깅, LLM 추적, 메트릭
- **security/** - Token 인증, CORS, OAuth 2.0

### [project/](project/) - 프로젝트 관리
거버넌스, 계획, 의사결정 기록

- **planning/** - 로드맵 및 Phase 계획 (active/completed/planned)
- **decisions/** - ADR (Architecture Decision Records)
- **archive/** - 완료/폐기된 문서

---

## 🚀 Quick Start

| 역할 | 시작점 | 다음 단계 |
|------|--------|-----------|
| **신규 개발자** | [developers/](developers/) | architecture/ → testing/ → workflows/ |
| **코드 기여자** | [developers/guides/](developers/guides/) | implementation/ → standards/ |
| **운영 담당자** | [operators/](operators/) | deployment/ → observability/ |
| **프로젝트 매니저** | [project/planning/](project/planning/) | active/ → decisions/ |

---

## 🔍 Frequently Accessed

| 목적 | 직접 링크 |
|------|----------|
| 아키텍처 이해 | [developers/architecture/](developers/architecture/) |
| Dual-Track 통합 (Phase 7) | [developers/architecture/integrations/dual-track.md](developers/architecture/integrations/dual-track.md) |
| Method C Signal Pattern (HITL) | [developers/architecture/layer/patterns/method-c-signal.md](developers/architecture/layer/patterns/method-c-signal.md) |
| SDK Track API (Phase 6) | [developers/architecture/api/sdk-track.md](developers/architecture/api/sdk-track.md) |
| HITL SSE Events (Phase 6) | [developers/architecture/api/hitl-sse.md](developers/architecture/api/hitl-sse.md) |
| Playground Testing (Phase 6+) | [../tests/manual/playground/README.md](../tests/manual/playground/README.md) |
| 테스트 작성 | [developers/testing/](developers/testing/) |
| 배포/설정 | [operators/deployment/](operators/deployment/) |
| 현재 작업 (Plan 07) | [project/planning/active/](project/planning/active/) |
| 표준 통합 (MCP/A2A) | [developers/guides/standards/](developers/guides/standards/) |
| Lifecycle 관리 | [developers/guides/implementation/lifecycle-management.md](developers/guides/implementation/lifecycle-management.md) |

---

## 📖 Related Core Documentation

- [../CLAUDE.md](../CLAUDE.md) - AI 지침 (프로젝트 원칙, 아키텍처)
- [../tests/README.md](../tests/README.md) - 테스트 설정 (전체 전략)
- [../README.md](../README.md) - 프로젝트 개요

---

*Last Updated: 2026-02-07*
*Structure: Hub-and-Spoke (2-level)*
