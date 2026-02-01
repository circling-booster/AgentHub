# AgentHub 아키텍처

> 헥사고날 아키텍처 (Hexagonal / Ports and Adapters) 기반 설계

**최종 수정일:** 2026-01-28

---

## 개요

AgentHub는 **헥사고날 아키텍처**를 채택합니다. 외부 시스템(MCP, A2A, 다양한 LLM)과의 연동이 핵심인 이 프로젝트에서 유연성과 테스트 용이성을 확보하기 위한 선택입니다.

### 왜 헥사고날 아키텍처인가?

| 특성 | AgentHub 요구사항 | 헥사고날 해결책 |
|------|-------------------|-----------------|
| **다양한 외부 시스템** | MCP, A2A, LiteLLM (100+ LLM) | 각 시스템을 Adapter로 격리 |
| **프로토콜 진화** | MCP/A2A 표준이 빠르게 변화 | Adapter만 수정, 도메인 불변 |
| **LLM 교체 용이성** | Claude ↔ GPT-4 ↔ Gemini 전환 | LLM Adapter만 교체 |
| **테스트 용이성** | 외부 서버 없이 단위 테스트 | Fake Adapter로 도메인 테스트 |

---

## 핵심 구조

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Adapters (외부)                                 │
│                                                                         │
│   ┌───────────────────────┐           ┌───────────────────────────┐    │
│   │    Inbound Adapters   │           │    Outbound Adapters      │    │
│   │                       │           │                           │    │
│   │  - HTTP API (FastAPI) │           │  - ADK Orchestrator       │    │
│   │  - A2A Server         │           │  - DynamicToolset         │    │
│   │                       │           │  - A2A Client             │    │
│   │                       │           │  - Storage (JSON/SQLite)  │    │
│   └───────────┬───────────┘           └─────────────▲─────────────┘    │
│               │                                     │                   │
│   ┌───────────┼─────────────────────────────────────┼───────────────┐  │
│   │           │           Ports (인터페이스)         │               │  │
│   │   ┌───────▼───────┐                 ┌───────────┴───────┐       │  │
│   │   │ Inbound Ports │                 │  Outbound Ports   │       │  │
│   │   │ - ChatPort    │                 │  - OrchestratorPort│      │  │
│   │   │ - MgmtPort    │                 │  - A2aPort        │       │  │
│   │   └───────┬───────┘                 │  - StoragePort    │       │  │
│   │           │                         └───────────▲───────┘       │  │
│   └───────────┼─────────────────────────────────────┼───────────────┘  │
│               │                                     │                   │
│   ┌───────────▼─────────────────────────────────────┴───────────────┐  │
│   │                     Domain (핵심 비즈니스 로직)                   │  │
│   │                                                                  │  │
│   │   Entities: Agent, Tool, Endpoint, Conversation                 │  │
│   │   Services: OrchestratorService, RegistryService,               │  │
│   │             ConversationService, HealthMonitorService           │  │
│   │                                                                  │  │
│   │              ★ 외부 의존성 없음 - 순수 Python ★                   │  │
│   └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **의존성 역전** | 도메인 로직이 외부 시스템을 모름. 어댑터가 도메인에 의존 |
| **포트 추상화** | 인터페이스(Port)를 통해 외부 시스템과 통신 |
| **어댑터 교체** | 포트 구현체(Adapter)만 교체하면 외부 시스템 변경 가능 |

---

## 디렉토리 구조

```
src/
├── domain/                   # 핵심 비즈니스 로직 (순수 Python)
│   ├── entities/             # 도메인 엔티티
│   │   ├── agent.py          # Agent 모델
│   │   ├── tool.py           # Tool (MCP 도구) 모델
│   │   ├── endpoint.py       # MCP/A2A 엔드포인트 모델
│   │   └── conversation.py   # 대화 세션/메시지 모델
│   │
│   ├── services/             # 도메인 서비스 (비즈니스 로직)
│   │   ├── orchestrator.py   # 에이전트 오케스트레이션
│   │   ├── registry.py       # 엔드포인트 등록 관리
│   │   ├── conversation.py   # 대화 처리 로직
│   │   └── health_monitor.py # 상태 모니터링
│   │
│   ├── ports/                # 포트 (인터페이스 정의)
│   │   ├── inbound/          # Driving Ports (외부 → 도메인)
│   │   │   ├── chat_port.py
│   │   │   └── management_port.py
│   │   └── outbound/         # Driven Ports (도메인 → 외부)
│   │       ├── orchestrator_port.py
│   │       ├── a2a_port.py
│   │       └── storage_port.py
│   │
│   └── exceptions.py         # 도메인 예외
│
├── adapters/                 # 어댑터 (포트 구현체)
│   ├── inbound/              # Primary Adapters (입력 처리)
│   │   ├── http/             # FastAPI HTTP API
│   │   │   ├── app.py        # FastAPI 앱 팩토리
│   │   │   ├── routes/       # 라우트 (chat, mcp, a2a, health)
│   │   │   ├── schemas/      # Pydantic 요청/응답 모델
│   │   │   └── exceptions.py # HTTP 예외 핸들러
│   │   └── a2a_server/       # A2A 서버 (ADK to_a2a)
│   │
│   └── outbound/             # Secondary Adapters (외부 연동)
│       ├── adk/              # Google ADK 어댑터
│       │   ├── dynamic_toolset.py     # DynamicToolset (BaseToolset 상속)
│       │   └── orchestrator_adapter.py
│       ├── a2a_client/       # A2A 클라이언트 (JSON-RPC 2.0)
│       └── storage/          # 저장소 어댑터
│           ├── json_storage.py       # JSON 파일 (설정)
│           └── sqlite_storage.py     # SQLite (대화 이력)
│
└── config/                   # 설정 및 의존성 주입
    ├── container.py          # DI 컨테이너 (dependency-injector)
    └── settings.py           # 환경설정 (pydantic-settings + YAML)
```

---

## 레이어별 역할

### 1. Domain Layer (핵심 비즈니스 로직)

**외부 의존성 없는 순수 Python 코드**. Google ADK, FastAPI, SQLite 등 어떤 라이브러리도 import하지 않습니다.

| 컴포넌트 | 역할 |
|---------|------|
| **Entities** | 비즈니스 개념 모델링 (Endpoint, Tool, Conversation 등) |
| **Services** | 비즈니스 로직 (OrchestratorService, RegistryService 등) |
| **Ports** | 외부 시스템과의 계약 정의 (추상 인터페이스) |
| **Exceptions** | 도메인 예외 (EndpointNotFoundError 등) |

### 2. Adapters Layer (외부 연동)

Port 인터페이스를 **구현**하여 실제 외부 시스템과 연동합니다.

| 어댑터 | 역할 |
|--------|------|
| **HTTP API** | FastAPI 라우트, SSE 스트리밍 |
| **ADK Orchestrator** | LlmAgent, DynamicToolset |
| **A2A Client** | JSON-RPC 2.0 통신 |
| **Storage** | JSON 파일, SQLite (WAL 모드) |

### 3. Config Layer (설정)

| 컴포넌트 | 역할 | 구현 상태 |
|---------|------|:--------:|
| **Settings** | pydantic-settings (환경변수 > .env > 기본값) | ✅ `src/config/settings.py` |
| **Container** | dependency-injector `DeclarativeContainer` (Singleton providers) | ✅ `src/config/container.py` |

**설정 우선순위:** 환경변수 > `.env` > 기본값 (YAML은 Phase 2에서 추가 예정)

---

## 데이터 흐름

### 채팅 요청 흐름

```
1. Extension → POST /api/chat/stream
2. HTTP Adapter → OrchestratorService.chat()
3. OrchestratorService → ConversationService.send_message()
4. ConversationService → OrchestratorPort.process_message()
5. AdkOrchestratorAdapter → LlmAgent.run_async()
6. LlmAgent → DynamicToolset.get_tools() (도구 목록)
7. LlmAgent → MCP 서버 (도구 실행)
8. Response streaming → Extension
```

### MCP 서버 등록 흐름

```
1. Extension → POST /api/mcp/servers
2. HTTP Adapter → RegistryService.register_mcp()
3. RegistryService → DynamicToolset.add_mcp_server()
4. DynamicToolset → MCPToolset (연결 + 도구 조회)
5. RegistryService → EndpointStorage.save_endpoint()
6. Response → Extension
```

---

## Extension ↔ API 통신

| 방식 | 용도 | 예시 |
|------|------|------|
| **HTTP REST** | CRUD 작업 | MCP 서버 등록/해제, 설정 변경 |
| **SSE (POST)** | 실시간 스트리밍 | LLM 응답 스트리밍 |

> **중요**: Extension은 Offscreen Document를 통해 장시간 SSE 요청을 처리합니다. 자세한 내용은 [extension-guide.md](extension-guide.md) 참조.

---

## 테스트 전략

헥사고날 아키텍처의 핵심 장점: **도메인 로직을 Mocking 없이 테스트**할 수 있습니다.

| 테스트 유형 | 범위 | 방법 |
|------------|------|------|
| **Unit** | 도메인 서비스 | Fake Adapter 사용 |
| **Integration** | 어댑터 | 실제 연결 (테스트 서버) |
| **E2E** | 전체 흐름 | Extension + Server |

---

## 관련 문서

- [implementation-guide.md](implementation-guide.md) - 구현 패턴 및 코드 예시
- [extension-guide.md](extension-guide.md) - Chrome Extension 개발 가이드
- [feasibility-analysis-2026-01.md](feasibility-analysis-2026-01.md) - 기술 스택 분석

---

*문서 생성일: 2026-01-28*
