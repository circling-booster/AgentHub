# Documentation Map

> 이 문서는 AgentHub 프로젝트의 전체 문서 구조를 보여주는 "메타 지도"입니다.

---

## How to Use This Map

이 지도는 **프랙탈(계층적) 구조**로 구성되어 있습니다:

1. **Level 1 (이 문서)**: 전체 문서 구조 개요 및 하위 섹션 진입점
2. **Level 2 (하위 README.md)**: 각 주제별 상세 문서 목록
   - `developers/` - 개발자용 가이드
   - `operators/` - 운영자용 가이드
   - `project/` - 프로젝트 관리 문서

### Navigation Guidelines

- **강한 결합 (직접 링크 허용)**: 순차적으로 읽어야 하는 문서 (예: 설치 → 환경변수 설정)
- **약한 결합 (MAP 참조 권장)**: 다른 도메인의 참고 문서는 "docs/MAP.md의 XX 섹션 참고"로 안내

---

## Directory Structure

```
docs/
├── developers/                      # 개발자용 문서
│   ├── architecture/                # 시스템 아키텍처
│   │   ├── api/                     # REST API 설계
│   │   ├── extension/               # Chrome Extension 구조
│   │   ├── integrations/            # MCP/A2A 통합
│   │   └── layer/                   # 헥사고날 레이어
│   │       ├── core/                # 도메인 핵심 (Entity, Service)
│   │       ├── ports/               # 포트 인터페이스
│   │       ├── adapters/            # 어댑터 구현체
│   │       └── patterns/            # 디자인 패턴
│   ├── guides/                      # 구현 가이드
│   │   ├── playground/              # Playground 사용 및 API 테스트
│   │   ├── extension/               # Extension 개발
│   │   ├── implementation/          # 코드 작성 패턴
│   │   ├── standards/               # 프로토콜 표준 검증
│   │   │   ├── mcp/                 # MCP 스펙
│   │   │   ├── a2a/                 # A2A 스펙
│   │   │   └── adk/                 # ADK 스펙
│   │   └── troubleshooting/         # 문제 해결
│   ├── testing/                     # 테스트 전략 (TDD, Fake Adapter)
│   └── workflows/                   # Git, CI/CD, 자동화 훅
│
├── operators/                       # 운영자용 문서
│   ├── deployment/                  # 설치, 설정, 실행
│   ├── observability/               # 로깅, LLM 추적, 메트릭
│   └── security/                    # Token 인증, CORS, OAuth
│
└── project/                         # 프로젝트 관리
    ├── archive/                     # 완료/폐기된 문서
    ├── decisions/                   # ADR (Architecture Decision Records)
    │   ├── architecture/            # 아키텍처 결정
    │   └── technical/               # 기술적 결정
    └── planning/                    # 로드맵 및 Phase 계획
        ├── active/                  # 진행 중
        ├── completed/               # 완료
        └── planned/                 # 예정
```

---

## Quick Reference (By Purpose)

각 주제의 **상세 지도(Sub-Map)**는 해당 폴더의 `README.md`를 참고하세요.

| 목적 | 상세 지도 (Level 2) |
|------|---------------------|
| 개발자 가이드 | [developers/README.md](developers/README.md) - 아키텍처, 테스트, 워크플로우, 구현 가이드 |
| 운영자 가이드 | [operators/README.md](operators/README.md) - 배포, 모니터링, 보안 |
| 프로젝트 관리 | [project/README.md](project/README.md) - 로드맵, ADR, 아카이브 |

### Direct Access (Frequently Used)

| 목적 | 경로 |
|------|------|
| 아키텍처 이해 | [developers/architecture/](developers/architecture/) |
| Playground 사용 | [developers/guides/playground/](developers/guides/playground/) |
| 테스트 작성 | [developers/testing/](developers/testing/) |
| 구현 패턴 | [developers/guides/implementation/](developers/guides/implementation/) |
| 배포/설정 | [operators/deployment/](operators/deployment/) |
| 보안 설정 | [operators/security/](operators/security/) |
| 프로젝트 로드맵 | [project/planning/](project/planning/) |
| ADR 조회 | [project/decisions/](project/decisions/) |

---

## Related

- [README.md](README.md) - 전체 문서 소개
- [../tests/README.md](../tests/README.md) - 테스트 설정
- [../CLAUDE.md](../CLAUDE.md) - AI 어시스턴트 지침
