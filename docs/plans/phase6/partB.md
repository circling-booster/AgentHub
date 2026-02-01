# Phase 6 Part B: MCP Resources, Prompts, Apps (Steps 5-8)

> **상태:** 📋 Planned
> **선행 조건:** Phase 6 Part A Complete
> **목표:** MCP Python SDK 기반 Resources/Prompts 지원, MCP Apps 메타데이터 표시
> **예상 테스트:** 38 신규 (Backend 17 + Extension 21)
> **실행 순서:** Step 5 → Step 6 + Step 7 (병렬) → Step 8

---

## 📋 Prerequisites (사전 조건)

| 항목 | 검증 방법 | 필수 |
|------|----------|:---:|
| **Phase 6 Part A 완료** | `pytest tests/integration/adapters/test_mcp_gateway.py -v` | ✅ |
| **MCP Python SDK 설치** | `pip list \| grep mcp` (v1.26.0+) | ✅ |
| **로컬 MCP 서버 실행** | `curl http://127.0.0.1:9000/mcp` (Resources/Prompts 지원) | ✅ |
| **MCP Apps 스펙 검증** | 웹 검색으로 최신 MCP 스펙 확인 (Step 8 시작 전 필수) | ✅ |
| **외부 테스트 서버 확인** | `curl https://remote-mcp-server-authless.idosalomon.workers.dev/mcp` | ⚠️ |

**검증 게이트:**
```bash
# Step 5 시작 전
pytest tests/integration/adapters/test_cost_tracking.py -v  # Phase 6A 검증
pip show mcp | grep Version  # MCP SDK >= 1.26.0

# Step 8 시작 전 (필수 웹 검색)
# - "MCP Apps specification 2025"
# - "MCP _meta.ui.resourceUri standard"
# - "remote-mcp-server-authless MCP Apps support"
```

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

### 전체 구조

```
┌───────────────────────────────────────────────────────────────┐
│                    AgentHub Domain Layer                       │
│  ┌─────────────────┐         ┌──────────────────────────┐    │
│  │ OrchestratorPort│         │   McpClientPort (NEW)     │    │
│  │   (기존)         │         │  - list_resources()       │    │
│  │                 │         │  - read_resource()        │    │
│  │                 │         │  - list_prompts()         │    │
│  │                 │         │  - get_prompt()           │    │
│  └────────┬────────┘         └───────────┬──────────────┘    │
└───────────┼──────────────────────────────┼───────────────────┘
            │                              │
            ▼                              ▼
┌───────────────────────┐    ┌──────────────────────────────┐
│  ADK LlmAgent         │    │  MCP Python SDK Client       │
│  + DynamicToolset     │    │  (ClientSession)             │
│  (MCPToolset)         │    │                              │
│                       │    │  - Resources API             │
│  ✅ Tools Only         │    │  - Prompts API               │
│  ✅ 기존 코드 유지      │    │  - Sampling API (Phase 6D)   │
└───────────┬───────────┘    └──────────┬───────────────────┘
            │                           │
            ▼                           ▼
    ┌───────────────┐          ┌──────────────┐
    │  MCP Server   │          │  MCP Server  │
    │  (Tools)      │          │ (Resources,  │
    │               │          │  Prompts)    │
    └───────────────┘          └──────────────┘
```

### 하이브리드 전략 상세

| 기능 | 구현 방식 | 이유 |
|------|----------|------|
| **Tools** | ADK MCPToolset | LlmAgent 네이티브 통합, 기존 코드 안정성 |
| **Resources** | MCP Python SDK | ADK 미지원, 직접 MCP 프로토콜 필요 |
| **Prompts** | MCP Python SDK | ADK 미지원, 프롬프트 변수 바인딩 필요 |
| **Sampling** | MCP Python SDK | ADK 미지원 (Phase 6D에서 구현) |
| **Apps** | MCP Python SDK | 메타데이터만 표시, 렌더링 제외 |

### 포트 인터페이스 분리

```python
# 기존 (유지)
OrchestratorPort:
    - process_message()  # ADK LlmAgent 사용
    - add_mcp_tools()    # DynamicToolset 사용

# 신규 (Phase 6B)
McpClientPort:
    - connect(endpoint)
    - list_resources(endpoint_id)
    - read_resource(endpoint_id, uri)
    - list_prompts(endpoint_id)
    - get_prompt(endpoint_id, name, args)
    - disconnect(endpoint_id)
```

### DI Container 통합 계획

```python
# src/config/container.py 수정 예정

class Container(containers.DeclarativeContainer):
    # 기존
    dynamic_toolset = providers.Singleton(DynamicToolset)
    orchestrator_adapter = providers.Singleton(AdkOrchestratorAdapter, ...)

    # 신규 (Step 5에서 추가)
    mcp_client_adapter = providers.Singleton(
        McpClientAdapter,  # MCP Python SDK 구현체
        session_timeout=config.mcp.session_timeout,
    )
```

### 외부 의존성 버전

| 패키지 | 버전 | 용도 |
|--------|------|------|
| `google-adk` | 1.23.0+ | LlmAgent, MCPToolset |
| `mcp` | **1.26.0** | Resources, Prompts, ClientSession |
| `httpx` | 0.27.0 | MCP Streamable HTTP Transport |

---

## Step 5: MCP Python SDK Client Port

**예상 테스트:** 11개 (Entity 4 + Unit 5 + Integration 2)

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/entities/resource.py` | NEW | Resource 엔티티 (순수 Python) |
| `src/domain/entities/resource_content.py` | NEW | ResourceContent 엔티티 (uri, mimeType, text) |
| `src/domain/entities/prompt_template.py` | NEW | PromptTemplate 엔티티 (순수 Python) |
| `src/domain/ports/outbound/mcp_client_port.py` | NEW | McpClientPort 인터페이스 |
| `src/adapters/outbound/mcp/__init__.py` | NEW | MCP 어댑터 패키지 |
| `src/adapters/outbound/mcp/mcp_client_adapter.py` | NEW | MCP Python SDK 구현체 |
| `src/config/container.py` | MODIFY | mcp_client_adapter DI 추가 |
| `tests/unit/fakes/fake_mcp_client.py` | NEW | Fake Adapter |
| `tests/unit/domain/entities/test_resource.py` | NEW | Resource 엔티티 테스트 (2 tests) |
| `tests/unit/domain/entities/test_resource_content.py` | NEW | ResourceContent 테스트 (2 tests) |
| `tests/unit/domain/entities/test_prompt_template.py` | NEW | PromptTemplate 테스트 (2 tests) |
| `tests/unit/adapters/test_mcp_client_adapter.py` | NEW | MCP Client Adapter 테스트 (5 tests) |
| `tests/integration/adapters/test_mcp_client_integration.py` | NEW | MCP Client 통합 테스트 (2 tests) |

**핵심 설계:**
```python
# src/domain/ports/outbound/mcp_client_port.py
from abc import ABC, abstractmethod
from domain.entities.endpoint import Endpoint
from domain.entities.resource import Resource
from domain.entities.resource_content import ResourceContent
from domain.entities.prompt_template import PromptTemplate


class McpClientPort(ABC):
    """MCP Python SDK 기반 Resources/Prompts 클라이언트 포트"""

    @abstractmethod
    async def connect(self, endpoint: Endpoint) -> None:
        """MCP 서버와 ClientSession 연결"""
        ...

    @abstractmethod
    async def list_resources(self, endpoint_id: str) -> list[Resource]:
        """등록된 리소스 목록 조회"""
        ...

    @abstractmethod
    async def read_resource(self, endpoint_id: str, uri: str) -> ResourceContent:
        """리소스 내용 읽기"""
        ...

    @abstractmethod
    async def list_prompts(self, endpoint_id: str) -> list[PromptTemplate]:
        """프롬프트 템플릿 목록 조회"""
        ...

    @abstractmethod
    async def get_prompt(
        self,
        endpoint_id: str,
        name: str,
        arguments: dict[str, str] | None = None
    ) -> str:
        """프롬프트 렌더링 (변수 바인딩)"""
        ...

    @abstractmethod
    async def disconnect(self, endpoint_id: str) -> None:
        """ClientSession 종료"""
        ...
```

**DI Container 통합:**
```python
# src/config/container.py 수정 내용

from adapters.outbound.mcp.mcp_client_adapter import McpClientAdapter

class Container(containers.DeclarativeContainer):
    # ... 기존 코드 ...

    # Step 5에서 추가
    mcp_client_adapter = providers.Singleton(
        McpClientAdapter,
        session_timeout=settings.mcp.session_timeout,  # default: 120초
    )

    # Step 6에서 사용
    resource_service = providers.Factory(
        ResourceService,
        mcp_client=mcp_client_adapter,
        endpoint_storage=endpoint_storage,
    )
```

**⚠️ 웹 검색 필수 (구현 전 + 구현 중):**

MCP Python SDK (`mcp` 패키지 v1.26.0+) 최신 API 확인:

**구현 전 검색 (필수):**
- `ClientSession` 생성 방법 및 파라미터
- `list_resources()` 메서드 시그니처 및 반환 타입
- `read_resource(uri)` 메서드 시그니처 및 반환 타입
- `list_prompts()` 메서드 시그니처
- `get_prompt(name, arguments)` 메서드 시그니처

**구현 중 검색 (권장):**
- Import 에러 발생 시 최신 패키지 구조 확인
- API 시그니처 불일치 시 재검증
- Deprecation Warning 발생 시 대체 API 확인

**검색 키워드 예시:**
- "mcp python sdk ClientSession 2025"
- "mcp package list_resources API"
- "mcp python sdk read_resource example"

**TDD 순서 (/tdd 스킬 호출 필수):**

**Phase 1: RED (실패하는 테스트 작성)**
1. `test_resource_entity_creation` - Resource 엔티티 생성
2. `test_resource_content_entity_creation` - ResourceContent 엔티티
3. `test_prompt_template_entity_creation` - PromptTemplate 엔티티
4. `test_prompt_template_with_arguments` - 변수 포함 프롬프트
5. `test_mcp_client_connect` - MCP 서버 연결
6. `test_mcp_client_list_resources` - 리소스 목록 조회
7. `test_mcp_client_read_resource` - 리소스 읽기
8. `test_mcp_client_list_prompts` - 프롬프트 목록
9. `test_mcp_client_get_prompt_with_args` - 프롬프트 렌더링
10. `test_fake_mcp_client_returns_fixtures` - Fake Adapter
11. `test_mcp_client_integration_with_real_server` - 통합 테스트

**Phase 2: GREEN (최소 구현)**
- Resource, ResourceContent, PromptTemplate 엔티티 구현
- McpClientPort 인터페이스 구현
- McpClientAdapter (MCP Python SDK 기반) 구현
- FakeMcpClient 구현
- DI Container 연결

**Phase 3: REFACTOR (코드 개선)**
- 에러 처리 개선 (McpConnectionError, McpResourceNotFoundError)
- 리소스 캐싱 로직 추가 (선택적)
- 로깅 개선

**DoD:**
- [ ] **웹 검색으로 MCP Python SDK v1.26.0+ API 시그니처 검증 완료**
- [ ] McpClientPort 인터페이스 정의 (6개 메서드)
- [ ] Resource, ResourceContent, PromptTemplate 엔티티 구현 (순수 Python)
- [ ] MCP Python SDK 기반 어댑터 구현 (ClientSession 사용)
- [ ] Fake Adapter로 도메인 서비스 테스트 가능
- [ ] DI Container에 mcp_client_adapter 등록
- [ ] 11개 테스트 통과 (Entity 4 + Unit 5 + Integration 2)
- [ ] 로컬 MCP 서버로 Resources/Prompts 조회 성공

---

## Step 6: Resources API + Extension UI

**예상 테스트:** 11개 (Backend 4 + Extension 7)

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/services/resource_service.py` | NEW | Resource 도메인 서비스 |
| `src/adapters/inbound/http/routes/resources.py` | NEW | Resources API 라우터 |
| `src/adapters/inbound/http/schemas/resource.py` | NEW | Resource Pydantic 스키마 |
| `extension/components/ResourceList.tsx` | NEW | Resources 목록 컴포넌트 |
| `extension/components/ResourceViewer.tsx` | NEW | 리소스 내용 뷰어 |
| `extension/lib/types.ts` | MODIFY | Resource TypeScript 타입 추가 |
| `extension/lib/api.ts` | MODIFY | Resources API 클라이언트 |
| `tests/unit/domain/services/test_resource_service.py` | NEW | Resource Service 테스트 (2 tests) |
| `tests/integration/adapters/test_resources_api.py` | NEW | Resources API 통합 테스트 (2 tests) |
| `extension/components/ResourceList.test.tsx` | NEW | ResourceList Vitest 테스트 (4 tests) |
| `extension/components/ResourceViewer.test.tsx` | NEW | ResourceViewer Vitest 테스트 (3 tests) |

**API 엔드포인트:**
- `GET /api/mcp/servers/{id}/resources` - 리소스 목록
- `GET /api/mcp/servers/{id}/resources/{uri}` - 리소스 읽기 (URI는 URL 인코딩)

**Extension UI Wireframe:**
```
┌─────────────────────────────────────────┐
│ MCP Server: Example Server             │
├─────────────────────────────────────────┤
│ Resources (3)                       [▼] │
│  📄 file://project/README.md            │
│  📊 data://sales/2025-q1                │
│  🗂️ schema://database/users              │
│                                    [📖] │ ← 읽기 버튼
└─────────────────────────────────────────┘

ResourceViewer Modal:
┌─────────────────────────────────────────┐
│ Resource: file://project/README.md  [✕] │
├─────────────────────────────────────────┤
│ MIME Type: text/markdown                │
│                                         │
│ # Project Title                         │
│ This is the README content...           │
│                                         │
│                            [Copy] [Close]│
└─────────────────────────────────────────┘
```

**Extension UI 테스트 시나리오 (Vitest):**

**ResourceList.test.tsx (4 tests):**
1. `test_renders_empty_state_when_no_resources` - 리소스 없을 때 빈 상태
2. `test_displays_resource_list_with_icons` - 리소스 목록 + 아이콘 표시
3. `test_expands_and_collapses_resource_list` - 펼침/접기 토글
4. `test_calls_api_on_read_button_click` - 읽기 버튼 클릭 시 API 호출

**ResourceViewer.test.tsx (3 tests):**
1. `test_displays_loading_state` - 로딩 상태 표시
2. `test_renders_resource_content_with_mime_type` - MIME 타입 + 내용 표시
3. `test_copy_button_copies_to_clipboard` - 클립보드 복사 기능

**TDD 순서 (Step 6):**

**Backend (Red-Green-Refactor):**
1. RED: `test_resource_service_list_resources`
2. RED: `test_resource_service_read_resource`
3. RED: `test_resources_api_list_endpoint`
4. RED: `test_resources_api_read_endpoint_url_encoding`
5. GREEN: ResourceService + API 구현
6. REFACTOR: 에러 처리 개선

**Extension (Vitest):**
1. RED: 7개 Extension 테스트 작성
2. GREEN: ResourceList + ResourceViewer 구현
3. REFACTOR: 컴포넌트 재사용성 개선

**DoD:**
- [ ] ResourceService 도메인 서비스 구현
- [ ] GET /api/mcp/servers/{id}/resources API 구현
- [ ] GET /api/mcp/servers/{id}/resources/{uri} API 구현 (URI URL 인코딩)
- [ ] Extension ResourceList 컴포넌트 구현
- [ ] Extension ResourceViewer 모달 구현
- [ ] 11개 테스트 통과 (Backend 4 + Extension 7)
- [ ] MCP 서버에서 실제 리소스 조회 성공
- [ ] Extension UI에서 리소스 읽기 + 클립보드 복사 동작

---

## Step 7: Prompts API + Extension UI

**예상 테스트:** 10개 (Backend 4 + Extension 6)

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/services/prompt_service.py` | NEW | Prompt 도메인 서비스 |
| `src/adapters/inbound/http/routes/prompts.py` | NEW | Prompts API 라우터 |
| `src/adapters/inbound/http/schemas/prompt.py` | NEW | Prompt Pydantic 스키마 |
| `extension/components/PromptSelector.tsx` | NEW | 프롬프트 선택/실행 UI |
| `extension/components/PromptArgumentsForm.tsx` | NEW | 프롬프트 변수 입력 폼 |
| `extension/lib/api.ts` | MODIFY | Prompts API 클라이언트 |
| `tests/unit/domain/services/test_prompt_service.py` | NEW | Prompt Service 테스트 (2 tests) |
| `tests/integration/adapters/test_prompts_api.py` | NEW | Prompts API 통합 테스트 (2 tests) |
| `extension/components/PromptSelector.test.tsx` | NEW | PromptSelector Vitest 테스트 (3 tests) |
| `extension/components/PromptArgumentsForm.test.tsx` | NEW | ArgumentsForm Vitest 테스트 (3 tests) |

**API 엔드포인트:**
- `GET /api/mcp/servers/{id}/prompts` - 프롬프트 템플릿 목록
- `POST /api/mcp/servers/{id}/prompts/{name}` - 프롬프트 렌더링 (변수 바인딩)
  - Request Body: `{"arguments": {"var1": "value1", "var2": "value2"}}`
  - Response: `{"rendered_prompt": "..."}`

**Extension UI Wireframe:**
```
┌─────────────────────────────────────────┐
│ MCP Server: Code Assistant             │
├─────────────────────────────────────────┤
│ Prompts (2)                         [▼] │
│  📝 code-review                          │
│      Args: file_path, language          │
│  📝 documentation-generator              │
│      Args: function_name                │
│                                    [▶️] │ ← 실행 버튼
└─────────────────────────────────────────┘

PromptArgumentsForm Modal:
┌─────────────────────────────────────────┐
│ Prompt: code-review                 [✕] │
├─────────────────────────────────────────┤
│ file_path: [___________________]        │
│ language:  [___________________]        │
│                                         │
│                   [Cancel] [Execute]    │
└─────────────────────────────────────────┘

Result Display (채팅창에 삽입):
┌─────────────────────────────────────────┐
│ > Executed Prompt: code-review          │
│ Please review the following code...     │
│ [Rendered prompt text inserted]         │
└─────────────────────────────────────────┘
```

**Extension UI 테스트 시나리오 (Vitest):**

**PromptSelector.test.tsx (3 tests):**
1. `test_renders_empty_state_when_no_prompts` - 프롬프트 없을 때 빈 상태
2. `test_displays_prompt_list_with_arguments` - 프롬프트 목록 + 인수 표시
3. `test_opens_arguments_form_on_execute_click` - 실행 버튼 클릭 시 폼 표시

**PromptArgumentsForm.test.tsx (3 tests):**
1. `test_renders_input_fields_for_each_argument` - 각 인수별 입력 필드
2. `test_validates_required_arguments` - 필수 인수 검증
3. `test_submits_form_and_inserts_to_chat` - 폼 제출 시 채팅창에 삽입

**TDD 순서 (Step 7):**

**Backend (Red-Green-Refactor):**
1. RED: `test_prompt_service_list_prompts`
2. RED: `test_prompt_service_render_with_arguments`
3. RED: `test_prompts_api_list_endpoint`
4. RED: `test_prompts_api_render_endpoint_with_validation`
5. GREEN: PromptService + API 구현
6. REFACTOR: 변수 검증 로직 개선

**Extension (Vitest):**
1. RED: 6개 Extension 테스트 작성
2. GREEN: PromptSelector + ArgumentsForm 구현
3. REFACTOR: 채팅창 통합 개선

**DoD:**
- [ ] PromptService 도메인 서비스 구현
- [ ] GET /api/mcp/servers/{id}/prompts API 구현
- [ ] POST /api/mcp/servers/{id}/prompts/{name} API 구현 (변수 검증 포함)
- [ ] Extension PromptSelector 컴포넌트 구현
- [ ] Extension PromptArgumentsForm 컴포넌트 구현
- [ ] 렌더링된 프롬프트를 채팅창에 삽입 기능
- [ ] 10개 테스트 통과 (Backend 4 + Extension 6)
- [ ] MCP 서버에서 실제 프롬프트 렌더링 성공
- [ ] Extension UI에서 변수 입력 + 실행 동작

---

## Step 8: MCP Apps Metadata

**예상 테스트:** 6개 (Backend 3 + Extension 3)

**목표:** MCP Apps 메타데이터 표시 (렌더링은 Phase 7에서 구현)

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/entities/mcp_app.py` | NEW | McpApp 엔티티 (uri, type, title) |
| `src/adapters/outbound/adk/dynamic_toolset.py` | MODIFY | Tool 응답에서 `_meta` 파싱 |
| `extension/components/McpAppIndicator.tsx` | NEW | MCP App 메타데이터 표시 |
| `extension/lib/types.ts` | MODIFY | McpApp TypeScript 타입 |
| `tests/unit/domain/entities/test_mcp_app.py` | NEW | McpApp 엔티티 테스트 (2 tests) |
| `tests/integration/adapters/test_mcp_apps_detection.py` | NEW | MCP Apps 감지 테스트 (1 test) |
| `extension/components/McpAppIndicator.test.tsx` | NEW | Indicator Vitest 테스트 (3 tests) |

**외부 테스트 엔드포인트:**

MCP Apps 구현 검증을 위해 다음 외부 서버 사용 (웹 검색으로 사전 검증 필수):
- SSE Transport: `https://remote-mcp-server-authless.idosalomon.workers.dev/sse`
- Streamable HTTP: `https://remote-mcp-server-authless.idosalomon.workers.dev/mcp`

**⚠️ 웹 검색 필수 (구현 전 + 구현 중 반드시 수행):**

**구현 전 필수 검색 (Step 8 시작 전):**

1. **MCP Apps 공식 스펙 확인:**
   ```
   검색: "MCP Apps specification 2025"
   확인 사항:
   - MCP Apps가 공식 MCP Specification에 포함되었는가?
   - `_meta.ui.resourceUri` 필드가 표준 프로토콜인가?
   - Tool 응답 형식: `content: [{type: "text", text: "..."}, {type: "resource", resource: {..., _meta: {...}}}]`
   - 최신 스펙 버전: 2025-11-25 이후 변경 사항
   ```

2. **외부 테스트 엔드포인트 검증:**
   ```
   검색: "remote-mcp-server-authless MCP Apps support 2025"
   확인 사항:
   - idosalomon.workers.dev 서버가 MCP Apps를 지원하는가?
   - 응답 형식이 MCP 표준을 준수하는가?
   - 대체 테스트 서버가 필요한가?
   ```

3. **Breaking Changes 확인:**
   ```
   검색: "MCP specification breaking changes 2025"
   확인 사항:
   - MCP Apps 관련 API 변경 사항
   - Deprecated 필드 또는 메서드
   ```

**구현 중 검색 (권장):**
- Import 에러 발생 시: "mcp python sdk _meta parsing 2025"
- API 시그니처 불일치 시: "mcp tool response format 2025"
- 외부 서버 응답 형식 불일치 시: "MCP Apps resource metadata structure"

**검색 결과 문서화:**
- 검색 결과를 `docs/research/mcp-apps-verification.md`에 기록
- 표준 준수 여부를 DoD에 체크리스트로 추가

**Extension UI Wireframe:**
```
Chat Message Bubble:
┌─────────────────────────────────────────┐
│ Tool: weather_forecast                  │
│ Result: "Temperature: 25°C"             │
│                                         │
│ 🌐 MCP App Available                    │ ← Indicator
│    Type: weather-widget                 │
│    URI: https://example.com/widget.html │
│                          [View Details] │
└─────────────────────────────────────────┘

Details Modal (Phase 7에서 구현):
┌─────────────────────────────────────────┐
│ MCP App: Weather Widget             [✕] │
├─────────────────────────────────────────┤
│ URI: https://example.com/widget.html    │
│ Type: weather-widget                    │
│ Title: Interactive Weather Forecast     │
│                                         │
│ [Render] ← Phase 7 구현                 │
└─────────────────────────────────────────┘
```

**Extension UI 테스트 시나리오 (Vitest):**

**McpAppIndicator.test.tsx (3 tests):**
1. `test_hides_indicator_when_no_mcp_app` - MCP App 없을 때 숨김
2. `test_displays_indicator_with_metadata` - 메타데이터 표시 (URI, type)
3. `test_opens_details_modal_on_click` - 클릭 시 상세 정보 모달

**TDD 순서 (Step 8):**

**Phase 1: RED (웹 검색 후 테스트 작성)**
1. 웹 검색으로 MCP Apps 스펙 검증 (필수)
2. RED: `test_mcp_app_entity_creation`
3. RED: `test_mcp_app_entity_with_optional_title`
4. RED: `test_dynamic_toolset_parses_meta_ui_resourceUri`
5. RED: `test_mcp_app_indicator_displays_metadata`
6. RED: `test_mcp_app_indicator_hides_when_no_app`
7. RED: `test_mcp_app_indicator_opens_modal`

**Phase 2: GREEN (최소 구현)**
- McpApp 엔티티 구현
- DynamicToolset `_meta` 파싱 로직 추가
- McpAppIndicator 컴포넌트 구현

**Phase 3: REFACTOR (코드 개선)**
- 에러 처리 (잘못된 `_meta` 형식)
- 로깅 추가 (MCP App 감지 시)

**DoD:**
- [ ] **웹 검색으로 MCP Apps 공식 스펙 검증 완료 (구현 전 필수)**
- [ ] **검색 결과 문서화 (`docs/research/mcp-apps-verification.md`)**
- [ ] **외부 테스트 엔드포인트가 MCP Apps 지원 확인 (웹 검색)**
- [ ] **MCP Apps가 공식 MCP Specification에 포함되었는지 확인**
- [ ] **`_meta.ui.resourceUri` 필드가 표준 프로토콜임을 확인**
- [ ] McpApp 엔티티 구현 (uri, type, title)
- [ ] DynamicToolset에서 Tool 응답 `_meta` 파싱
- [ ] Extension McpAppIndicator 컴포넌트 구현
- [ ] 6개 테스트 통과 (Backend 3 + Extension 3)
- [ ] 외부 MCP 서버에서 MCP App 메타데이터 감지 성공
- [ ] Extension UI에서 MCP App 메타데이터 표시 (URI, type, title)
- [ ] HTML 렌더링은 포함하지 않음 (Phase 7로 연기)

**⚠️ 구현 차단 조건:**
- 웹 검색으로 MCP Apps가 **비표준**으로 확인되면 Step 8 구현 중단
- 대체 솔루션: MCP Apps 대신 일반 Tool Result로 폴백

---

## Part B Definition of Done

### 1. 기능 완성도 (Feature Completeness)

**Step 5: MCP Python SDK Client Port**
- [ ] McpClientPort 인터페이스 정의 (6개 메서드)
- [ ] Resource, ResourceContent, PromptTemplate 엔티티 구현 (순수 Python)
- [ ] MCP Python SDK v1.26.0 기반 어댑터 구현
- [ ] FakeMcpClient 구현 (Fake Adapter 패턴)
- [ ] DI Container에 mcp_client_adapter 등록
- [ ] 웹 검색으로 MCP Python SDK API 시그니처 검증 완료

**Step 6: Resources API + Extension UI**
- [ ] ResourceService 도메인 서비스 구현
- [ ] GET /api/mcp/servers/{id}/resources API
- [ ] GET /api/mcp/servers/{id}/resources/{uri} API (URI URL 인코딩)
- [ ] Extension ResourceList 컴포넌트
- [ ] Extension ResourceViewer 모달
- [ ] 클립보드 복사 기능

**Step 7: Prompts API + Extension UI**
- [ ] PromptService 도메인 서비스 구현
- [ ] GET /api/mcp/servers/{id}/prompts API
- [ ] POST /api/mcp/servers/{id}/prompts/{name} API (변수 검증)
- [ ] Extension PromptSelector 컴포넌트
- [ ] Extension PromptArgumentsForm 컴포넌트
- [ ] 렌더링된 프롬프트를 채팅창에 삽입

**Step 8: MCP Apps Metadata**
- [ ] **웹 검색으로 MCP Apps 공식 스펙 검증 완료 (구현 전 필수)**
- [ ] **검색 결과 문서화 (`docs/research/mcp-apps-verification.md`)**
- [ ] **외부 테스트 엔드포인트 MCP Apps 지원 확인**
- [ ] **MCP Apps가 공식 MCP Specification에 포함되었는지 확인**
- [ ] McpApp 엔티티 구현 (uri, type, title)
- [ ] DynamicToolset `_meta` 파싱
- [ ] Extension McpAppIndicator 컴포넌트
- [ ] HTML 렌더링은 포함하지 않음

### 2. 테스트 품질 (Test Quality)

**테스트 개수 목표: 38개 신규 테스트**
- [ ] **Step 5:** 11 tests (Entity 6 + Unit 5 + Integration 2)
- [ ] **Step 6:** 11 tests (Backend 4 + Extension 7)
- [ ] **Step 7:** 10 tests (Backend 4 + Extension 6)
- [ ] **Step 8:** 6 tests (Backend 3 + Extension 3)

**커버리지 목표:**
- [ ] Backend coverage >= 90% (기존 91% 유지)
- [ ] Extension 테스트 regression 없음 (기존 232 tests 유지)
- [ ] 모든 신규 코드에 TDD Red-Green-Refactor 적용

**통합 테스트 검증:**
- [ ] 로컬 MCP 서버에서 Resources 조회 성공
- [ ] 로컬 MCP 서버에서 Prompts 렌더링 성공
- [ ] 외부 MCP 서버에서 MCP Apps 메타데이터 감지 성공

### 3. 표준 준수 (Standards Compliance)

**MCP Python SDK 검증:**
- [ ] 웹 검색으로 `mcp` v1.26.0 API 시그니처 검증 (Step 5 구현 전)
- [ ] ClientSession 생성 방법 확인
- [ ] list_resources(), read_resource() 시그니처 확인
- [ ] list_prompts(), get_prompt() 시그니처 확인

**MCP Apps 표준 검증 (Step 8 차단 조건):**
- [ ] MCP Apps가 공식 MCP Specification에 포함되었는지 웹 검색 확인
- [ ] `_meta.ui.resourceUri` 필드가 표준 프로토콜인지 확인
- [ ] 외부 테스트 서버가 표준을 준수하는지 확인
- [ ] 비표준일 경우 구현 중단 및 대체 방안 검토

**헥사고날 아키텍처 준수:**
- [ ] McpClientPort가 순수 인터페이스 (외부 의존성 없음)
- [ ] Resource, PromptTemplate 엔티티가 순수 Python
- [ ] Fake Adapter로 도메인 서비스 테스트 가능

### 4. 통합 및 배포 (Integration & Deployment)

**DI Container 통합:**
- [ ] mcp_client_adapter Provider 등록
- [ ] resource_service, prompt_service Provider 등록
- [ ] FastAPI 라우터 등록 (resources, prompts)

**의존성 관리:**
- [ ] `requirements.txt`에 `mcp==1.26.0` 추가 (버전 고정)
- [ ] `requirements.txt`에 `httpx==0.27.0` 추가 (버전 고정)
- [ ] Extension `package.json` 의존성 추가 (필요 시)

**문서화:**
- [ ] `src/adapters/outbound/mcp/README.md` 생성 (MCP Client 사용법)
- [ ] `docs/research/mcp-apps-verification.md` 생성 (Step 8 웹 검색 결과)
- [ ] `src/README.md`에 Hybrid MCP Architecture 설명 추가

### 5. 사용자 수용 (User Acceptance)

**수동 검증 시나리오:**
- [ ] Extension에서 MCP 서버 등록 후 Resources 목록 표시
- [ ] 리소스 읽기 버튼 클릭 시 내용 표시 및 클립보드 복사
- [ ] Prompts 목록 표시 및 변수 입력 폼 동작
- [ ] 렌더링된 프롬프트가 채팅창에 삽입
- [ ] MCP App 메타데이터 표시 (외부 서버 사용)

**에러 처리 검증:**
- [ ] MCP 서버 연결 실패 시 적절한 에러 메시지
- [ ] 리소스/프롬프트 조회 실패 시 UI 에러 표시
- [ ] 잘못된 프롬프트 변수 입력 시 검증 메시지

---

## 커밋 정책 (Commit Policy)

### Step별 커밋 전략

| Step | 커밋 단위 | 예시 커밋 메시지 |
|------|----------|------------------|
| **Step 5** | 3개 커밋 | `feat(mcp): Add Resource/PromptTemplate entities`<br>`feat(mcp): Add McpClientPort and adapter`<br>`test(mcp): Add MCP Client integration tests` |
| **Step 6** | 3개 커밋 | `feat(api): Add Resources API endpoints`<br>`feat(extension): Add ResourceList UI`<br>`test(extension): Add ResourceList Vitest tests` |
| **Step 7** | 3개 커밋 | `feat(api): Add Prompts API endpoints`<br>`feat(extension): Add PromptSelector UI`<br>`test(extension): Add PromptSelector Vitest tests` |
| **Step 8** | 2개 커밋 | `feat(mcp): Add MCP Apps metadata parsing`<br>`feat(extension): Add McpAppIndicator UI` |

### 커밋 전 체크리스트

**모든 커밋 전 실행:**
```bash
# Backend 린트 및 포맷
ruff check src/ tests/ --fix
ruff format src/ tests/

# Backend 테스트
pytest tests/ --cov=src --cov-fail-under=90 -q

# Extension 테스트
cd extension && npm test

# 타입 체크
cd extension && npm run typecheck
```

**Git Hook 활용:**
- PreToolUse Hook: main 브랜치 직접 커밋 차단
- UserPromptSubmit Hook: `/commit` 시 전체 테스트 실행

### PR 생성 전 검증

**Part B 완료 시 PR 체크리스트:**
- [ ] 38개 신규 테스트 모두 통과
- [ ] Backend coverage >= 90%
- [ ] Extension 테스트 regression 없음
- [ ] ruff 린트 0개 에러
- [ ] mypy 타입 체크 통과 (선택적)
- [ ] 모든 DoD 항목 완료
- [ ] 수동 검증 시나리오 통과
- [ ] `docs/research/mcp-apps-verification.md` 작성 완료 (Step 8)

**PR 제목 예시:**
```
feat(phase6-partB): MCP Resources, Prompts, Apps (Steps 5-8)

- Add MCP Python SDK Client Port (Step 5)
- Add Resources API + Extension UI (Step 6)
- Add Prompts API + Extension UI (Step 7)
- Add MCP Apps Metadata (Step 8)

Tests: 38 new (Backend 17 + Extension 21)
Coverage: 90% (maintained)
```

---

## Extension UI Mockup/Wireframe

### 전체 UI 구조

```
┌─────────────────────────────────────────────────────┐
│ AgentHub Sidepanel                              [⚙️] │
├─────────────────────────────────────────────────────┤
│ Tabs: [Chat] [MCP Servers] [A2A Agents]             │
├─────────────────────────────────────────────────────┤
│                                                     │
│ MCP Servers                                    [+]  │
│                                                     │
│ ┌─────────────────────────────────────────────┐    │
│ │ 📡 Example MCP Server                   [▼] │    │
│ │    URL: http://127.0.0.1:9000/mcp           │    │
│ │    Status: 🟢 Connected                     │    │
│ │                                             │    │
│ │    Resources (3)                        [▼] │ ← Step 6
│ │     📄 file://project/README.md         [📖]│    │
│ │     📊 data://sales/2025-q1             [📖]│    │
│ │     🗂️ schema://database/users           [📖]│    │
│ │                                             │    │
│ │    Prompts (2)                          [▼] │ ← Step 7
│ │     📝 code-review                      [▶️]│    │
│ │        Args: file_path, language            │    │
│ │     📝 documentation-generator          [▶️]│    │
│ │        Args: function_name                  │    │
│ │                                             │    │
│ │    Tools (5)                            [▼] │ ← 기존
│ │     🔧 weather_forecast                     │    │
│ │     🔧 file_search                          │    │
│ └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### ResourceViewer Modal (Step 6)

```
┌─────────────────────────────────────────────────────┐
│ Resource: file://project/README.md              [✕] │
├─────────────────────────────────────────────────────┤
│ MIME Type: text/markdown                            │
│ Size: 2.5 KB                                        │
├─────────────────────────────────────────────────────┤
│ Content Preview:                                    │
│ ┌─────────────────────────────────────────────────┐ │
│ │ # Project Title                                 │ │
│ │                                                 │ │
│ │ This is the README content with markdown...    │ │
│ │                                                 │ │
│ │ ## Installation                                 │ │
│ │ ```bash                                         │ │
│ │ npm install                                     │ │
│ │ ```                                             │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│                         [Copy to Clipboard] [Close] │
└─────────────────────────────────────────────────────┘
```

### PromptArgumentsForm Modal (Step 7)

```
┌─────────────────────────────────────────────────────┐
│ Execute Prompt: code-review                     [✕] │
├─────────────────────────────────────────────────────┤
│ This prompt will generate a code review based on:   │
│                                                     │
│ file_path: (required)                               │
│ ┌─────────────────────────────────────────────────┐ │
│ │ src/main.py                                     │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ language: (optional)                                │
│ ┌─────────────────────────────────────────────────┐ │
│ │ python                                          │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│                              [Cancel] [Execute ▶️]  │
└─────────────────────────────────────────────────────┘

Result:
┌─────────────────────────────────────────────────────┐
│ Chat Interface                                      │
├─────────────────────────────────────────────────────┤
│ > Executed Prompt: code-review                      │
│                                                     │
│ Please review the following Python code from        │
│ src/main.py and provide suggestions for...          │
│ [Rendered prompt text inserted into chat input]     │
└─────────────────────────────────────────────────────┘
```

### McpAppIndicator (Step 8)

```
Chat Message Bubble:
┌─────────────────────────────────────────────────────┐
│ Assistant:                                          │
│ I've fetched the weather forecast for you.          │
│                                                     │
│ Tool: weather_forecast                              │
│ Status: ✅ Success                                  │
│ Result: "Temperature: 25°C, Humidity: 60%"          │
│                                                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 🌐 Interactive Widget Available                 │ │ ← Step 8
│ │    Type: weather-widget                         │ │
│ │    URI: https://example.com/weather.html        │ │
│ │    Title: Interactive Weather Forecast          │ │
│ │                             [View Details 🔍]   │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘

Note: 실제 HTML 렌더링은 Phase 7에서 구현
```

---

## 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|--------|:------:|------|
| MCP Python SDK API 변경 | 🟡 | 웹 검색으로 최신 확인, 버전 고정 (`mcp==1.26.0`) |
| 외부 엔드포인트가 MCP Apps 미지원 | 🟡 | 웹 검색으로 사전 검증, 대체 엔드포인트 탐색 |
| MCP Apps 스펙이 비표준 | 🟡 | 웹 검색으로 최신 MCP 스펙 확인, 비표준 시 구현 중단 |
| 하이브리드 아키텍처 복잡도 | 🟡 | 명확한 Port 분리로 관리, `src/adapters/outbound/mcp/README.md` 문서화 |
| Resources/Prompts API 성능 이슈 | 🟢 | 캐싱 추가 (선택적), 페이지네이션 (Phase 7) |
| Extension UI 복잡도 증가 | 🟢 | 컴포넌트 재사용성 강화, Storybook 도입 (선택적) |

---

*Part B 계획 작성일: 2026-01-31*
*Part B 계획 개선일: 2026-02-02 (plan-validator 검증 반영)*
