# Architecture Decisions

아키텍처 관련 ADR(Architecture Decision Record) 인덱스.

---

## ADR 목록

### 채택된 결정

| ID | 제목 | 상태 | 결정일 |
|----|------|------|--------|
| ADR-001 | 헥사고날 아키텍처 채택 | Accepted | 2025-12 |
| ADR-002 | Chrome Extension Manifest V3 구조 | Accepted | 2025-12 |
| ADR-003 | SSE 스트리밍 방식 채택 | Accepted | 2025-12 |
| ADR-004 | Offscreen Document 패턴 | Accepted | 2026-01 |
| [ADR-A05](./ADR-A05-method-c-callback-centric.md) | Method C — Callback-Centric LLM Placement | Accepted | 2026-02-06 |
| [ADR-A06](./ADR-A06-hybrid-timeout-strategy.md) | Hybrid Timeout Strategy | Accepted | 2026-02-06 |
| [ADR-A07](./ADR-A07-dual-track-architecture.md) | Dual-Track Architecture (ADK + SDK) | Accepted | 2026-02-06 |

---

## 주요 결정 요약

### 헥사고날 아키텍처

**컨텍스트:** MCP/A2A/ADK 등 외부 시스템과의 통합이 필요하며, 테스트 용이성이 중요함.

**결정:** Ports and Adapters 패턴을 채택하여 Domain 레이어를 외부 의존성으로부터 격리.

**결과:**
- Domain Layer는 순수 Python으로 유지
- 외부 시스템 변경 시 Adapter만 수정
- Fake Adapter를 통한 단위 테스트 가능

---

### Chrome Extension 구조

**컨텍스트:** Manifest V3 제약(Service Worker 생명주기, DOM 접근 불가) 내에서 SSE 스트리밍 지원 필요.

**결정:** 4개 컴포넌트 구조 채택.
- Background: Service Worker (API 라우팅)
- Offscreen: DOM 컨텍스트 (SSE 처리)
- Sidepanel: 사용자 인터페이스
- Popup: 간단한 상태 표시

**결과:**
- SSE 스트리밍 안정적 처리
- 컴포넌트 간 메시지 기반 통신
- Service Worker 재시작 시에도 연결 유지

---

### SSE 스트리밍 방식

**컨텍스트:** LLM 응답을 실시간으로 Extension에 전달해야 함.

**결정:** WebSocket 대신 SSE(Server-Sent Events) 채택.

**결과:**
- 단방향 스트리밍에 최적화
- HTTP 인프라 재사용 가능
- 연결 복구 로직 단순화

---

### Offscreen Document 패턴

**컨텍스트:** Manifest V3 Service Worker에서 EventSource API 사용 불가.

**결정:** Offscreen Document를 통해 SSE 연결 처리.

**결과:**
- Service Worker와 독립적인 DOM 컨텍스트 확보
- SSE 연결의 안정적 유지
- 메시지 릴레이를 통한 데이터 전달

---

*Last Updated: 2026-02-05*
