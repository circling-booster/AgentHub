# 아키텍처 결정 기록 (ADR)

> **목적**: 통합 호스트 아키텍처 결정 기록
> **상태**: ✅ 확정
> **확정일**: 2026-01-27
> **기반 기술**: Google ADK (Agent Development Kit)

---

## 최종 결정

### 확정 아키텍처: 하이브리드 레이어드 (시나리오 B+)

| 항목 | 결정 |
|------|------|
| 아키텍처 | 하이브리드 레이어드 (3계층) |
| 기반 프레임워크 | Google ADK v1.0.0+ |
| MCP 통합 | ADK MCPToolset (Streamable HTTP) |
| A2A 통합 | ADK to_a2a() |
| LLM | LiteLLM (Claude, GPT-4, Gemini 등 100+) |

### 확정 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                   사용자 인터페이스                           │
│            (Chrome Extension / Web UI / API)                │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│           Layer 1: Orchestration Layer (A2A)                │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  • Agent Registry (Agent Cards 관리)                 │   │
│   │  • Task Router (요청 분배)                           │   │
│   │  • A2A Protocol Handler (에이전트 간 통신)           │   │
│   └─────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│           Layer 2: Agent Logic Layer (ADK)                  │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│   │  음악 처리    │ │  문서 처리    │ │  유틸리티     │        │
│   │  Domain      │ │  Domain      │ │  Router      │        │
│   │  Agent       │ │  Agent       │ │  Agent       │        │
│   └──────┬───────┘ └──────┬───────┘ └──────┬───────┘        │
└──────────┼────────────────┼────────────────┼────────────────┘
           ↓                ↓                ↓
┌─────────────────────────────────────────────────────────────┐
│           Layer 3: Tool Access Layer (MCP)                  │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│   │  음원분리     │ │  OCR        │ │  캡차인식     │        │
│   │  MCP Server  │ │  MCP Server │ │  MCP Server  │        │
│   │  (Demucs)    │ │             │ │              │        │
│   └──────────────┘ └──────────────┘ └──────────────┘        │
│                    Transport: Streamable HTTP               │
└─────────────────────────────────────────────────────────────┘
```

---

## 결정 근거

### 프로젝트 조건

| 조건 | 값 | 영향 |
|------|-----|------|
| 타겟 사용자 | 개발자 + 일반사용자 | 확장성과 사용성 모두 필요 |
| Claude Desktop 호환 | **불필요** | 시나리오 A의 주요 장점 제거 |
| MCP Transport | Streamable HTTP | Cloud Run 등 서버리스 배포 가능 |

### 핵심 발견

업계 컨센서스는 "MCP vs A2A" 선택이 아닌 **"MCP + A2A" 조합**입니다.

```
A2A = 에이전트 간 수평 통신 (협업, 위임)
      ↓
MCP = 에이전트-도구 수직 통합 (능력, 접근)
```

> *"Together, ADK, MCP, and A2A form a layered architecture that powers intelligent, interoperable multi-agent systems."*
> — [Tietoevry](https://www.tietoevry.com/en/blog/2025/07/building-multi-agents-google-ai-services/)

---

## 시나리오 A 포기: Trade-offs

### 포기한 장점

| 항목 | 설명 | 영향도 |
|------|------|--------|
| **MCP 클라이언트 호환** | Claude Desktop, VS Code Copilot 등과 직접 연동 불가 | 낮음 (자체 UI 개발 예정) |
| **기존 MCP 호스트 코드 활용** | MetaMCP, MCPX 등 오픈소스 코드 직접 활용 불가 | 낮음 (ADK MCPToolset 대체) |
| **단일 진입점 단순성** | MCP 호스트 하나로 모든 것 관리 | 중간 (3계층으로 분리됨) |

### 수용한 단점

| 단점 | 설명 | 완화 방안 |
|------|------|-----------|
| **ADK 프레임워크 의존성** | Google ADK에 종속됨 | Apache 2.0 오픈소스, 커뮤니티 거버넌스 |
| **ADK 학습 곡선** | 새로운 프레임워크 학습 필요 | v1.0.0 안정 버전, 문서화 양호 |
| **MCP 직접 제어 제한** | MCPToolset 추상화로 세부 제어 복잡 | 필요시 MCP SDK 직접 사용 가능 |
| **LLM 불가지론 간접적** | ADK 기본은 Gemini | LiteLLM 통합으로 100+ LLM 지원 |

### 포기하지 않은 것

| 항목 | 설명 |
|------|------|
| MCP 서버 사용 | MCPToolset으로 기존 MCP 서버 그대로 사용 |
| 다양한 LLM | LiteLLM 통합으로 Claude, GPT-4 등 지원 |
| 확장성 | A2A 표준으로 에이전트 간 협업 |
| 업계 표준 정렬 | 150+ 기업이 지원하는 A2A 프로토콜 |

---

## 시나리오 비교 (참고용)

### 시나리오 A: MCP 호스트 중심 (미채택)

```
사용자 프롬프트
    ↓
MCP 호스트 (오케스트레이터)
    ├── MCP 서버 직접 호출
    └── A2A 에이전트 호출 (래퍼 통해)
            ↓
        A2A-to-MCP 래퍼 (직접 개발 필요)
```

**미채택 이유:**
- Claude Desktop 호환이 불필요하여 주요 장점 상실
- A2A → MCP 래퍼 직접 개발 필요 (비표준)
- 에이전트 간 수평 협업 패턴 부재
- 확장성 한계 (N² connectivity 문제)

**프로덕션 레퍼런스 (참고):**
- [MetaMCP](https://github.com/metatool-ai/metamcp)
- [MCPX](https://github.com/TheLunarCompany/mcpx)
- [mcp-agent](https://github.com/lastmile-ai/mcp-agent)

### 시나리오 B/B+: A2A/ADK 중심 (채택)

```
사용자 프롬프트
    ↓
A2A 클라이언트 (ADK 기반)
    ├── A2A 에이전트 호출 (표준)
    └── MCP 서버 호출 (MCPToolset)
```

**채택 이유:**
- ADK가 MCP 통합 기본 제공 (MCPToolset)
- A2A 표준으로 에이전트 간 협업
- 150+ 기업 지원, 업계 표준 정렬
- ADK v1.0.0 안정 버전 (프로덕션 준비)

**프로덕션 레퍼런스:**
- Google Agent Engine, Cloud Run
- Microsoft Azure AI Foundry
- SAP Joule
- [Tietoevry 사례](https://www.tietoevry.com/en/blog/2025/07/building-multi-agents-google-ai-services/)

---

## 비교 요약

| 기준 | 시나리오 A | 시나리오 B+ (채택) |
|------|-----------|-------------------|
| 오케스트레이터 | MCP 호스트 | A2A + 명시적 계층 |
| MCP 통합 | 직접 | ADK MCPToolset |
| A2A 통합 | 래퍼 필요 | 기본 지원 |
| Claude Desktop 호환 | O | X |
| 장기 실행 태스크 | 추가 구현 | 기본 지원 |
| 에이전트 협업 | 호스트 경유 | 직접 통신 |
| 확장성 | 낮음 | 높음 |
| 업계 정렬 | 낮음 | 높음 |

---

## 구현 예시

### 기본 구현 (Phase 1 - PoC)

```python
from google.adk import Agent
from google.adk.tools import MCPToolset, SseServerParams
from google.adk.models.lite_llm import LiteLlm
from google.adk.a2a import to_a2a

# Layer 3: MCP Tool Access
audio_mcp = MCPToolset.from_server(
    "audio-separation",
    SseServerParams(url="http://localhost:8001/sse")
)

# Layer 2: Agent Logic
agent = Agent(
    name="fhly-agent",
    model=LiteLlm(model="anthropic/claude-sonnet-4-20250514"),
    tools=[audio_mcp],
    description="FHLY unified agent for audio processing"
)

# Layer 1: A2A Orchestration
a2a_app = to_a2a(agent)
```

### 확장 구현 (Phase 2+)

```python
# 도메인별 에이전트 분리
music_agent = Agent(
    name="music-agent",
    tools=[audio_mcp_tools],
    description="Handles audio separation and music processing"
)

document_agent = Agent(
    name="document-agent",
    tools=[ocr_mcp_tools],
    description="Handles OCR and document processing"
)

# 오케스트레이터
orchestrator = Agent(
    name="fhly-orchestrator",
    description="Routes tasks to appropriate domain agents",
    sub_agents=[music_agent, document_agent, utility_agent]
)
```

---

## 진화 경로

```
Phase 1 (PoC): 단일 에이전트 + 기존 MCP 서버 1개 연결
    ↓
Phase 2 (확장): 도메인 에이전트 분리 (음악, 문서, 유틸리티)
    ↓
Phase 3 (대규모): 오케스트레이터 분리, Chrome Extension 통합
```

---

## 참고 자료

### 공식 문서
- [Google ADK 문서](https://google.github.io/adk-docs/)
- [ADK MCP 통합](https://google.github.io/adk-docs/mcp/)
- [A2A Protocol](https://github.com/a2aproject/A2A)
- [MCP 명세](https://modelcontextprotocol.io/)

### 업계 분석
- [MCP vs A2A Guide - Auth0](https://auth0.com/blog/mcp-vs-a2a/)
- [Multi-Agent Systems with ADK - Tietoevry](https://www.tietoevry.com/en/blog/2025/07/building-multi-agents-google-ai-services/)
- [A2A MCP Orchestration - Iguazio](https://www.iguazio.com/blog/orchestrating-multi-agent-workflows-with-mcp-a2a/)

### 학술 연구
- [MCP × A2A Framework](https://arxiv.org/pdf/2506.01804)
- [AgentMaster Framework](https://arxiv.org/html/2507.21105v1)
- [Agent Interoperability Protocols Survey](https://arxiv.org/html/2505.02279v1)
