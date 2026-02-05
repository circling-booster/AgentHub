# Hexagonal Architecture Layers

AgentHub의 헥사고날 아키텍처 레이어 구조입니다.

---

## Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│    ┌─────────────────────────────────────────────────┐      │
│    │                                                  │      │
│    │    ┌─────────────────────────────────────┐      │      │
│    │    │                                      │      │      │
│    │    │           Core (Domain)              │      │      │
│    │    │       Entities, Services             │      │      │
│    │    │        (Pure Python)                 │      │      │
│    │    │                                      │      │      │
│    │    └─────────────────────────────────────┘      │      │
│    │                                                  │      │
│    │                    Ports                         │      │
│    │           (Inbound / Outbound)                  │      │
│    │            Abstract Interfaces                   │      │
│    │                                                  │      │
│    └─────────────────────────────────────────────────┘      │
│                                                              │
│                        Adapters                              │
│            (HTTP, ADK, Storage, A2A, OAuth)                 │
│               External Dependencies                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer Responsibilities

| Layer | 역할 | 위치 |
|-------|------|------|
| **Core** | 비즈니스 로직 (Entities + Services) | `src/domain/entities/`, `src/domain/services/` |
| **Ports** | 추상 인터페이스 정의 | `src/domain/ports/` |
| **Adapters** | 외부 시스템 연동 구현체 | `src/adapters/` |

---

## Dependency Rule

```
Adapters → Ports → Core
(바깥쪽)   (중간)   (안쪽)
```

**핵심 원칙:**
- 의존성은 **안쪽으로만** 향합니다
- Core는 Ports와 Adapters를 알지 못합니다
- Ports는 Core만 의존합니다
- Adapters는 Ports를 구현하고 Core를 사용합니다

---

## Layer Constraints

| Layer | 허용 | 금지 |
|-------|------|------|
| **Core** | 순수 Python, dataclass | 외부 라이브러리 (ADK, FastAPI, SQLite) |
| **Ports** | ABC, abstractmethod, Core 타입 | 구현 로직, 외부 라이브러리 |
| **Adapters** | 모든 외부 라이브러리, Port 구현 | 다른 Adapter 직접 의존 |

---

## Folders

| 폴더 | 설명 |
|------|------|
| **core/** | Domain Entity, Service 설계 원칙 |
| **ports/** | Inbound/Outbound Port 인터페이스 설계 |
| **adapters/** | Adapter 구현 패턴 |
| **patterns/** | 아키텍처 설계 패턴 (DI, Repository, Observer) |

---

*Last Updated: 2026-02-05*
