# Lifecycle Management

서버 시작/종료 시 리소스 정리 패턴과 주기적 cleanup 스케줄러 구현 가이드입니다.

---

## Overview

AgentHub는 다음 리소스의 수명 주기를 관리합니다:

| 리소스 | 타입 | Startup | Shutdown | Cleanup Scheduler |
|--------|------|---------|----------|-------------------|
| **SQLite Storage** | Persistent | `initialize()` | `close()` | - |
| **MCP SDK Track Sessions** | Network | `restore_endpoints()` | `disconnect_all()` | - |
| **HITL Requests** | Memory | - | - | ✅ 60초 주기 |
| **Orchestrator** | LLM Agent | `initialize()` | `close()` | - |

**구현 위치:** `src/adapters/inbound/http/app.py`

---

## Lifespan Context Manager

FastAPI의 `lifespan` 컨텍스트 매니저를 사용하여 애플리케이션 수명 주기를 관리합니다.

### 기본 구조

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 수명 주기 관리

    Startup:
    - SQLite 스토리지 초기화 (테이블 생성)
    - Orchestrator 비동기 초기화 (DynamicToolset + LlmAgent)
    - 저장된 엔드포인트 복원
    - Cleanup 스케줄러 시작 (Phase 7 Step 5.3)

    Shutdown:
    - Cleanup 태스크 취소
    - MCP SDK Track 세션 정리 (disconnect_all)
    - Storage 연결 종료
    """
    # Startup
    logger.info("AgentHub API starting up")

    # ... startup 작업 ...

    yield

    # Shutdown
    logger.info("AgentHub API shutting down")

    # ... shutdown 작업 ...

app = FastAPI(lifespan=lifespan)
```

---

## Startup Sequence

애플리케이션 시작 시 순차적으로 실행되는 작업:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    container = app.container
    settings = container.settings()

    # 1. 로깅 설정 초기화 (최우선)
    from src.config.logging_config import setup_logging
    setup_logging(settings)
    logger.info("AgentHub API starting up")

    # 2. API 키 환경변수 반영 (LiteLLM용)
    _export_api_keys(settings)

    # 3. SQLite 스토리지 초기화
    conv_storage = container.conversation_storage()
    await conv_storage.initialize()
    logger.info("SQLite conversation storage initialized")

    usage_storage = container.usage_storage()
    await usage_storage.initialize()
    logger.info("SQLite usage storage initialized")

    # 4. Orchestrator 초기화 (Async Factory Pattern)
    orchestrator = container.orchestrator_adapter()
    await orchestrator.initialize()
    logger.info("Orchestrator initialized")

    # 5. 저장된 엔드포인트 복원
    registry = container.registry_service()
    restore_result = await registry.restore_endpoints()
    logger.info(
        f"Endpoints restored: {len(restore_result['restored'])} succeeded, "
        f"{len(restore_result['failed'])} failed"
    )

    # 6. Cleanup 스케줄러 시작 (Phase 7 Step 5.3)
    sampling_service = container.sampling_service()
    elicitation_service = container.elicitation_service()
    cleanup_task = asyncio.create_task(
        _periodic_cleanup(sampling_service, elicitation_service, interval=60)
    )
    logger.info("Cleanup scheduler started")

    yield

    # Shutdown 시퀀스 (아래 섹션 참조)
```

**중요 포인트:**
1. **로깅 최우선**: 나머지 작업의 로그를 기록하기 위해 가장 먼저 초기화
2. **순차 초기화**: 각 리소스는 이전 리소스에 의존할 수 있으므로 순서 중요
3. **복원 실패 허용**: `restore_endpoints()`는 실패한 엔드포인트를 로그로만 기록

---

## Shutdown Sequence

애플리케이션 종료 시 역순으로 리소스를 정리합니다:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... Startup ...
    global cleanup_task

    yield

    # Shutdown
    logger.info("AgentHub API shutting down")

    # 1. Cleanup 태스크 취소 (Phase 7 Step 5.3)
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
        logger.info("Cleanup scheduler stopped")

    # 2. MCP SDK Track 세션 정리 (Phase 7 Step 5.3)
    mcp_client = container.mcp_client_adapter()
    await mcp_client.disconnect_all()
    logger.info("MCP SDK Track sessions closed")

    # 3. Orchestrator 종료
    await orchestrator.close()
    logger.info("Orchestrator closed")

    # 4. Storage 연결 종료
    await conv_storage.close()
    await usage_storage.close()
    logger.info("Storage connections closed")
```

**중요 포인트:**
1. **역순 정리**: Startup의 역순으로 리소스 해제
2. **CancelledError 처리**: asyncio.Task 취소 시 예외를 무시
3. **로깅 유지**: shutdown 중에도 로그가 기록되도록 로깅은 마지막까지 유지

---

## Periodic Cleanup Scheduler

만료된 HITL 요청을 주기적으로 정리하는 백그라운드 태스크입니다.

### 구현

```python
import asyncio
import logging

logger = logging.getLogger(__name__)

# 전역 변수 (lifespan 외부에서 접근 가능)
cleanup_task = None

async def _periodic_cleanup(sampling_service, elicitation_service, interval: int = 60) -> None:
    """만료된 HITL 요청 주기적 정리

    Args:
        sampling_service: SamplingService 인스턴스
        elicitation_service: ElicitationService 인스턴스
        interval: 정리 주기 (초, 기본 60초)
    """
    while True:
        await asyncio.sleep(interval)
        try:
            await sampling_service.cleanup_expired()
            await elicitation_service.cleanup_expired()
            logger.debug("HITL cleanup completed")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
```

**동작 방식:**
1. 60초마다 `cleanup_expired()` 호출
2. TTL이 만료된 요청 삭제 (기본: 600초 = 10분)
3. 예외 발생 시 로그만 기록하고 계속 실행

### 시작 및 종료

```python
# Startup
cleanup_task = asyncio.create_task(
    _periodic_cleanup(sampling_service, elicitation_service, interval=60)
)

# Shutdown
if cleanup_task:
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
```

**주의사항:**
- `cleanup_task`를 전역 변수로 관리 (lifespan 외부에서도 접근 가능)
- `cancel()` 호출 후 `await`로 완전한 취소 대기
- `CancelledError` 예외는 정상 종료 신호이므로 무시

---

## MCP SDK Track Session Cleanup

서버 종료 시 모든 MCP SDK Track 세션을 정리합니다.

### 구현

```python
# src/adapters/outbound/mcp/mcp_client_adapter.py

class McpClientAdapter(McpClientPort):
    """MCP SDK Track 어댑터"""

    def __init__(self) -> None:
        self._sessions: dict[str, ClientSession] = {}

    async def disconnect_all(self) -> None:
        """모든 세션 정리 (서버 종료 시)"""
        for endpoint_id in list(self._sessions.keys()):
            try:
                await self.disconnect(endpoint_id)
            except Exception as e:
                logger.warning(f"Failed to disconnect {endpoint_id}: {e}")
        logger.info(f"All MCP SDK Track sessions closed ({len(self._sessions)} total)")
```

**호출 위치:**

```python
# src/adapters/inbound/http/app.py (lifespan shutdown)

mcp_client = container.mcp_client_adapter()
await mcp_client.disconnect_all()
logger.info("MCP SDK Track sessions closed")
```

**장점:**
1. **리소스 누수 방지**: HTTP 연결, 메모리 정리
2. **Graceful Shutdown**: 각 세션에 정리 시간 부여
3. **로깅**: 종료 시 정리된 세션 수 기록

---

## Error Handling

### Startup 실패 처리

Startup 중 예외가 발생하면 애플리케이션이 시작되지 않습니다:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Startup 작업
        await conv_storage.initialize()
        # ...
    except Exception as e:
        logger.critical(f"Startup failed: {e}")
        raise  # 애플리케이션 시작 중단
```

**결과:** 서버가 시작되지 않으며, 사용자에게 명확한 오류 메시지 표시

### Shutdown 실패 처리

Shutdown 중 예외는 로그만 기록하고 계속 진행합니다:

```python
# Shutdown
try:
    await mcp_client.disconnect_all()
except Exception as e:
    logger.error(f"Failed to disconnect MCP sessions: {e}")
    # 계속 진행 (다른 리소스 정리)

try:
    await orchestrator.close()
except Exception as e:
    logger.error(f"Failed to close orchestrator: {e}")
```

**이유:** 일부 리소스 정리 실패가 다른 정리를 막지 않도록

---

## Testing

### Integration Test

```python
# tests/integration/test_app_startup.py

async def test_lifespan_startup_and_shutdown():
    """Lifespan startup/shutdown 통합 테스트"""
    from src.adapters.inbound.http.app import create_app
    from httpx import AsyncClient

    app = create_app()

    # AsyncClient는 자동으로 lifespan 실행
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Startup 완료 확인
        response = await client.get("/health")
        assert response.status_code == 200

    # Shutdown 완료 (자동)
    # 세션이 정리되었는지 확인 (FakeMcpClient로 검증)
```

### Unit Test (Cleanup Scheduler)

```python
# tests/unit/adapters/test_periodic_cleanup.py

async def test_periodic_cleanup_calls_services():
    """Cleanup 스케줄러가 주기적으로 서비스 호출"""
    from src.adapters.inbound.http.app import _periodic_cleanup
    from tests.unit.fakes import FakeSamplingService, FakeElicitationService

    sampling = FakeSamplingService()
    elicitation = FakeElicitationService()

    # 0.1초 간격으로 테스트
    task = asyncio.create_task(_periodic_cleanup(sampling, elicitation, interval=0.1))

    # 0.3초 대기 (3번 호출)
    await asyncio.sleep(0.3)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    # cleanup_expired() 호출 확인
    assert sampling.cleanup_count >= 2
    assert elicitation.cleanup_count >= 2
```

---

## Common Pitfalls

### 1. Cleanup Task 누락

**Bad:**

```python
# Startup에서 task 생성만 하고 전역 변수에 저장 안 함
asyncio.create_task(_periodic_cleanup(...))  # ❌ 참조 손실
```

**Good:**

```python
global cleanup_task
cleanup_task = asyncio.create_task(_periodic_cleanup(...))  # ✅ 전역 저장
```

### 2. CancelledError 미처리

**Bad:**

```python
if cleanup_task:
    cleanup_task.cancel()
    # await 누락 → task가 완전히 취소되지 않음 ❌
```

**Good:**

```python
if cleanup_task:
    cleanup_task.cancel()
    try:
        await cleanup_task  # ✅ 완전한 취소 대기
    except asyncio.CancelledError:
        pass
```

### 3. Shutdown 순서 오류

**Bad:**

```python
# Storage를 먼저 닫으면 세션 정리 시 데이터 저장 불가 ❌
await conv_storage.close()
await mcp_client.disconnect_all()
```

**Good:**

```python
# 세션 정리 후 Storage 닫기 ✅
await mcp_client.disconnect_all()
await conv_storage.close()
```

---

## References

- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
- [Asyncio Task Cancellation](https://docs.python.org/3/library/asyncio-task.html#asyncio.Task.cancel)
- [Dual-Track Architecture](../../architecture/integrations/dual-track.md) - MCP SDK Track 세션 관리
- [DI Container Pattern](./README.md#di-container-provide-pattern) - Container에서 서비스 주입

---

*Last Updated: 2026-02-07*
*Phase: Plan 07 Phase 5 (Integration)*
