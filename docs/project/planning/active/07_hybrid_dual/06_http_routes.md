# Phase 6: HTTP Routes + Playground (Playground-First Testing)

## 개요

SDK Track API와 Playground UI를 함께 구현합니다.

**Playground-First Principle:**
- Backend API 구현 → Playground UI 추가 → E2E 테스트 작성 → 즉시 회귀 테스트
- Extension UI는 Production Phase로 연기

**핵심:**
- Resources API + Playground Tab
- Prompts API + Playground Tab
- Sampling HITL API (Method C 적용) + Playground Tab
- Elicitation HITL API + Playground Tab
- MCP Apps Raw 응답 (resource로 제공, 별도 API 불필요)

---

## Step 6.1: Resources API + Playground Tab

**파일:**
- `src/adapters/inbound/http/schemas/resources.py` (Response Models)
- `src/adapters/inbound/http/routes/resources.py` (Routes)

**테스트:** `tests/integration/test_resources_routes.py` + `tests/e2e/test_playground.py`

### Response Models

```python
# src/adapters/inbound/http/schemas/resources.py
"""Resource API Response Schemas"""

from pydantic import BaseModel

from src.domain.entities.resource import Resource, ResourceContent


class ResourceSchema(BaseModel):
    """Resource 응답 스키마"""

    uri: str
    name: str
    description: str
    mime_type: str | None = None

    @classmethod
    def from_entity(cls, resource: Resource) -> "ResourceSchema":
        """Domain Entity → HTTP Response Schema"""
        return cls(
            uri=resource.uri,
            name=resource.name,
            description=resource.description,
            mime_type=resource.mime_type or None,  # L1 수정: 빈 문자열 → None
        )


class ResourceContentSchema(BaseModel):
    """ResourceContent 응답 스키마"""

    uri: str
    mime_type: str | None = None
    text: str | None = None
    blob: str | None = None  # Base64 인코딩된 바이너리

    @classmethod
    def from_entity(cls, content: ResourceContent) -> "ResourceContentSchema":
        """Domain Entity → HTTP Response Schema (H4 수정: Base64 인코딩)"""
        import base64

        blob_str = base64.b64encode(content.blob).decode("ascii") if content.blob else None

        return cls(
            uri=content.uri,
            mime_type=content.mime_type,
            text=content.text,
            blob=blob_str,
        )


class ResourceListResponse(BaseModel):
    """Resource 목록 응답"""

    resources: list[ResourceSchema]
```

### API 구현

```python
# src/adapters/inbound/http/routes/resources.py
from fastapi import APIRouter, Depends, HTTPException
from dependency_injector.wiring import inject, Provide
from src.config.container import Container
from src.domain.services.resource_service import ResourceService
from src.domain.exceptions import EndpointNotFoundError, ResourceNotFoundError
from src.adapters.inbound.http.schemas.resources import (
    ResourceSchema,
    ResourceContentSchema,
    ResourceListResponse,
)

router = APIRouter(prefix="/api/mcp/servers", tags=["resources"])

@router.get("/{endpoint_id}/resources", response_model=ResourceListResponse)
@inject
async def list_resources(
    endpoint_id: str,
    resource_service: ResourceService = Depends(Provide[Container.resource_service]),
):
    """리소스 목록 조회"""
    try:
        resources = await resource_service.list_resources(endpoint_id)
        return ResourceListResponse(
            resources=[ResourceSchema.from_entity(r) for r in resources]
        )
    except EndpointNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{endpoint_id}/resources/{uri:path}", response_model=ResourceContentSchema)
@inject
async def read_resource(
    endpoint_id: str,
    uri: str,
    resource_service: ResourceService = Depends(Provide[Container.resource_service]),
):
    """리소스 콘텐츠 읽기"""
    try:
        content = await resource_service.read_resource(endpoint_id, uri)
        return ResourceContentSchema.from_entity(content)
    except (EndpointNotFoundError, ResourceNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### Integration 테스트

```python
# tests/integration/test_resources_routes.py

import pytest
from httpx import AsyncClient
from src.adapters.inbound.http.app import app

class TestResourcesRoutes:
    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture
    async def registered_mcp_endpoint(self, client):
        """Synapse 엔드포인트 등록 fixture"""
        response = await client.post("/api/endpoints", json={
            "url": "http://localhost:9000/mcp",
            "type": "mcp",
        })
        return response.json()

    @pytest.mark.local_mcp
    async def test_list_resources_returns_list(self, client, registered_mcp_endpoint):
        """리소스 목록 조회 성공"""
        response = await client.get(f"/api/mcp/servers/{registered_mcp_endpoint['id']}/resources")

        assert response.status_code == 200
        assert "resources" in response.json()
        assert len(response.json()["resources"]) > 0

    async def test_list_resources_not_found(self, client):
        """존재하지 않는 엔드포인트 → 404"""
        response = await client.get("/api/mcp/servers/nonexistent/resources")
        assert response.status_code == 404

    @pytest.mark.local_mcp
    async def test_read_resource_returns_content(self, client, registered_mcp_endpoint):
        """리소스 읽기 성공"""
        # 먼저 목록 조회
        list_response = await client.get(f"/api/mcp/servers/{registered_mcp_endpoint['id']}/resources")
        resources = list_response.json()["resources"]
        test_uri = resources[0]["uri"]

        # 리소스 읽기
        response = await client.get(
            f"/api/mcp/servers/{registered_mcp_endpoint['id']}/resources/{test_uri}"
        )

        assert response.status_code == 200
        assert ("text" in response.json()) or ("blob" in response.json())
```

### Playground UI

**파일:** `tests/manual/playground/index.html`, `tests/manual/playground/js/main.js`

**HTML Tab:**
```html
<button class="tab-btn" data-tab="resources" data-testid="tab-resources">Resources</button>

<div id="resources-tab" class="tab-pane">
    <h2>MCP Resources</h2>
    <div class="form-group">
        <label>MCP Server:</label>
        <select data-testid="resources-endpoint-select"></select>
        <button data-testid="resources-list-btn">List Resources</button>
    </div>
    <div class="resources-list" data-testid="resources-list"></div>
    <div class="resource-content" data-testid="resource-content"></div>
</div>
```

**JavaScript:**
```javascript
// tests/manual/playground/js/main.js

async function listResources() {
    const endpointId = document.querySelector('[data-testid="resources-endpoint-select"]').value;
    const response = await fetch(`${API_BASE}/api/mcp/servers/${endpointId}/resources`);
    const data = await response.json();
    renderResourcesList(data.resources);
}

function renderResourcesList(resources) {
    const listEl = document.querySelector('[data-testid="resources-list"]');
    listEl.innerHTML = resources.map(r => `
        <div class="resource-card" data-uri="${r.uri}">
            <h4>${r.name}</h4>
            <p>${r.description}</p>
            <button onclick="readResource('${r.uri}')">Read</button>
        </div>
    `).join('');
}
```

### E2E 테스트

```python
# tests/e2e/test_playground.py

import pytest
from playwright.async_api import async_playwright

@pytest.mark.e2e_playwright
class TestPlaygroundResources:
    async def test_list_resources_displays_cards(self, page, registered_mcp_endpoint):
        """Resources 탭에서 리소스 목록 표시"""
        await page.goto("http://localhost:3000")
        await page.click('[data-testid="tab-resources"]')

        # Endpoint 선택
        await page.select_option('[data-testid="resources-endpoint-select"]', registered_mcp_endpoint['id'])
        await page.click('[data-testid="resources-list-btn"]')

        # 리소스 카드 확인
        resource_cards = await page.locator('.resource-card').all()
        assert len(resource_cards) > 0
```

---

## Step 6.2: Prompts API + Playground Tab

**파일:**
- `src/adapters/inbound/http/schemas/prompts.py` (Response Models)
- `src/adapters/inbound/http/routes/prompts.py` (Routes)

**테스트:** `tests/integration/test_prompts_routes.py` + E2E

### Response Models

```python
# src/adapters/inbound/http/schemas/prompts.py
"""Prompt API Response Schemas"""

from pydantic import BaseModel

from src.domain.entities.prompt_template import PromptTemplate, PromptArgument  # C3 수정


class PromptArgumentSchema(BaseModel):
    """PromptArgument 응답 스키마"""

    name: str
    required: bool = True
    description: str = ""


class PromptTemplateSchema(BaseModel):
    """PromptTemplate 응답 스키마"""

    name: str
    description: str = ""
    arguments: list[PromptArgumentSchema]

    @classmethod
    def from_entity(cls, prompt: PromptTemplate) -> "PromptTemplateSchema":
        """Domain Entity → HTTP Response Schema"""
        return cls(
            name=prompt.name,
            description=prompt.description,
            arguments=[
                PromptArgumentSchema(
                    name=arg.name,
                    required=arg.required,
                    description=arg.description,
                )
                for arg in prompt.arguments
            ],
        )


class PromptListResponse(BaseModel):
    """Prompt 목록 응답"""

    prompts: list[PromptTemplateSchema]


class PromptContentRequest(BaseModel):
    """Prompt 렌더링 요청"""

    arguments: dict[str, str] = {}


class PromptContentResponse(BaseModel):
    """Prompt 렌더링 응답"""

    content: str
```

### API 구현

```python
# src/adapters/inbound/http/routes/prompts.py
from src.adapters.inbound.http.schemas.prompts import (
    PromptTemplateSchema,
    PromptListResponse,
    PromptContentRequest,
    PromptContentResponse,
)

router = APIRouter(prefix="/api/mcp/servers", tags=["prompts"])

@router.get("/{endpoint_id}/prompts", response_model=PromptListResponse)
@inject
async def list_prompts(
    endpoint_id: str,
    prompt_service: PromptService = Depends(Provide[Container.prompt_service]),
):
    """프롬프트 목록 조회"""
    try:
        prompts = await prompt_service.list_prompts(endpoint_id)
        return PromptListResponse(
            prompts=[PromptTemplateSchema.from_entity(p) for p in prompts]
        )
    except EndpointNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{endpoint_id}/prompts/{name}", response_model=PromptContentResponse)
@inject
async def get_prompt(
    endpoint_id: str,
    name: str,
    request_body: PromptContentRequest,
    prompt_service: PromptService = Depends(Provide[Container.prompt_service]),
):
    """프롬프트 렌더링"""
    try:
        result = await prompt_service.get_prompt(endpoint_id, name, request_body.arguments)
        return PromptContentResponse(content=result)
    except (EndpointNotFoundError, PromptNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
```

**Playground UI:** 동일한 패턴 (Tab + Form + E2E)

---

## Step 6.3: Sampling HITL API (Method C 적용)

**파일:**
- `src/adapters/inbound/http/schemas/sampling.py` (Response Models)
- `src/adapters/inbound/http/routes/sampling.py` (Routes)

**테스트:** `tests/integration/test_sampling_routes.py` + E2E

### Response Models

```python
# src/adapters/inbound/http/schemas/sampling.py
"""Sampling HITL API Response Schemas"""

from typing import Any
from pydantic import BaseModel

from src.domain.entities.sampling_request import SamplingRequest, SamplingStatus


class SamplingRequestSchema(BaseModel):
    """SamplingRequest 응답 스키마"""

    id: str
    endpoint_id: str
    messages: list[dict[str, Any]]
    model_preferences: dict[str, Any] | None = None
    system_prompt: str | None = None
    max_tokens: int
    status: str
    llm_result: dict[str, Any] | None = None
    rejection_reason: str = ""

    @classmethod
    def from_entity(cls, request: SamplingRequest) -> "SamplingRequestSchema":
        """Domain Entity → HTTP Response Schema"""
        return cls(
            id=request.id,
            endpoint_id=request.endpoint_id,
            messages=request.messages,
            model_preferences=request.model_preferences,
            system_prompt=request.system_prompt,
            max_tokens=request.max_tokens,
            status=request.status.value,
            llm_result=request.llm_result,
            rejection_reason=request.rejection_reason,
        )


class SamplingRequestListResponse(BaseModel):
    """Sampling 요청 목록 응답"""

    requests: list[SamplingRequestSchema]


class SamplingApproveResponse(BaseModel):
    """Sampling 승인 응답"""

    status: str
    result: dict[str, Any]


class SamplingRejectRequest(BaseModel):
    """Sampling 거부 요청"""

    reason: str = ""


class SamplingRejectResponse(BaseModel):
    """Sampling 거부 응답"""

    status: str
```

### API 구현 (Method C 핵심)

```python
# src/adapters/inbound/http/routes/sampling.py
from src.domain.services.sampling_service import SamplingService
from src.domain.ports.outbound.orchestrator_port import OrchestratorPort
from src.domain.exceptions import HitlRequestNotFoundError
from src.adapters.inbound.http.schemas.sampling import (
    SamplingRequestSchema,
    SamplingRequestListResponse,
    SamplingApproveResponse,
    SamplingRejectRequest,
    SamplingRejectResponse,
)

router = APIRouter(prefix="/api/sampling", tags=["sampling"])

@router.get("/requests", response_model=SamplingRequestListResponse)
@inject
async def list_sampling_requests(
    sampling_service: SamplingService = Depends(Provide[Container.sampling_service]),
):
    """대기 중인 Sampling 요청 목록"""
    requests = sampling_service.list_pending()
    return SamplingRequestListResponse(
        requests=[SamplingRequestSchema.from_entity(r) for r in requests]
    )

@router.post("/requests/{request_id}/approve", response_model=SamplingApproveResponse)
@inject
async def approve_sampling_request(
    request_id: str,
    sampling_service: SamplingService = Depends(Provide[Container.sampling_service]),
    orchestrator: OrchestratorPort = Depends(Provide[Container.orchestrator_adapter]),
):
    """Sampling 요청 승인 + LLM 실행 (Method C)

    1. LLM 호출 (orchestrator.generate_response)
    2. 결과를 sampling_service.approve()로 시그널
    3. RegistryService의 콜백이 깨어나서 MCP 서버에 전달
    """
    # 1. 요청 조회
    request = sampling_service.get_request(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    # 2. LLM 호출 (Port 사용 - 헥사고날 위반 아님)
    llm_result = await orchestrator.generate_response(
        messages=request.messages,
        model=request.model_preferences.get("model") if request.model_preferences else None,
        system_prompt=request.system_prompt,
        max_tokens=request.max_tokens,
    )

    # 3. 시그널 (콜백이 깨어남)
    await sampling_service.approve(request_id, llm_result)

    return SamplingApproveResponse(status="approved", result=llm_result)

@router.post("/requests/{request_id}/reject", response_model=SamplingRejectResponse)
@inject
async def reject_sampling_request(
    request_id: str,
    reject_body: SamplingRejectRequest,
    sampling_service: SamplingService = Depends(Provide[Container.sampling_service]),
):
    """Sampling 요청 거부"""
    success = await sampling_service.reject(request_id, reject_body.reason)
    if not success:
        raise HTTPException(status_code=404, detail="Request not found")
    return SamplingRejectResponse(status="rejected")
```

**핵심 차이:**
- LLM 호출은 Route에서 하지만, `orchestrator_port`를 통해 호출하므로 헥사고날 위반 아님
- 결과를 `sampling_service.approve()`로 전달하면 콜백의 asyncio.Event가 시그널받아 MCP 서버에 반환

### Integration 테스트

```python
# tests/integration/test_sampling_routes.py

@pytest.mark.local_mcp
@pytest.mark.llm
class TestSamplingRoutes:
    async def test_list_pending_requests(self, client, pending_sampling_request):
        """대기 중인 요청 목록"""
        response = await client.get("/api/sampling/requests")

        assert response.status_code == 200
        assert len(response.json()["requests"]) >= 1

    async def test_approve_triggers_llm(self, client, pending_sampling_request):
        """승인 시 LLM 호출됨"""
        response = await client.post(f"/api/sampling/requests/{pending_sampling_request['id']}/approve")

        assert response.status_code == 200
        assert "result" in response.json()
        assert response.json()["result"]["content"]  # LLM 응답 포함

    async def test_reject_sets_status(self, client, pending_sampling_request):
        """거부 시 상태 변경"""
        response = await client.post(
            f"/api/sampling/requests/{pending_sampling_request['id']}/reject",
            json={"reason": "Not authorized"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "rejected"
```

**Playground UI:** approve/reject 버튼 + 요청 목록 표시

---

## Step 6.4: Elicitation HITL API

**파일:**
- `src/adapters/inbound/http/schemas/elicitation.py` (Response Models)
- `src/adapters/inbound/http/routes/elicitation.py` (Routes)

**테스트:** `tests/integration/test_elicitation_routes.py` + E2E

### Response Models

```python
# src/adapters/inbound/http/schemas/elicitation.py
"""Elicitation HITL API Response Schemas"""

from typing import Any
from pydantic import BaseModel

from src.domain.entities.elicitation_request import ElicitationRequest, ElicitationStatus


class ElicitationRequestSchema(BaseModel):
    """ElicitationRequest 응답 스키마 (C1 수정: 필드명 일치)"""

    id: str
    endpoint_id: str
    message: str  # "prompt" → "message"
    requested_schema: dict[str, Any]  # "accepted_actions" → "requested_schema"
    status: str
    action: str | None = None  # "user_response" 분리 → "action"
    content: dict[str, Any] | None = None  # "user_response" 분리 → "content"

    @classmethod
    def from_entity(cls, request: ElicitationRequest) -> "ElicitationRequestSchema":
        """Domain Entity → HTTP Response Schema"""
        return cls(
            id=request.id,
            endpoint_id=request.endpoint_id,
            message=request.message,
            requested_schema=request.requested_schema,
            status=request.status.value,
            action=request.action.value if request.action else None,
            content=request.content,
        )


class ElicitationRequestListResponse(BaseModel):
    """Elicitation 요청 목록 응답"""

    requests: list[ElicitationRequestSchema]


class ElicitationRespondRequest(BaseModel):
    """Elicitation 응답 요청 (C2 수정: content 타입)"""

    action: str  # "accept", "decline", "cancel"
    content: dict[str, Any] | None = None  # str → dict


class ElicitationRespondResponse(BaseModel):
    """Elicitation 응답"""

    status: str
```

### API 구현

```python
# src/adapters/inbound/http/routes/elicitation.py
from src.adapters.inbound.http.schemas.elicitation import (
    ElicitationRequestSchema,
    ElicitationRequestListResponse,
    ElicitationRespondRequest,
    ElicitationRespondResponse,
)

router = APIRouter(prefix="/api/elicitation", tags=["elicitation"])

@router.get("/requests", response_model=ElicitationRequestListResponse)
@inject
async def list_elicitation_requests(
    elicitation_service: ElicitationService = Depends(Provide[Container.elicitation_service]),
):
    """대기 중인 Elicitation 요청 목록"""
    requests = elicitation_service.list_pending()
    return ElicitationRequestListResponse(
        requests=[ElicitationRequestSchema.from_entity(r) for r in requests]
    )

@router.post("/requests/{request_id}/respond", response_model=ElicitationRespondResponse)
@inject
async def respond_elicitation_request(
    request_id: str,
    respond_body: ElicitationRespondRequest,
    elicitation_service: ElicitationService = Depends(Provide[Container.elicitation_service]),
):
    """Elicitation 응답 (accept/decline/cancel)"""
    from src.domain.entities.elicitation_request import ElicitationAction
    action_enum = ElicitationAction(respond_body.action)

    success = await elicitation_service.respond(request_id, action_enum, respond_body.content)
    if not success:
        raise HTTPException(status_code=404, detail="Request not found")

    return ElicitationRespondResponse(status=respond_body.action)
```

**Playground UI:** 동일한 패턴

---

## Step 6.5: MCP Apps Raw Response (신규)

**구현 방법:**
- MCP Apps는 `ui://` URI scheme의 resource로 제공됨
- 기존 Resources API 활용 (`read_resource`)
- Playground UI에서 `text/html` MIME type 감지 시 iframe sandbox로 raw HTML 표시

**Playground JavaScript:**
```javascript
async function readResource(uri) {
    const response = await fetch(`${API_BASE}/api/mcp/servers/${endpointId}/resources/${uri}`);
    const content = await response.json();

    if (content.mime_type === 'text/html') {
        // MCP Apps - iframe sandbox 표시
        const contentEl = document.querySelector('[data-testid="resource-content"]');
        contentEl.innerHTML = `<iframe sandbox="allow-scripts" srcdoc="${escapeHtml(content.text)}"></iframe>`;
    } else {
        // 일반 리소스 - 텍스트 표시
        contentEl.textContent = content.text;
    }
}
```

**별도 API 불필요** - MCP Apps는 resource로 제공됨

---

## Step 6.5a: HITL SSE 이벤트 엔드포인트 (신규)

**파일:** `src/adapters/inbound/http/routes/hitl_events.py`
**테스트:** `tests/integration/test_hitl_events_routes.py` + E2E

### API 구현

```python
# src/adapters/inbound/http/routes/hitl_events.py
"""HITL SSE 이벤트 스트림 API"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from dependency_injector.wiring import inject, Provide
from src.config.container import Container
from src.adapters.outbound.sse.broker import SseBroker
import json


router = APIRouter(prefix="/api/hitl", tags=["hitl-events"])


@router.get("/events")
@inject
async def hitl_events_stream(
    sse_broker: SseBroker = Depends(Provide[Container.sse_broker]),
):
    """HITL 이벤트 SSE 스트림

    sampling_request, elicitation_request 이벤트를 실시간으로 수신합니다.
    """

    async def event_generator():
        async for event in sse_broker.subscribe():
            # SSE 형식으로 전송
            event_type = event["type"]
            data = event["data"]
            yield f"event: {event_type}\n"
            yield f"data: {json.dumps(data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx buffering 방지
        },
    )
```

### Integration 테스트

```python
# tests/integration/test_hitl_events_routes.py

import pytest
import asyncio
from httpx import AsyncClient
from src.adapters.inbound.http.app import app
from src.config.container import Container


@pytest.mark.asyncio
class TestHitlEventsRoutes:
    async def test_events_stream_receives_broadcasts(self):
        """SSE 스트림이 브로드캐스트 이벤트 수신"""
        sse_broker = Container.sse_broker()

        async with AsyncClient(app=app, base_url="http://test") as client:
            # SSE 스트림 연결
            async with client.stream("GET", "/api/hitl/events") as response:
                assert response.status_code == 200
                assert response.headers["content-type"] == "text/event-stream"

                # 이벤트 브로드캐스트
                await sse_broker.broadcast("sampling_request", {
                    "request_id": "req-1",
                    "endpoint_id": "ep-1",
                })

                # 첫 이벤트 수신
                async for line in response.aiter_lines():
                    if line.startswith("event: sampling_request"):
                        break
                    if line.startswith("data: "):
                        assert "req-1" in line
                        break
```

### Playground UI 통합

```javascript
// tests/manual/playground/js/main.js

let eventSource = null;

function connectHitlEvents() {
    if (eventSource) {
        eventSource.close();
    }

    eventSource = new EventSource(`${API_BASE}/api/hitl/events`);

    eventSource.addEventListener("sampling_request", (event) => {
        const data = JSON.parse(event.data);
        showNotification(`Sampling Request: ${data.request_id}`);
        refreshSamplingRequests();
    });

    eventSource.addEventListener("elicitation_request", (event) => {
        const data = JSON.parse(event.data);
        showNotification(`Elicitation Request: ${data.request_id}`);
        refreshElicitationRequests();
    });

    eventSource.onerror = () => {
        console.error("SSE connection error");
        setTimeout(connectHitlEvents, 5000);  // 재연결
    };
}

// Playground 로드 시 자동 연결
document.addEventListener("DOMContentLoaded", connectHitlEvents);
```

---

## Step 6.6: Router 등록

**파일:** `src/adapters/inbound/http/app.py`

```python
from src.adapters.inbound.http.routes import (
    resources,
    prompts,
    sampling,
    elicitation,
    hitl_events,
)

app.include_router(resources.router)
app.include_router(prompts.router)
app.include_router(sampling.router)
app.include_router(elicitation.router)
app.include_router(hitl_events.router)
```

---

## Step 6.7: Playground Regression Tests

```bash
# All playground tests
pytest tests/e2e/test_playground.py -v

# New features only
pytest tests/e2e/test_playground.py -v -k "resources or prompts or sampling or elicitation"
```

---

## Verification

```bash
# Phase 1-5 복습
pytest tests/unit/ -q --tb=line -x
pytest tests/integration/ -m "local_mcp or llm" -v

# Phase 6 Integration Tests (Routes)
pytest tests/integration/test_resources_routes.py -v
pytest tests/integration/test_prompts_routes.py -v
pytest tests/integration/test_sampling_routes.py -m "local_mcp and llm" -v
pytest tests/integration/test_elicitation_routes.py -v

# Phase 6 E2E Tests (Playground)
pytest tests/e2e/test_playground.py -v

# Coverage
pytest --cov=src --cov-fail-under=80 -q
```

---

## Step 6.8: Documentation Update

**목표:** Phase 6에서 구현된 HTTP API 및 Playground Testing 문서화

**문서화 항목:**

| 작업 | 대상 파일 | 유형 | 내용 |
|------|----------|------|------|
| Create | docs/developers/architecture/api/sdk-track.md | API Documentation | SDK Track API 전체 엔드포인트 문서 (Resources, Prompts, Sampling, Elicitation) |
| Modify | docs/developers/architecture/api/sdk-track.md | API Documentation | Request/Response Schema, Method C 패턴 (approve 엔드포인트) 설명 |
| Create | docs/developers/architecture/api/hitl-sse.md | API Documentation | HITL SSE 이벤트 스트림 API 문서 (/api/hitl/events, 이벤트 타입) |
| Create | tests/manual/playground/README.md | Component README | Playground 개요 (목적, 실행 방법, 탭 구조, E2E 테스트 연동) |
| Modify | tests/manual/playground/README.md | Component README | Playground-First Testing 원칙 설명 (ADR-T07 참조) |
| Modify | tests/docs/EXECUTION.md | Test Documentation | Playground E2E 테스트 실행 섹션 추가 (Playwright 마커 e2e_playwright) |
| Modify | tests/docs/STRUCTURE.md | Test Documentation | tests/manual/playground/ 구조 설명 추가 |
| Modify | docs/MAP.md | Directory Structure | tests/manual/playground/ 폴더 추가, API 문서 파일 반영 |

**ADR 참조:**
- [ADR-T07 (Playground-First Testing)](../../decisions/technical/ADR-T07-playground-first-testing.md) — Phase 6+ 원칙
- [ADR-A05 (Method C)](../../decisions/architecture/ADR-A05-method-c-callback-centric.md) — Sampling approve API 패턴

**주의사항:**
- sdk-track.md는 4개 API 전체 포함 (OpenAPI 스펙 아닌 개발자 문서 형식)
- Playground README.md는 ToC + 빠른 시작, 상세 E2E 테스트 가이드는 tests/docs/에 작성
- MCP Apps Raw Response (iframe sandbox) 처리 방법 포함

---

## Step 6.9: Git Commit

**목표:** Phase 6 완료 커밋

**절차:**

1. **Phase 시작 전 회귀 테스트**
   ```bash
   pytest tests/unit/ -q --tb=line -x
   pytest tests/integration/ -m "local_mcp or llm" -v
   ```

2. **Phase 6 Integration 테스트 실행**
   ```bash
   pytest tests/integration/test_resources_routes.py -v
   pytest tests/integration/test_prompts_routes.py -v
   pytest tests/integration/test_sampling_routes.py -m "local_mcp and llm" -v
   pytest tests/integration/test_elicitation_routes.py -v
   pytest tests/integration/test_hitl_events_routes.py -v
   ```

3. **Phase 6 E2E 테스트 실행**
   ```bash
   pytest tests/e2e/test_playground.py -v
   ```

4. **커버리지 확인**
   ```bash
   pytest --cov=src --cov-fail-under=80 -q
   ```

5. **커밋 수행**
   ```bash
   git add src/adapters/inbound/http/schemas/resources.py \
           src/adapters/inbound/http/schemas/prompts.py \
           src/adapters/inbound/http/schemas/sampling.py \
           src/adapters/inbound/http/schemas/elicitation.py \
           src/adapters/inbound/http/routes/resources.py \
           src/adapters/inbound/http/routes/prompts.py \
           src/adapters/inbound/http/routes/sampling.py \
           src/adapters/inbound/http/routes/elicitation.py \
           src/adapters/inbound/http/routes/hitl_events.py \
           src/adapters/inbound/http/app.py \
           tests/integration/test_resources_routes.py \
           tests/integration/test_prompts_routes.py \
           tests/integration/test_sampling_routes.py \
           tests/integration/test_elicitation_routes.py \
           tests/integration/test_hitl_events_routes.py \
           tests/manual/playground/index.html \
           tests/manual/playground/js/main.js \
           tests/manual/playground/css/style.css \
           tests/e2e/test_playground.py \
           docs/developers/architecture/api/sdk-track.md \
           docs/developers/architecture/api/hitl-sse.md \
           tests/manual/playground/README.md \
           tests/docs/EXECUTION.md \
           tests/docs/STRUCTURE.md \
           docs/MAP.md

   git commit -m "$(cat <<'EOF'
   feat: implement Phase 6 - HTTP Routes + Playground (Playground-First)

   - Add Resources API (list/read) with ResourceSchema response models
   - Add Prompts API (list/get) with PromptTemplateSchema response models
   - Add Sampling HITL API (list/approve/reject) with Method C LLM integration
   - Add Elicitation HITL API (list/respond) with accept/decline/cancel support
   - Add HITL SSE events endpoint (/api/hitl/events) for real-time notifications
   - Add Playground UI tabs for all SDK Track APIs
   - Add Playground E2E tests (Playwright) for immediate regression prevention
   - Support MCP Apps raw response via iframe sandbox (text/html resources)

   Method C Implementation in Routes:
   - /api/sampling/requests/{id}/approve: calls orchestrator.generate_response()
   - Results signaled via sampling_service.approve() to wake callback
   - Hexagonal architecture preserved (Route uses OrchestratorPort)

   Playground-First Testing:
   - Backend API + Playground UI + E2E tests implemented together
   - Immediate feedback without Extension build
   - Fast regression tests (< 10 seconds)
   - Extension UI deferred to Production Preparation Phase

   Test Coverage:
   - Integration tests for all Routes (Resources, Prompts, Sampling, Elicitation)
   - E2E tests for Playground tabs (resource listing, prompt rendering, HITL approval)
   - SSE event stream tested with AsyncClient
   - MCP Apps iframe sandbox tested with Playwright

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
   EOF
   )"
   ```

6. **Phase Status 업데이트**
   - `docs/project/planning/active/07_hybrid_dual/README.md`에서 Phase 6 Status를 ✅로 변경

---

## Checklist

- [ ] **Phase 시작**: Status 변경 (⏸️ → 🔄)
- [ ] Step 6.1: Resources API + Playground Tab (TDD, E2E)
- [ ] Step 6.2: Prompts API + Playground Tab (TDD, E2E)
- [ ] Step 6.3: Sampling API (Method C) + Playground Tab (TDD, E2E)
- [ ] Step 6.4: Elicitation API + Playground Tab (TDD, E2E)
- [ ] Step 6.5: MCP Apps Raw Response (iframe sandbox)
- [ ] Step 6.5a: HITL SSE 이벤트 엔드포인트 (TDD, Integration)
- [ ] Step 6.6: Router 등록
- [ ] Step 6.7: Playground Regression Tests
- [ ] Step 6.8: Documentation Update (API Docs + Playground README + Test Docs + ADR References)
- [ ] **Phase 완료**: Status 변경 (🔄 → ✅)
- [ ] Git 커밋: `docs: complete phase N - {phase_name}`

---

*Last Updated: 2026-02-07*
*Playground-First: Backend + Playground UI + E2E Tests together*
