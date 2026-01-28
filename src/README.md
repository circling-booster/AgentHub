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

## Security (Phase 1.5)

**Zero-Trust localhost API 보안**으로 Drive-by RCE 공격 차단.

### 위협 모델

| 위협 | 설명 | 완화 |
|------|------|------|
| **Drive-by RCE** | 악성 웹사이트가 `fetch('http://localhost:8000/api/...')` 호출 | Token Handshake |
| **CORS Bypass** | 웹 페이지에서 localhost API 접근 | Origin 제한 |
| **Token Spoofing** | 토큰 없이 API 우회 | Middleware 검증 |

### 보안 컴포넌트

```
┌─────────────────────────────────────────────────────────────┐
│  Chrome Extension                                            │
│    1. 서버에 /auth/token 요청 (Origin: chrome-extension://) │
│    2. 토큰 수신 후 chrome.storage.session에 저장             │
│    3. 모든 /api/* 요청에 X-Extension-Token 헤더 포함         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  AgentHub API Server                                         │
│                                                              │
│  1. CORSMiddleware                                           │
│     - allow_origin_regex: ^chrome-extension://[a-zA-Z0-9_-]+$│
│     - 웹 Origin (https://evil.com) 차단                      │
│                                                              │
│  2. ExtensionAuthMiddleware                                  │
│     - /api/* 요청에 X-Extension-Token 검증                   │
│     - 토큰 불일치 시 403 Forbidden                           │
│                                                              │
│  3. TokenProvider                                            │
│     - secrets.token_urlsafe(32)로 암호학적 토큰 생성         │
│     - 서버 세션당 1개 토큰 유지                              │
└─────────────────────────────────────────────────────────────┘
```

### 주요 파일

| 파일 | 역할 |
|------|------|
| `adapters/inbound/http/security.py` | TokenProvider, ExtensionAuthMiddleware |
| `adapters/inbound/http/routes/auth.py` | POST /auth/token (Origin 검증) |
| `adapters/inbound/http/app.py` | CORS 설정, Middleware 순서 |

### 공개 엔드포인트 (토큰 불필요)

- `/health` - 서버 상태 확인
- `/auth/token` - 토큰 교환 (Origin 검증)
- `/docs`, `/redoc`, `/openapi.json` - API 문서

참조: [docs/implementation-guide.md#9-보안-패턴](../docs/implementation-guide.md#9-보안-패턴)

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
