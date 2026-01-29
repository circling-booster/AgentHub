# AgentHub Tests

> TDD + 헥사고날 아키텍처 기반 테스트 전략

## Purpose

AgentHub의 품질 보장을 위한 테스트 코드를 관리합니다. Fake Adapter 패턴으로 외부 의존성 없이 Domain 로직을 테스트합니다.

## Structure

```
tests/
├── unit/                          # 단위 테스트
│   ├── domain/
│   │   ├── entities/              # 엔티티 테스트 (7개)
│   │   │   ├── test_agent.py
│   │   │   ├── test_conversation.py
│   │   │   ├── test_endpoint.py
│   │   │   ├── test_enums.py
│   │   │   ├── test_message.py
│   │   │   ├── test_tool.py
│   │   │   └── test_tool_call.py
│   │   ├── services/              # 서비스 테스트 (4개)
│   │   │   ├── test_conversation_service.py
│   │   │   ├── test_health_monitor_service.py
│   │   │   ├── test_orchestrator_service.py
│   │   │   └── test_registry_service.py
│   │   └── test_exceptions.py
│   │
│   ├── fakes/                     # Fake Adapter (테스트용, 중앙 관리)
│   │   ├── __init__.py            # 전체 export (from tests.unit.fakes import ...)
│   │   ├── fake_storage.py        # FakeConversationStorage, FakeEndpointStorage
│   │   ├── fake_orchestrator.py   # FakeOrchestrator
│   │   ├── fake_toolset.py        # FakeToolset
│   │   └── fake_conversation_service.py  # FakeConversationService
│   │
│   └── conftest.py                # Fake Adapter fixture 중앙 제공
│
├── integration/                   # 통합 테스트
│   └── adapters/
│       ├── test_sqlite_storage.py # SQLite WAL 테스트
│       ├── test_http_app.py       # FastAPI + CORS/Auth 미들웨어 테스트
│       ├── test_auth_routes.py    # Token Handshake 테스트
│       └── test_health_routes.py  # Health 엔드포인트 테스트
│
├── e2e/                           # E2E 테스트 (Phase 3)
│
└── conftest.py                    # 루트 pytest fixtures
```

## Test Strategy

### 테스트 피라미드

```
                    ┌─────────────┐
      Phase 3 ────► │    E2E      │  Extension + Server
                    └──────┬──────┘
                           │
                ┌──────────┴──────────┐
   Phase 2 ───► │    Integration      │  Adapter + External
                └──────────┬──────────┘
                           │
          ┌────────────────┴────────────────┐
 Phase 1  │             Unit                │  Domain Only
          │    (Fake Adapters, No Mocking)  │
          └─────────────────────────────────┘
```

### Phase별 테스트

| Phase | 테스트 유형 | 대상 | 커버리지 목표 |
|-------|-----------|------|--------------|
| 1 | Unit | Domain Layer | 80% |
| 2 | Integration | Adapter Layer | 70% |
| 3 | E2E | Full Stack | Critical Path |

## Fake Adapter Pattern

헥사고날 아키텍처의 핵심 장점: **Mocking 없이 테스트**

### 왜 Fake Adapter인가?

```python
# ❌ Mocking (권장하지 않음)
@mock.patch('src.adapters.outbound.storage.SqliteStorage')
def test_with_mock(mock_storage):
    mock_storage.get_conversation.return_value = ...  # 실제 동작과 다를 수 있음

# ✅ Fake Adapter (권장)
def test_with_fake():
    fake_storage = FakeConversationStorage()  # Port 인터페이스 구현
    service = ConversationService(storage=fake_storage)
    # 실제 동작과 동일한 인터페이스, 인메모리 저장
```

### Fake Adapter 사용 예시

```python
# 중앙 관리 패키지에서 import (권장)
from tests.unit.fakes import FakeConversationStorage, FakeOrchestrator

class TestConversationService:
    @pytest.fixture
    def storage(self):
        return FakeConversationStorage()

    @pytest.fixture
    def orchestrator(self):
        return FakeOrchestrator(responses=["Hello!", " How can I help?"])

    @pytest.fixture
    def service(self, storage, orchestrator):
        return ConversationService(storage=storage, orchestrator=orchestrator)

    async def test_send_message(self, service):
        # Given: 새 대화
        # When: 메시지 전송
        chunks = []
        async for chunk in service.send_message(None, "Hi"):
            chunks.append(chunk)

        # Then: 스트리밍 응답
        assert "".join(chunks) == "Hello! How can I help?"
```

> **중요:** 모든 Fake Adapter는 `tests/unit/fakes/` 패키지에서 중앙 관리됩니다.
> 테스트 파일 내에 인라인으로 Fake 클래스를 정의하지 마세요.
> conftest.py가 공통 fixture를 제공하므로 직접 인스턴스화 없이도 사용 가능합니다.

## Key Files

| 파일 | 역할 |
|------|------|
| `unit/fakes/fake_storage.py` | 인메모리 저장소 (ConversationStoragePort, EndpointStoragePort 구현) |
| `unit/fakes/fake_orchestrator.py` | 설정 가능한 응답 반환 (OrchestratorPort 구현) |
| `unit/fakes/fake_toolset.py` | MCP 도구 시뮬레이션 (ToolsetPort 구현) |
| `unit/fakes/fake_conversation_service.py` | 대화 서비스 시뮬레이션 (OrchestratorService 테스트용) |
| `unit/conftest.py` | Fake Adapter fixture 중앙 제공 |
| `conftest.py` | 루트 공통 fixtures |

## Usage

```bash
# 전체 테스트
pytest

# 단위 테스트만
pytest tests/unit/

# 통합 테스트만
pytest tests/integration/

# 커버리지 리포트
pytest --cov=src --cov-report=html

# 커버리지 검증 (80% 미만 시 실패)
pytest --cov=src --cov-fail-under=80

# 특정 테스트 실행
pytest tests/unit/domain/services/test_conversation_service.py -v
```

## Current Status

- **Unit Tests:** 136 passed
- **Integration Tests:** 46 passed
- **Total:** 182 tests
- **Coverage:** 91%

## References

- [docs/roadmap.md](../docs/roadmap.md) - 테스트 전략 상세
- [docs/architecture.md](../docs/architecture.md) - 헥사고날 아키텍처
- [src/domain/ports/](../src/domain/ports/) - Port 인터페이스 정의
