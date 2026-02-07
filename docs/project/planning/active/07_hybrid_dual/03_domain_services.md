# Phase 3: Domain Services (TDD)

## 개요

SDK Track(Resources/Prompts/Sampling/Elicitation) 서비스를 Method C(Callback-Centric) 패턴으로 구현합니다.

**핵심 원칙:**
- ResourceService, PromptService는 McpClientPort 위임
- SamplingService, ElicitationService는 HITL 큐 + Signal 패턴 (asyncio.Event)
- **Method C**: LLM 호출은 Route에서, 결과는 Service.approve()로 시그널 전달

---

## Step 3.1: ResourceService

**파일:** `src/domain/services/resource_service.py`
**테스트:** `tests/unit/domain/services/test_resource_service.py`

### TDD Required

```python
# 테스트 먼저 작성
class TestResourceService:
    async def test_list_resources_returns_list(self, fake_mcp_client):
        """리소스 목록 조회 성공"""
        fake_mcp_client.set_resources("ep-1", [
            Resource(uri="file:///test.txt", name="test.txt")
        ])
        service = ResourceService(mcp_client=fake_mcp_client)

        resources = await service.list_resources("ep-1")
        assert len(resources) == 1
        assert resources[0].uri == "file:///test.txt"

    async def test_read_resource_returns_content(self, fake_mcp_client):
        """리소스 읽기 성공"""
        fake_mcp_client.set_resource_content("ep-1", "file:///test.txt",
            ResourceContent(uri="file:///test.txt", text="Hello", mime_type="text/plain"))
        service = ResourceService(mcp_client=fake_mcp_client)

        content = await service.read_resource("ep-1", "file:///test.txt")
        assert content.text == "Hello"

    async def test_list_resources_endpoint_not_found(self, fake_mcp_client):
        """존재하지 않는 endpoint_id → EndpointNotFoundError"""
        service = ResourceService(mcp_client=fake_mcp_client)

        with pytest.raises(EndpointNotFoundError):
            await service.list_resources("nonexistent")
```

### 구현

```python
from src.domain.ports.outbound.mcp_client_port import McpClientPort
from src.domain.entities.resource import Resource, ResourceContent
from src.domain.exceptions import EndpointNotFoundError, ResourceNotFoundError

class ResourceService:
    """MCP Resource 조회 서비스

    McpClientPort를 통해 리소스 목록 및 콘텐츠를 조회합니다.
    """

    def __init__(self, mcp_client: McpClientPort) -> None:
        self._mcp_client = mcp_client

    async def list_resources(self, endpoint_id: str) -> list[Resource]:
        """엔드포인트의 리소스 목록 조회

        Args:
            endpoint_id: MCP 서버 엔드포인트 ID

        Returns:
            Resource 목록

        Raises:
            EndpointNotFoundError: 연결되지 않은 엔드포인트
        """
        return await self._mcp_client.list_resources(endpoint_id)

    async def read_resource(self, endpoint_id: str, uri: str) -> ResourceContent:
        """리소스 콘텐츠 읽기

        Args:
            endpoint_id: MCP 서버 엔드포인트 ID
            uri: 리소스 URI (file://, ui:// 등)

        Returns:
            ResourceContent (text 또는 blob)

        Raises:
            EndpointNotFoundError: 연결되지 않은 엔드포인트
            ResourceNotFoundError: 존재하지 않는 리소스
        """
        return await self._mcp_client.read_resource(endpoint_id, uri)
```

---

## Step 3.2: PromptService

**파일:** `src/domain/services/prompt_service.py`
**테스트:** `tests/unit/domain/services/test_prompt_service.py`

### TDD Required

```python
class TestPromptService:
    async def test_list_prompts_returns_templates(self, fake_mcp_client):
        """프롬프트 목록 조회"""
        fake_mcp_client.set_prompts("ep-1", [
            PromptTemplate(name="greeting", description="Greet user")
        ])
        service = PromptService(mcp_client=fake_mcp_client)

        prompts = await service.list_prompts("ep-1")
        assert len(prompts) == 1
        assert prompts[0].name == "greeting"

    async def test_get_prompt_renders_with_arguments(self, fake_mcp_client):
        """프롬프트 렌더링 (arguments 적용)"""
        fake_mcp_client.set_prompt_result("ep-1", "greeting", "Hello, Alice!")
        service = PromptService(mcp_client=fake_mcp_client)

        result = await service.get_prompt("ep-1", "greeting", {"name": "Alice"})
        assert "Hello, Alice!" in result

    async def test_get_prompt_not_found(self, fake_mcp_client):
        """존재하지 않는 prompt → PromptNotFoundError"""
        service = PromptService(mcp_client=fake_mcp_client)

        with pytest.raises(PromptNotFoundError):
            await service.get_prompt("ep-1", "nonexistent")
```

### 구현

```python
from src.domain.ports.outbound.mcp_client_port import McpClientPort
from src.domain.entities.prompt_template import PromptTemplate
from src.domain.exceptions import EndpointNotFoundError, PromptNotFoundError

class PromptService:
    """MCP Prompt 템플릿 서비스

    McpClientPort를 통해 프롬프트 목록 및 렌더링 결과를 조회합니다.
    """

    def __init__(self, mcp_client: McpClientPort) -> None:
        self._mcp_client = mcp_client

    async def list_prompts(self, endpoint_id: str) -> list[PromptTemplate]:
        """엔드포인트의 프롬프트 목록 조회

        Args:
            endpoint_id: MCP 서버 엔드포인트 ID

        Returns:
            PromptTemplate 목록

        Raises:
            EndpointNotFoundError: 연결되지 않은 엔드포인트
        """
        return await self._mcp_client.list_prompts(endpoint_id)

    async def get_prompt(
        self,
        endpoint_id: str,
        name: str,
        arguments: dict | None = None
    ) -> str:
        """프롬프트 렌더링

        Args:
            endpoint_id: MCP 서버 엔드포인트 ID
            name: 프롬프트 이름
            arguments: 템플릿 인자 (optional)

        Returns:
            렌더링된 프롬프트 문자열

        Raises:
            EndpointNotFoundError: 연결되지 않은 엔드포인트
            PromptNotFoundError: 존재하지 않는 프롬프트
        """
        return await self._mcp_client.get_prompt(endpoint_id, name, arguments)
```

---

## Step 3.3: SamplingService (Method C 핵심)

**파일:** `src/domain/services/sampling_service.py`
**테스트:** `tests/unit/domain/services/test_sampling_service.py`

### Method C Signal 패턴

```
1. create_request() → 요청 생성 + asyncio.Event 준비
2. wait_for_response(timeout) → Event.wait() (callback에서 대기)
3. approve(request_id, llm_result) → Event.set() (Route에서 시그널)
4. callback이 깨어나서 결과 반환
```

### TDD Required

```python
class TestSamplingService:
    async def test_create_request_stores_in_pending(self):
        """요청 생성 시 pending 목록에 추가"""
        service = SamplingService()
        request = SamplingRequest(id="req-1", endpoint_id="ep-1", messages=[])

        await service.create_request(request)

        pending = service.list_pending()
        assert len(pending) == 1
        assert pending[0].id == "req-1"

    async def test_get_request_returns_request(self):
        """get_request() - 요청 조회"""
        service = SamplingService()
        request = SamplingRequest(id="req-1", endpoint_id="ep-1", messages=[])
        await service.create_request(request)

        result = service.get_request("req-1")
        assert result.id == "req-1"

    async def test_get_request_returns_none_for_unknown(self):
        """get_request() - 존재하지 않는 요청 → None"""
        service = SamplingService()

        result = service.get_request("nonexistent")
        assert result is None

    async def test_list_pending_returns_only_pending(self):
        """list_pending() - PENDING 상태만 반환"""
        service = SamplingService()
        req1 = SamplingRequest(id="req-1", endpoint_id="ep-1", messages=[])
        req2 = SamplingRequest(id="req-2", endpoint_id="ep-1", messages=[])
        await service.create_request(req1)
        await service.create_request(req2)

        await service.approve("req-1", {"content": "test"})

        pending = service.list_pending()
        assert len(pending) == 1
        assert pending[0].id == "req-2"

    async def test_approve_signals_event(self):
        """approve() - asyncio.Event 시그널"""
        service = SamplingService()
        request = SamplingRequest(id="req-1", endpoint_id="ep-1", messages=[])
        await service.create_request(request)

        success = await service.approve("req-1", {"content": "LLM response"})

        assert success
        result = service.get_request("req-1")
        assert result.status == SamplingStatus.APPROVED
        assert result.llm_result == {"content": "LLM response"}

    async def test_wait_for_response_returns_after_signal(self):
        """wait_for_response() - 시그널 후 즉시 반환"""
        service = SamplingService()
        request = SamplingRequest(id="req-1", endpoint_id="ep-1", messages=[])
        await service.create_request(request)

        # Background task: 1초 후 approve
        async def delayed_approve():
            await asyncio.sleep(1.0)
            await service.approve("req-1", {"content": "test"})
        asyncio.create_task(delayed_approve())

        # 30초 타임아웃이지만 1초 내 반환됨
        result = await service.wait_for_response("req-1", timeout=30.0)

        assert result is not None
        assert result.status == SamplingStatus.APPROVED

    async def test_wait_for_response_timeout(self):
        """wait_for_response() - timeout → None"""
        service = SamplingService()
        request = SamplingRequest(id="req-1", endpoint_id="ep-1", messages=[])
        await service.create_request(request)

        # 0.1초 timeout (approve 없이)
        result = await service.wait_for_response("req-1", timeout=0.1)

        assert result is None  # Timeout

    async def test_reject_sets_status(self):
        """reject() - 상태 REJECTED로 변경"""
        service = SamplingService()
        request = SamplingRequest(id="req-1", endpoint_id="ep-1", messages=[])
        await service.create_request(request)

        success = await service.reject("req-1", reason="Not authorized")

        assert success
        result = service.get_request("req-1")
        assert result.status == SamplingStatus.REJECTED

    async def test_cleanup_expired_removes_old_requests(self):
        """cleanup_expired() - TTL 초과 요청 제거"""
        service = SamplingService(ttl_seconds=1)
        request = SamplingRequest(id="req-1", endpoint_id="ep-1", messages=[])
        await service.create_request(request)

        await asyncio.sleep(1.5)
        removed = await service.cleanup_expired()

        assert removed == 1
        assert service.get_request("req-1") is None
```

### 구현

```python
import asyncio
from datetime import datetime, timezone
from src.domain.entities.sampling_request import SamplingRequest, SamplingStatus
from src.domain.exceptions import HitlRequestNotFoundError

class SamplingService:
    """Sampling HITL 요청 큐 관리 (Method C Signal 패턴)

    Note:
    - McpClientPort를 직접 사용하지 않음
    - RegistryService가 콜백을 생성하여 MCP SDK에 전달
    - Route는 LLM 호출 후 approve()로 시그널 전송
    """

    def __init__(self, ttl_seconds: int = 600) -> None:
        self._requests: dict[str, SamplingRequest] = {}
        self._events: dict[str, asyncio.Event] = {}
        self._ttl_seconds = ttl_seconds

    async def create_request(self, request: SamplingRequest) -> None:
        """요청 생성 및 대기 이벤트 설정

        Args:
            request: SamplingRequest 엔티티
        """
        self._requests[request.id] = request
        self._events[request.id] = asyncio.Event()

    def get_request(self, request_id: str) -> SamplingRequest | None:
        """요청 조회

        Args:
            request_id: 요청 ID

        Returns:
            SamplingRequest 또는 None
        """
        return self._requests.get(request_id)

    async def wait_for_response(
        self,
        request_id: str,
        timeout: float = 30.0
    ) -> SamplingRequest | None:
        """Long-polling 대기 (Method C 핵심)

        asyncio.Event를 대기하다가 approve() 또는 reject() 호출 시 깨어남.

        Args:
            request_id: 요청 ID
            timeout: 대기 시간 (초)

        Returns:
            업데이트된 SamplingRequest 또는 None (timeout)
        """
        if request_id not in self._events:
            return None

        try:
            await asyncio.wait_for(
                self._events[request_id].wait(),
                timeout=timeout
            )
            return self._requests.get(request_id)
        except asyncio.TimeoutError:
            return None

    async def approve(self, request_id: str, llm_result: dict) -> bool:
        """요청 승인 및 LLM 결과 설정 (Method C Signal)

        Route에서 LLM 호출 후 이 메서드로 결과를 전달하면,
        wait_for_response()가 깨어나서 callback에 결과 반환.

        Args:
            request_id: 요청 ID
            llm_result: LLM 응답 dict (role, content, model)

        Returns:
            성공 여부
        """
        if request_id not in self._requests:
            return False

        request = self._requests[request_id]
        request.status = SamplingStatus.APPROVED
        request.llm_result = llm_result

        # Signal waiting callback
        if request_id in self._events:
            self._events[request_id].set()

        return True

    async def reject(self, request_id: str, reason: str = "") -> bool:
        """요청 거부

        Args:
            request_id: 요청 ID
            reason: 거부 사유 (optional)

        Returns:
            성공 여부
        """
        if request_id not in self._requests:
            return False

        request = self._requests[request_id]
        request.status = SamplingStatus.REJECTED
        request.rejection_reason = reason

        # Signal waiting callback
        if request_id in self._events:
            self._events[request_id].set()

        return True

    def list_pending(self) -> list[SamplingRequest]:
        """대기 중인 요청 목록

        Returns:
            PENDING 상태인 요청 목록
        """
        return [
            req for req in self._requests.values()
            if req.status == SamplingStatus.PENDING
        ]

    async def cleanup_expired(self) -> int:
        """만료된 요청 정리 (TTL 기반)

        Returns:
            제거된 요청 수
        """
        now = datetime.now(timezone.utc)
        expired_ids = [
            req_id for req_id, req in self._requests.items()
            if (now - req.created_at).total_seconds() > self._ttl_seconds
        ]

        for req_id in expired_ids:
            del self._requests[req_id]
            if req_id in self._events:
                del self._events[req_id]

        return len(expired_ids)
```

---

## Step 3.4: ElicitationService

**파일:** `src/domain/services/elicitation_service.py`
**테스트:** `tests/unit/domain/services/test_elicitation_service.py`

### TDD Required

```python
class TestElicitationService:
    async def test_create_request_stores_in_pending(self):
        """요청 생성 시 pending 목록에 추가"""
        # SamplingService와 동일한 패턴

    async def test_respond_accept_with_content(self):
        """respond(ACCEPT) - content 저장"""
        service = ElicitationService()
        request = ElicitationRequest(
            id="req-1",
            endpoint_id="ep-1",
            message="Enter API key",
            requested_schema={}
        )
        await service.create_request(request)

        success = await service.respond(
            "req-1",
            ElicitationAction.ACCEPT,
            content={"api_key": "sk-xxx"}
        )

        assert success
        result = service.get_request("req-1")
        assert result.action == ElicitationAction.ACCEPT
        assert result.content == {"api_key": "sk-xxx"}

    async def test_respond_decline(self):
        """respond(DECLINE)"""
        # ...

    async def test_respond_cancel(self):
        """respond(CANCEL)"""
        # ...

    async def test_wait_for_response_timeout(self):
        """wait_for_response() - timeout"""
        # SamplingService와 동일

    async def test_list_pending_returns_only_pending(self):
        """list_pending() - PENDING 상태만 반환"""
        service = ElicitationService()

        # 여러 상태의 요청 생성
        pending_req = ElicitationRequest(
            id="req-pending",
            endpoint_id="ep-1",
            message="Enter data",
            requested_schema={"type": "object", "properties": {"data": {"type": "string"}}},
        )
        await service.create_request(pending_req)

        accepted_req = ElicitationRequest(
            id="req-accepted",
            endpoint_id="ep-1",
            message="Enter data 2",
            requested_schema={"type": "object", "properties": {"data": {"type": "string"}}},
        )
        await service.create_request(accepted_req)
        await service.respond("req-accepted", ElicitationAction.ACCEPT, content={"data": "value"})

        # list_pending()는 pending만 반환
        pending_list = service.list_pending()
        assert len(pending_list) == 1
        assert pending_list[0].id == "req-pending"
```

### 구현

```python
import asyncio
from datetime import datetime, timezone
from src.domain.entities.elicitation_request import (
    ElicitationRequest,
    ElicitationAction,
    ElicitationStatus
)
from src.domain.exceptions import HitlRequestNotFoundError

class ElicitationService:
    """Elicitation HITL 요청 큐 관리

    SamplingService와 동일한 Signal 패턴 사용.
    """

    def __init__(self, ttl_seconds: int = 600) -> None:
        self._requests: dict[str, ElicitationRequest] = {}
        self._events: dict[str, asyncio.Event] = {}
        self._ttl_seconds = ttl_seconds

    async def create_request(self, request: ElicitationRequest) -> None:
        """요청 생성 및 대기 이벤트 설정"""
        self._requests[request.id] = request
        self._events[request.id] = asyncio.Event()

    def get_request(self, request_id: str) -> ElicitationRequest | None:
        """요청 조회"""
        return self._requests.get(request_id)

    async def wait_for_response(
        self,
        request_id: str,
        timeout: float = 30.0
    ) -> ElicitationRequest | None:
        """Long-polling 대기 (asyncio.Event)"""
        if request_id not in self._events:
            return None

        try:
            await asyncio.wait_for(
                self._events[request_id].wait(),
                timeout=timeout
            )
            return self._requests.get(request_id)
        except asyncio.TimeoutError:
            return None

    async def respond(
        self,
        request_id: str,
        action: ElicitationAction,
        content: dict | None = None
    ) -> bool:
        """Elicitation 응답 (accept/decline/cancel)

        Args:
            request_id: 요청 ID
            action: ACCEPT, DECLINE, CANCEL
            content: 사용자 입력 (ACCEPT 시 필수)

        Returns:
            성공 여부
        """
        if request_id not in self._requests:
            return False

        request = self._requests[request_id]
        request.action = action
        request.content = content

        if action == ElicitationAction.ACCEPT:
            request.status = ElicitationStatus.ACCEPTED
        elif action == ElicitationAction.DECLINE:
            request.status = ElicitationStatus.DECLINED
        elif action == ElicitationAction.CANCEL:
            request.status = ElicitationStatus.CANCELLED

        # Signal waiting callback
        if request_id in self._events:
            self._events[request_id].set()

        return True

    def list_pending(self) -> list[ElicitationRequest]:
        """대기 중인 요청 목록"""
        return [
            req for req in self._requests.values()
            if req.status == ElicitationStatus.PENDING
        ]

    async def cleanup_expired(self) -> int:
        """만료된 요청 정리"""
        now = datetime.now(timezone.utc)
        expired_ids = [
            req_id for req_id, req in self._requests.items()
            if (now - req.created_at).total_seconds() > self._ttl_seconds
        ]

        for req_id in expired_ids:
            del self._requests[req_id]
            if req_id in self._events:
                del self._events[req_id]

        return len(expired_ids)
```

---

## Verification

```bash
# Unit Tests (Fake Adapters 사용, 외부 의존성 없음)
pytest tests/unit/domain/services/test_resource_service.py -v
pytest tests/unit/domain/services/test_prompt_service.py -v
pytest tests/unit/domain/services/test_sampling_service.py -v
pytest tests/unit/domain/services/test_elicitation_service.py -v

# 전체 Domain 테스트
pytest tests/unit/domain/ -q --tb=line
```

---

## Step 3.5: Documentation Update

**목표:** Phase 3에서 구현된 Domain Service 및 Method C 패턴 문서화

**문서화 항목:**

| 작업 | 대상 파일 | 유형 | 내용 |
|------|----------|------|------|
| Create | docs/developers/architecture/layer/patterns/method-c-signal.md | Architecture Pattern | Method C Signal 패턴 상세 설명 (asyncio.Event 기반 HITL 큐, LLM 호출 분리) |
| Modify | docs/developers/architecture/layer/core/README.md | Architecture | SamplingService/ElicitationService Signal 패턴 섹션 추가, ADR-A05 참조 링크 |
| Modify | docs/developers/architecture/layer/core/README.md | Architecture | ResourceService/PromptService 위임 패턴 설명 |
| Modify | tests/docs/WritingGuide.md | Test Documentation | asyncio.Event 기반 서비스 테스트 레시피 (delayed_approve 패턴) |
| Modify | docs/MAP.md | Directory Structure | docs/developers/architecture/layer/patterns/ 폴더 추가 반영 |

**ADR 참조:**
- [ADR-A05 (Method C — Callback-Centric LLM Placement)](../../decisions/architecture/ADR-A05-method-c-callback-centric.md)

**주의사항:**
- method-c-signal.md는 신규 파일 생성 (3+ 관련 서비스 존재)
- Phase 5 RegistryService 콜백 구현 시 이 패턴 참조

---

## Step 3.6: Git Commit

**목표:** Phase 3 완료 커밋

**절차:**

1. **Phase 시작 전 회귀 테스트**
   ```bash
   pytest -q --tb=line -x
   ```

2. **Phase 3 테스트 실행**
   ```bash
   pytest tests/unit/domain/services/test_resource_service.py -v
   pytest tests/unit/domain/services/test_prompt_service.py -v
   pytest tests/unit/domain/services/test_sampling_service.py -v
   pytest tests/unit/domain/services/test_elicitation_service.py -v
   pytest tests/unit/domain/ -q --tb=line
   ```

3. **커버리지 확인**
   ```bash
   pytest --cov=src --cov-fail-under=80 -q
   ```

4. **커밋 수행**
   ```bash
   git add src/domain/services/resource_service.py \
           src/domain/services/prompt_service.py \
           src/domain/services/sampling_service.py \
           src/domain/services/elicitation_service.py \
           tests/unit/domain/services/test_resource_service.py \
           tests/unit/domain/services/test_prompt_service.py \
           tests/unit/domain/services/test_sampling_service.py \
           tests/unit/domain/services/test_elicitation_service.py \
           docs/developers/architecture/layer/patterns/method-c-signal.md \
           docs/developers/architecture/layer/core/README.md \
           tests/docs/WritingGuide.md \
           docs/MAP.md

   git commit -m "$(cat <<'EOF'
   feat: implement Phase 3 - Domain Services (Method C Signal Pattern)

   - Add ResourceService (delegates to McpClientPort)
   - Add PromptService (delegates to McpClientPort)
   - Add SamplingService with Method C Signal pattern (asyncio.Event)
   - Add ElicitationService with Signal pattern
   - Implement wait_for_response() with timeout support
   - Implement approve()/reject()/respond() for HITL signal transmission
   - Add cleanup_expired() for TTL-based request management

   Method C Architecture:
   - Services manage HITL queue with asyncio.Event for signaling
   - Route calls OrchestratorPort.generate_response() for LLM
   - Route signals result via approve() to wake callback
   - Callback waits on Event.wait() and returns result to MCP server

   Test Coverage:
   - All services tested with Fake adapters (TDD approach)
   - Signal pattern tested with delayed_approve background tasks
   - Timeout scenarios tested with asyncio.TimeoutError

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
   EOF
   )"
   ```

5. **Phase Status 업데이트**
   - `docs/project/planning/active/07_hybrid_dual/README.md`에서 Phase 3 Status를 ✅로 변경

---

## Checklist

- [ ] **Phase 시작**: Status 변경 (⏸️ → 🔄)
- [ ] Step 3.1: ResourceService 구현 (TDD)
- [ ] Step 3.2: PromptService 구현 (TDD)
- [ ] Step 3.3: SamplingService 구현 (Method C Signal 패턴, TDD)
- [ ] Step 3.4: ElicitationService 구현 (Signal 패턴, TDD)
- [ ] Step 3.5: Documentation Update (Architecture Pattern + ADR References)
- [ ] 모든 테스트 통과 확인
- [ ] Git 커밋: `docs: complete phase 3 - domain services`
- [ ] **Phase 완료**: Status 변경 (🔄 → ✅)
- [ ] Git 커밋: `docs: complete phase N - {phase_name}`

---

*Last Updated: 2026-02-07*
*Method C: Callback waits for Signal, Route calls LLM + Signal*
