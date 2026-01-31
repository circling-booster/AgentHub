# Phase 6 Part B: MCP Resources, Prompts, Apps (Steps 5-8)

> **상태:** 📋 Planned
> **선행 조건:** Phase 6 Part A Complete
> **목표:** MCP Python SDK 기반 Resources/Prompts 지원, MCP Apps 메타데이터 표시
> **예상 테스트:** ~17 신규
> **실행 순서:** Step 5 → Step 6 + Step 7 (병렬) → Step 8

---

## 🎯 Progress Checklist

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **5** | MCP Python SDK Client Port | ⬜ |
| **6** | Resources API + Extension UI | ⬜ |
| **7** | Prompts API + Extension UI | ⬜ |
| **8** | MCP Apps Metadata | ⬜ |

---

## 아키텍처: 하이브리드 MCP 접근법

```
┌─────────────────────────────────────────┐
│            ADK LlmAgent                  │
│  tools=[DynamicToolset(MCPToolset)]      │  ← 기존 유지 (Tools)
└─────────────┬───────────────────────────┘
              │
┌─────────────┴───────────────────────────┐
│         MCP Python SDK Client            │  ← 신규 (Resources/Prompts/Sampling)
│  ClientSession via Streamable HTTP       │
└─────────────────────────────────────────┘
```

- **ADK MCPToolset:** Tools 전용 (기존 코드 변경 없음)
- **MCP Python SDK (v1.26+):** Resources, Prompts, Sampling, Elicitation
- **Domain Port 인터페이스:** McpClientPort로 추상화 (헥사고날 준수)

---

## Step 5: MCP Python SDK Client Port

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/entities/resource.py` | NEW | Resource 엔티티 (순수 Python) |
| `src/domain/entities/prompt_template.py` | NEW | PromptTemplate 엔티티 (순수 Python) |
| `src/domain/ports/outbound/mcp_client_port.py` | NEW | McpClientPort 인터페이스 |
| `src/adapters/outbound/mcp/__init__.py` | NEW | MCP 어댑터 패키지 |
| `src/adapters/outbound/mcp/mcp_client_adapter.py` | NEW | MCP Python SDK 구현체 |
| `tests/unit/fakes/fake_mcp_client.py` | NEW | Fake Adapter |
| `tests/unit/domain/entities/test_resource.py` | NEW | Resource 엔티티 테스트 |
| `tests/unit/domain/entities/test_prompt_template.py` | NEW | PromptTemplate 테스트 |

**핵심 설계:**
```python
# src/domain/ports/outbound/mcp_client_port.py
class McpClientPort(ABC):
    @abstractmethod
    async def connect(self, endpoint: Endpoint) -> None: ...
    @abstractmethod
    async def list_resources(self, endpoint_id: str) -> list[Resource]: ...
    @abstractmethod
    async def read_resource(self, endpoint_id: str, uri: str) -> ResourceContent: ...
    @abstractmethod
    async def list_prompts(self, endpoint_id: str) -> list[PromptTemplate]: ...
    @abstractmethod
    async def get_prompt(self, endpoint_id: str, name: str, args: dict) -> str: ...
    @abstractmethod
    async def disconnect(self, endpoint_id: str) -> None: ...
```

**웹 검색 필수:** MCP Python SDK (`mcp` 패키지) 최신 API 확인
- `ClientSession` 생성 방법
- `list_resources()`, `read_resource()` 시그니처
- `list_prompts()`, `get_prompt()` 시그니처

**TDD 순서:**
1. RED: `test_resource_entity_creation`
2. RED: `test_prompt_template_entity_creation`
3. RED: `test_mcp_client_connect_and_list_resources`
4. RED: `test_mcp_client_read_resource`
5. RED: `test_mcp_client_list_and_get_prompts`
6. RED: `test_fake_mcp_client_returns_fixtures`
7. GREEN: 모든 구현

**DoD:**
- [ ] McpClientPort 인터페이스 정의
- [ ] MCP Python SDK 기반 어댑터 구현
- [ ] Fake Adapter로 도메인 서비스 테스트 가능

---

## Step 6: Resources API + Extension UI

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/inbound/http/routes/resources.py` | NEW | Resources API 라우터 |
| `extension/components/ResourceList.tsx` | NEW | Resources 목록 컴포넌트 |
| `extension/lib/types.ts` | MODIFY | Resource TypeScript 타입 추가 |
| `tests/integration/adapters/test_resources_api.py` | NEW | Resources API 통합 테스트 |

**API:**
- `GET /api/mcp/servers/{id}/resources` - 리소스 목록
- `GET /api/mcp/servers/{id}/resources/{uri}` - 리소스 읽기

**DoD:**
- [ ] API로 리소스 목록 조회 + 내용 읽기
- [ ] Extension에서 MCP 서버별 리소스 표시

---

## Step 7: Prompts API + Extension UI

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/inbound/http/routes/prompts.py` | NEW | Prompts API 라우터 |
| `extension/components/PromptSelector.tsx` | NEW | 프롬프트 선택/실행 UI |
| `tests/integration/adapters/test_prompts_api.py` | NEW | Prompts API 통합 테스트 |

**API:**
- `GET /api/mcp/servers/{id}/prompts` - 프롬프트 목록
- `POST /api/mcp/servers/{id}/prompts/{name}` - 프롬프트 렌더링 (변수 바인딩)

**DoD:**
- [ ] 프롬프트 목록 조회 + 변수 바인딩 실행
- [ ] Extension에서 프롬프트 선택 및 실행 UI

---

## Step 8: MCP Apps Metadata

**목표:** MCP Apps 메타데이터 표시 (렌더링은 추후)

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/entities/mcp_app.py` | NEW | McpApp 엔티티 |
| `extension/components/McpAppIndicator.tsx` | NEW | MCP App 메타데이터 표시 |
| `tests/unit/domain/entities/test_mcp_app.py` | NEW | McpApp 테스트 |

**참고:** Synapse MCP 서버는 현재 MCP Apps 미지원. 외부 테스트 서버 또는 Synapse에 간단한 App 구현 필요.

**DoD:**
- [ ] Tool 응답에서 `_meta.ui.resourceUri` 감지
- [ ] Extension에서 MCP App 메타데이터 표시 (URI, type)
- [ ] 실제 HTML 렌더링은 포함하지 않음

---

## Part B Definition of Done

### 기능
- [ ] MCP Resources 목록/읽기 API + UI
- [ ] MCP Prompts 목록/실행 API + UI
- [ ] MCP Apps 메타데이터 표시

### 품질
- [ ] 17+ 테스트 추가
- [ ] Coverage >= 90% 유지

---

## 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|--------|:------:|------|
| MCP Python SDK API 변경 | 🟡 | 웹 검색으로 최신 확인, 버전 고정 |
| Synapse MCP Apps 미지원 | 🟡 | 외부 서버 또는 간단 구현 |
| 하이브리드 아키텍처 복잡도 | 🟡 | 명확한 Port 분리로 관리 |

---

*Part B 계획 작성일: 2026-01-31*
