# Phase 4 Part E: Production Hardening

> **상태:** 📋 초안 (Idea Stage)
> **선행 조건:** Phase 4 Part A-D Complete
> **목표:** 프로덕션 안정성 확보 및 확장성 기반 구축
> **예상 기간:** 2주

---

## 개요

Phase 4 Part E는 **프로덕션 환경 준비**를 위한 안정성 및 확장성 개선 단계입니다. MCP Gateway 패턴, 비용 추적, 시맨틱 도구 라우팅, Chaos Engineering 테스트를 통해 실제 운영 환경에서의 안정성을 확보합니다.

**핵심 설계 원칙:**
- **Protocol Standards Compliance**: MCP/A2A 표준 준수 (독자 확장 금지)
- **Graceful Degradation**: 장애 시 부분 서비스 제공 (Circuit Breaker)
- **Cost Awareness**: LLM 비용 추적 및 예산 집행
- **Semantic Intelligence**: 임베딩 기반 도구 선택 (Context Overflow 방지)

---

## Step 번호 매핑

| Step | Title | 설명 |
|:----:|-------|------|
| **12** | MCP Gateway Pattern | Circuit Breaker + Rate Limiting + Fallback |
| **13** | Cost Tracking & Budgeting | LiteLLM CustomLogger 기반 비용 추적 |
| **14** | Semantic Tool Routing | Embedding 기반 도구 추천 (top-k 선택) |
| **15** | Chaos Engineering Tests | MCP 서버 장애, LLM Rate Limit 시나리오 |
| **16** | Plugin System (Mock) | 독자 확장 격리 인터페이스 (실제 구현 Phase 5) |

---

## Step 12: MCP Gateway Pattern

### 목표
MCP 서버 장애가 전체 시스템으로 전파되지 않도록 Gateway 레이어 구축

### 구현 개요

```python
# src/adapters/outbound/mcp/gateway.py
class McpGateway:
    """
    MCP 서버 앞단 Gateway (Circuit Breaker + Rate Limiting + Fallback)

    Features:
    - Circuit Breaker: 서버 장애 시 자동 차단 (Open → Half-Open → Closed)
    - Rate Limiting: 도구 호출 빈도 제한 (Token Bucket 알고리즘)
    - Request Pooling: 동일 요청 중복 방지 (LRU Cache)
    - Fallback: 백업 서버 자동 전환
    """

    def __init__(self):
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._rate_limiters: dict[str, TokenBucketRateLimiter] = {}
        self._request_cache: LRUCache = LRUCache(maxsize=1000, ttl=300)
        self._fallback_map: dict[str, str] = {}  # primary_id -> fallback_id

    async def call_tool(self, endpoint_id: str, tool_name: str, args: dict) -> Any:
        # 1. Circuit Breaker 확인
        if self._circuit_breakers[endpoint_id].is_open():
            raise CircuitOpenError(f"Circuit open for {endpoint_id}")

        # 2. Rate Limiting
        if not await self._rate_limiters[endpoint_id].allow():
            raise RateLimitExceededError(f"Too many requests to {endpoint_id}")

        # 3. Request Pooling (캐시 확인)
        cache_key = self._make_cache_key(endpoint_id, tool_name, args)
        if cached := self._request_cache.get(cache_key):
            return cached

        # 4. 실제 호출
        try:
            result = await self._do_call(endpoint_id, tool_name, args)
            self._circuit_breakers[endpoint_id].record_success()
            self._request_cache.set(cache_key, result)
            return result
        except Exception as e:
            self._circuit_breakers[endpoint_id].record_failure()

            # 5. Fallback 시도
            if fallback_id := self._fallback_map.get(endpoint_id):
                logger.warning(f"Primary {endpoint_id} failed, trying fallback {fallback_id}")
                return await self.call_tool(fallback_id, tool_name, args)
            raise


# Circuit Breaker 구현
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._timeout = timeout
        self._state = CircuitState.CLOSED
        self._opened_at: datetime | None = None

    def is_open(self) -> bool:
        if self._state == CircuitState.OPEN:
            # Half-Open 전환 확인
            if (datetime.now() - self._opened_at).seconds > self._timeout:
                self._state = CircuitState.HALF_OPEN
                return False
            return True
        return False

    def record_success(self):
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
        self._failure_count = 0

    def record_failure(self):
        self._failure_count += 1
        if self._failure_count >= self._failure_threshold:
            self._state = CircuitState.OPEN
            self._opened_at = datetime.now()
```

### DynamicToolset 통합

```python
# src/adapters/outbound/adk/dynamic_toolset.py
class DynamicToolset(BaseToolset):
    def __init__(self, cache_ttl_seconds: int = 300):
        super().__init__()
        self._gateway = McpGateway()  # Gateway 통합
        # ...

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        # Gateway를 통한 호출 (Circuit Breaker + Rate Limiting)
        for endpoint_id in self._mcp_toolsets.keys():
            try:
                return await self._gateway.call_tool(endpoint_id, tool_name, arguments)
            except CircuitOpenError:
                continue  # 다음 서버 시도
            except ToolNotFoundError:
                continue

        raise ToolNotFoundError(f"Tool not found in any server: {tool_name}")
```

### 테스트

```python
# tests/unit/adapters/test_mcp_gateway.py
async def test_circuit_breaker_opens_after_failures():
    gateway = McpGateway()

    # 5번 연속 실패 → Circuit Open
    for _ in range(5):
        with pytest.raises(Exception):
            await gateway.call_tool("endpoint1", "failing_tool", {})

    # Circuit Open 확인
    with pytest.raises(CircuitOpenError):
        await gateway.call_tool("endpoint1", "any_tool", {})

async def test_fallback_on_primary_failure():
    gateway = McpGateway()
    gateway.register_fallback("primary", "fallback")

    # Primary 실패 시 Fallback 성공
    result = await gateway.call_tool("primary", "tool", {})
    assert result == "fallback_result"
```

---

## Step 13: Cost Tracking & Budgeting

### 목표
LLM API 호출 비용을 실시간 추적하고 예산 초과 방지

### 구현 개요

```python
# src/adapters/outbound/adk/cost_tracker.py
from litellm import success_callback, failure_callback

class CostTracker:
    """
    LiteLLM Callbacks 기반 비용 추적

    Features:
    - 실시간 비용 집계 (모델별/사용자별/대화별)
    - 예산 초과 시 자동 차단 (BudgetExceededError)
    - 일일/월간 리포트 생성
    - SQLite 저장 (usage.db)
    """

    def __init__(self, budget_manager: BudgetManager, storage: UsageStorage):
        self._budget = budget_manager
        self._storage = storage

    @success_callback
    async def on_llm_success(self, kwargs, completion_response, start_time, end_time):
        """LLM 호출 성공 시 콜백"""
        # 비용 계산
        usage = completion_response.usage
        cost = usage.get("total_cost", 0.0)

        # 메타데이터 추출
        user_id = kwargs.get("metadata", {}).get("user_id", "default")
        conversation_id = kwargs.get("metadata", {}).get("conversation_id")
        model = kwargs.get("model")

        # DB 저장
        await self._storage.record_usage(
            user_id=user_id,
            conversation_id=conversation_id,
            model=model,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            cost=cost,
            latency_ms=int((end_time - start_time) * 1000),
        )

        # 예산 확인 (월별)
        monthly_usage = await self._storage.get_monthly_usage(user_id)
        if monthly_usage > self._budget.get_monthly_limit(user_id):
            raise BudgetExceededError(
                f"User {user_id} exceeded monthly budget: ${monthly_usage:.2f}"
            )

    @failure_callback
    async def on_llm_failure(self, kwargs, exception, start_time, end_time):
        """LLM 호출 실패 시 콜백"""
        logger.error(f"LLM call failed: {exception}")
        # 실패도 기록 (비용은 0)
        await self._storage.record_failure(
            user_id=kwargs.get("metadata", {}).get("user_id", "default"),
            model=kwargs.get("model"),
            error=str(exception),
        )


# 예산 관리자
class BudgetManager:
    """사용자별 예산 관리"""

    def __init__(self):
        self._limits = {
            "default": 100.0,  # $100/month
        }

    def get_monthly_limit(self, user_id: str) -> float:
        return self._limits.get(user_id, self._limits["default"])

    def set_limit(self, user_id: str, limit: float):
        self._limits[user_id] = limit
```

### ADK Orchestrator 통합

```python
# src/adapters/outbound/adk/orchestrator_adapter.py
class AdkOrchestratorAdapter(OrchestratorPort):
    async def initialize(self) -> None:
        # CostTracker 초기화 및 LiteLLM 콜백 등록
        self._cost_tracker = CostTracker(
            budget_manager=BudgetManager(),
            storage=SqliteUsageStorage("usage.db"),
        )

        import litellm
        litellm.success_callback = [self._cost_tracker.on_llm_success]
        litellm.failure_callback = [self._cost_tracker.on_llm_failure]

        # Agent 생성
        self._agent = LlmAgent(...)
```

### 테스트

```python
# tests/integration/adapters/test_cost_tracker.py
async def test_budget_exceeded_error():
    tracker = CostTracker(
        budget_manager=BudgetManager(),
        storage=FakeUsageStorage(),
    )

    # 예산 설정: $10
    tracker._budget.set_limit("user1", 10.0)

    # $11 소비 시도
    with pytest.raises(BudgetExceededError):
        await tracker.on_llm_success(
            kwargs={"metadata": {"user_id": "user1"}},
            completion_response={"usage": {"total_cost": 11.0}},
            start_time=0,
            end_time=1,
        )
```

---

## Step 14: Semantic Tool Routing

### 목표
도구 개수 증가 시 Context Overflow 방지 (Embedding 기반 top-k 선택)

### 구현 개요

```python
# src/domain/services/tool_router.py
class SemanticToolRouter:
    """
    Embedding 기반 시맨틱 도구 라우팅

    Phase 4D Step 11 (Defer Loading) 확장:
    - Defer Loading: 도구 메타데이터만 로드 (30개 초과 시)
    - Semantic Routing: 쿼리와 유사한 도구 top-k 선택
    """

    def __init__(self, embedding_model: str = "text-embedding-3-small"):
        self._embedder = OpenAIEmbeddings(model=embedding_model)
        self._tool_index: dict[str, np.ndarray] = {}  # tool_name -> embedding
        self._tool_metadata: dict[str, ToolMetadata] = {}

    async def index_tool(self, tool: Tool) -> None:
        """도구 설명 임베딩 생성 및 인덱싱"""
        description = f"{tool.name}: {tool.description}"
        embedding = await self._embedder.embed(description)

        self._tool_index[tool.name] = embedding
        self._tool_metadata[tool.name] = ToolMetadata(
            name=tool.name,
            description=tool.description,
            endpoint_id=tool.endpoint_id,
        )

    async def route(self, user_query: str, top_k: int = 5) -> list[str]:
        """사용자 쿼리와 유사한 도구 top-k 반환"""
        if not self._tool_index:
            return []

        # 쿼리 임베딩
        query_embedding = await self._embedder.embed(user_query)

        # 코사인 유사도 계산
        similarities = {
            name: self._cosine_similarity(query_embedding, tool_emb)
            for name, tool_emb in self._tool_index.items()
        }

        # Top-k 선택
        sorted_tools = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
        return [name for name, _ in sorted_tools[:top_k]]

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

### OrchestratorService 통합

```python
# src/domain/services/orchestrator.py
class OrchestratorService:
    def __init__(
        self,
        conversation_service: ConversationService,
        tool_router: SemanticToolRouter | None = None,
    ):
        self._conversation = conversation_service
        self._router = tool_router

    async def chat(self, conversation_id: str, message: str) -> AsyncIterator[StreamChunk]:
        # Semantic Routing 활성화 시
        if self._router:
            selected_tools = await self._router.route(message, top_k=5)
            # DynamicToolset에 선택된 도구만 활성화
            # (실제 구현은 DynamicToolset 확장 필요)

        # 대화 처리
        async for chunk in self._conversation.process_message(...):
            yield chunk
```

### 테스트

```python
# tests/unit/domain/services/test_tool_router.py
async def test_semantic_routing_selects_relevant_tools():
    router = SemanticToolRouter()

    # 도구 인덱싱
    await router.index_tool(Tool(name="web_search", description="Search the web for information"))
    await router.index_tool(Tool(name="calculator", description="Perform mathematical calculations"))
    await router.index_tool(Tool(name="slack_send", description="Send message to Slack channel"))

    # 쿼리: "What is 2+2?"
    selected = await router.route("What is 2+2?", top_k=2)

    # calculator가 최상위여야 함
    assert selected[0] == "calculator"
```

---

## Step 15: Chaos Engineering Tests

### 목표
프로덕션 장애 시나리오 테스트 (MCP 서버 다운, LLM Rate Limit 등)

### 구현 개요

```python
# tests/chaos/scenarios.py
import pytest
import asyncio
from httpx import AsyncClient

class ChaosScenarios:
    """프로덕션 장애 시나리오"""

    @pytest.mark.chaos
    async def test_mcp_server_sudden_death(self, client: AsyncClient, mcp_server):
        """시나리오 1: MCP 서버 갑작스런 종료"""
        # 1. 정상 상태 확인
        response = await client.post("/api/chat/stream", json={
            "conversation_id": "test",
            "message": "Use the search tool",
        })
        assert response.status_code == 200

        # 2. MCP 서버 강제 종료 (SIGKILL)
        await mcp_server.kill()

        # 3. 시스템 복구 확인 (Circuit Breaker 작동 대기)
        await asyncio.sleep(10)

        # 4. Health 엔드포인트 확인
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()

        # 5. Degraded 상태 확인 (완전 실패는 아님)
        assert data["status"] == "degraded"
        assert "mcp_server_1" in data["unavailable_services"]

        # 6. 채팅은 여전히 가능 (도구 없이)
        response = await client.post("/api/chat/stream", json={
            "conversation_id": "test",
            "message": "Hello",
        })
        assert response.status_code == 200

    @pytest.mark.chaos
    async def test_llm_rate_limit_cascade(self, client: AsyncClient):
        """시나리오 2: LLM Rate Limit → 대화 실패 폭포수"""
        # 1. 100개 동시 요청 → Rate Limit 유발
        tasks = [
            client.post("/api/chat/stream", json={
                "conversation_id": f"conv_{i}",
                "message": "Hello",
            })
            for i in range(100)
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 2. 일부는 성공, 일부는 429 에러
        success = [r for r in responses if not isinstance(r, Exception) and r.status_code == 200]
        failures = [r for r in responses if isinstance(r, Exception) or r.status_code == 429]

        # 3. 검증
        assert len(success) > 0, "At least some requests should succeed"
        assert len(failures) > 0, "Rate limiting should kick in"

        # 4. 시스템 복구 확인 (10초 후)
        await asyncio.sleep(10)
        response = await client.post("/api/chat/stream", json={
            "conversation_id": "recovery_test",
            "message": "Hello",
        })
        assert response.status_code == 200, "System should recover after cooldown"

    @pytest.mark.chaos
    async def test_concurrent_tool_calls_race_condition(self, client: AsyncClient):
        """시나리오 3: 동시 도구 호출 경쟁 조건"""
        # 동일 도구를 동시 호출 (Request Pooling 테스트)
        tasks = [
            client.post("/api/tools/call", json={
                "tool_name": "expensive_tool",
                "arguments": {"query": "same_query"},
            })
            for _ in range(50)
        ]

        responses = await asyncio.gather(*tasks)

        # 모든 응답이 동일해야 함 (캐싱)
        results = [r.json()["result"] for r in responses]
        assert len(set(results)) == 1, "All responses should be cached"
```

### CI 통합

```yaml
# .github/workflows/chaos.yml
name: Chaos Engineering Tests

on:
  schedule:
    - cron: '0 2 * * *'  # 매일 새벽 2시
  workflow_dispatch:

jobs:
  chaos:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run Chaos Tests
        run: pytest tests/chaos/ -v --tb=short -m chaos
```

---

## Step 16: Plugin System (Mock Implementation)

### 목표
독자적 확장을 격리하여 MCP/A2A 표준 준수 보장

### 설계 원칙

**Protocol Standards Compliance (CLAUDE.md Principle #7):**
- MCP 핵심 기능: 표준 준수
- A2A 프로토콜: 0.3 스펙 기반
- 독자 확장: Plugin System으로 격리

### 인터페이스 정의 (Mock)

```python
# src/domain/ports/plugin_port.py
from abc import ABC, abstractmethod
from typing import Any

class PluginInterface(ABC):
    """
    Plugin System 인터페이스 (Phase 4E Mock)

    실제 구현은 Phase 5에서 진행.
    독자적 확장(LangChain, AutoGen 등)을 MCP/A2A와 격리하여
    프로토콜 업그레이드 시 영향 최소화.
    """

    @abstractmethod
    async def initialize(self, config: dict[str, Any]) -> None:
        """플러그인 초기화"""
        pass

    @abstractmethod
    async def get_capabilities(self) -> list[str]:
        """제공 기능 목록 (예: ["langchain_agent", "retrieval_qa"])"""
        pass

    @abstractmethod
    async def execute(self, capability: str, request: dict[str, Any]) -> dict[str, Any]:
        """기능 실행"""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """리소스 정리"""
        pass


# 예시: LangChain Plugin (Mock)
class LangChainPlugin(PluginInterface):
    """LangChain 에이전트를 AgentHub에 통합 (Phase 5 구현 예정)"""

    async def initialize(self, config: dict[str, Any]) -> None:
        # from langchain.agents import initialize_agent
        # self._agent = initialize_agent(...)
        pass

    async def get_capabilities(self) -> list[str]:
        return ["langchain_agent", "retrieval_qa", "react_agent"]

    async def execute(self, capability: str, request: dict[str, Any]) -> dict[str, Any]:
        # result = await self._agent.arun(request["query"])
        # return {"result": result}
        return {"result": "mock_result"}

    async def shutdown(self) -> None:
        pass
```

### Plugin 아이디어 (Phase 5 기획 참고용)

> **주의:** 아래 아이디어는 초안 단계이며, Phase 5 계획 수립 시 참고용입니다.
> Phase 4E에서는 인터페이스 정의만 진행하고, 실제 구현은 하지 않습니다.

#### 1. Agent Framework Plugins ⭐ (최우선 후보)

**LangChain Plugin:**
```python
# 문서 검색, ReAct Agent, SQL Agent 등 제공
capabilities = [
    "langchain_retrieval_qa",    # 벡터 DB 기반 문서 QA
    "langchain_react_agent",     # 추론+행동 반복 에이전트
    "langchain_sql_agent",       # 자연어 → SQL 쿼리
]

# 사용 예시:
# "내 문서 폴더에서 'AI 윤리' 관련 내용 찾아줘"
# → LangChain RetrievalQA 실행 → 벡터 검색 결과 반환
```

**AutoGen Plugin:**
```python
# Microsoft AutoGen의 Multi-Agent 협업
capabilities = [
    "autogen_group_chat",        # 여러 에이전트 회의
    "autogen_code_executor",     # 샌드박스 코드 실행
]

# 사용 예시:
# "코드 리뷰해줘" → Coder + Reviewer 에이전트 협업
```

**CrewAI Plugin:**
```python
# 역할 기반 에이전트 팀
capabilities = [
    "crewai_research_crew",      # 리서치 → 분석 → 보고서 파이프라인
]
```

#### 2. Custom Protocol Adapters

**GraphQL Adapter Plugin:**
```python
# GraphQL API를 MCP 도구처럼 사용
# 예시: GitHub GraphQL API
capabilities = [
    "github_get_user",
    "github_list_repos",
    "github_create_issue",
]
```

**gRPC Service Plugin:**
```python
# 내부 마이크로서비스를 A2A Agent처럼 노출
# 예시: 회사 내부 gRPC 서비스 통합
```

**Legacy REST API Wrapper:**
```python
# 복잡한 인증/세션 관리를 래핑
# 예시: OAuth 2.0 기반 내부 API
```

#### 3. Domain-Specific Tools ⭐

**Code Analysis Plugin:**
```python
capabilities = [
    "analyze_complexity",           # 순환 복잡도 분석
    "detect_code_smells",           # 코드 스멜 탐지
    "generate_dependency_graph",    # 의존성 그래프
    "find_security_vulnerabilities" # Bandit 기반 보안 검사
]
```

**Data Science Plugin:**
```python
capabilities = [
    "visualize_dataframe",          # Pandas + Matplotlib 시각화
    "train_ml_model",               # Scikit-learn 모델 학습
    "statistical_analysis",         # 통계 분석
]

# 사용 예시:
# "CSV 파일 시각화해줘" → Base64 인코딩 이미지 반환
```

**Document Processing Plugin:**
```python
capabilities = [
    "extract_pdf_text",             # PyPDF2 기반 텍스트 추출
    "ocr_image",                    # Tesseract OCR
    "summarize_document",           # 문서 요약
    "translate_document",           # 다국어 번역
]
```

#### 4. UI Extension Plugins 🎨

```typescript
// Extension UI에 커스텀 컴포넌트 추가
interface UiPlugin {
  renderPanel(): React.Component;           // 커스텀 패널
  renderMessage(message): React.Component;  // 메시지 렌더러 확장
  getToolbarButtons(): ToolbarButton[];     // 툴바 버튼 추가
}

// 예시 1: Mermaid Diagram Renderer
class MermaidPlugin {
  renderMessage(message) {
    if (message.type === "mermaid_diagram") {
      return <MermaidViewer code={message.content} />;
    }
  }
}

// 예시 2: Interactive Data Table
class DataTablePlugin {
  renderMessage(message) {
    if (message.type === "dataframe") {
      return <DataGrid data={message.data} />;
    }
  }

  getToolbarButtons() {
    return [{ icon: "📊", label: "Export CSV", onClick: ... }];
  }
}
```

#### 5. Security & Compliance Plugins 🔒

**PII Redaction Plugin:**
```python
# 개인정보 자동 마스킹 (GDPR/HIPAA 준수)
capabilities = [
    "redact_pii",                   # 이메일, 전화번호 마스킹
    "detect_sensitive_data",        # 민감 데이터 탐지
]

# 사용 예시:
# 입력: "내 이메일은 user@example.com입니다"
# 출력: "내 이메일은 ***@***.***입니다"
```

**Audit Log Plugin:**
```python
# 감사 로그 자동 생성
capabilities = [
    "log_action",                   # 모든 도구 호출 기록
    "generate_compliance_report",   # 규정 준수 리포트
]
```

#### Plugin Manager Architecture

```python
# src/domain/services/plugin_manager.py
class PluginManager:
    """
    Plugin 생명주기 관리

    기능:
    - 동적 로딩/언로딩 (Hot Reload)
    - 의존성 해결
    - 격리 실행 (실패 시 Core 영향 없음)
    - Timeout 설정 (Runaway Plugin 방지)
    """

    async def register(self, plugin: PluginInterface, config: dict):
        """Plugin 등록 (실패해도 Core 계속 동작)"""
        pass

    async def execute(self, capability: str, request: dict) -> dict:
        """Capability 실행 (5분 timeout)"""
        pass
```

#### Plugin 배포 (Phase 5 검토 사항)

```yaml
# plugins/langchain-plugin.yaml
name: langchain-plugin
version: 1.0.0
author: AgentHub Community
description: LangChain integration for AgentHub

entry_point: plugins.langchain_plugin.LangChainPlugin

dependencies:
  - langchain>=0.1.0
  - chromadb>=0.4.0

capabilities:
  - name: langchain_retrieval_qa
    description: Retrieval-based QA over documents
    input_schema:
      query: string
      top_k: integer
```

```bash
# CLI로 Plugin 설치 (Phase 5 검토)
agenthub plugin install langchain-plugin

# 또는 Extension UI에서 Marketplace 통해 설치
```

#### Plugin 우선순위 (Phase 5 기획 참고)

| 우선순위 | Plugin 유형 | 이유 |
|:-------:|------------|------|
| **1** | Agent Frameworks (LangChain, AutoGen) | 고급 기능 즉시 제공 |
| **2** | Domain-Specific (Code, Data Science) | 실무 효용 높음 |
| **3** | Custom Protocol Adapters | 기업 환경 대응 |
| **4** | UI Extensions | UX 개선 |
| **5** | Security & Compliance | 엔터프라이즈 필요 시 |

### 문서화

```python
# docs/architecture/plugin-system.md (새로 생성 - Phase 5)
"""
# Plugin System Architecture

## 설계 목적

MCP/A2A 표준을 준수하면서도 독자적 확장을 허용하기 위한 격리 메커니즘.

## 지원 플러그인 유형

1. **Agent Frameworks**: LangChain, AutoGen, CrewAI
2. **Custom Protocols**: 비표준 에이전트 프로토콜
3. **Specialized Tools**: 도메인 특화 도구 (RAG, 코드 분석 등)

## 플러그인 등록

```python
plugin_manager = PluginManager()
await plugin_manager.register(LangChainPlugin(), config={...})
```

## 격리 보장

- 플러그인 실패가 Core System에 영향 없음
- MCP/A2A 표준 업그레이드 시 플러그인 독립 업데이트
"""
```

---

## 보류 항목: Event-Driven Architecture (Job Queue)

### 보류 이유

**현재 단계에서 불필요:**
- AgentHub는 **단일 사용자** 로컬 앱 (Multi-Tenancy 미지원)
- 대부분 작업이 **30초 이내** 완료 (Offscreen Document로 충분, 최대 5분 지원)
- Job Queue 도입 시 **복잡도 및 사용자 진입장벽 급증** (아래 상세 분석 참조)

**재검토 시점:**
- Multi-User Support 구현 시 (Phase 5+)
- 장시간 작업 (5분 이상) 비율이 20% 초과 시
- 백그라운드 작업 요구사항 발생 시 (예: 일괄 데이터 처리)
- **클라우드 배포 결정 시** (사용자 PC → 서버로 실행 환경 변경)

### Event-Driven Architecture 개요

**장점:**
- ✅ **비동기 작업 처리**: 시간이 오래 걸리는 작업을 백그라운드에서 실행 (5분 이상 가능)
- ✅ **확장성**: 워커 수평 확장으로 처리량 증가
- ✅ **탄력성**: 작업 실패 시 자동 재시도, 데드레터 큐

**단점:**
- ❌ **복잡도 증가**: Message Broker (Redis, RabbitMQ), Worker 프로세스 관리
- ❌ **디버깅 어려움**: 비동기 흐름 추적, 이벤트 순서 보장 어려움
- ❌ **사용자 부담 증가**: 리소스 비용, Docker 의존성, 설정 복잡도 (아래 상세 분석)

---

### ⚠️ 비용 및 복잡도 상세 분석

#### 💰 비용 부담: **사용자(이용자) 부담**

AgentHub는 **로컬 앱**이므로:
- 개발자(AgentHub)는 **소프트웨어만 제공** (오픈소스)
- 사용자가 **자신의 PC에서 인프라 실행**
- Redis, Celery Worker는 **사용자 PC 리소스 소비**

**구체적 리소스 소비:**
```
사용자 PC에서 실행되는 프로세스:
1. AgentHub Server (FastAPI)         : RAM 200MB, CPU 0.5 코어
2. Redis (Message Broker)           : RAM 500MB ~ 2GB
3. Celery Worker (1-2개)            : RAM 500MB ~ 1GB, CPU 1-2 코어
-------------------------------------------------------------
총합                                : RAM 1.2GB ~ 3.2GB, CPU 1.5-2.5 코어 상시 점유
배터리 소모                          : 백그라운드 프로세스로 20-30% 증가
```

**저사양 기기 영향:**
- RAM 8GB 노트북: **AgentHub 실행 시 다른 앱 사용 제약**
- 개발자 PC (RAM 16GB+): 문제없음
- **일반 사용자 (RAM 8GB 이하)**: 사용 불가능 수준

#### 🐳 Docker 필수 여부: **거의 필수** (95%)

**Docker 없이 설치 시 (수동 설치):**

| OS | 설치 난이도 | 예상 시간 | 일반 사용자 성공률 |
|----|:-----------:|:---------:|:----------------:|
| **Windows** | ⚠️⚠️⚠️ 매우 어려움 | 1-2시간 | **< 5%** |
| **macOS** | ⚠️⚠️ 어려움 | 30분 | **< 20%** |
| **Linux** | ⚠️ 중간 | 15분 | 50% |

**Windows 수동 설치 과정 (비개발자 관점):**
```bash
# 1. WSL 2 설치 (Windows Subsystem for Linux)
wsl --install  # Windows 재시작 필요

# 2. Ubuntu 실행 및 Redis 설치
wsl -d Ubuntu
sudo apt update
sudo apt install redis-server

# 3. Redis 서버 실행
redis-server --daemonize yes

# 4. Python 가상환경 및 Celery 설치
cd /mnt/c/Users/UserName/AgentHub
python -m venv .venv
source .venv/bin/activate
pip install celery redis

# 5. Celery Worker 실행
celery -A src.workers worker --loglevel=info

→ "WSL이 뭔가요?", "왜 Linux를 설치하나요?" 포기 😢
```

**Docker 사용 시:**
```bash
# 1. Docker Desktop 설치 (GUI 인스톨러)
# https://www.docker.com/products/docker-desktop

# 2. 프로젝트 폴더에서 실행 (클릭 한 번)
docker-compose up -d

→ 훨씬 간단하지만, Docker 설치 자체가 진입장벽 (4GB 다운로드)
```

**Docker 의존성 문제:**
- Docker Desktop 라이선스: 개인/소규모는 무료, **대기업은 유료** ($9/월)
- Docker Daemon 상시 실행: **RAM 2GB 추가 소모**
- Windows Home 에디션: Docker Desktop 미지원 (WSL 2 백엔드 필요)

#### 📉 일반 사용자 확장성: **매우 떨어짐** ❌

| 사용자 유형 | Docker 없이 | Docker 있어도 | 평가 |
|------------|:----------:|:------------:|:----:|
| **개발자** (CLI 익숙) | ⚠️ 가능 (30분 설정) | ✅ 쉬움 (5분 설정) | OK |
| **파워유저** (기술 지식 있음) | ❌ 어려움 (2시간 설정) | ⚠️ 가능 (30분 설정) | 진입장벽 높음 |
| **일반 사용자** (비개발자) | ❌ 불가능 | ❌ 거의 불가능 | **확장성 0%** |

**일반 사용자 설치 시나리오 (실패 예상):**
```
1. AgentHub 다운로드 → ✅ 성공
2. "Docker Desktop을 설치하세요" → ❓ 뭐지?
3. Docker 설치 시작 (4GB 다운로드) → ⏳ 왜 이렇게 오래 걸리지?
4. WSL 2 업데이트 필요 → 😵 무슨 말인지 모르겠음
5. docker-compose up -d 실행 → 💻 명령줄? 어디서 치나요?
6. "Redis connection refused" 에러 → 😭 포기

→ ChatGPT Desktop, Claude Desktop처럼 "설치 후 클릭만" UX 불가능
```

**결론:**
- Event-Driven 도입 시 **사용자층이 "개발자/파워유저"로 제한됨**
- 대중화 (Mass Adoption) **불가능**
- AgentHub의 목표가 "로컬 개발 도구"라면 OK
- 목표가 "일반 사용자도 쓰는 앱"이라면 **치명적 장애**

---

### 구현 예시 (참고용 - Phase 5)

```python
# src/domain/events/event_bus.py (보류)
class DomainEvent:
    event_id: str
    occurred_at: datetime
    user_id: str

class ToolCallStarted(DomainEvent):
    tool_name: str
    arguments: dict

class ToolCallCompleted(DomainEvent):
    tool_name: str
    result: Any
    duration_ms: int

# src/adapters/outbound/queue/celery_adapter.py (보류)
from celery import Celery

app = Celery('agenthub', broker='redis://localhost:6379/0')

@app.task
def execute_long_running_tool(tool_name: str, arguments: dict):
    """백그라운드 작업: 장시간 도구 실행"""
    result = tool_executor.execute(tool_name, arguments)
    # 완료 이벤트 발행
    event_bus.publish(ToolCallCompleted(...))
    return result
```

### ✅ 현재 대안: Offscreen Document (충분히 효과적)

**AgentHub는 Offscreen Document로 충분한 이유:**
- ✅ Service Worker 30초 제약 회피
- ✅ 최대 **5분 작업 지원** (브라우저 제한)
- ✅ **추가 인프라 불필요** (Redis, Docker 등)
- ✅ **사용자 진입장벽 0** (Extension 설치만으로 동작)
- ✅ **리소스 소비 최소** (RAM 200MB 이하)

**실제 사용 패턴 분석 (예상):**
```
작업 시간 분포:
- 0-30초: 85% (일반 채팅, 간단한 도구 호출)
- 30초-2분: 10% (복잡한 코드 분석, 문서 요약)
- 2-5분: 4% (대용량 데이터 처리)
- 5분 이상: 1% (극히 드문 케이스)

→ 99%의 작업이 Offscreen Document로 처리 가능
```

**5분 초과 작업 발생 시 점진적 대응 (Event-Driven 도입 전):**

1. **Phase 4: 사용자 피드백 수집**
   - 작업 시간 모니터링 및 로깅
   - 5분 초과 작업 비율 측정

2. **Phase 5: Lightweight Job Queue**
   - SQLite 기반 Job 테이블 (Redis 불필요)
   - FastAPI Background Tasks 활용
   - Job ID 반환 후 폴링 (`GET /api/jobs/{id}/status`)
   - 완료 시 Browser Notification

3. **Phase 6: Full Event-Driven (조건부)**
   - **조건 1**: 5분 이상 작업이 20% 초과
   - **조건 2**: 클라우드 배포 결정 (사용자 PC → 서버)
   - **조건 3**: Multi-User 지원 필요성 확인

**Lightweight Job Queue 예시 (Event-Driven보다 단순):**
```python
# SQLite만으로 구현 (Redis 불필요)
@router.post("/api/chat/async")
async def chat_async(body: ChatRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())

    # FastAPI Background Task (별도 Worker 프로세스 불필요)
    background_tasks.add_task(execute_chat_task, job_id, body.message)

    return {"job_id": job_id, "status": "queued"}

# SQLite에 Job 상태 저장
async def execute_chat_task(job_id: str, message: str):
    await job_storage.update(job_id, status="running")
    try:
        result = await orchestrator.process_message(message)
        await job_storage.update(job_id, status="completed", result=result)
    except Exception as e:
        await job_storage.update(job_id, status="failed", error=str(e))
```

**결론:**
- 현재 단계: **Offscreen Document로 충분**
- 문제 발생 시: **Lightweight Job Queue** (Redis 없이)
- 최후 수단: **Full Event-Driven** (클라우드 배포 시)

---

## DoD (Definition of Done)

### Part E 전체

- [ ] MCP Gateway 구현 및 테스트 (Circuit Breaker, Rate Limiting, Fallback)
- [ ] Cost Tracker 구현 및 LiteLLM 통합
- [ ] Semantic Tool Router 구현 및 임베딩 인덱싱
- [ ] Chaos Engineering 시나리오 3개 통과 (MCP 다운, LLM Rate Limit, Race Condition)
- [ ] Plugin System 인터페이스 정의 (Mock 구현)
- [ ] Backend coverage >= 90% 유지
- [ ] 문서화: Plugin 아이디어 정리 (본 파일 Step 16에 포함 완료)
- [ ] 문서화: Event-Driven 보류 사유 상세 분석 (본 파일에 포함 완료)
- [ ] 문서화: `docs/architecture/plugin-system.md` 생성 (Phase 5 기획 시 작성)

### 검증 명령어

```bash
# 전체 테스트 + 커버리지
pytest tests/ --cov=src --cov-fail-under=90 -q --tb=line -x

# Chaos Tests
pytest tests/chaos/ -v -m chaos

# Gateway 테스트
pytest tests/unit/adapters/test_mcp_gateway.py -v

# Cost Tracker 테스트
pytest tests/integration/adapters/test_cost_tracker.py -v
```

---

## 참고 자료

### Production Hardening
- [15 Best Practices for Production MCP Servers](https://thenewstack.io/15-best-practices-for-building-mcp-servers-in-production/)
- [What It Takes to Run MCP in Production](https://bytebridge.medium.com/what-it-takes-to-run-mcp-model-context-protocol-in-production-3bbf19413f69)
- [Circuit Breaker Pattern - Martin Fowler](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Chaos Engineering Principles](https://principlesofchaos.org/)

### Observability & Cost Tracking
- [LiteLLM Callbacks](https://docs.litellm.ai/docs/observability/callbacks)
- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)

### Plugin System & Agent Frameworks
- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [CrewAI Documentation](https://docs.crewai.com/)
- [Plugin Architecture Best Practices](https://www.oreilly.com/library/view/software-architecture-patterns/9781491971437/ch05.html)

### Event-Driven Architecture
- [Celery Documentation](https://docs.celeryq.dev/)
- [Redis Documentation](https://redis.io/docs/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

---

*작성일: 2026-01-31*
*상태: 초안 (Idea Stage)*
