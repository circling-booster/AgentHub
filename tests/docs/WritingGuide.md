# **📝 How to Write Tests**

## **Recipes**

### **Recipe 1: Domain Entity 단위 테스트**

\# tests/unit/domain/entities/test\_my\_entity.py  
import pytest  
from src.domain.entities.my\_entity import MyEntity

class TestMyEntity:  
    def test\_create(self):  
        entity \= MyEntity(id="1", name="test")  
        assert entity.id \== "1"

    def test\_equality(self):  
        e1 \= MyEntity(id="1", name="test")  
        e2 \= MyEntity(id="1", name="test")  
        assert e1 \== e2

**⚠️ Import 표준:** 반드시 from src.domain... 형식 사용 (src. 접두사 필수)

### **Recipe 2: Domain Service 단위 테스트 (Fake Adapter 사용)**

\# tests/unit/domain/services/test\_my\_service.py  
import pytest  
from src.domain.services.my\_service import MyService  
from tests.unit.fakes import FakeConversationStorage, FakeOrchestrator

class TestMyService:  
    @pytest.fixture  
    def service(self):  
        storage \= FakeConversationStorage()  
        orchestrator \= FakeOrchestrator(responses=\["Hello"\])  
        return MyService(storage=storage, orchestrator=orchestrator)

    async def test\_process(self, service):  
        \# async def \- asyncio\_mode="auto"이므로 @pytest.mark.asyncio 불필요  
        result \= await service.process("input")  
        assert result \== "Hello"

**⚠️ @pytest.mark.asyncio 불필요:** asyncio\_mode \= "auto" 설정으로 자동 감지됨.

### **Recipe 3: API Integration 테스트**

\# tests/integration/adapters/test\_my\_routes.py  
import pytest

class TestMyRoutes:  
    async def test\_get\_endpoint(self, authenticated\_client):  
        \# authenticated\_client \= TestClient \+ 토큰 자동 주입 \+ 임시 DB  
        response \= authenticated\_client.get("/api/my-endpoint")  
        assert response.status\_code \== 200

    async def test\_post\_with\_body(self, authenticated\_client):  
        response \= authenticated\_client.post(  
            "/api/my-endpoint",  
            json={"key": "value"}  
        )  
        assert response.status\_code \== 201

**⚠️ Integration 테스트:** 반드시 authenticated\_client fixture 사용 (토큰 없으면 403\)

### **Recipe 4: 새 Fake Adapter 추가**

\# 1\. tests/unit/fakes/fake\_my\_port.py 생성  
from src.domain.ports.outbound.my\_port import MyPort

class FakeMyPort(MyPort):  
    def \_\_init\_\_(self):  
        self.\_data \= {}

    async def get(self, id: str):  
        return self.\_data.get(id)

\# 2\. tests/unit/fakes/\_\_init\_\_.py에 export 추가  
from tests.unit.fakes.fake\_my\_port import FakeMyPort  
\_\_all\_\_ \= \[..., "FakeMyPort"\]

\# 3\. tests/unit/conftest.py에 fixture 추가 (필요 시)
@pytest.fixture
def fake\_my\_port():
    return FakeMyPort()

### **Recipe 5: 콜백 테스트 (Protocol 타입)**

\# Callback Protocol 정의 (Domain Purity용)
from typing import Protocol, Any

class SamplingCallback(Protocol):
    async def \_\_call\_\_(
        self,
        request\_id: str,
        endpoint\_id: str,
        messages: list\[dict\[str, Any\]\],
        \*\*kwargs
    ) \-\> dict\[str, Any\]: ...

\# Fake Adapter에 콜백 저장 기능 추가
class FakeMcpClient(McpClientPort):
    def \_\_init\_\_(self):
        self.\_sampling\_callbacks \= {}  \# endpoint\_id \-\> callback

    async def connect(
        self,
        endpoint\_id: str,
        url: str,
        sampling\_callback: SamplingCallback | None \= None,
    ) \-\> None:
        self.\_connections\[endpoint\_id\] \= True
        if sampling\_callback:
            self.\_sampling\_callbacks\[endpoint\_id\] \= sampling\_callback

    def get\_sampling\_callback(self, endpoint\_id: str):
        """테스트 검증용: 저장된 콜백 반환"""
        return self.\_sampling\_callbacks.get(endpoint\_id)

\# 테스트: 콜백이 올바르게 저장되었는지 검증
async def test\_callback\_stored\_on\_connect():
    fake \= FakeMcpClient()

    async def sample\_callback(\*\*kwargs):
        return {"role": "assistant", "content": "test"}

    await fake.connect("ep-1", "http://localhost:8080/mcp", sampling\_callback=sample\_callback)
    stored \= fake.get\_sampling\_callback("ep-1")

    assert stored is sample\_callback  \# 동일 객체 참조 확인

**⚠️ Protocol 사용 이유:** Domain Layer에서 MCP SDK 타입을 직접 사용하지 않고 Duck Typing으로 추상화 (Domain Purity 유지)

### **Recipe 6: asyncio.Event-based Service Tests (Signal Pattern)**

HITL 서비스(SamplingService, ElicitationService)는 asyncio.Event 기반 Signal 패턴을 사용합니다.

**Pattern: delayed signal with background task**

```python
import asyncio
import pytest
from src.domain.services.sampling_service import SamplingService
from src.domain.entities.sampling_request import SamplingRequest, SamplingStatus

async def test_wait_for_response_returns_after_signal():
    """wait_for_response() - 시그널 후 즉시 반환"""
    # Given: Service와 Request 준비
    service = SamplingService()
    request = SamplingRequest(
        id="req-1",
        endpoint_id="ep-1",
        messages=[{"role": "user", "content": "Hello"}]
    )
    await service.create_request(request)

    # Background task: 1초 후 approve
    async def delayed_approve():
        await asyncio.sleep(1.0)
        await service.approve("req-1", {"content": "test"})

    asyncio.create_task(delayed_approve())

    # When: 30초 타임아웃이지만 1초 내 반환됨
    result = await service.wait_for_response("req-1", timeout=30.0)

    # Then: 승인된 결과 반환
    assert result is not None
    assert result.status == SamplingStatus.APPROVED
    assert result.llm_result == {"content": "test"}
```

**Key Points:**
- `asyncio.create_task()`: Background task로 Signal 전송
- `wait_for_response()`: Event.wait()로 대기하다가 approve() 호출 시 즉시 반환
- Timeout 없이 빠른 테스트 (실제로는 1초만 대기)

**Timeout Test:**

```python
async def test_wait_for_response_timeout():
    """wait_for_response() - timeout → None"""
    # Given: Request 생성
    service = SamplingService()
    request = SamplingRequest(id="req-1", endpoint_id="ep-1", messages=[])
    await service.create_request(request)

    # When: approve 없이 0.1초 timeout
    result = await service.wait_for_response("req-1", timeout=0.1)

    # Then: Timeout (None 반환)
    assert result is None
```

**참조:** [Method C Signal Pattern](../docs/developers/architecture/layer/patterns/method-c-signal.md#testing-strategy)

## **📐 Test Structure Patterns**

### **Given-When-Then Pattern (BDD)**

async def test\_send\_message\_creates\_conversation(fake\_storage, fake\_orchestrator):  
    \# Given: 서비스와 초기 상태 준비  
    service \= ConversationService(  
        storage=fake\_storage,  
        orchestrator=fake\_orchestrator  
    )  
    fake\_orchestrator.responses \= \["Hello\!"\]

    \# When: 액션 수행  
    conversation\_id \= None  
    async for chunk in service.send\_message(conversation\_id, "Hi"):  
        pass

    \# Then: 결과 검증  
    conversations \= await fake\_storage.get\_all\_conversations()  
    assert len(conversations) \== 1

### **Parametrize: Avoid Duplicate Tests**

from src.domain.entities.message import MessageRole

@pytest.mark.parametrize("role", \[MessageRole.USER, MessageRole.ASSISTANT\])  
def test\_message\_with\_different\_roles(role):  
    from src.domain.entities.message import Message  
    message \= Message(id="msg-1", conversation\_id="conv-1", role=role, content="Test")  
    assert message.role \== role

## **🔍 Test Naming Conventions**

### **파일 네이밍**

test\_\<module\_name\>.py 또는 test\_\<feature\>.py

* 예: test\_conversation\_service.py, test\_endpoint\_entity.py

### **함수/메서드 네이밍**

def test\_\<what\>\_\<condition\>\_\<expected\>():

* **Good**: test\_send\_message\_with\_no\_conversation\_creates\_new\_conversation  
* **Bad**: test\_1

## **⚠️ Common Pitfalls**

| 함정 | 원인 | 해결 |
| :---- | :---- | :---- |
| @pytest.mark.asyncio 불필요하게 추가 | asyncio\_mode \= "auto" 설정으로 자동 감지 | 붙이지 않아도 됨 (기존 코드에 남아있는 건 레거시) |
| Integration 테스트에서 403 오류 | authenticated\_client fixture 미사용 | 반드시 authenticated\_client 사용 |
| Storage 초기화 누락 | await storage.initialize() 필요 | authenticated\_client가 자동 처리, 직접 사용 시 명시적 호출 |
| Fake Adapter 인라인 정의 | 중앙 관리 원칙 위반 | tests/unit/fakes/에서 import |
| FakeUsageStorage import 실패 | 직접 import 필요 | from tests.unit.fakes import FakeUsageStorage |
| 포트 충돌 | 여러 서버가 같은 포트 사용 | 환경변수로 오버라이드 또는 기본 포트 표 참조 |
| CI에서 MCP 테스트 실패 | CI는 Mock, 로컬은 실제 서버 | os.getenv("CI") 분기 이해 필요 |
| Import 에러 | from domain... 대신 from src.domain... 사용 | 프로젝트 표준은 src. 접두사 사용 |
| pytest 통과하지만 uvicorn 실패 | pytest는 pythonpath로 양쪽 허용, uvicorn은 src. 필수 | Import Validation 테스트 실행 (아래 참조) |

## **🔍 Import Validation Tests (uvicorn 환경 재현)**

**문제:** pytest는 pyproject.toml의 pythonpath \= \["."\] 설정으로 유연한 import를 허용하지만, uvicorn은 엄격하여 ModuleNotFoundError가 발생할 수 있습니다.

**해결:** tests/integration/test\_app\_startup.py::TestImportValidation

이 테스트들은 \*\*uvicorn과 동일한 환경(subprocess)\*\*에서 import를 검증합니다.

### **실행 방법**

pytest tests/integration/test\_app\_startup.py::TestImportValidation \-v

### **베스트 프랙티스**

1. **새 파일 추가 시**: src/adapters/outbound/new\_module.py 등을 테스트 목록에 추가하세요.  
2. **검증 내용**:  
   * src.main:app import 가능 여부  
   * 모든 adapter 및 domain service가 from src. 접두사를 사용하는지 확인