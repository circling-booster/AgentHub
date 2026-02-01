# Phase 6 Part D: Sampling, Elicitation, Vector Search (Steps 13-15)

> **상태:** 📋 Planned
> **선행 조건:** Phase 6 Part B Step 5 (McpClientPort) Complete
> **목표:** MCP Sampling/Elicitation HITL 패턴, 임베딩 기반 Semantic Tool Routing
> **예상 테스트:** ~14 신규
> **실행 순서:** Step 13 → Step 14 → Step 15

---

## 🎯 Progress Checklist

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **13** | MCP Sampling | ⬜ |
| **14** | MCP Elicitation | ⬜ |
| **15** | Vector Search (Semantic Tool Routing) | ⬜ |

---

## Step 13: MCP Sampling

**목표:** MCP 서버가 AgentHub의 LLM을 호출하는 역방향 패턴

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/ports/outbound/mcp_client_port.py` | MODIFY | sampling_handler 콜백 추가 |
| `src/adapters/outbound/mcp/mcp_client_adapter.py` | MODIFY | sampling handler 구현 |
| `tests/integration/adapters/test_sampling.py` | NEW | Sampling 통합 테스트 |

**패턴:**
```
MCP Server → sampling/createMessage 요청
    ↓
AgentHub (MCP Client) → sampling handler 호출
    ↓
AgentHub → 자체 LLM 호출 (LiteLLM)
    ↓
LLM 응답 → MCP Server로 반환
```

**보안:** Sampling 요청 시 사용자 승인 플로우 (Extension에서 confirm)

**TDD 순서:**
1. RED: `test_sampling_handler_calls_llm`
2. RED: `test_sampling_returns_llm_response`
3. RED: `test_sampling_user_approval_required`
4. RED: `test_sampling_rejection_returns_error`
5. GREEN: sampling handler 구현

**DoD:**
- [ ] MCP 서버의 sampling 요청에 LLM 응답 반환
- [ ] 사용자 승인 플로우 동작

---

## Step 14: MCP Elicitation

**목표:** MCP 서버가 사용자에게 추가 정보를 요청하는 HITL(Human-In-The-Loop) 패턴

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/entities/elicitation.py` | NEW | Elicitation 엔티티 (순수 Python) |
| `src/adapters/outbound/mcp/mcp_client_adapter.py` | MODIFY | elicitation handler 추가 |
| `src/adapters/inbound/http/routes/elicitation.py` | NEW | 대기중 elicitation API |
| `extension/components/ElicitationForm.tsx` | NEW | 동적 폼 렌더링 (JSON Schema → React) |
| `extension/hooks/useElicitation.ts` | NEW | Elicitation 상태 관리 |
| `tests/unit/domain/entities/test_elicitation.py` | NEW | Elicitation 엔티티 테스트 |
| `tests/integration/adapters/test_elicitation.py` | NEW | Elicitation 통합 테스트 |

**플로우:**
```
MCP Server → elicitation/create(schema) → AgentHub Backend
  → SSE/Polling → Extension Sidepanel
  → JSON Schema → React Form 렌더링
  → 사용자 입력 → AgentHub Backend → MCP Server
```

**API:**
- `GET /api/elicitation/pending` - 대기 중인 elicitation 요청
- `POST /api/elicitation/{id}/respond` - 사용자 응답 전송
- `POST /api/elicitation/{id}/cancel` - 요청 거부

**JSON Schema 지원 범위 (서브셋):**
- `string`, `number`, `boolean`, `enum`
- `object` (nested fields)
- `required` 필드 표시

**DoD:**
- [ ] MCP 서버의 elicitation 요청을 Extension에 표시
- [ ] 동적 폼 렌더링 (JSON Schema 기반)
- [ ] 사용자 응답이 MCP 서버로 전달

---

## Step 15: Vector Search (Semantic Tool Routing)

**목표:** 도구 > 50개일 때 임베딩 기반으로 관련 도구만 선택

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/entities/tool_embedding.py` | NEW | ToolEmbedding 엔티티 (순수 Python) |
| `src/domain/ports/outbound/vector_port.py` | NEW | VectorStoragePort 인터페이스 |
| `src/domain/services/tool_router_service.py` | NEW | SemanticToolRouter (순수 Python) |
| `src/adapters/outbound/vector/chromadb_adapter.py` | NEW | ChromaDB 구현체 |
| `src/config/settings.py` | MODIFY | VectorSearchSettings 추가 |
| `tests/unit/domain/services/test_tool_router.py` | NEW | 라우터 서비스 테스트 |
| `tests/integration/adapters/test_vector_search.py` | NEW | Vector search 통합 테스트 |

**핵심 설계:**
```python
class SemanticToolRouter:
    """임베딩 기반 도구 선택 (순수 Python 로직)"""

    def __init__(self, vector_port: VectorStoragePort, top_k: int = 10):
        self._vector = vector_port
        self._top_k = top_k

    async def select_tools(self, query: str, all_tools: list[Tool]) -> list[Tool]:
        """사용자 메시지와 가장 관련 있는 도구 top-k 선택"""
        if len(all_tools) <= 30:
            return all_tools  # 30개 이하면 전체 반환 (오버엔지니어링 방지)

        query_embedding = await self._vector.embed(query)
        similar = await self._vector.search(query_embedding, self._top_k)
        return [t for t in all_tools if t.name in similar]
```

**활성화 조건:**
- 도구 > 50개: 자동 활성화
- 도구 30~50개: 설정에 따라 선택
- 도구 < 30개: 비활성화

**DoD:**
- [ ] 도구 임베딩 생성 및 ChromaDB 저장
- [ ] 사용자 메시지 기반 top-k 도구 선택
- [ ] 50+ 도구 시 자동 활성화, <30 시 비활성화

---

## Part D Definition of Done

### 기능
- [ ] MCP Sampling: 서버 → AgentHub LLM 호출 동작
- [ ] MCP Elicitation: 동적 폼 렌더링 + 사용자 응답 전달
- [ ] Vector Search: 임베딩 기반 도구 라우팅

### 품질
- [ ] 14+ 테스트 추가
- [ ] Coverage >= 90% 유지

---

## 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|--------|:------:|------|
| Elicitation 동적 폼 복잡도 | 🟡 | JSON Schema 서브셋만 지원 |
| ChromaDB 의존성 크기 | 🟡 | 선택적 의존성 (`[vector]`) |
| 임베딩 비용 (OpenAI API) | 🟢 | 캐싱 + Phase 6A Cost Tracking 연동 |

---

*Part D 계획 작성일: 2026-01-31*
