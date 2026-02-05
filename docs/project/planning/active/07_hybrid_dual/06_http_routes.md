# Phase 6: HTTP Routes (TDD)

## 개요

새로운 API 엔드포인트를 추가합니다. 기존 라우트 구조를 따릅니다.

**테스트 경로:** `tests/integration/test_*_routes.py` (기존 구조 준수)

---

## Step 6.1: Resources API

**파일:** `src/adapters/inbound/http/routes/resources.py`
**테스트:** `tests/integration/test_resources_routes.py`

| Endpoint | 설명 |
|----------|------|
| `GET /api/mcp/servers/{id}/resources` | 리소스 목록 |
| `GET /api/mcp/servers/{id}/resources/{uri}` | 리소스 읽기 |

### 구현

```python
from fastapi import APIRouter, Depends, HTTPException
from src.config.container import Container
from src.domain.services.resource_service import ResourceService

router = APIRouter(prefix="/api/mcp/servers", tags=["resources"])

@router.get("/{endpoint_id}/resources")
async def list_resources(
    endpoint_id: str,
    resource_service: ResourceService = Depends(lambda: Container.resource_service()),
):
    try:
        resources = await resource_service.list_resources(endpoint_id)
        return {"resources": [r.to_dict() for r in resources]}
    except EndpointNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{endpoint_id}/resources/{uri:path}")
async def read_resource(
    endpoint_id: str,
    uri: str,
    resource_service: ResourceService = Depends(lambda: Container.resource_service()),
):
    try:
        content = await resource_service.read_resource(endpoint_id, uri)
        return content.to_dict()
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### 테스트

```python
# tests/integration/test_resources_routes.py

class TestResourcesRoutes:
    async def test_list_resources_returns_list(self, client, registered_mcp_endpoint):
        """리소스 목록 조회 성공"""
        response = await client.get(f"/api/mcp/servers/{registered_mcp_endpoint.id}/resources")
        assert response.status_code == 200
        assert "resources" in response.json()

    async def test_list_resources_not_found(self, client):
        """존재하지 않는 엔드포인트 → 404"""
        response = await client.get("/api/mcp/servers/nonexistent/resources")
        assert response.status_code == 404

    async def test_read_resource_returns_content(self, client, registered_mcp_endpoint):
        """리소스 읽기 성공"""
        uri = "file:///test.txt"
        response = await client.get(
            f"/api/mcp/servers/{registered_mcp_endpoint.id}/resources/{uri}"
        )
        assert response.status_code == 200
```

---

## Step 6.2: Prompts API

**파일:** `src/adapters/inbound/http/routes/prompts.py`
**테스트:** `tests/integration/test_prompts_routes.py`

| Endpoint | 설명 |
|----------|------|
| `GET /api/mcp/servers/{id}/prompts` | 프롬프트 목록 |
| `POST /api/mcp/servers/{id}/prompts/{name}` | 프롬프트 렌더링 |

### 테스트

```python
class TestPromptsRoutes:
    async def test_list_prompts_returns_templates(self, client, registered_mcp_endpoint):
        """프롬프트 목록 조회"""
        response = await client.get(f"/api/mcp/servers/{registered_mcp_endpoint.id}/prompts")
        assert response.status_code == 200

    async def test_get_prompt_renders_with_arguments(self, client, registered_mcp_endpoint):
        """프롬프트 렌더링 (arguments 적용)"""
        response = await client.post(
            f"/api/mcp/servers/{registered_mcp_endpoint.id}/prompts/greeting",
            json={"arguments": {"name": "Alice"}}
        )
        assert response.status_code == 200
        assert "Hello, Alice" in response.json()["content"]
```

---

## Step 6.3: Sampling HITL API

**파일:** `src/adapters/inbound/http/routes/sampling.py`
**테스트:** `tests/integration/test_sampling_routes.py`

| Endpoint | 설명 |
|----------|------|
| `GET /api/sampling/requests` | 대기 중인 요청 목록 |
| `POST /api/sampling/requests/{id}/approve` | 승인 + LLM 실행 |
| `POST /api/sampling/requests/{id}/reject` | 거부 |

### 구현

```python
router = APIRouter(prefix="/api/sampling", tags=["sampling"])

@router.get("/requests")
async def list_sampling_requests(
    sampling_service: SamplingService = Depends(lambda: Container.sampling_service()),
):
    """대기 중인 Sampling 요청 목록"""
    requests = sampling_service.list_pending()
    return {"requests": [r.to_dict() for r in requests]}

@router.post("/requests/{request_id}/approve")
async def approve_sampling_request(
    request_id: str,
    sampling_service: SamplingService = Depends(lambda: Container.sampling_service()),
    orchestrator: OrchestratorPort = Depends(lambda: Container.orchestrator_adapter()),
):
    """Sampling 요청 승인 + LLM 실행"""
    # 1. 요청 조회
    request = sampling_service.get_request(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    # 2. LLM 호출 (OrchestratorPort 사용)
    llm_result = await orchestrator.generate(
        messages=request.messages,
        model=request.model_preferences.get("model") if request.model_preferences else None,
        max_tokens=request.max_tokens,
    )

    # 3. 결과 저장 및 이벤트 시그널
    await sampling_service.approve(request_id, llm_result)

    return {"status": "approved", "result": llm_result}

@router.post("/requests/{request_id}/reject")
async def reject_sampling_request(
    request_id: str,
    reason: str = "",
    sampling_service: SamplingService = Depends(lambda: Container.sampling_service()),
):
    """Sampling 요청 거부"""
    success = await sampling_service.reject(request_id, reason)
    if not success:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"status": "rejected"}
```

### 테스트

```python
class TestSamplingRoutes:
    async def test_list_pending_requests(self, client, pending_sampling_request):
        """대기 중인 요청 목록"""
        response = await client.get("/api/sampling/requests")
        assert response.status_code == 200
        assert len(response.json()["requests"]) >= 1

    async def test_approve_triggers_llm(self, client, pending_sampling_request, mock_llm):
        """승인 시 LLM 호출됨"""
        response = await client.post(
            f"/api/sampling/requests/{pending_sampling_request.id}/approve"
        )
        assert response.status_code == 200
        assert mock_llm.generate_called

    async def test_reject_sets_status(self, client, pending_sampling_request):
        """거부 시 상태 변경"""
        response = await client.post(
            f"/api/sampling/requests/{pending_sampling_request.id}/reject",
            json={"reason": "Not authorized"}
        )
        assert response.status_code == 200
```

---

## Step 6.4: Elicitation HITL API

**파일:** `src/adapters/inbound/http/routes/elicitation.py`
**테스트:** `tests/integration/test_elicitation_routes.py`

| Endpoint | 설명 |
|----------|------|
| `GET /api/elicitation/requests` | 대기 중인 요청 목록 |
| `POST /api/elicitation/requests/{id}/respond` | accept/decline/cancel |

### 테스트

```python
class TestElicitationRoutes:
    async def test_list_pending_requests(self, client, pending_elicitation_request):
        """대기 중인 요청 목록"""
        response = await client.get("/api/elicitation/requests")
        assert response.status_code == 200

    async def test_respond_accept_with_content(self, client, pending_elicitation_request):
        """accept + content 응답"""
        response = await client.post(
            f"/api/elicitation/requests/{pending_elicitation_request.id}/respond",
            json={"action": "accept", "content": {"api_key": "sk-xxx"}}
        )
        assert response.status_code == 200

    async def test_respond_decline(self, client, pending_elicitation_request):
        """decline 응답"""
        response = await client.post(
            f"/api/elicitation/requests/{pending_elicitation_request.id}/respond",
            json={"action": "decline"}
        )
        assert response.status_code == 200
```

---

## Step 6.5: Router 등록

**파일:** `src/adapters/inbound/http/app.py`

```python
from src.adapters.inbound.http.routes import resources, prompts, sampling, elicitation

app.include_router(resources.router)
app.include_router(prompts.router)
app.include_router(sampling.router)
app.include_router(elicitation.router)
```
