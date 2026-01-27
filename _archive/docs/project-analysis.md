# FHLY 프로젝트 종합 분석

> **작성일**: 2026-01-27
> **목적**: 프로젝트 검토, Google ADK 스펙 정리, 구현 가이드

---

## 1. 프로젝트 검토 결과

### 1.1 발견된 문제점

#### 코드 예제의 import 구조 오류

현재 문서의 코드 예제가 실제 ADK API와 일치하지 않습니다.

| 항목 | 현재 문서 (오류) | 실제 ADK API |
|------|------------------|--------------|
| Agent 클래스 | `from google.adk import Agent` | `from google.adk.agents import LlmAgent` |
| MCPToolset | `from google.adk.tools import MCPToolset` | `from google.adk.tools.mcp_tool import McpToolset` |
| Connection Params | `SseServerParams` | `StreamableHTTPConnectionParams`, `SseConnectionParams` |
| LiteLLM | `from google.adk.models.lite_llm import LiteLlm` | `from google.adk.models.lite_llm import LiteLlm` (정확) |
| to_a2a | `from google.adk.a2a import to_a2a` | `from google.adk.a2a.utils.agent_to_a2a import to_a2a` |

#### Transport 방식 변경

MCP 프로토콜이 2025-03-26 버전에서 **SSE를 Streamable HTTP로 대체**했습니다.

```
❌ 문서: "Transport: Streamable HTTP" (명칭은 맞지만 SseServerParams 사용)
✅ 실제: StreamableHTTPConnectionParams 사용 필요
```

#### 버전 정보 불일치

- [architecture-scenarios.md](architecture-scenarios.md): "v1.0.0+"
- [architecture-research.md](architecture-research.md): "최신 버전 1.23.0 (2026년 1월 22일)"
- **권장**: 구체적 버전(1.23.0+)으로 통일

### 1.2 누락된 정보

| 항목 | 상태 | 필요성 |
|------|------|--------|
| 기존 MCP 서버 위치/코드 | 언급만 있음 | 높음 - Phase 1에서 연결 필요 |
| 프로젝트 디렉토리 구조 | 없음 | 높음 - 구현 시작 전 필요 |
| 환경 설정 가이드 | 없음 | 높음 - API 키, 환경변수 등 |
| 테스트 전략 | 없음 | 중간 - Phase 1 완료 전 필요 |
| 에러 처리 패턴 | 없음 | 중간 |

### 1.3 모호한 부분

1. **"기존 MCP 서버(음원분리, OCR, 캡차) 구축 완료"**
   - 이 서버들이 어디에 있는가? (별도 레포? 로컬?)
   - 어떤 Transport를 사용하는가?
   - 현재 실행 가능한 상태인가?

2. **"핵심 문제 정의" 미완료**
   - Phase 0에서 미완료로 남겨둠
   - 프로젝트 방향성에 영향

3. **Chrome Extension 구체적 범위**
   - UI 주입의 구체적 형태?
   - 어떤 페이지에서 동작?

### 1.4 모순된 부분

| 모순 | 문서 A | 문서 B |
|------|--------|--------|
| ADK 버전 | "v1.0.0+" (scenarios) | "1.23.0" (research) |
| 없음 | - | - |

**결론**: 큰 모순은 없으나, 코드 예제 정확성 문제가 가장 심각

---

## 2. Google ADK (Agent Development Kit) 스펙 정리

### 2.1 개요

| 항목 | 내용 |
|------|------|
| 정의 | AI 에이전트 구축을 위한 오픈소스 Python 프레임워크 |
| 개발사 | Google |
| 라이선스 | Apache 2.0 |
| 최신 버전 | **1.23.0** (2026-01-22) |
| Python 요구사항 | ≥ 3.10 |
| 릴리스 주기 | 약 2주 |

### 2.2 설치

```bash
# 가상환경 생성 및 활성화
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Mac / Linux
source .venv/bin/activate

# ADK 설치
pip install google-adk

# 개발 버전 (최신 기능 필요 시)
pip install git+https://github.com/google/adk-python.git@main
```

### 2.3 핵심 컴포넌트

#### LlmAgent

```python
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

agent = LlmAgent(
    model=LiteLlm(model="anthropic/claude-sonnet-4-20250514"),
    name="my-agent",
    instruction="You are a helpful assistant.",
    tools=[...],           # 도구 목록
    sub_agents=[...],      # 하위 에이전트 (멀티 에이전트)
)
```

#### McpToolset (MCP 서버 연결)

```python
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StreamableHTTPConnectionParams,
    SseConnectionParams,
    StdioConnectionParams,
)
from mcp import StdioServerParameters

# 1. Streamable HTTP (권장 - 프로덕션)
http_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8001/mcp",
        headers={"Authorization": "Bearer token"}  # 선택적
    ),
    tool_filter=['tool1', 'tool2']  # 선택적 - 특정 도구만 사용
)

# 2. SSE (레거시)
sse_toolset = McpToolset(
    connection_params=SseConnectionParams(
        url="http://localhost:8001/sse"
    ),
)

# 3. Stdio (로컬 프로세스)
stdio_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='python',
            args=['mcp_server.py'],
            env={"API_KEY": "..."}
        ),
    ),
)
```

#### to_a2a (A2A 서버 노출)

```python
from google.adk.a2a.utils.agent_to_a2a import to_a2a

# ADK 에이전트를 A2A 서버로 변환
a2a_app = to_a2a(root_agent)

# uvicorn으로 실행
# uvicorn main:a2a_app --host 0.0.0.0 --port 8000
```

### 2.4 LiteLLM 통합 (다중 LLM 지원)

```python
from google.adk.models.lite_llm import LiteLlm

# Claude (ANTHROPIC_API_KEY 환경변수 필요)
claude_model = LiteLlm(model="anthropic/claude-sonnet-4-20250514")

# GPT-4 (OPENAI_API_KEY 환경변수 필요)
gpt_model = LiteLlm(model="openai/gpt-4o")

# Gemini (기본 - GOOGLE_API_KEY 또는 Vertex AI)
gemini_model = "gemini-2.5-flash"
```

**주의사항**:
- Google 내장 도구(SearchTool 등)는 Gemini에서만 동작
- YAML 설정에서는 아직 비-Gemini 모델 미지원

### 2.5 멀티 에이전트 구조

```python
# 하위 에이전트 정의
music_agent = LlmAgent(
    name="music-agent",
    tools=[audio_mcp],
    instruction="Handle audio processing tasks"
)

document_agent = LlmAgent(
    name="document-agent",
    tools=[ocr_mcp],
    instruction="Handle document processing tasks"
)

# 오케스트레이터
orchestrator = LlmAgent(
    name="orchestrator",
    instruction="Route tasks to appropriate sub-agents",
    sub_agents=[music_agent, document_agent]
)
```

---

## 3. MCP (Model Context Protocol) 활용

### 3.1 프로젝트에서의 역할

```
┌─────────────────────────────────────────┐
│        Layer 3: Tool Access (MCP)       │
│                                         │
│  ADK Agent                              │
│      ↓ McpToolset                       │
│  MCP Server (음원분리/OCR/캡차)          │
│      ↓ Tool 실행                        │
│  결과 반환                               │
└─────────────────────────────────────────┘
```

### 3.2 MCP 서버 구성 (FHLY 기존 자산)

| MCP 서버 | 기능 | 기술 | Transport |
|----------|------|------|-----------|
| 음원분리 | 보컬/악기 분리 | Demucs | Streamable HTTP |
| OCR | 이미지→텍스트 | - | Streamable HTTP |
| 캡차인식 | 캡차 자동 인식 | - | Streamable HTTP |

### 3.3 MCP 최신 동향 (2026년 1월)

| 항목 | 내용 |
|------|------|
| 최신 스펙 버전 | 2025-03-26 |
| Transport 표준 | **Streamable HTTP** (SSE 대체) |
| 인증 | OAuth 2.1 기반 |
| Python SDK | v1.x 안정, v2 Q1 2026 예정 |
| 관리 | Linux Foundation AAIF |

**Streamable HTTP 이점**:
- AWS ALB, Cloudflare 호환
- 양방향 스트리밍 (SSE는 단방향)
- 프록시 친화적

**새 기능 (2026)**:
- Tool Annotations: 도구 동작 설명 (read-only, destructive 등)
- MCP Apps: 대화형 UI 컴포넌트 반환 가능

### 3.4 ADK에서 MCP 사용 패턴

```python
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.models.lite_llm import LiteLlm

# MCP 서버 연결
audio_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8001/mcp"
    ),
)

# 에이전트에 도구로 등록
agent = LlmAgent(
    model=LiteLlm(model="anthropic/claude-sonnet-4-20250514"),
    name="fhly-agent",
    instruction="FHLY unified agent for processing tasks",
    tools=[audio_mcp],
)
```

---

## 4. A2A (Agent-to-Agent Protocol) 활용

### 4.1 프로젝트에서의 역할

```
┌─────────────────────────────────────────┐
│     Layer 1: Orchestration (A2A)        │
│                                         │
│  외부 A2A 클라이언트/에이전트            │
│      ↓ A2A Protocol                     │
│  FHLY A2A Server (to_a2a로 노출)        │
│      ↓ 내부 라우팅                       │
│  도메인 에이전트들                        │
└─────────────────────────────────────────┘
```

### 4.2 A2A 최신 동향 (2026년 1월)

| 항목 | 내용 |
|------|------|
| 최신 버전 | **v0.3** (2025년 7월) |
| 관리 | Linux Foundation |
| 지원사 | 150+ (Google, Microsoft, SAP, Salesforce 등) |
| ADK 통합 | 네이티브 지원 |

**v0.3 주요 기능**:
- gRPC 지원
- 보안 카드 서명
- Python SDK 확장
- Stateless 상호작용 지원

### 4.3 A2A vs MCP 역할 분담

```
A2A = 에이전트 ↔ 에이전트 (수평 협업)
      - 태스크 위임
      - 에이전트 발견 (Agent Cards)
      - 장기 실행 태스크

MCP = 에이전트 ↔ 도구 (수직 통합)
      - 외부 API 호출
      - 데이터 소스 접근
      - 도구 실행
```

### 4.4 ADK에서 A2A 사용 패턴

```python
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

# 에이전트 정의
root_agent = LlmAgent(
    name="fhly-agent",
    model=LiteLlm(model="anthropic/claude-sonnet-4-20250514"),
    instruction="FHLY unified agent",
    tools=[...],
)

# A2A 서버로 변환 (Agent Card 자동 생성)
a2a_app = to_a2a(root_agent)

# 실행: uvicorn main:a2a_app --host 0.0.0.0 --port 8000
```

---

## 5. 권장 프로젝트 구조

### 5.1 디렉토리 구조 제안

```
FHLY/
├── src/
│   ├── fhly/
│   │   ├── __init__.py
│   │   ├── main.py              # 진입점
│   │   ├── config.py            # 설정 관리
│   │   │
│   │   ├── agents/              # Layer 2: Agent Logic
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py  # 오케스트레이터
│   │   │   ├── music_agent.py   # 음악 처리 에이전트
│   │   │   ├── document_agent.py# 문서 처리 에이전트
│   │   │   └── utility_agent.py # 유틸리티 라우터
│   │   │
│   │   ├── tools/               # Layer 3: MCP 연결
│   │   │   ├── __init__.py
│   │   │   ├── mcp_config.py    # MCP 서버 설정
│   │   │   ├── audio_tools.py   # 음원분리 MCP
│   │   │   ├── ocr_tools.py     # OCR MCP
│   │   │   └── captcha_tools.py # 캡차 MCP
│   │   │
│   │   └── a2a/                 # Layer 1: A2A 노출
│   │       ├── __init__.py
│   │       └── server.py        # A2A 서버 설정
│   │
│   └── mcp_servers/             # MCP 서버들 (별도 프로세스)
│       ├── audio_separation/
│       │   ├── __init__.py
│       │   └── server.py
│       ├── ocr/
│       └── captcha/
│
├── tests/
│   ├── test_agents/
│   ├── test_tools/
│   └── test_integration/
│
├── docs/                        # 문서
│   ├── architecture-scenarios.md
│   ├── architecture-research.md
│   ├── roadmap.md
│   ├── project-analysis.md     # 이 파일
│   └── archived-ideas.md
│
├── .env.example                 # 환경변수 템플릿
├── pyproject.toml              # 프로젝트 메타데이터
├── requirements.txt            # 또는 poetry.lock
├── CLAUDE.md
└── README.md
```

### 5.2 핵심 파일 설명

| 파일 | 역할 | Phase |
|------|------|-------|
| `main.py` | 애플리케이션 진입점 | Phase 1 |
| `config.py` | 환경변수, API 키 관리 | Phase 1 |
| `agents/orchestrator.py` | 요청 라우팅 | Phase 2 |
| `tools/mcp_config.py` | MCP 서버 URL/설정 | Phase 1 |
| `a2a/server.py` | A2A 서버 노출 | Phase 1+ |

### 5.3 Phase 1 최소 구현 파일

```
src/fhly/
├── __init__.py
├── main.py           # 단일 에이전트 + 음원분리 MCP
├── config.py         # 환경변수 로드
└── tools/
    ├── __init__.py
    └── audio_tools.py  # 음원분리 MCP 연결
```

---

## 6. 수정이 필요한 문서 항목

### 6.1 README.md

| 위치 | 현재 | 수정 |
|------|------|------|
| 구현 예시 import | `from google.adk import Agent` | `from google.adk.agents import LlmAgent` |
| MCPToolset import | `from google.adk.tools import MCPToolset, SseServerParams` | `from google.adk.tools.mcp_tool import McpToolset` |
| Connection params | `SseServerParams(url=...)` | `StreamableHTTPConnectionParams(url=...)` |

### 6.2 architecture-scenarios.md

동일한 코드 예제 수정 필요

### 6.3 추가 필요 문서

- `docs/setup-guide.md`: 환경 설정 가이드
- `docs/mcp-servers.md`: 기존 MCP 서버 위치/실행 방법
- `.env.example`: 환경변수 템플릿

---

## 7. 참고 자료

### 공식 문서
- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [ADK MCP Integration](https://google.github.io/adk-docs/tools-custom/mcp-tools/)
- [ADK A2A Integration](https://google.github.io/adk-docs/a2a/)
- [ADK LiteLLM Integration](https://google.github.io/adk-docs/agents/models/litellm/)
- [MCP Specification](https://modelcontextprotocol.io/specification/2025-11-25)
- [A2A Protocol](https://a2a-protocol.org/latest/)

### GitHub
- [google/adk-python](https://github.com/google/adk-python)
- [a2aproject/A2A](https://github.com/a2aproject/A2A)
- [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)

### PyPI
- [google-adk](https://pypi.org/project/google-adk/)

### 튜토리얼
- [Google Codelabs: MCP, ADK, A2A](https://codelabs.developers.google.com/codelabs/currency-agent)
- [LiteLLM + ADK Tutorial](https://docs.litellm.ai/docs/tutorials/google_adk)

### 업계 분석
- [MCP Transport Future](http://blog.modelcontextprotocol.io/posts/2025-12-19-mcp-transport-future/)
- [A2A Protocol Upgrade](https://cloud.google.com/blog/products/ai-machine-learning/agent2agent-protocol-is-getting-an-upgrade)
