# Standards Integration Guide

외부 표준(MCP, A2A, ADK) 통합을 위한 가이드입니다.

---

## Standards Verification Protocol

MCP, A2A, ADK는 빠르게 진화하는 표준입니다. 구현 시 반드시 최신 스펙을 확인해야 합니다.

### Two-Phase Verification

```
┌──────────────────┐    ┌──────────────────────┐
│   Plan Phase     │    │ Implementation Phase │
│                  │    │                      │
│  아키텍처 설계     │ →  │  실제 코드 작성        │
│  API 구조 검토    │    │  메서드명/파라미터 확인  │
│                  │    │                      │
│  ↓ Web Search   │    │  ↓ Web Search        │
│  최신 스펙 확인   │    │  최신 스펙 재확인      │
└──────────────────┘    └──────────────────────┘
```

**중요:** Plan → Implementation 사이에 스펙이 변경될 수 있으므로 **양쪽 단계 모두**에서 검증 필요

---

## Supported Protocols

| 프로토콜 | 용도 | 현재 지원 |
|---------|------|----------|
| **MCP** | Model Context Protocol (도구 통합) | Streamable HTTP Transport |
| **A2A** | Agent-to-Agent (에이전트 간 통신) | JSON-RPC over HTTP |
| **ADK** | Google Agent Development Kit | v1.23.0+ |

---

## Protocol Versions

| 항목 | 버전/정보 |
|------|----------|
| MCP Transport | Streamable HTTP (구: stdio, SSE 대체) |
| A2A Spec | 2024 Draft |
| ADK Version | 1.23.0+ |
| LiteLLM | 100+ LLM Provider 지원 |

---

## Search Keywords

최신 스펙 검색 시 사용할 키워드:

| 프로토콜 | 검색 키워드 |
|---------|------------|
| MCP | `MCP Streamable HTTP`, `Model Context Protocol spec` |
| A2A | `A2A Protocol spec`, `Agent-to-Agent protocol` |
| ADK | `Google ADK Python`, `Agent Development Kit LiteLLM` |

---

## Folders

| 폴더 | 설명 |
|------|------|
| **mcp/** | MCP Streamable HTTP 구현 가이드 |
| **a2a/** | A2A Protocol 구현 가이드 |
| **adk/** | Google ADK 사용 가이드 |

---

*Last Updated: 2026-02-05*
