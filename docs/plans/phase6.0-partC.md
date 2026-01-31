# Phase 6 Part C: Plugin System (Steps 9-12)

> **상태:** 📋 Planned
> **선행 조건:** Phase 5 Part A Complete (테스트 인프라)
> **목표:** 독립 Port 인터페이스 기반 Plugin System, Echo/Chat 테스트 플러그인
> **예상 테스트:** ~17 신규
> **실행 순서:** Step 9 → Step 10 → Step 11 → Step 12
> **병렬:** Phase 6 Part B와 병렬 가능

---

## 🎯 Progress Checklist

| Step | 내용 | 상태 |
|:----:|------|:----:|
| **9** | PluginPort Interface | ⬜ |
| **10** | PluginToolset (ADK BaseToolset) | ⬜ |
| **11** | Echo + LangChain Tool Plugins | ⬜ |
| **12** | Plugin Management API + Extension UI | ⬜ |

---

## 아키텍처: Option 2 (독립 Port Interface)

**채택 결정 (ADR-7):** PluginPort를 별도 Domain Port로 정의. 독립 인프라 (DynamicToolset과 비공유).

**범위 명확화 (ADR-9):**
- Plugin = **프로세스 내 개별 도구 확장** (LangChain Tool, REST wrapper, 사용자 정의 함수)
- Plugin ≠ **외부 에이전트** (LangGraph, CrewAI 등 → A2A 프로토콜로 통합)
- 참조: [ADR-0009](../../decisions/0009-langgraph-a2a-not-plugin.md)

```
Plugin (LangChain Tool/REST) → PluginPort → PluginToolset(BaseToolset) → ADK Agent
                                                                           ↑
MCP Server → ToolsetPort → DynamicToolset ─────────────────────────────────┘
                                                                           ↑
A2A Agent (LangGraph 등) → RemoteA2aAgent ─────────────────────── sub_agents
```

**Phase 8 호환성:** `AGENTHUB_TOOLS` 컨벤션으로 동적 로딩 준비.

---

## Step 9: PluginPort Interface

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/domain/ports/outbound/plugin_port.py` | NEW | PluginPort 인터페이스 |
| `src/domain/entities/plugin.py` | NEW | Plugin, PluginConfig 엔티티 (순수 Python) |
| `tests/unit/domain/entities/test_plugin.py` | NEW | Plugin 엔티티 테스트 |

**핵심 설계:**
```python
# src/domain/entities/plugin.py
@dataclass
class PluginConfig:
    """Plugin 등록 설정"""
    name: str
    plugin_type: str  # "echo", "langchain", "rest"
    config: dict[str, Any] = field(default_factory=dict)

@dataclass
class Plugin:
    """Plugin 도메인 엔티티"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    plugin_type: str = ""
    enabled: bool = True
    tools: list[Tool] = field(default_factory=list)
    status: str = "unknown"  # "active", "error", "disabled"

# src/domain/ports/outbound/plugin_port.py
class PluginPort(ABC):
    @abstractmethod
    async def register_plugin(self, config: PluginConfig) -> Plugin: ...
    @abstractmethod
    async def unregister_plugin(self, plugin_id: str) -> bool: ...
    @abstractmethod
    async def list_plugins(self) -> list[Plugin]: ...
    @abstractmethod
    async def get_tools(self, plugin_id: str) -> list[Tool]: ...
    @abstractmethod
    async def call_tool(self, plugin_id: str, tool_name: str, args: dict) -> Any: ...
    @abstractmethod
    async def health_check(self, plugin_id: str) -> bool: ...
```

**TDD 순서:**
1. RED: `test_plugin_config_creation`
2. RED: `test_plugin_entity_defaults`
3. RED: `test_plugin_port_interface_methods`
4. GREEN: 엔티티 + Port 구현

**DoD:**
- [ ] PluginPort ABC 정의
- [ ] Plugin, PluginConfig 엔티티 정의
- [ ] 엔티티 테스트 통과

---

## Step 10: PluginToolset (ADK BaseToolset)

**목표:** ADK BaseToolset 상속, 독립적 cache/retry/circuit breaker 구현

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/outbound/plugins/__init__.py` | NEW | Plugin 어댑터 패키지 |
| `src/adapters/outbound/plugins/plugin_toolset.py` | NEW | PluginToolset(BaseToolset) |
| `src/adapters/outbound/plugins/base_plugin.py` | NEW | BasePluginAdapter ABC |
| `src/adapters/outbound/adk/orchestrator_adapter.py` | MODIFY | tools에 plugin_toolset 추가 |
| `src/config/container.py` | MODIFY | plugin_toolset 프로바이더 추가 |
| `src/config/settings.py` | MODIFY | PluginSettings 추가 |
| `tests/unit/adapters/test_plugin_toolset.py` | NEW | PluginToolset 테스트 |

**핵심 설계:**
```python
# src/adapters/outbound/plugins/plugin_toolset.py
class PluginToolset(BaseToolset):
    """독립 Plugin 툴셋 (DynamicToolset과 별도 인프라)"""

    def __init__(self, settings: PluginSettings):
        super().__init__()
        self._plugins: dict[str, BasePluginAdapter] = {}
        self._tool_cache: dict[str, list[BaseTool]] = {}
        self._cache_ttl = settings.cache_ttl_seconds
        self._max_retries = settings.max_retries
        # 독립 Circuit Breaker (per-plugin)
        self._circuit_breakers: dict[str, CircuitBreaker] = {}

    async def get_tools(self, readonly_context=None) -> list[BaseTool]:
        """등록된 모든 플러그인의 도구 반환 (캐싱)"""
        all_tools = []
        for plugin_id, plugin in self._plugins.items():
            if self._is_cache_valid(plugin_id):
                all_tools.extend(self._tool_cache[plugin_id])
            else:
                tools = await plugin.get_tools()
                self._tool_cache[plugin_id] = tools
                all_tools.extend(tools)
        return all_tools

# Orchestrator 변경
self._agent = LlmAgent(
    model=LiteLlm(model=self._model_name),
    instruction=dynamic_instruction,
    tools=[self._dynamic_toolset, self._plugin_toolset],  # 양쪽 모두
    sub_agents=list(self._sub_agents.values()),
)
```

**TDD 순서:**
1. RED: `test_plugin_toolset_returns_empty_initially`
2. RED: `test_plugin_toolset_caches_tools`
3. RED: `test_plugin_toolset_retry_on_transient_error`
4. RED: `test_plugin_toolset_circuit_breaker`
5. RED: `test_orchestrator_includes_plugin_toolset`
6. RED: `test_plugin_toolset_independent_from_dynamic`
7. GREEN: 모든 구현

**DoD:**
- [ ] PluginToolset이 ADK Agent에 통합
- [ ] 독립적 cache, retry, circuit breaker 동작
- [ ] DynamicToolset과 독립적으로 동작

---

## Step 11: Echo + LangChain Tool Plugins

> **범위 (ADR-9):** LangChain **개별 Tool** 래핑만. LangGraph Agent는 A2A로 통합 (Phase 3 완료).

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/outbound/plugins/echo_plugin.py` | NEW | Echo Plugin |
| `src/adapters/outbound/plugins/langchain_tool_plugin.py` | NEW | LangChain 개별 Tool Plugin |
| `tests/unit/adapters/test_echo_plugin.py` | NEW | Echo Plugin 테스트 |
| `tests/unit/adapters/test_langchain_tool_plugin.py` | NEW | LangChain Tool Plugin 테스트 |

**Echo Plugin:**
```python
class EchoPlugin(BasePluginAdapter):
    """단순 Echo 플러그인 (테스트용)"""
    async def get_tools(self) -> list[BaseTool]:
        return [EchoTool()]  # "echo" 도구: 입력 그대로 반환
```

**LangChain Tool Plugin (Phase 8 호환):**
```python
class LangChainToolPlugin(BasePluginAdapter):
    """
    LangChain 개별 Tool 래핑 Plugin (AGENTHUB_TOOLS 컨벤션)

    대상: WikipediaQueryRun, RequestsGet 등 개별 Tool
    비대상: LangGraph Agent (→ A2A 프로토콜로 통합, ADR-9 참조)
    """

    def __init__(self, config: PluginConfig):
        # config.config["tools"] = list of LangChain Tool definitions
        self._tools = self._wrap_langchain_tools(config.config.get("tools", []))

    def _wrap_langchain_tools(self, tools: list) -> list[BaseTool]:
        """LangChain Tool → ADK BaseTool 래핑"""
        return [LangChainToolWrapper(t) for t in tools]
```

**TDD 순서:**
1. RED: `test_echo_plugin_returns_tool`
2. RED: `test_echo_tool_echoes_input`
3. RED: `test_langchain_plugin_wraps_tools`
4. RED: `test_langchain_tool_execution`
5. GREEN: 양쪽 플러그인 구현

**DoD:**
- [ ] Echo Plugin: echo 도구 동작
- [ ] LangChain Tool Plugin: LangChain 개별 Tool 래핑 동작 (WikipediaQueryRun 등)
- [ ] `AGENTHUB_TOOLS` 컨벤션 준수 (Phase 8 호환)
- [ ] LangGraph Agent는 Plugin 대상에서 제외 (A2A 사용, ADR-9)

---

## Step 12: Plugin Management API + Extension UI

**수정 파일:**

| 파일 | 작업 | 변경 내용 |
|------|:----:|----------|
| `src/adapters/inbound/http/routes/plugins.py` | NEW | Plugin CRUD API |
| `extension/components/PluginManager.tsx` | NEW | Plugin 관리 UI |
| `extension/lib/types.ts` | MODIFY | Plugin TypeScript 타입 |
| `tests/integration/adapters/test_plugin_api.py` | NEW | Plugin API 통합 테스트 |

**API 엔드포인트:**
- `POST /api/plugins` - 플러그인 등록
- `GET /api/plugins` - 플러그인 목록
- `DELETE /api/plugins/{id}` - 플러그인 해제
- `GET /api/plugins/{id}/tools` - 플러그인 도구 목록
- `GET /api/plugins/{id}/health` - 상태 확인

**Extension UI:**
- Sidepanel에 "Plugins" 탭 추가
- 플러그인 등록/해제 UI
- 플러그인별 도구 목록 + 상태 표시

**DoD:**
- [ ] CRUD API 동작
- [ ] Extension에서 플러그인 관리 가능
- [ ] 플러그인 상태 및 도구 목록 표시

---

## Part C Definition of Done

### 기능
- [ ] PluginPort 인터페이스 정의
- [ ] PluginToolset 독립 동작 (cache, retry, CB)
- [ ] Echo + LangChain Tool 플러그인 (개별 Tool만, ADR-9)
- [ ] Plugin CRUD API + Extension UI

### 품질
- [ ] 17+ 테스트 추가
- [ ] Coverage >= 90% 유지
- [ ] Phase 8 dynamic loading 호환 설계

---

## 리스크 및 대응

| 리스크 | 심각도 | 대응 |
|--------|:------:|------|
| ADK BaseToolset 복수 등록 지원 여부 | 🟡 | 웹 검색 확인, 미지원 시 합성 toolset |
| LangChain 의존성 버전 충돌 | 🟡 | 별도 requirements, 격리된 import |
| Plugin 도구와 MCP 도구 이름 충돌 | 🟢 | 네임스페이스 prefix (plugin:{name}) |

---

*Part C 계획 작성일: 2026-01-31*
