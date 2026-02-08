# Plan 11: MCP App UI Rendering (Draft)

> **상태:** 📋 Draft
> **선행 조건:** Plan 07 Complete (MCP SDK 통합)
> **목표:** MCP App의 실제 UI 렌더링 지원 (Playground + Extension)

---

## Overview

**핵심 문제:**
- 현재: MCP Apps의 UI 정의는 받지만, 렌더링하지 않음
- 필요: MCP Apps의 UI Schema를 파싱하여 실제 UI로 렌더링

**구현 범위:**
1. **McpAppUiSchema Domain Model**: MCP App UI 정의 (JSON Schema)
2. **McpAppUiService**: UI Schema 파싱 및 변환
3. **McpAppUiRenderingAdapter**: HTML/React 컴포넌트 렌더링
4. **Playground UI**: MCP App UI Renderer 탭 (Phase 6)
5. **Extension UI**: MCP App UI 모달 (추후)

**참고:**
- MCP Apps Protocol: https://modelcontextprotocol.io/docs/concepts/apps
- UI Schema 표준은 빠르게 진화 중 → Plan Phase에서 웹 검색 검증 필수

---

## Key Features

### 1. McpAppUiSchema Domain Model

**Domain Entity:**
```python
@dataclass
class McpAppUiSchema:
    """MCP App UI 정의 (순수 Python)"""
    app_id: str
    schema_version: str  # "1.0", "1.1", etc.
    ui_type: str  # "form", "chart", "table", "markdown", etc.
    components: list[UiComponent]
    actions: list[UiAction]

@dataclass
class UiComponent:
    """UI 컴포넌트 (입력 필드, 버튼, 차트 등)"""
    component_id: str
    component_type: str  # "text", "number", "select", "button", etc.
    label: str
    properties: dict[str, Any]  # 컴포넌트별 속성

@dataclass
class UiAction:
    """사용자 액션 (Submit, Cancel, etc.)"""
    action_id: str
    action_type: str  # "submit", "cancel", "reset", etc.
    target_tool: str | None  # MCP Tool 호출 대상
```

### 2. McpAppUiService

**Domain Service:**
```python
class McpAppUiService:
    """UI Schema 파싱 및 변환"""

    def parse_schema(self, raw_schema: dict) -> McpAppUiSchema:
        """MCP App raw schema → Domain entity"""

    def validate_schema(self, schema: McpAppUiSchema) -> bool:
        """UI Schema 유효성 검증 (버전, 타입 체크)"""

    def extract_actions(self, schema: McpAppUiSchema) -> list[UiAction]:
        """액션 목록 추출 (Submit, Cancel 등)"""
```

### 3. McpAppUiRenderingAdapter

**Adapter (Outbound):**
```python
class McpAppUiRenderingAdapter:
    """HTML/React 컴포넌트 렌더링"""

    def render_html(self, schema: McpAppUiSchema) -> str:
        """Playground용 HTML 생성 (Jinja2 템플릿)"""

    def render_react_schema(self, schema: McpAppUiSchema) -> dict:
        """Extension용 React 컴포넌트 스키마 생성"""
```

**렌더링 전략:**
- **Playground**: Server-side 렌더링 (Jinja2) → HTML 반환
- **Extension**: Client-side 렌더링 (React) → JSON Schema 반환 → Extension에서 렌더링

### 4. Playground UI (Phase 6)

**MCP App UI Renderer 탭:**
```
[ MCP App UI ]

App: [ filesystem-app v ]

┌────────────────────────────────────────┐
│  [렌더링된 UI가 여기에 표시됩니다]       │
│                                        │
│  예: Form (Name, Path, Permissions)   │
│                                        │
│  [ Submit ]  [ Cancel ]                │
└────────────────────────────────────────┘

Result:
{
  "status": "success",
  "data": {...}
}
```

### 5. Extension UI (추후)

**MCP App UI Modal:**
- Full-screen modal
- React 컴포넌트로 렌더링
- 액션 핸들러 (Submit → MCP Tool 호출)

---

## Phases (Preliminary)

| Phase | 설명 | Playground | Status |
|-------|------|------------|--------|
| **1** | Domain Entities (McpAppUiSchema, UiComponent, UiAction) | - | ⏸️ |
| **2** | Port Interface (McpAppUiRenderingPort) | - | ⏸️ |
| **3** | Domain Services (McpAppUiService) | - | ⏸️ |
| **4** | Adapter Implementation (Jinja2 Rendering, React Schema) | - | ⏸️ |
| **5** | Integration (DI Container) | - | ⏸️ |
| **6** | HTTP Routes + Playground UI | ✅ | ⏸️ |
| **7** | E2E Tests + Extension UI (Production Phase) | ✅ | ⏸️ |

**Phase 상세는 Plan 승인 후 작성 예정**

---

## Design Considerations

### UI Schema Standards Verification

**중요:** MCP App UI Schema는 빠르게 진화하는 표준입니다.

**Plan Phase (웹 검색):**
1. MCP Apps Protocol 최신 스펙 확인
2. UI Schema 버전 확인 (1.0, 1.1, etc.)
3. 지원 컴포넌트 타입 확인 (form, chart, table, etc.)

**Implementation Phase (재검증):**
1. API 메서드명/파라미터 재확인
2. Schema 필드명 재확인

**검색 키워드:**
- "MCP Apps UI Schema spec 2026"
- "Model Context Protocol Apps UI rendering"

### Supported Component Types (Preliminary)

| 타입 | 설명 | 예시 |
|------|------|------|
| **text** | 텍스트 입력 | Name, Description |
| **number** | 숫자 입력 | Age, Amount |
| **select** | 드롭다운 | Country, Category |
| **checkbox** | 체크박스 | Agree, Enable |
| **radio** | 라디오 버튼 | Gender, Priority |
| **button** | 버튼 | Submit, Cancel |
| **markdown** | Markdown 렌더링 | Instructions |
| **chart** | 차트 (Chart.js) | Line, Bar, Pie |
| **table** | 테이블 | Data Grid |

**주의:** 실제 지원 타입은 MCP 스펙 확인 후 결정

### Rendering Strategy

**Playground (Server-side):**
```python
# Jinja2 템플릿 예시
<form id="mcp-app-{{ app_id }}">
  {% for component in schema.components %}
    {% if component.component_type == "text" %}
      <label>{{ component.label }}</label>
      <input type="text" name="{{ component.component_id }}" />
    {% elif component.component_type == "select" %}
      <label>{{ component.label }}</label>
      <select name="{{ component.component_id }}">
        {% for option in component.properties.options %}
          <option value="{{ option.value }}">{{ option.label }}</option>
        {% endfor %}
      </select>
    {% endif %}
  {% endfor %}

  {% for action in schema.actions %}
    <button type="{{ action.action_type }}">{{ action.label }}</button>
  {% endfor %}
</form>
```

**Extension (Client-side):**
```typescript
// React Schema 예시
{
  "appId": "filesystem-app",
  "components": [
    {
      "componentId": "name",
      "componentType": "text",
      "label": "Name",
      "properties": {}
    },
    {
      "componentId": "path",
      "componentType": "text",
      "label": "Path",
      "properties": {"placeholder": "/path/to/file"}
    }
  ],
  "actions": [
    {"actionId": "submit", "actionType": "submit", "label": "Submit"},
    {"actionId": "cancel", "actionType": "cancel", "label": "Cancel"}
  ]
}
```

### Security

**XSS 방지:**
- Jinja2 자동 이스케이프 활성화
- React는 기본적으로 XSS 방지

**Schema 검증:**
- UI Schema 버전 체크 (지원되는 버전만 허용)
- 컴포넌트 타입 화이트리스트 검증
- 악의적인 스크립트 삽입 방지

---

## Example: MCP App UI Flow

### 1. MCP Server → AgentHub (UI Schema 제공)

```json
// MCP App UI Schema (raw)
{
  "appId": "filesystem-app",
  "schemaVersion": "1.0",
  "uiType": "form",
  "components": [
    {
      "componentId": "path",
      "componentType": "text",
      "label": "File Path",
      "properties": {"required": true}
    },
    {
      "componentId": "permissions",
      "componentType": "select",
      "label": "Permissions",
      "properties": {
        "options": [
          {"value": "read", "label": "Read Only"},
          {"value": "write", "label": "Read & Write"}
        ]
      }
    }
  ],
  "actions": [
    {"actionId": "submit", "actionType": "submit", "targetTool": "filesystem_write"},
    {"actionId": "cancel", "actionType": "cancel"}
  ]
}
```

### 2. AgentHub → Playground (렌더링된 HTML)

```html
<form id="mcp-app-filesystem-app">
  <label>File Path</label>
  <input type="text" name="path" required />

  <label>Permissions</label>
  <select name="permissions">
    <option value="read">Read Only</option>
    <option value="write">Read & Write</option>
  </select>

  <button type="submit">Submit</button>
  <button type="button" onclick="cancel()">Cancel</button>
</form>
```

### 3. User → AgentHub (폼 제출)

```json
// POST /api/mcp-app-ui/{app_id}/submit
{
  "path": "/path/to/file.txt",
  "permissions": "write"
}
```

### 4. AgentHub → MCP Server (Tool 호출)

```json
// tools/call: filesystem_write
{
  "name": "filesystem_write",
  "arguments": {
    "path": "/path/to/file.txt",
    "permissions": "write"
  }
}
```

---

## Testing Strategy

### Unit Tests

**Domain:**
- `test_mcp_app_ui_schema_creation`
- `test_ui_component_types`
- `test_ui_action_validation`

**Service:**
- `test_parse_schema`
- `test_validate_schema_version`
- `test_extract_actions`

### Integration Tests

**Rendering:**
- `test_render_html_form` (Jinja2)
- `test_render_react_schema`
- `test_render_chart_component`

**Marker:**
- (default - 외부 의존성 없음)

### E2E Tests (Playwright)

**Playground:**
- `test_playground_mcp_app_ui_tab`
- `test_mcp_app_ui_form_submission`
- `test_mcp_app_ui_chart_rendering`

---

## Risks

| 위험 | 심각도 | 대응 |
|------|:------:|------|
| MCP App UI Schema 표준 변경 | 🔴 | 스펙 웹 검색 검증 (Plan + Implementation Phase) |
| 지원하지 않는 컴포넌트 타입 | 🟡 | 화이트리스트 검증 + 에러 핸들링 |
| XSS 공격 (악의적 Schema) | 🟠 | Jinja2 자동 이스케이프 + Schema 검증 |
| Rendering 성능 이슈 (복잡한 UI) | 🟢 | Lazy loading + 페이지네이션 |

---

## Definition of Done

### Functionality
- [ ] MCP App UI Schema 파싱 동작
- [ ] Playground UI 렌더링 동작 (Form, Chart, Table)
- [ ] 폼 제출 → MCP Tool 호출 동작
- [ ] React Schema 생성 동작 (Extension용)
- [ ] Schema 유효성 검증 동작

### Quality
- [ ] Backend coverage >= 80%
- [ ] Playground E2E 테스트 통과
- [ ] TDD Red-Green-Refactor 사이클 준수

### Documentation
- [ ] `docs/developers/guides/standards/mcp/README.md` 업데이트 (MCP Apps UI)
- [ ] `extension/README.md` 업데이트 (MCP App UI 기능)
- [ ] ADR 작성 (렌더링 전략, 보안 검증)

---

## Related Plans

- **Plan 07**: Hybrid-Dual Architecture (선행 조건 - MCP SDK)
- **Plan 09**: Dynamic Configuration (독립적, 병렬 가능)
- **Plan 10**: stdio Transport (독립적, 병렬 가능)

---

*Draft Created: 2026-02-07*
*Next: MCP Apps UI Schema 스펙 확인 → Plan 승인 후 Phase 상세 계획 작성*
