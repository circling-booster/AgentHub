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
├── e2e/                           # E2E 테스트 (12 tests, 2 skipped)
│   ├── conftest.py               # E2E 공통 fixture
│   └── test_extension_server.py  # Extension API 시퀀스 시뮬레이션
│       ├── TestFullChatFlow      # Health → 토큰 교환 → 대화 → SSE 채팅
│       ├── TestMcpManagementFlow # 서버 등록 → 조회 → 삭제
│       └── TestTokenRequired     # 토큰 없이 API 호출 시 403
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
| `@pytest.mark.mcp` | MCP 서버 필요 (`--run-mcp` 옵션) | 기본 제외 |

### 커스텀 옵션

| 옵션 | 설명 |
|------|------|
| `--run-llm` | LLM 테스트 활성화 (API 키 + 비용 필요) |
| `--run-mcp` | MCP 서버 E2E 테스트 활성화 (로컬 서버 필요) |

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

# E2E 테스트
pytest tests/e2e/ -v

# 특정 테스트 실행
pytest tests/unit/domain/services/test_conversation_service.py -v

# Extension 테스트 (Vitest)
cd extension && npx vitest run

# Extension 특정 테스트
cd extension && npx vitest run tests/hooks/useChat.test.ts
```

## Troubleshooting

### MCP 관련 오류

MCP 테스트 실패 시 **디버깅 전 필수 확인사항:**

#### 1. 로컬 MCP 서버 실행 확인

```bash
# Synapse MCP 서버 실행 (별도 터미널)
cd C:\Users\sungb\Documents\GitHub\MCP_SERVER\MCP_Streamable_HTTP
SYNAPSE_PORT=9000 python -m synapse

# 서버 동작 확인
curl http://127.0.0.1:9000/mcp
# 또는
pytest tests/e2e/test_extension_server.py::TestMcpManagementFlow::test_mcp_server_registration -v
```

#### 2. 포트 충돌 확인

```bash
# Windows
netstat -ano | findstr :9000

# Linux/Mac
lsof -i :9000
```

포트가 이미 사용 중이면 `SYNAPSE_PORT`를 변경하거나 프로세스를 종료하세요.

#### 3. CI 환경과 로컬 환경 차이

- **로컬:** 실제 MCP 서버 연결 (`127.0.0.1:9000`)
- **CI:** Mock MCPToolset 자동 적용 (`tests/integration/adapters/conftest.py`)

CI 환경에서는 `os.getenv("CI")`가 "true"일 때 자동으로 Mock이 활성화됩니다.

---

### LLM 관련 오류

LLM 테스트 실패 시 **디버깅 전 필수 확인사항:**

#### 1. .env 파일 API 키 확인

```bash
# .env 파일 존재 및 API 키 설정 확인
cat .env | grep OPENAI_API_KEY
cat .env | grep ANTHROPIC_API_KEY
```

**필수 API 키:**
- `OPENAI_API_KEY`: LLM 테스트용 (`openai/gpt-4o-mini` 사용, 비용 최소화)
- `ANTHROPIC_API_KEY`: 프로덕션 LLM (선택적)

#### 2. load_dotenv() 호출 확인

`tests/conftest.py`가 `.env` 파일을 자동 로드합니다:

```python
# tests/conftest.py
from dotenv import load_dotenv
load_dotenv()  # 루트 .env 파일 로드
```

만약 환경변수가 로드되지 않는다면:

```bash
# pytest 실행 전 수동 로드
export $(cat .env | xargs)  # Linux/Mac
# 또는
foreach($line in Get-Content .env) { $name, $value = $line -split '=', 2; [System.Environment]::SetEnvironmentVariable($name, $value) }  # PowerShell
```

#### 3. API 키 유효성 테스트

```bash
# OpenAI API 키 테스트
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"

# Anthropic API 키 테스트
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":1,"messages":[{"role":"user","content":"test"}]}'
```

#### 4. LLM 테스트 명시적 실행

```bash
# LLM 테스트는 기본적으로 제외되므로 --run-llm 옵션 필요
pytest -m llm --run-llm -v

# 특정 LLM 테스트만 실행
pytest tests/integration/adapters/test_chat_routes.py::test_chat_stream_success --run-llm -v
```

---

### SQLite 관련 오류

#### 1. "database is locked" 에러

```bash
# SQLite WAL 파일 삭제 (주의: 데이터 손실 가능)
rm data/agenthub.db-wal data/agenthub.db-shm

# 또는 테스트 DB만 삭제
rm tests/test_*.db*
```

**근본 원인:**
- 비동기 쓰기 작업 중 다른 프로세스가 DB 접근
- SQLite WAL 모드 + `asyncio.Lock` 사용으로 완화됨 (`src/adapters/outbound/storage/sqlite_storage.py`)

#### 2. 테스트 격리 실패

```bash
# 각 테스트마다 독립적인 DB 사용 확인
# tests/integration/adapters/conftest.py의 temp_db_path fixture 확인
pytest tests/integration/adapters/test_sqlite_storage.py -v --tb=short
```

---

### 비동기 테스트 타임아웃

```bash
# asyncio 타임아웃 증가
pytest tests/integration/adapters/test_orchestrator_adapter.py --timeout=60

# 또는 pytest-timeout 설치
pip install pytest-timeout
```

**일반적 원인:**
- 외부 LLM API 응답 지연
- MCP 서버 연결 타임아웃
- 비동기 이벤트 루프 블로킹

**해결책:**
- `asyncio.wait_for()` 타임아웃 설정 확인
- `DynamicToolset` 캐시 TTL 조정 (기본 300초)

---

### Coverage 임계값 실패

```bash
# 현재 커버리지 확인
pytest --cov=src --cov-report=term-missing

# 커버리지가 낮은 파일 확인
pytest --cov=src --cov-report=html
# 브라우저로 htmlcov/index.html 열기
```

**Target:** 80% 이상 (Phase 1: 91%, Phase 2: 88% 달성)

**낮은 커버리지 원인:**
- Port 인터페이스 (추상 메서드, 실제 실행 안 됨)
- 에러 핸들러 (특정 조건에서만 발생)
- Main 엔트리포인트 (`src/main.py`)

---

### Extension (Vitest) 관련 오류

#### 1. TypeScript 타입 에러

```bash
cd extension
npx tsc --noEmit  # 타입 체크만 실행
```

#### 2. Mock 관련 에러

```typescript
// vi.mock() 호출 순서 확인
// tests/lib/api.test.ts 참조
vi.mock('../lib/api', () => ({
  authenticatedFetch: vi.fn(),
}))
```

#### 3. Chrome Extension API Mock

```typescript
// Vitest setup에서 chrome API mock 확인
// vitest.setup.ts
global.chrome = {
  runtime: { sendMessage: vi.fn(), onMessage: { addListener: vi.fn() } },
  storage: { session: { get: vi.fn(), set: vi.fn() } },
}
```

---

### 기타 유용한 팁

#### 특정 테스트만 실패 시 격리 실행

```bash
# 단일 테스트 메서드만 실행
pytest tests/unit/domain/services/test_conversation_service.py::TestConversationService::test_send_message -v

# 실패한 테스트만 재실행
pytest --lf  # --last-failed

# 새로운 실패만 재실행
pytest --ff  # --failed-first
```

#### Verbose 모드로 상세 출력

```bash
# 상세 출력 + 짧은 traceback
pytest -vv --tb=short

# 로깅 출력 포함
pytest -vv --log-cli-level=DEBUG
```

#### Parallel 실행 (속도 향상)

```bash
# pytest-xdist 설치
pip install pytest-xdist

# CPU 코어 수만큼 병렬 실행
pytest -n auto
```

**주의:** SQLite 쓰기 경합 가능성 있으므로 통합 테스트는 순차 실행 권장.

---

## Current Status

### Server Tests (Python / pytest)

- **Unit Tests:** 155 passed
- **Integration Tests:** 91 passed (+4 LLM deselected)
- **E2E Tests:** 10 passed, 2 skipped (MCP 서버 필요)
- **Total:** 260 passed, 2 skipped, 4 deselected
- **Coverage:** 88%

### Extension Tests (TypeScript / Vitest)

- **Library Tests:** 51 passed (messaging, api, sse, background-handlers)
- **Hook Tests:** 22 passed (useChat, useMcpServers, useServerHealth)
- **Component Tests:** 34 passed (ChatInterface, ChatInput, MessageBubble, McpServerManager, ServerStatus, App)
- **Entrypoint Tests:** 22 passed (background, offscreen)
- **Total:** 129 passed

### Grand Total: 389+ tests

## Advanced Testing Tools (Optional)

### 1. 파일 변경 감지 자동 테스트 (Watch Mode)

```bash
# pytest-watch 설치
pip install pytest-watch

# 파일 변경 시 자동 테스트 실행
ptw tests/unit/ --onpass="echo '\n✅ Tests passed!'" --onfail="echo '\n❌ Tests failed!'"

# 특정 파일만 감시
ptw tests/unit/domain/services/ --ignore=__pycache__
```

### 2. 성능 회귀 테스트 (Benchmarking)

```bash
# pytest-benchmark 설치
pip install pytest-benchmark

# 성능 측정 예시
def test_conversation_service_performance(benchmark):
    service = ConversationService(...)
    benchmark(service.send_message, "test message")

# 벤치마크 비교
pytest tests/unit/ --benchmark-compare=0001
```

### 3. HTML 테스트 리포트

```bash
# pytest-html 설치
pip install pytest-html

# HTML 리포트 생성
pytest --html=report.html --self-contained-html
```

### 4. 테스트 데이터 관리 (Factory Pattern)

```python
# tests/factories.py (추천)
from dataclasses import dataclass
from domain.entities import Conversation, Message, MessageRole

@dataclass
class ConversationFactory:
    @staticmethod
    def create(conversation_id: str = "test-conv-1", title: str = "Test") -> Conversation:
        return Conversation(id=conversation_id, title=title, messages=[])

    @staticmethod
    def with_messages(message_count: int = 3) -> Conversation:
        conv = ConversationFactory.create()
        for i in range(message_count):
            conv.messages.append(
                Message(
                    id=f"msg-{i}",
                    conversation_id=conv.id,
                    role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                    content=f"Message {i}",
                )
            )
        return conv
```

### 5. E2E 테스트 서버 자동화

```bash
# tests/e2e/start_test_server.sh
#!/bin/bash
# MCP 테스트 서버 자동 시작/종료

MCP_SERVER_PID=""

start_mcp_server() {
    echo "Starting MCP test server..."
    cd C:/Users/sungb/Documents/GitHub/MCP_SERVER/MCP_Streamable_HTTP
    SYNAPSE_PORT=9000 python -m synapse &
    MCP_SERVER_PID=$!
    sleep 2
    echo "MCP server started (PID: $MCP_SERVER_PID)"
}

stop_mcp_server() {
    if [ ! -z "$MCP_SERVER_PID" ]; then
        echo "Stopping MCP server (PID: $MCP_SERVER_PID)..."
        kill $MCP_SERVER_PID 2>/dev/null || true
    fi
}

trap stop_mcp_server EXIT

start_mcp_server
pytest tests/e2e/ --run-mcp -v
```

사용법:
```bash
chmod +x tests/e2e/start_test_server.sh
./tests/e2e/start_test_server.sh
```

---

## References

- [docs/roadmap.md](../docs/roadmap.md) - 테스트 전략 상세
- [docs/architecture.md](../docs/architecture.md) - 헥사고날 아키텍처
- [src/domain/ports/](../src/domain/ports/) - Port 인터페이스 정의
- [pytest Documentation](https://docs.pytest.org/) - pytest 공식 문서
- [Vitest Documentation](https://vitest.dev/) - Vitest 공식 문서
