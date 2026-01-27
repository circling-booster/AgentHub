# AgentHub

> Google ADK 기반 MCP + A2A 통합 Agent System

**AgentHub는** 개발자와 파워유저가 **다양한 AI 도구(MCP)와 에이전트(A2A)를** 로컬 환경에서 통합 관리하고, **브라우저에서 바로 호출**할 수 있게 해주는 데스크톱 애플리케이션입니다.

---

## 누구를 위한 도구인가?

| 사용자 유형 | 설명 |
|------------|------|
| **AI 도구 개발자** | MCP 서버나 A2A 에이전트를 개발하고 테스트하는 사람 |
| **파워 유저** | 다양한 AI 도구를 조합해서 워크플로우를 만들고 싶은 사람 |
| **프라이버시 중시 사용자** | 클라우드가 아닌 로컬에서 AI 에이전트를 실행하고 싶은 사람 |
| **기업 내부 개발자** | 사내 시스템을 MCP/A2A로 연동하려는 사람 |

---

## 해결하는 문제

| 문제 | 현재 상황 | AgentHub 해결책 |
|------|----------|----------------|
| **MCP/A2A 분리** | MCP 클라이언트와 A2A 클라이언트를 따로 사용해야 함 | 하나의 UI에서 MCP(도구) + A2A(에이전트) 통합 관리 |
| **브라우저 컨텍스트 단절** | 웹 페이지 내용을 AI에게 전달하려면 복사/붙여넣기 필요 | Chrome Extension이 현재 페이지에서 바로 AI + 도구 호출 |
| **LLM 종속성** | 특정 LLM에 종속된 도구는 다른 LLM으로 교체 불가 | LiteLLM으로 100+ LLM 지원, 설정만 바꾸면 전환 가능 |
| **도구 추가 번거로움** | 새 MCP 서버 추가 시 설정 파일 수정 후 재시작 필요 | UI에서 URL 입력만으로 동적 등록/해제 (재시작 불필요) |
| **클라우드 의존** | 대부분 AI 도구가 클라우드 종속, 민감 데이터 외부 전송 | Self-hosted로 localhost에서 실행, API 키만 외부 통신 |

---

## 개요

AgentHub는 **MCP 서버**와 **A2A 에이전트**를 하나의 인터페이스로 통합 관리하는 시스템입니다.

```
┌─────────────────────────────────────────────────────────┐
│                    Chrome Extension                     │
│              (웹 페이지에서 프롬프트 입력)                 │
└──────────────────────────┬──────────────────────────────┘
                           ↓ HTTP REST + SSE
┌─────────────────────────────────────────────────────────┐
│                AgentHub API Server (ADK)                │
│                                                         │
│   ┌─────────────┐    ┌─────────────┐                    │
│   │   LlmAgent  │    │  동적 등록   │                    │
│   │  (Claude 등)│    │   관리자    │                    │
│   └──────┬──────┘    └─────────────┘                    │
│          ↓                                              │
│   ┌──────┴───────────────────────┐                      │
│   │         McpToolset           │                      │
│   │  (MCP 서버들을 도구로 사용)   │                      │
│   └──────────────────────────────┘                      │
└──────────────────────────┬──────────────────────────────┘
                           ↓
        ┌──────────────────┴──────────────────┐
        ↓                                      ↓
┌───────────────┐                    ┌───────────────┐
│  MCP Servers  │                    │  A2A Agents   │
│ (외부 도구들)  │                    │ (외부 에이전트)│
└───────────────┘                    └───────────────┘
```

### 핵심 기능

| 기능 | 설명 |
|------|------|
| **Chrome Extension** | 웹 페이지에서 직접 LLM과 대화 및 에이전트 호출 |
| **동적 등록** | UI에서 MCP 서버 / A2A 에이전트 URL 추가/제거 |
| **다중 LLM 지원** | Claude, GPT-4, Gemini 등 100+ LLM 지원 (LiteLLM) |
| **MCP + A2A 통합** | ADK의 McpToolset과 A2A 프로토콜 네이티브 지원 |

---

## 기술 스택

### 핵심 프레임워크

| 기술 | 버전 | 역할 |
|------|------|------|
| [Google ADK](https://google.github.io/adk-docs/) | 1.23.0+ | Agent 프레임워크 |
| [FastAPI](https://fastapi.tiangolo.com/) | - | API 서버 (ADK 내장) |
| [LiteLLM](https://docs.litellm.ai/) | - | 다중 LLM 통합 |
| Python | 3.10+ | 백엔드 런타임 |

### 의존성 관리 및 설정

| 기술 | 버전 | 역할 |
|------|------|------|
| [dependency-injector](https://python-dependency-injector.ets-labs.org/) | 4.48+ | DI 컨테이너 |
| [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | 2.12+ | 설정 관리 (환경변수 + YAML) |
| [PyYAML](https://pyyaml.org/) | - | YAML 파싱 |

### 저장소

| 유형 | 기술 | 용도 |
|------|------|------|
| 설정/등록 정보 | JSON 파일 | MCP/A2A 서버 목록, 사용자 설정 |
| 히스토리/로그 | SQLite | 대화 이력, 도구 호출 로그 |

### Extension 개발

| 기술 | 버전 | 역할 |
|------|------|------|
| [WXT](https://wxt.dev/) | 최신 | Extension 빌드 프레임워크 |
| TypeScript | 5.0+ | Extension 개발 언어 |
| React | 18+ | Extension UI (선택) |

### 테스트

| 기술 | 버전 | 역할 |
|------|------|------|
| [pytest](https://docs.pytest.org/) | 8.0+ | 테스트 프레임워크 |
| [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) | 1.3+ | 비동기 테스트 지원 |
| [pytest-cov](https://pytest-cov.readthedocs.io/) | - | 커버리지 측정 |

### 프로토콜

| 프로토콜 | 역할 | Transport |
|----------|------|-----------|
| [MCP](https://modelcontextprotocol.io/) | 에이전트 ↔ 도구 (수직 통합) | Streamable HTTP |
| [A2A](https://a2a-protocol.org/) | 에이전트 ↔ 에이전트 (수평 협업) | HTTP/JSON-RPC |

### Extension ↔ API 서버 통신

| 방식 | 용도 |
|------|------|
| **HTTP REST** | MCP/A2A 등록, 설정 변경 등 CRUD 작업 |
| **SSE (Server-Sent Events)** | LLM 응답 스트리밍, 실시간 상태 알림 |

---

## 개발 환경 설정

### 요구사항

- Python 3.10+
- Node.js 18+ (Extension 개발용)
- Git

### 설치

```bash
# 저장소 클론
git clone https://github.com/user/agenthub.git
cd agenthub

# Python 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Python 의존성 설치
pip install -e ".[dev]"

# Extension 의존성 설치
cd extension
npm install
```

### 환경변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 필수 환경변수
ANTHROPIC_API_KEY=your-api-key      # Claude 사용 시
OPENAI_API_KEY=your-api-key         # GPT-4 사용 시
GOOGLE_API_KEY=your-api-key         # Gemini 사용 시
```

---

## 설정 관리

AgentHub는 **pydantic-settings**를 사용하여 환경변수와 YAML 설정을 통합 관리합니다.

### 설정 파일 구조

```
configs/
├── default.yaml          # 기본 설정 (Git 추적)
├── development.yaml      # 개발 환경 설정
├── production.yaml       # 프로덕션 설정
└── .env.example          # 환경변수 템플릿
```

### 설정 우선순위

```
환경변수 > 환경별 YAML > default.yaml
```

### default.yaml 예시

```yaml
server:
  host: localhost
  port: 8000

llm:
  default_model: anthropic/claude-sonnet-4-20250514
  # api_key는 환경변수에서 로드 (ANTHROPIC_API_KEY)

mcp_servers: []   # 동적으로 등록

a2a_agents: []    # 동적으로 등록

storage:
  data_dir: ./data
  database: agenthub.db
```

### 설정 클래스 구조

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class LLMSettings(BaseSettings):
    default_model: str = "anthropic/claude-sonnet-4-20250514"
    api_key: str = Field(default="", env="ANTHROPIC_API_KEY")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        yaml_file="configs/default.yaml",
    )

    server: ServerSettings
    llm: LLMSettings
    storage: StorageSettings
```

---

## 의존성 주입 (DI)

AgentHub는 **dependency-injector**를 사용하여 서비스 의존성을 관리합니다.

### 컨테이너 구조

```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    # 설정
    config = providers.Configuration()

    # 저장소
    json_store = providers.Singleton(
        JsonStore,
        path=config.storage.data_dir,
    )

    sqlite_store = providers.Singleton(
        SqliteStore,
        db_path=config.storage.database,
    )

    # 서비스
    mcp_service = providers.Singleton(
        McpService,
        store=json_store,
    )

    agent_service = providers.Factory(
        AgentService,
        mcp_service=mcp_service,
        llm_config=config.llm,
    )
```

### FastAPI 통합

```python
from dependency_injector.wiring import Provide, inject
from fastapi import Depends

@router.post("/chat")
@inject
async def chat(
    request: ChatRequest,
    agent_service: AgentService = Depends(Provide[Container.agent_service]),
):
    return await agent_service.process(request)
```

---

## 저장소 구조

AgentHub는 하이브리드 저장소 전략을 사용합니다.

### JSON 파일 (설정/등록 정보)

```
data/
├── mcp_servers.json      # MCP 서버 등록 목록
├── a2a_agents.json       # A2A 에이전트 등록 목록
└── settings.json         # 사용자 설정
```

**mcp_servers.json 예시:**

```json
{
  "servers": [
    {
      "id": "example-server",
      "name": "Example MCP Server",
      "url": "https://example-server.modelcontextprotocol.io/mcp",
      "enabled": true,
      "registered_at": "2025-01-28T00:00:00Z"
    }
  ]
}
```

### SQLite (히스토리/로그)

```
data/
└── agenthub.db
    ├── conversations     # 대화 세션
    ├── messages          # 메시지 히스토리
    └── tool_calls        # 도구 호출 로그
```

**스키마 예시:**

```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT REFERENCES conversations(id),
    role TEXT NOT NULL,  -- 'user', 'assistant', 'tool'
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tool_calls (
    id TEXT PRIMARY KEY,
    message_id TEXT REFERENCES messages(id),
    tool_name TEXT NOT NULL,
    server_url TEXT,
    input JSON,
    output JSON,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Extension 개발

AgentHub Chrome Extension은 **WXT** 프레임워크를 사용합니다.

### WXT 선택 이유

| 특징 | 설명 |
|------|------|
| **Vite 기반** | 빠른 HMR, 현대적 개발 경험 |
| **TypeScript 우선** | 타입 안전성 보장 |
| **MV3 완벽 지원** | Chrome Manifest V3 네이티브 지원 |
| **자동 manifest 생성** | 파일 기반으로 manifest.json 자동 생성 |
| **다중 브라우저** | Chrome, Firefox, Safari 등 동시 지원 |

### Extension 프로젝트 구조

```
extension/
├── wxt.config.ts           # WXT 설정
├── package.json
├── tsconfig.json
│
├── entrypoints/            # WXT 엔트리포인트 (자동 감지)
│   ├── popup/              # 팝업 UI
│   │   ├── index.html
│   │   ├── main.tsx
│   │   └── App.tsx
│   │
│   ├── sidepanel/          # 사이드패널 (MV3)
│   │   ├── index.html
│   │   └── main.tsx
│   │
│   ├── background.ts       # 서비스 워커
│   │
│   └── content.ts          # 콘텐츠 스크립트
│
├── components/             # 공유 React 컴포넌트
├── lib/                    # 유틸리티, API 클라이언트
│   ├── api.ts              # REST API 클라이언트
│   └── sse.ts              # SSE 클라이언트
│
├── assets/                 # 아이콘, 이미지
└── public/                 # 정적 파일
```

### WXT 설정

```typescript
// wxt.config.ts
import { defineConfig } from 'wxt';

export default defineConfig({
  modules: ['@wxt-dev/module-react'],
  manifest: {
    name: 'AgentHub',
    permissions: ['activeTab', 'storage', 'sidePanel'],
    host_permissions: ['http://localhost:8000/*'],
  },
});
```

### API 통신: HTTP REST + SSE

```typescript
// lib/api.ts
const API_BASE = 'http://localhost:8000/api';

// REST API (CRUD 작업)
export async function registerMcpServer(url: string) {
  const response = await fetch(`${API_BASE}/mcp/servers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });
  return response.json();
}

// lib/sse.ts
// SSE (LLM 응답 스트리밍)
export function streamChat(prompt: string, onChunk: (chunk: string) => void) {
  const eventSource = new EventSource(
    `${API_BASE}/chat/stream?prompt=${encodeURIComponent(prompt)}`
  );

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onChunk(data.content);
  };

  eventSource.onerror = () => {
    eventSource.close();
  };

  return () => eventSource.close();
}
```

### 개발 명령어

```bash
cd extension

# 개발 모드 (HMR 활성화)
npm run dev

# Chrome용 빌드
npm run build

# Firefox용 빌드
npm run build:firefox

# 타입 체크
npm run typecheck
```

---

## 테스트 전략

AgentHub는 **TDD (Test-Driven Development)** 방식으로 개발합니다.

### TDD 사이클

```
1. RED    : 실패하는 테스트 먼저 작성
2. GREEN  : 테스트 통과하는 최소 코드 작성
3. REFACTOR : 코드 개선 (테스트는 계속 통과)
```

### 테스트 구조

```
tests/
├── conftest.py              # 공통 fixture
│
├── unit/                    # 단위 테스트 (Mock 사용)
│   ├── test_mcp_service.py
│   ├── test_a2a_service.py
│   └── test_agent_service.py
│
├── integration/             # 통합 테스트 (실제 연동)
│   ├── test_mcp_connection.py
│   ├── test_api_endpoints.py
│   └── test_storage.py
│
└── e2e/                     # E2E 테스트
    └── test_chat_flow.py
```

### pytest 설정

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --cov=src --cov-report=term-missing --cov-report=html"
markers = [
    "unit: 단위 테스트",
    "integration: 통합 테스트",
    "e2e: End-to-End 테스트",
]

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/__init__.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
]
```

### 테스트 예시

```python
# tests/unit/test_mcp_service.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_mcp_server_success():
    """MCP 서버 등록 시 도구 목록을 반환해야 함"""
    # Arrange
    service = McpService(store=AsyncMock())
    mock_tools = [{"name": "echo"}, {"name": "add"}]

    with patch.object(service, '_connect_to_server', return_value=mock_tools):
        # Act
        result = await service.register("https://example.com/mcp")

        # Assert
        assert result.success is True
        assert len(result.tools) == 2
        assert result.server_url == "https://example.com/mcp"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_mcp_server_invalid_url():
    """잘못된 URL로 등록 시 에러를 반환해야 함"""
    service = McpService(store=AsyncMock())

    with pytest.raises(InvalidUrlError):
        await service.register("not-a-valid-url")
```

### conftest.py (공통 Fixture)

```python
# tests/conftest.py
import pytest
from dependency_injector import providers

from src.container import Container

@pytest.fixture
def container():
    """테스트용 DI 컨테이너"""
    container = Container()
    container.config.from_dict({
        "storage": {"data_dir": ":memory:", "database": ":memory:"},
        "llm": {"default_model": "mock/model"},
    })
    return container

@pytest.fixture
def mock_mcp_service(container):
    """Mock MCP 서비스"""
    with container.mcp_service.override(providers.Object(AsyncMock())):
        yield container.mcp_service()
```

### 테스트 실행 명령어

```bash
# 전체 테스트 실행
pytest

# 단위 테스트만 실행
pytest -m unit

# 통합 테스트만 실행
pytest -m integration

# 특정 파일 테스트
pytest tests/unit/test_mcp_service.py

# 커버리지 리포트 생성
pytest --cov=src --cov-report=html
open htmlcov/index.html

# 실패 시 즉시 중단
pytest -x

# 변경된 파일만 테스트 (pytest-watch 필요)
ptw
```

### CI/CD 통합

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run tests
        run: pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

---

## ADK 코드 패턴

### 기본 구조

```python
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StreamableHTTPConnectionParams,
)
from google.adk.models.lite_llm import LiteLlm

# MCP 서버 연결 (Streamable HTTP)
mcp_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://example-server.modelcontextprotocol.io/mcp"
    ),
)

# 에이전트 정의
agent = LlmAgent(
    model=LiteLlm(model="anthropic/claude-sonnet-4-20250514"),
    name="agenthub-agent",
    instruction="You are a helpful assistant with access to various tools.",
    tools=[mcp_toolset],
)
```

### A2A 서버로 노출

```python
from google.adk.a2a.utils.agent_to_a2a import to_a2a

# ADK 에이전트를 A2A 서버로 변환
a2a_app = to_a2a(agent)

# 실행: uvicorn main:a2a_app --host 0.0.0.0 --port 8000
```

### LLM 모델 설정

```python
from google.adk.models.lite_llm import LiteLlm

# Claude (ANTHROPIC_API_KEY 환경변수 필요)
claude = LiteLlm(model="anthropic/claude-sonnet-4-20250514")

# GPT-4 (OPENAI_API_KEY 환경변수 필요)
gpt4 = LiteLlm(model="openai/gpt-4o")

# Gemini (기본 지원)
gemini = "gemini-2.5-flash"
```

> **주의**: Google 내장 도구 (SearchTool, CodeExecutionTool 등)는 **Gemini 모델에서만** 동작합니다. Claude, GPT-4 등 비-Gemini 모델 사용 시 내장 도구는 사용할 수 없습니다.

---

## 테스트 서버

### MCP 테스트 서버

| 항목 | 내용 |
|------|------|
| URL | `https://example-server.modelcontextprotocol.io/mcp` |
| 제공 도구 | echo, add, long-running operations 등 7개 |
| 인증 | OAuth 2.0 |
| 레포지토리 | [modelcontextprotocol/example-remote-server](https://github.com/modelcontextprotocol/example-remote-server) |

### A2A 테스트 에이전트

| 항목 | 내용 |
|------|------|
| 샘플 레포 | [a2aproject/a2a-samples](https://github.com/a2aproject/a2a-samples) |
| 언어 | Python |
| 용도 | 로컬에서 별도의 경로에 A2A 에이전트 실행하여 테스트 |

---

## 배포 방식

**Self-hosted** (사용자가 직접 서버 실행)

### 지원 플랫폼

| 플랫폼 | 패키지 형식 | 비고 |
|--------|------------|------|
| **Windows** | `.exe` | Windows 10/11 |
| **macOS** | `.dmg` | macOS 12+ (Intel/Apple Silicon) |

### 설치 및 실행

```
1. AgentHub 설치 (Windows: exe 설치 / macOS: dmg 설치)
2. AgentHub 실행 → localhost:8000에서 API 서버 자동 시작
3. Chrome Extension 설치 → localhost:8000에 연결
```

---

## 라이선스

[Apache 2.0](LICENSE)

---

## 참고 자료

### 공식 문서

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [ADK MCP Integration](https://google.github.io/adk-docs/tools-custom/mcp-tools/)
- [ADK A2A Integration](https://google.github.io/adk-docs/a2a/)
- [ADK LiteLLM Integration](https://google.github.io/adk-docs/agents/models/litellm/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [A2A Protocol](https://a2a-protocol.org/)

### 개발 도구

- [dependency-injector Documentation](https://python-dependency-injector.ets-labs.org/)
- [pydantic-settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [WXT Framework](https://wxt.dev/)
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)

### 패키지

- [google-adk (PyPI)](https://pypi.org/project/google-adk/)
- [LiteLLM Documentation](https://docs.litellm.ai/)
