# Testing

AgentHub 테스트 전략 및 가이드입니다.

---

## TDD Philosophy

AgentHub는 **Test-Driven Development (TDD)**를 따릅니다.

```
┌─────────────────────────────────────────────────────────────┐
│                    Red-Green-Refactor                        │
│                                                              │
│   1. RED    →  실패하는 테스트 작성                           │
│   2. GREEN  →  테스트 통과하는 최소 구현                       │
│   3. REFACTOR → 코드 개선 (테스트는 통과 유지)                 │
│                                                              │
│   ⚠️ 테스트 없이 구현 코드 작성 금지                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Test Pyramid

```
                    ┌─────────────┐
      Chaos  ──────►│   Chaos     │  장애 주입 시나리오
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
      E2E   ───────►│    E2E      │  Extension + Server
                    └──────┬──────┘
                           │
                ┌──────────┴──────────┐
   Integration ►│    Integration      │  Adapter + External
                └──────────┬──────────┘
                           │
          ┌────────────────┴────────────────┐
 Unit     │             Unit                │  Domain Only
          │    (Fake Adapters, No Mocking)  │
          └─────────────────────────────────┘
```

| 레벨 | 범위 | 속도 | 마커 |
|------|------|------|------|
| **Unit** | Domain Layer | 빠름 | (기본) |
| **Integration** | Adapter + API | 보통 | `@pytest.mark.integration` |
| **E2E** | Extension + Server | 느림 | `@pytest.mark.e2e_playwright` |
| **Chaos** | 장애 시나리오 | 느림 | `@pytest.mark.chaos` |

---

## Fake Adapter Pattern

### Why Fake over Mock?

| 항목 | Mock | Fake |
|------|------|------|
| **정의** | 호출 기록 + 반환값 제어 | 실제 동작하는 단순 구현 |
| **유지보수** | 인터페이스 변경 시 깨지기 쉬움 | Port 구현으로 컴파일 타임 검증 |
| **가독성** | `mock.return_value = ...` | 실제 코드처럼 읽힘 |
| **AgentHub 정책** | 외부 API만 허용 | **기본 권장** |

### Fake Adapter Example

```python
# tests/unit/fakes/fake_storage.py
from src.domain.ports.outbound.storage_port import ConversationStoragePort
from src.domain.entities.conversation import Conversation

class FakeConversationStorage(ConversationStoragePort):
    def __init__(self):
        self._conversations = {}  # 인메모리 저장

    async def save_conversation(self, conversation: Conversation) -> None:
        self._conversations[conversation.id] = conversation

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        return self._conversations.get(conversation_id)
```

### Available Fakes

| Fake | Port | 위치 |
|------|------|------|
| `FakeConversationStorage` | `ConversationStoragePort` | [fake_storage.py](../../../tests/unit/fakes/fake_storage.py) |
| `FakeOrchestrator` | `OrchestratorPort` | [fake_orchestrator.py](../../../tests/unit/fakes/fake_orchestrator.py) |
| `FakeA2AClient` | `A2APort` | [fake_a2a_client.py](../../../tests/unit/fakes/fake_a2a_client.py) |
| `FakeToolset` | `ToolsetPort` | [fake_toolset.py](../../../tests/unit/fakes/fake_toolset.py) |
| `FakeUsageStorage` | `UsagePort` | [fake_usage_storage.py](../../../tests/unit/fakes/fake_usage_storage.py) |

---

## Test Directory Structure

```
tests/
├── conftest.py              # 공통 fixture (authenticated_client 등)
├── unit/
│   ├── conftest.py          # Unit 전용 fixture
│   ├── fakes/               # Fake Adapter 모음
│   │   ├── __init__.py      # Export 집합
│   │   ├── fake_storage.py
│   │   └── fake_orchestrator.py
│   ├── domain/
│   │   ├── entities/        # Entity 테스트
│   │   └── services/        # Service 테스트
│   └── adapters/            # Adapter 단위 테스트
├── integration/
│   ├── conftest.py          # Integration fixture
│   └── adapters/            # API 통합 테스트
└── e2e/
    └── playwright/          # E2E 테스트
```

---

## Fixture Hierarchy

| Fixture | Scope | 설명 |
|---------|-------|------|
| `temp_data_dir` | function | 임시 데이터 디렉토리 |
| `authenticated_client` | function | TestClient + 토큰 + 임시 DB |
| `fake_storage` | function | FakeConversationStorage 인스턴스 |
| `fake_orchestrator` | function | FakeOrchestrator 인스턴스 |
| `mcp_server` | session | 로컬 MCP 서버 프로세스 |
| `a2a_echo_agent` | session | Echo A2A 에이전트 프로세스 |

---

## Pytest Markers

| Marker | 설명 | 기본 제외 |
|--------|------|----------|
| `@pytest.mark.llm` | 실제 LLM 호출 | Yes |
| `@pytest.mark.e2e_playwright` | Playwright E2E | Yes |
| `@pytest.mark.local_mcp` | 로컬 MCP 서버 필요 | Yes |
| `@pytest.mark.local_a2a` | 로컬 A2A 에이전트 필요 | Yes |
| `@pytest.mark.chaos` | Chaos Engineering | Yes |
| `@pytest.mark.integration` | 통합 테스트 | No |

---

## Quick Commands

```bash
# 전체 테스트 (기본 마커 제외)
pytest

# 커버리지 포함
pytest --cov=src --cov-fail-under=80

# 빠른 실패 모드 (AI 컨텍스트 절약)
pytest -q --tb=line -x

# 특정 테스트
pytest tests/unit/domain/entities/test_conversation.py

# 마커 포함 실행
pytest -m "local_mcp" --local-mcp

# 테스트 수 확인
pytest --co -q
```

---

## Common Pitfalls

| 문제 | 원인 | 해결 |
|------|------|------|
| `403 Forbidden` | `authenticated_client` 미사용 | Integration 테스트에서 반드시 사용 |
| `@pytest.mark.asyncio` 불필요 | `asyncio_mode = "auto"` 설정됨 | 붙이지 않아도 됨 |
| Import 실패 | `from domain...` 사용 | `from src.domain...` 사용 |
| Fake 인라인 정의 | 중앙 관리 원칙 위반 | `tests/unit/fakes/`에서 import |

---

## Related Documentation

- **상세 전략**: [tests/docs/STRATEGY.md](../../../tests/docs/STRATEGY.md)
- **작성 가이드**: [tests/docs/WritingGuide.md](../../../tests/docs/WritingGuide.md)
- **설정 정보**: [tests/docs/CONFIGURATION.md](../../../tests/docs/CONFIGURATION.md)
- **트러블슈팅**: [tests/docs/TROUBLESHOOTING.md](../../../tests/docs/TROUBLESHOOTING.md)

---

*Last Updated: 2026-02-05*
