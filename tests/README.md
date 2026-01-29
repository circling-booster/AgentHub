# AgentHub Tests

> TDD + 헥사고날 아키텍처 기반 테스트 전략

## Purpose

AgentHub의 품질 보장을 위한 테스트 코드를 관리합니다. Fake Adapter 패턴으로 외부 의존성 없이 Domain 로직을 테스트합니다.

## Structure

```
tests/
├── unit/                          # 단위 테스트 (155 tests)
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
│   ├── adapters/
│   │   └── test_security.py       # Security 미들웨어 단위 테스트
│   │
│   ├── config/
│   │   ├── test_container.py      # DI Container 테스트
│   │   └── test_settings.py       # Settings 로드 테스트
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
├── integration/                   # 통합 테스트 (91 tests + 4 LLM deselected)
│   └── adapters/
│       ├── conftest.py            # 공통 fixture (authenticated_client, CI Mock)
│       ├── test_sqlite_storage.py # SQLite WAL 테스트
│       ├── test_json_endpoint_storage.py  # JSON 엔드포인트 저장소 테스트
│       ├── test_http_app.py       # FastAPI + CORS/Auth 미들웨어 테스트
│       ├── test_http_exceptions.py # HTTP 예외 핸들러 테스트
│       ├── test_auth_routes.py    # Token Handshake 테스트
│       ├── test_health_routes.py  # Health 엔드포인트 테스트
│       ├── test_mcp_routes.py     # MCP 서버 관리 API 테스트
│       ├── test_chat_routes.py    # Chat SSE 스트리밍 테스트 (LLM 마커 포함)
│       ├── test_conversation_routes.py  # Conversation CRUD 테스트
│       ├── test_dynamic_toolset.py     # DynamicToolset 테스트
│       └── test_orchestrator_adapter.py # ADK Orchestrator 테스트 (LLM 마커 포함)
│
├── e2e/                           # E2E 테스트 (Phase 3)
│
└── conftest.py                    # 루트 pytest fixtures (.env 로드, --run-llm 옵션)
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
| 1.5 | Unit | Security Middleware | - |
| 2 | Integration | Adapter Layer, MCP, API | 70% |
| 3 | E2E | Full Stack | Critical Path |

## pytest Markers & Options

### 마커 (Markers)

| 마커 | 설명 | 기본 동작 |
|------|------|----------|
| `@pytest.mark.llm` | LLM API 호출 필요 (비용 발생) | **기본 제외** (`addopts = "-m 'not llm'"`) |
| `@pytest.mark.local_mcp` | 로컬 MCP 서버 필요 (127.0.0.1:9000) | 기본 제외 |

### 커스텀 옵션

| 옵션 | 설명 |
|------|------|
| `--run-llm` | LLM 테스트 활성화 (API 키 + 비용 필요) |

### LLM 테스트 환경

- `.env` 파일의 API 키를 `tests/conftest.py`에서 `load_dotenv()`로 로드
- LLM 테스트는 **OpenAI API (`openai/gpt-4o-mini`)** 만 사용 (비용 최소화)
- `tests/integration/adapters/conftest.py`에서 기본 모델을 `openai/gpt-4o-mini`로 오버라이드

### CI 환경 분기

| 환경 | MCP 서버 | LLM 테스트 |
|------|---------|-----------|
| **로컬** | 실제 서버 (`localhost:9000`) | `--run-llm` 옵션으로 실행 |
| **CI** (GitHub Actions) | Mock MCPToolset 자동 적용 | 제외 (비용 방지) |

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
| `integration/adapters/conftest.py` | 통합 테스트 공통 fixture (authenticated_client, CI Mock) |
| `conftest.py` | 루트 공통 fixtures (.env 로드, --run-llm 옵션) |

## Usage

```bash
# 전체 테스트 (LLM 제외)
pytest

# 단위 테스트만
pytest tests/unit/

# 통합 테스트만
pytest tests/integration/

# LLM 테스트 포함 실행 (API 키 필요)
pytest -m llm --run-llm -v

# 커버리지 리포트
pytest --cov=src --cov-report=html

# 커버리지 검증 (80% 미만 시 실패)
pytest --cov=src --cov-fail-under=80

# 특정 테스트 실행
pytest tests/unit/domain/services/test_conversation_service.py -v
```

## Current Status

- **Unit Tests:** 155 passed
- **Integration Tests:** 91 passed (+4 LLM deselected)
- **Total:** 246 passed, 4 deselected
- **Coverage:** 89%

## References

- [docs/roadmap.md](../docs/roadmap.md) - 테스트 전략 상세
- [docs/architecture.md](../docs/architecture.md) - 헥사고날 아키텍처
- [src/domain/ports/](../src/domain/ports/) - Port 인터페이스 정의
