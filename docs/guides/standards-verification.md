# Standards Verification Protocol

> MCP, A2A, ADK는 빠르게 진화하는 표준. **구현 전 웹 검색으로 최신 스펙 검증 필수.**

---

## 교차 검증 프로토콜 (Plan ↔ 구현)

> **핵심 원칙:** Plan 단계와 구현 단계 **모두**에서 웹 검색 필수. 스펙이 빠르게 변하므로 Plan 시점의 정보가 구현 시점에 outdated될 수 있음.

| 단계 | 검증 목적 | 확인 사항 |
|------|----------|----------|
| **Plan 단계** | 아키텍처/설계 방향 검증 | Breaking Changes, Deprecated API, 권장 패턴 변경 |
| **구현 단계** | API 시그니처 재검증 | 메서드명, 파라미터, 반환 타입, Import 경로 |

### 교차 검증 체크리스트

```
[ ] Plan 단계: 설계 전 최신 스펙 웹 검색 완료
[ ] Plan 단계: Breaking Changes 확인
[ ] 구현 단계: API 시그니처 재검증 완료
[ ] 구현 단계: Import 경로 확인
```

---

## 웹 검색 필수 시점

| 상황 | 확인 사항 |
|------|----------|
| **Plan 단계 진입** | 전체 아키텍처 영향, 권장 패턴, Breaking Changes |
| **구현 단계 진입** | API 메서드명, 파라미터, 반환 타입 |
| Import 에러 | 패키지 구조 변경, 모듈 리네이밍 |
| Deprecation Warning | 대체 API, 마이그레이션 가이드 |

---

## 표준별 확인 항목

| 표준 | 핵심 확인 |
|------|----------|
| **MCP** | Transport (Streamable HTTP/SSE), inputSchema 구조, Sampling 정책 |
| **A2A** | Agent Card 스펙, Handshake 프로토콜, JSON-RPC 2.0 |
| **ADK** | Import 경로 (`google.adk.*`), BaseToolset 인터페이스, Breaking Changes |

---

## 공식 소스 (우선순위)

| 표준 | 1순위 | 2순위 |
|------|-------|-------|
| **MCP** | [modelcontextprotocol.io/specification](https://modelcontextprotocol.io/specification) | GitHub Issues |
| **A2A** | [google.github.io/adk-docs/a2a](https://google.github.io/adk-docs/a2a/) | Google Developers Blog |
| **ADK** | [google.github.io/adk-docs](https://google.github.io/adk-docs) | PyPI Changelog |

---

## Red Flags (즉시 재검증)

- `ImportError: cannot import name 'X'` → API 리네이밍/삭제
- `DeprecationWarning` → 대체 API 마이그레이션
- `TypeError: unexpected keyword argument` → 파라미터 변경

---

## When Claude Should Ask

Claude는 다음 상황에서 반드시 질문하거나 웹 검색해야 함:

1. **API 메서드명 불확실**: MCP/A2A/ADK 웹 검색으로 최신 스펙 검증
2. **아키텍처 변경 영향**: 헥사고날 아키텍처 원칙 준수 검토 필요
3. **보안 관련 코드**: 보안 취약점 검토 필요
4. **테스트 누락**: TDD 테스트 작성 필요

---

*문서 생성일: 2026-01-29*
