# ADR-A07: Dual-Track Architecture (ADK + SDK)

## Status

Accepted

## Context

Plan 07에서 MCP 서버와 통합하면서 **MCP 프로토콜의 완전한 지원**을 위한 아키텍처를 결정해야 했습니다.

### MCP 프로토콜 범위

MCP는 다음 기능들을 제공합니다:

| 기능 | ADK 지원 | SDK 지원 |
|------|---------|---------|
| **Tools** (함수 호출) | ✅ DynamicToolset | ✅ SDK Client |
| **Resources** (데이터 제공) | ❌ | ✅ list_resources(), read_resource() |
| **Prompts** (템플릿) | ❌ | ✅ list_prompts(), get_prompt() |
| **Sampling** (LLM 요청) | ❌ | ✅ Callback 등록 |
| **Elicitation** (사용자 입력) | ❌ | ✅ Callback 등록 |

**문제점:**
- **ADK만 사용**: Tools만 지원, Resources/Prompts/Sampling/Elicitation 사용 불가
- **SDK만 사용**: 모든 기능 지원하지만, ADK Runner의 Tool Call Loop 자동화 포기

### 요구사항

1. **MCP 완전 지원**: Resources, Prompts, Sampling, Elicitation 모두 필요
2. **ADK Runner 활용**: 기존 Agent 인프라 (tool call loop, streaming) 유지
3. **코드 중복 최소화**: 두 개의 독립적인 시스템 관리 부담 최소화

## Decision

**Dual-Track Architecture를 채택합니다: 동일한 MCP 서버에 ADK(DynamicToolset)와 SDK(McpClientAdapter)를 이중 연결합니다.**

### 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    Chrome Extension                          │
│                                                               │
│  - Chat: ADK Runner (Tools via DynamicToolset)              │
│  - Resource Browser: SDK Track (list/read resources)        │
│  - Prompt Library: SDK Track (list/get prompts)            │
│  - HITL Approval: SDK Track (Sampling/Elicitation)          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
          ┌───────────────────────────────────┐
          │   AgentHub Backend (localhost)    │
          │                                    │
          │  ┌──────────────────────────────┐ │
          │  │  ADK Track (Tools Only)      │ │
          │  │  - DynamicToolset            │ │
          │  │  - ADK Runner                │ │
          │  │  - Tool Call Loop            │ │
          │  └──────────────────────────────┘ │
          │                                    │
          │  ┌──────────────────────────────┐ │
          │  │  SDK Track (Full Protocol)   │ │
          │  │  - McpClientAdapter          │ │
          │  │  - Resources, Prompts        │ │
          │  │  - Sampling, Elicitation     │ │
          │  └──────────────────────────────┘ │
          └───────────────────────────────────┘
                          │
                          ▼
          ┌───────────────────────────────────┐
          │  MCP Server (Streamable HTTP)     │
          │                                    │
          │  Connection 1: DynamicToolset     │
          │  Connection 2: McpClientAdapter   │
          └───────────────────────────────────┘
```

### 핵심 원리

1. **이중 연결**: 동일한 MCP 서버에 두 개의 클라이언트 연결
   - ADK DynamicToolset: Tools만 사용 (Agent Runner용)
   - SDK McpClientAdapter: Resources/Prompts/Sampling/Elicitation

2. **역할 분리**:
   - **Chat (Agent)**: ADK Runner + DynamicToolset → Tool Call Loop 자동화
   - **Resource Browser**: SDK Track → `list_resources()`, `read_resource()`
   - **HITL**: SDK Track → Sampling/Elicitation Callbacks

3. **리소스 최적화**:
   - MCP Streamable HTTP는 stateless → 두 연결이 독립적
   - 각 트랙은 필요한 기능만 초기화

## Consequences

### Positive

- **MCP 완전 지원**: Resources, Prompts, Sampling, Elicitation 모두 사용 가능
- **ADK 자동화 유지**: Tool Call Loop, Streaming 등 기존 인프라 활용
- **명확한 역할 분리**: Chat(ADK), Resources/HITL(SDK) 독립적 구현
- **점진적 마이그레이션**: ADK에 네이티브 지원 추가 시 SDK Track만 제거

### Negative

- **이중 연결 오버헤드**: MCP 서버에 두 개의 클라이언트 연결
  - **완화**: Streamable HTTP는 stateless이므로 오버헤드 낮음
  - **모니터링**: Connection pool, request count 추적 필요

- **구현 복잡도**: 두 개의 Adapter 유지보수
  - **완화**: 각 트랙의 역할이 명확하여 독립적 변경 가능

- **동기화 이슈 가능성**: Tools 목록이 ADK/SDK 간 불일치할 수 있음
  - **완화**: 동일한 MCP 서버를 참조하므로 실시간 동기화됨

### Neutral

- **ADK Native 지원 시**: SDK Track만 제거하고 ADK Track으로 통합 가능

## Alternatives Considered

### 1. ADK Only (Tools만 사용)

ADK DynamicToolset만 사용, SDK Track 없음

**장점:**
- 구현 간단
- 단일 연결

**단점:**
- **Resources/Prompts/Sampling/Elicitation 사용 불가**
- MCP 프로토콜의 핵심 기능 포기

**채택 안 한 이유:** 요구사항 불만족 (MCP 완전 지원 필요)

---

### 2. SDK Only (ADK 포기)

MCP SDK Client만 사용, ADK Runner 없음

**장점:**
- MCP 완전 지원
- 단일 클라이언트

**단점:**
- **ADK Runner 포기**: Tool Call Loop, Streaming 등 수동 구현 필요
- **기존 Agent 인프라 활용 불가**

**채택 안 한 이유:** ADK Runner의 자동화 이점 포기할 수 없음

---

### 3. Dual-Track Architecture (ADK + SDK) ✅

**채택됨** (위 Decision 섹션 참조)

---

### 4. Adapter Bridge (SDK → ADK 변환)

SDK로 모든 기능 가져온 후 ADK 형식으로 변환

**장점:**
- 단일 연결 (SDK만)

**단점:**
- **변환 레이어 복잡도**: Resources/Prompts를 Tools로 변환해야 함
- **ADK Runner와 맞지 않음**: Resources는 Tool이 아님

**채택 안 한 이유:** 변환 레이어가 불필요하게 복잡함

## Monitoring

이중 연결의 리소스 사용량을 모니터링합니다:

```python
# src/adapters/outbound/mcp/mcp_client_adapter.py
class McpClientAdapter:
    async def list_resources(self, endpoint_id: str):
        # Metrics 수집
        metrics.mcp_request_count.labels(
            endpoint=endpoint_id,
            track="sdk",
            method="list_resources"
        ).inc()
```

**알림 임계값:**
- Connection count per MCP server > 5: Warning
- Request rate > 100 req/s: Review

## References

- [Plan 07 README.md](../../planning/active/07_hybrid_dual/README.md) - Dual-Track 설명
- [Plan 07 Phase 4: Adapter Implementation](../../planning/active/07_hybrid_dual/04_adapter_implementation.md) - McpClientAdapter 구현
- [ADK Documentation](https://github.com/google/agent-development-kit) - DynamicToolset 사용법
- [MCP Specification](https://spec.modelcontextprotocol.io/) - Streamable HTTP Transport

---

*Created: 2026-02-06*
