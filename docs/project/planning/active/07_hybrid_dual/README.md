# Architecture C "Hybrid-Dual" Implementation Plan

## Overview

**목표:** ADK Track(MCP Tools + A2A)과 SDK Track(Resources/Prompts/Sampling/Elicitation)을 병행하는 Hybrid-Dual 아키텍처 구현

**현재 상태:**
- ADK Track: 작동 중 (DynamicToolset, GatewayToolset, RemoteA2aAgent)
- SDK Track: 삭제됨 (McpClientAdapter, SamplingService 등 복원 필요)

**핵심 원칙:**
- TDD (테스트 먼저 작성 - Red → Green → Refactor)
- 헥사고날 아키텍처 (Domain 레이어는 순수 Python)
- MCP SDK v1.25+ 사용 (`mcp>=1.25,<2`)

---

## Implementation Phases

각 Phase의 상세 내용은 아래 링크를 참조하세요:

| Phase | 설명 | TDD | 문서 |
|-------|------|-----|------|
| **Phase 1** | Domain Entities | ✅ | [01_domain_entities.md](01_domain_entities.md) |
| **Phase 2** | Port Interface + Fake | ✅ | [02_port_interface.md](02_port_interface.md) |
| **Phase 3** | Domain Services | ✅ | [03_domain_services.md](03_domain_services.md) |
| **Phase 4** | Adapter Implementation | ✅ | [04_adapter_implementation.md](04_adapter_implementation.md) |
| **Phase 5** | Integration | ✅ | [05_integration.md](05_integration.md) |
| **Phase 6** | HTTP Routes | ✅ | [06_http_routes.md](06_http_routes.md) |
| **Phase 7** | SSE Events & Extension | - | [07_sse_events_extension.md](07_sse_events_extension.md) |

**순서대로 구현 가능:** Phase 2에서 Fake를 함께 작성하여 Phase 3 테스트에서 사용

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Chrome Extension                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ SSE Stream  │  │ HITL Modal  │  │ Resources/Prompts View  │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
└─────────┼────────────────┼─────────────────────┼────────────────┘
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AgentHub API (FastAPI)                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    HTTP Routes (Phase 6)                     │ │
│  │  /api/sampling/*  /api/elicitation/*  /api/mcp/servers/*    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌───────────────────────────┴───────────────────────────────┐  │
│  │                    Domain Services (Phase 3/5)             │  │
│  │  ┌────────────────┐  ┌──────────────┐  ┌───────────────┐  │  │
│  │  │RegistryService │──│SamplingService│  │ResourceService│  │  │
│  │  │  (Extended)    │  │(HITL Queue)   │  │PromptService │  │  │
│  │  └───────┬────────┘  └───────────────┘  └───────┬───────┘  │  │
│  └──────────┼───────────────────────────────────────┼──────────┘  │
│             │                                       │            │
│  ┌──────────┴───────────────────────────────────────┴──────────┐  │
│  │                    Outbound Ports (Phase 2)                 │  │
│  │  ┌─────────────┐  ┌──────────────┐                         │  │
│  │  │ToolsetPort  │  │McpClientPort │ ← Domain 콜백 추상화     │  │
│  │  │ (ADK Track) │  │ (SDK Track)  │                         │  │
│  │  └──────┬──────┘  └──────┬───────┘                         │  │
│  └─────────┼────────────────┼──────────────────────────────────┘  │
│            │                │                                    │
│  ┌─────────┴────────────────┴──────────────────────────────────┐  │
│  │                    Adapters (Phase 4)                        │  │
│  │  ┌────────────────┐  ┌─────────────────┐                    │  │
│  │  │GatewayToolset  │  │McpClientAdapter │                    │  │
│  │  │(ADK + LiteLLM) │  │(MCP SDK 1.25+)  │                    │  │
│  │  └───────┬────────┘  └────────┬────────┘                    │  │
│  └──────────┼────────────────────┼─────────────────────────────┘  │
└─────────────┼────────────────────┼─────────────────────────────────┘
              │                    │
              ▼                    ▼
       ┌──────────────┐     ┌──────────────┐
       │  MCP Server  │     │  MCP Server  │
       │ (Tools only) │     │ (Full SDK)   │
       └──────────────┘     └──────────────┘
              ↑                    ↑
              └────────────────────┘
                  이중 연결 (Dual Connection)
```

---

## Verification

### Unit Tests
```bash
pytest tests/unit/ -q --tb=line
```

### Integration Tests
```bash
pytest tests/integration/ -q --tb=line
```

### Coverage
```bash
pytest --cov=src --cov-fail-under=80 -q
```

### Local MCP Server Test
```bash
# MCP 서버 시작 (별도 터미널)
cd C:\Users\sungb\Documents\GitHub\MCP_SERVER\MCP_Streamable_HTTP
python -m synapse

# 서버 시작 및 테스트
uvicorn src.main:app --port 8000
```

### E2E Test (Extension HITL Flow)
1. Extension에서 MCP 서버 등록
2. MCP 서버가 Sampling 요청 전송
3. Extension UI에서 승인 다이얼로그 확인
4. 승인 후 LLM 응답 확인

---

## Critical Files Summary

| 구분 | 파일 |
|------|------|
| **Domain Entities** | `src/domain/entities/resource.py`, `sampling_request.py`, `elicitation_request.py`, `prompt_template.py` |
| **Port Interface** | `src/domain/ports/outbound/mcp_client_port.py` |
| **Domain Services** | `src/domain/services/resource_service.py`, `prompt_service.py`, `sampling_service.py`, `elicitation_service.py` |
| **Adapter** | `src/adapters/outbound/mcp/mcp_client_adapter.py` |
| **Fake Adapter** | `tests/unit/fakes/fake_mcp_client.py` |
| **Integration** | `src/domain/services/registry_service.py`, `src/config/container.py` |
| **HTTP Routes** | `src/adapters/inbound/http/routes/resources.py`, `prompts.py`, `sampling.py`, `elicitation.py` |
| **Extension** | `extension/lib/types.ts`, `extension/lib/api.ts` |

---

## Design Decisions

### HITL Flow: Hybrid 방식
- **Short timeout (30s)**: 요청 수신 후 30초간 Long-Polling 대기
- **Timeout 초과 시**: 요청 큐잉 + SSE로 Extension에 알림
- **장점**: 빠른 응답(30s 이내)과 비동기 처리(30s 초과) 모두 지원

### Extension UI: Modal Dialog
- **전체 화면 모달**로 즉각적인 주의 환기
- Sampling: 메시지 내용 + 승인/거부 버튼
- Elicitation: 동적 폼 (requested_schema 기반) + accept/decline/cancel

### Domain 콜백 추상화
- MCP SDK 타입 대신 Domain 전용 Protocol 사용
- Adapter에서 MCP SDK 타입으로 변환 (Phase 4)
- Domain 레이어 순수 Python 유지

---

## Risk Mitigation

| 위험 | 대응 |
|------|------|
| MCP SDK v2 Breaking Changes | `mcp>=1.25,<2`로 버전 고정 |
| 이중 세션 오버헤드 | 로깅 모니터링, 리소스 영향 낮을 것으로 예상 |
| 콜백 시그니처 변경 | Domain 추상화로 격리, Adapter에서 변환 |
| HITL 타임아웃 | Hybrid 방식 (30s Long-Polling + Queue + TTL 자동 정리) |
| 세션 누수 | 서버 종료 시 `disconnect_all()` 호출 (Phase 5.3) |

---

## Review Notes (2026-02-05)

### 검토 완료 항목
- [x] TDD 원칙 가이드 (각 Phase에 테스트 먼저 명시)
- [x] 헥사고날 아키텍처 준수 (Domain 순수 Python)
- [x] MCP SDK 콜백 스펙 반영 (Domain 추상화)
- [x] 테스트 경로 기존 구조와 일치 (`tests/integration/test_*_routes.py`)
- [x] Phase 5 테스트 계획 추가
- [x] 예외 정의 기존 패턴 준수 (ErrorCode 사용)

### 주의사항
1. **Phase 순서대로 구현 가능**: Phase 2에서 Fake를 함께 작성하여 Phase 3 테스트에서 사용
2. **Phase 4 테스트는 Integration**: McpClientAdapter는 외부 SDK 사용하므로 `tests/integration/`에 위치
3. **콜백 변환 로직**: Adapter에서 Domain → MCP SDK 타입 변환 필수

---

*Last Updated: 2026-02-05*
*Reviewed: TDD, Hexagonal Architecture, MCP SDK Spec Compliance*
