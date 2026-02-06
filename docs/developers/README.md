# Developers

> AgentHub 개발자를 위한 리소스 허브

이 섹션은 AgentHub 프로젝트에 기여하거나 확장하려는 개발자를 위한 문서입니다.

---

## Quick Start (신규 개발자용)

### 1. 환경 설정

```bash
# 저장소 클론
git clone https://github.com/user/agenthub.git
cd agenthub

# Python 가상환경 (3.10+)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Extension 의존성
cd extension && npm install
```

### 2. 개발 서버 실행

```bash
# API 서버
uvicorn src.main:app --host localhost --port 8000 --reload

# Extension 개발 모드 (별도 터미널)
cd extension && npm run dev
```

### 3. 테스트 실행

```bash
# 전체 테스트
pytest

# 빠른 피드백 (Token 최적화)
pytest -q --tb=line -x

# 커버리지 검증
pytest --cov=src --cov-fail-under=80
```

---

## Sub-Sections

| 섹션 | 설명 | 주요 내용 |
|------|------|-----------|
| [**architecture/**](architecture/) | 시스템 아키텍처 | 헥사고날 레이어, 도메인 모델, Extension 구조, 데이터 플로우 |
| [**testing/**](testing/) | 테스트 전략 | TDD 철학, Fake Adapter 패턴, Pytest 설정, 커버리지 |
| [**workflows/**](workflows/) | 개발 워크플로우 | Git 브랜치 전략, 자동화 훅, CI/CD 파이프라인 |
| [**guides/**](guides/) | 구현 가이드 | Entity/Service/Adapter 작성법, SSE 패턴, 보안 패턴 |

---

## Key Concepts

AgentHub는 **헥사고날 아키텍처**를 기반으로 설계되었습니다. 핵심 개념을 이해하면 코드베이스를 빠르게 파악할 수 있습니다.

### Domain Layer

도메인 레이어는 순수 Python으로만 구현되며, 외부 의존성이 없습니다.

```
src/domain/
├── entities/      # 핵심 비즈니스 객체
├── services/      # 비즈니스 로직
├── ports/         # 인터페이스 정의
├── constants.py   # 상수
└── exceptions.py  # 도메인 예외
```

**주요 Entities:**

| Entity | 설명 |
|--------|------|
| `Agent` | LLM 에이전트 설정 (모델, instruction 등) |
| `Conversation` | 대화 세션 (messages, tool calls) |
| `Message` | 단일 메시지 (role, content, metadata) |
| `Endpoint` | MCP/A2A 엔드포인트 정보 |
| `StreamChunk` | SSE 스트리밍 청크 |
| `CircuitBreaker` | 장애 격리 상태 |

### Ports (인터페이스)

Port는 도메인과 외부 세계 사이의 계약을 정의합니다.

| 유형 | 위치 | 역할 |
|------|------|------|
| **Inbound Ports** | `ports/inbound/` | 외부 → 도메인 (API 요청 처리) |
| **Outbound Ports** | `ports/outbound/` | 도메인 → 외부 (저장소, LLM 호출) |

```python
# Outbound Port 예시 (도메인에서 정의)
class StoragePort(Protocol):
    async def save_conversation(self, conv: Conversation) -> None: ...
    async def get_conversation(self, id: str) -> Conversation | None: ...
```

### Adapters (구현체)

Adapter는 Port 인터페이스를 구현하여 외부 시스템과 연결합니다.

```
src/adapters/
├── inbound/       # HTTP API, A2A Server
│   ├── http/      # FastAPI 라우터
│   └── a2a/       # A2A 프로토콜 서버
└── outbound/      # 외부 시스템 연결
    ├── adk/       # Google ADK + LiteLLM
    ├── mcp/       # MCP 클라이언트
    ├── a2a/       # A2A 클라이언트
    └── storage/   # SQLite WAL 저장소
```

### Fake Adapters (테스트용)

테스트에서는 실제 외부 시스템 대신 **Fake Adapter**를 사용합니다.

```
tests/unit/fakes/
├── fake_storage_adapter.py     # In-memory 저장소
├── fake_orchestrator_adapter.py
└── ...
```

**Mock vs Fake:**

| 특성 | Mock | Fake |
|------|------|------|
| 동작 | 호출 검증 (Stub) | 실제 동작 (간소화) |
| 유지보수 | 테스트마다 설정 | 재사용 가능 |
| 신뢰도 | 낮음 | 높음 |
| AgentHub | 사용 안함 | **권장** |

---

## Technology Stack

### Backend

| 기술 | 버전 | 용도 |
|------|------|------|
| Python | 3.10+ | 런타임 |
| FastAPI | 0.100+ | HTTP API 서버 |
| Google ADK | 1.23.0+ | 에이전트 프레임워크 |
| LiteLLM | Latest | 100+ LLM 통합 |
| SQLite | WAL mode | 영구 저장소 |
| Pydantic | 2.0+ | 데이터 검증 |
| dependency-injector | Latest | DI 컨테이너 |

### Frontend (Extension)

| 기술 | 버전 | 용도 |
|------|------|------|
| WXT | 0.19+ | Extension 프레임워크 |
| TypeScript | 5.0+ | 타입 안전성 |
| React | 18+ | UI 컴포넌트 |
| Tailwind CSS | 3.0+ | 스타일링 |

### 개발 도구

| 도구 | 용도 |
|------|------|
| pytest | 테스트 프레임워크 |
| pytest-asyncio | 비동기 테스트 |
| pytest-cov | 커버리지 측정 |
| ruff | 린팅 + 포맷팅 |
| mypy | 타입 체크 |

---

## 다음 단계

- **Playground 사용**: [guides/playground/](guides/playground/) - 백엔드 API 수동 테스트 도구
- **아키텍처 이해**: [architecture/](architecture/) - 시스템 레이어와 데이터 플로우
- **테스트 작성**: [testing/](testing/) - TDD 철학과 Fake Adapter 패턴
- **기여하기**: [workflows/](workflows/) - Git 워크플로우와 CI/CD
- **코드 작성**: [guides/](guides/) - 구현 패턴과 코드 예제

---

*Last Updated: 2026-02-05*
