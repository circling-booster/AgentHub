# AgentHub Backend (src/)

> 헥사고날 아키텍처 기반 Python 백엔드

## Purpose

AgentHub API 서버의 핵심 비즈니스 로직과 외부 시스템 연동을 담당합니다.

## Structure

```
src/
├── domain/           # 핵심 비즈니스 로직 (순수 Python)
│   ├── entities/     # 도메인 엔티티 (Agent, Tool, Endpoint, Conversation)
│   ├── services/     # 도메인 서비스 (Orchestrator, Registry, Conversation)
│   ├── ports/        # 포트 인터페이스 (Inbound/Outbound)
│   └── exceptions.py # 도메인 예외
│
├── adapters/         # 외부 시스템 연동
│   ├── inbound/      # Driving Adapters (FastAPI HTTP, A2A Server)
│   └── outbound/     # Driven Adapters (ADK, Storage, A2A Client)
│
└── config/           # 설정 및 의존성 주입
    ├── settings.py   # pydantic-settings 기반 설정
    └── container.py  # DI 컨테이너
```

## Hexagonal Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Adapters (외부)                         │
│   ┌─────────────────┐           ┌─────────────────────┐     │
│   │ Inbound Adapters│           │  Outbound Adapters  │     │
│   │ - FastAPI HTTP  │           │  - ADK Orchestrator │     │
│   │ - A2A Server    │           │  - SQLite Storage   │     │
│   └────────┬────────┘           └──────────▲──────────┘     │
│            │                               │                 │
│   ┌────────▼───────────────────────────────┴────────┐       │
│   │                    Ports                         │       │
│   │   Inbound: ChatPort, ManagementPort             │       │
│   │   Outbound: OrchestratorPort, StoragePort, ...  │       │
│   └────────┬───────────────────────────────▲────────┘       │
│            │                               │                 │
│   ┌────────▼───────────────────────────────┴────────┐       │
│   │              Domain (순수 Python)                │       │
│   │   - Entities: Agent, Tool, Endpoint, ...        │       │
│   │   - Services: ConversationService, ...          │       │
│   │   - 외부 라이브러리 import 금지                   │       │
│   └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## Key Principles

| 원칙 | 설명 |
|------|------|
| **의존성 역전** | Domain이 외부를 모름. Adapter가 Domain에 의존 |
| **Port 추상화** | ABC 인터페이스로 외부 시스템과 통신 |
| **Domain 순수성** | 외부 라이브러리(ADK, FastAPI 등) import 금지 |

## Key Files

| 파일 | 역할 |
|------|------|
| `domain/services/conversation_service.py` | 대화 처리 핵심 로직 |
| `domain/services/registry_service.py` | 엔드포인트 등록/관리 |
| `domain/ports/outbound/orchestrator_port.py` | LLM 오케스트레이터 인터페이스 |
| `adapters/outbound/storage/sqlite_conversation_storage.py` | SQLite WAL 저장소 |

## Usage

```bash
# 서버 실행
uvicorn src.main:app --host localhost --port 8000

# 테스트
pytest tests/ --cov=src
```

## References

- [docs/architecture.md](../docs/architecture.md) - 헥사고날 아키텍처 상세
- [docs/implementation-guide.md](../docs/implementation-guide.md) - 구현 패턴
- [src/domain/README.md](domain/README.md) - Domain Layer 상세
- [src/config/README.md](config/README.md) - 설정 가이드
