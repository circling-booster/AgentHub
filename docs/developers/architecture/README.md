# Architecture

AgentHub 시스템 아키텍처 문서입니다.

---

## System Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Chrome Extension                          │
│            (Manifest V3 + Offscreen Document)                │
│   ┌────────────┬──────────────┬────────────────┐            │
│   │  Popup     │  Sidepanel   │  Background    │            │
│   └────────────┴──────────────┴────────────────┘            │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP REST + SSE
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   Inbound Adapters                           │
│        (FastAPI HTTP Routes, A2A Server)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │ Inbound Ports
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    Domain Layer                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  Services: OrchestratorService, ConversationService  │   │
│   └─────────────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  Entities: Conversation, Message, Agent, Tool, etc.  │   │
│   └─────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │ Outbound Ports
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   Outbound Adapters                          │
│   ┌─────────────┬─────────────┬─────────────┬──────────┐    │
│   │  ADK Agent  │  A2A Client │  Storage    │  OAuth   │    │
│   └─────────────┴─────────────┴─────────────┴──────────┘    │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        ↓                                      ↓
┌───────────────┐                    ┌───────────────┐
│  MCP Servers  │                    │  A2A Agents   │
│  (외부 도구)   │                    │  (외부 에이전트)│
└───────────────┘                    └───────────────┘
```

---

## Hexagonal Architecture (Ports & Adapters)

AgentHub는 **헥사고날 아키텍처**를 따릅니다. 핵심 원칙:

| Layer | 역할 | 의존성 규칙 |
|-------|------|-------------|
| **Domain** | 비즈니스 로직 | 외부 라이브러리 **금지** (순수 Python) |
| **Ports** | 인터페이스 정의 | Domain에 속함, 추상화만 |
| **Adapters** | 구현체 | Ports 구현, 외부 라이브러리 사용 가능 |

### Why Hexagonal?

- **테스트 용이성**: Domain을 Fake Adapter로 격리 테스트
- **유연성**: Adapter 교체로 외부 시스템 변경 대응
- **관심사 분리**: 비즈니스 로직과 인프라 분리

---

## Domain Model

### Entities

| Entity | 설명 | 파일 |
|--------|------|------|
| `Conversation` | 대화 세션 (Aggregate Root) | [conversation.py](../../../src/domain/entities/conversation.py) |
| `Message` | 개별 메시지 | [message.py](../../../src/domain/entities/message.py) |
| `Agent` | 에이전트 정보 | [agent.py](../../../src/domain/entities/agent.py) |
| `Tool` | 도구 정보 | [tool.py](../../../src/domain/entities/tool.py) |
| `Endpoint` | MCP/A2A 엔드포인트 | [endpoint.py](../../../src/domain/entities/endpoint.py) |
| `StreamChunk` | SSE 스트리밍 청크 | [stream_chunk.py](../../../src/domain/entities/stream_chunk.py) |
| `ToolCall` | 도구 호출 기록 | [tool_call.py](../../../src/domain/entities/tool_call.py) |
| `AuthConfig` | OAuth 설정 | [auth_config.py](../../../src/domain/entities/auth_config.py) |
| `CircuitBreaker` | 서킷 브레이커 상태 | [circuit_breaker.py](../../../src/domain/entities/circuit_breaker.py) |
| `Usage` | 사용량 추적 | [usage.py](../../../src/domain/entities/usage.py) |

### Ports

**Inbound Ports** (외부 → Domain):

| Port | 설명 | 파일 |
|------|------|------|
| `ChatPort` | 채팅 요청 처리 | [chat_port.py](../../../src/domain/ports/inbound/chat_port.py) |
| `ManagementPort` | 관리 API | [management_port.py](../../../src/domain/ports/inbound/management_port.py) |

**Outbound Ports** (Domain → 외부):

| Port | 설명 | 파일 |
|------|------|------|
| `OrchestratorPort` | LLM 오케스트레이션 | [orchestrator_port.py](../../../src/domain/ports/outbound/orchestrator_port.py) |
| `StoragePort` | 데이터 저장 | [storage_port.py](../../../src/domain/ports/outbound/storage_port.py) |
| `ToolsetPort` | 도구 관리 | [toolset_port.py](../../../src/domain/ports/outbound/toolset_port.py) |
| `A2APort` | A2A 클라이언트 | [a2a_port.py](../../../src/domain/ports/outbound/a2a_port.py) |
| `OAuthPort` | OAuth 인증 | [oauth_port.py](../../../src/domain/ports/outbound/oauth_port.py) |
| `UsagePort` | 사용량 저장 | [usage_port.py](../../../src/domain/ports/outbound/usage_port.py) |

---

## Chrome Extension Architecture

```
extension/
├── entrypoints/
│   ├── background.ts     # Service Worker (항상 실행)
│   ├── offscreen.ts      # Offscreen Document (SSE 처리)
│   ├── popup/            # Extension 아이콘 팝업
│   └── sidepanel/        # 사이드패널 UI (React)
└── lib/
    ├── api.ts            # REST API 클라이언트
    ├── sse.ts            # SSE 스트리밍 클라이언트
    └── types.ts          # TypeScript 타입 정의
```

### Component Responsibilities

| Component | 역할 | 특징 |
|-----------|------|------|
| **Background** | Service Worker | 토큰 관리, 메시지 라우팅 |
| **Offscreen** | SSE 처리 | Manifest V3 제약 우회 |
| **Sidepanel** | 메인 UI | React 기반 채팅 인터페이스 |
| **Popup** | 빠른 액세스 | 연결 상태 표시, Sidepanel 열기 |

---

## Data Flow: Chat Request

```
1. User types message in Sidepanel
         ↓
2. Sidepanel → Background (chrome.runtime.sendMessage)
         ↓
3. Background → Offscreen (message routing)
         ↓
4. Offscreen → POST /api/chat/stream (SSE)
         ↓
5. FastAPI HTTP Adapter receives request
         ↓
6. ChatPort → ConversationService
         ↓
7. ConversationService → OrchestratorPort
         ↓
8. ADK Adapter → LLM + MCP Tools
         ↓
9. SSE chunks streamed back
         ↓
10. Offscreen → Background → Sidepanel (UI update)
```

---

*Last Updated: 2026-02-05*
