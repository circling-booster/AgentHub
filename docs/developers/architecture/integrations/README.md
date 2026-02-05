# Integrations Architecture

외부 시스템 통합 아키텍처 문서입니다.

---

## Overview

AgentHub는 세 가지 외부 시스템과 통합됩니다:

```
┌─────────────────────────────────────────────────────────────┐
│                      AgentHub Core                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              OrchestratorService                       │  │
│  │         (Domain Layer - 순수 Python)                  │  │
│  └────────────────────────┬──────────────────────────────┘  │
│                           │ Outbound Ports                   │
│         ┌─────────────────┼─────────────────┐               │
│         ↓                 ↓                 ↓               │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐          │
│  │   LLM      │   │    MCP     │   │    A2A     │          │
│  │  Adapter   │   │  Adapter   │   │  Adapter   │          │
│  └─────┬──────┘   └─────┬──────┘   └─────┬──────┘          │
└────────┼────────────────┼────────────────┼──────────────────┘
         │                │                │
         ↓                ↓                ↓
   ┌──────────┐    ┌──────────┐    ┌──────────┐
   │   LLM    │    │   MCP    │    │   A2A    │
   │Providers │    │ Servers  │    │ Agents   │
   └──────────┘    └──────────┘    └──────────┘
```

---

## LLM Integration

### Architecture

```
OrchestratorPort (추상)
        │
        ↓
ADK Orchestrator Adapter
        │
        ├── LiteLLM (100+ LLM 지원)
        │       ├── OpenAI (GPT-4, GPT-4o)
        │       ├── Anthropic (Claude)
        │       ├── Google (Gemini)
        │       └── ... 기타 제공자
        │
        └── Google ADK LlmAgent
                └── 도구 호출, 멀티턴 대화 처리
```

### 구성 요소

| 구성 요소 | 역할 |
|-----------|------|
| **OrchestratorPort** | LLM 오케스트레이션 추상 인터페이스 |
| **ADK Adapter** | Google ADK LlmAgent 래핑 |
| **LiteLLM** | 다중 LLM Provider 통합 |
| **LlmAgent** | 도구 호출, 대화 흐름 관리 |

### Model 설정

LiteLLM 형식 사용:

```
openai/gpt-4o-mini      # OpenAI
anthropic/claude-3.5    # Anthropic
gemini/gemini-pro       # Google
```

---

## MCP Integration

### Architecture

```
ToolsetPort (추상)
        │
        ↓
DynamicToolset Adapter
        │
        ├── MCP Client (mcp 라이브러리)
        │       └── Streamable HTTP Transport
        │
        └── 도구 캐시 (로딩된 도구 관리)
                ├── list_tools()
                └── call_tool()

GatewayToolset (Phase 6)
        │
        ├── GatewayService (Circuit Breaker)
        └── Lazy Loading + Error Recovery
```

### 통합 흐름

```
1. 사용자가 MCP 서버 URL 등록
         ↓
2. DynamicToolset이 MCP Client 생성
         ↓
3. tools/list로 도구 목록 조회
         ↓
4. ADK Agent instruction에 도구 정보 주입
         ↓
5. LLM이 도구 호출 결정 시 tools/call 실행
```

### MCP Transport

| 프로토콜 | 설명 |
|----------|------|
| **Streamable HTTP** | HTTP 기반 양방향 통신 |
| **SSE** | 서버→클라이언트 스트리밍 |

### 인증 방식

| 방식 | 헤더 |
|------|------|
| **None** | 인증 없음 |
| **API Key** | `Authorization: Bearer {key}` |
| **OAuth 2.0** | `Authorization: Bearer {access_token}` |

---

## A2A Integration

### Dual Role Architecture

AgentHub는 A2A Client와 Server 모두 역할 수행:

```
┌─────────────────────────────────────────────────────────────┐
│                      AgentHub                                │
│                                                              │
│  ┌──────────────────┐       ┌──────────────────┐            │
│  │   A2A Client     │       │   A2A Server     │            │
│  │  (원격 호출)      │       │  (자신 노출)      │            │
│  └────────┬─────────┘       └────────┬─────────┘            │
└───────────┼──────────────────────────┼───────────────────────┘
            │                          │
            ↓                          ↓
    ┌───────────────┐          ┌───────────────┐
    │ External A2A  │          │ External A2A  │
    │   Agents      │          │   Clients     │
    └───────────────┘          └───────────────┘
```

### A2A Client

| 기능 | 설명 |
|------|------|
| **에이전트 발견** | `/.well-known/agent.json` 조회 |
| **Task 요청** | `tasks/send` 메시지 전송 |
| **결과 수신** | 동기/비동기 응답 처리 |

### A2A Server

| 기능 | 설명 |
|------|------|
| **Agent Card 제공** | 자신의 능력 광고 |
| **Task 수신** | 외부 요청 처리 |
| **결과 반환** | 처리 결과 응답 |

### Agent Card

```json
{
  "name": "AgentHub",
  "description": "MCP + A2A 통합 Agent",
  "url": "http://localhost:8000",
  "capabilities": {
    "tools": true,
    "streaming": true
  }
}
```

---

## Integration Sequence

### Chat with MCP Tools

```
User                Extension           AgentHub            MCP Server
  │                    │                   │                    │
  │─── 메시지 전송 ────▶│                   │                    │
  │                    │─── POST /chat ───▶│                    │
  │                    │                   │─── tools/list ────▶│
  │                    │                   │◀── 도구 목록 ───────│
  │                    │                   │                    │
  │                    │                   │── LLM 호출 ──▶     │
  │                    │                   │◀── tool_call ──    │
  │                    │                   │                    │
  │                    │                   │─── tools/call ────▶│
  │                    │                   │◀── 결과 ───────────│
  │                    │                   │                    │
  │                    │◀── SSE 스트림 ────│                    │
  │◀── UI 업데이트 ────│                   │                    │
```

### A2A Agent Delegation

```
User                AgentHub            External A2A
  │                    │                    │
  │── "번역해줘" ──────▶│                    │
  │                    │                    │
  │                    │─ tasks/send ──────▶│
  │                    │                    │
  │                    │◀─ 번역 결과 ────────│
  │                    │                    │
  │◀── 응답 ───────────│                    │
```

---

## Error Handling

### Circuit Breaker (Phase 6)

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ CLOSED  │────▶│  OPEN   │────▶│HALF_OPEN│
└─────────┘     └─────────┘     └─────────┘
     ▲               │               │
     └───────────────┴───────────────┘
```

| 상태 | 동작 |
|------|------|
| **CLOSED** | 정상 동작, 실패 카운트 |
| **OPEN** | 즉시 실패 반환 (서버 보호) |
| **HALF_OPEN** | 제한적 요청 허용, 복구 확인 |

### Retry Policy

| 설정 | 값 |
|------|-----|
| **최대 재시도** | 3회 |
| **지수 백오프** | 1s, 2s, 4s |
| **재시도 대상** | 일시적 네트워크 오류 |

---

*Last Updated: 2026-02-05*
