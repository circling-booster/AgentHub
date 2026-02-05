# **🧪 Test Strategy**

## **Test Pyramid**

                    ┌─────────────┐  
      Chaos  ──────►│   Chaos     │  장애 주입 시나리오  
                    └──────┬──────┘  
                           │  
                    ┌──────┴──────┐  
      E2E   ───────►│    E2E      │  Extension \+ Server  
                    └──────┬──────┘  
                           │  
                ┌──────────┴──────────┐  
   Integration ►│    Integration      │  Adapter \+ External  
                └──────────┬──────────┘  
                           │  
          ┌────────────────┴────────────────┐  
 Unit     │             Unit                │  Domain Only  
          │    (Fake Adapters, No Mocking)  │  
          └─────────────────────────────────┘

### **헥사고날 아키텍처 장점**

* **Domain Layer:** Fake Adapter로 외부 의존성 없이 테스트  
* **Adapter Layer:** Port 인터페이스 기반 테스트 격리  
* **No Mocking:** 실제 구현체 또는 Fake Adapter 사용

## **🧪 Test Isolation Strategy**

### **원칙: 각 테스트는 완전히 독립적으로 실행 가능해야 함**

### **1\. DB 격리 (temp\_data\_dir fixture)**

\# ❌ 나쁜 예: 전역 DB 공유  
\_shared\_db \= SqliteStorage("test.db")  \# 상태 오염

\# ✅ 좋은 예: 각 테스트마다 독립 DB  
def test\_something(temp\_data\_dir):  
    db \= SqliteStorage(str(temp\_data\_dir / "test.db"))  
    \# 다른 테스트와 완전히 독립

*Note: authenticated\_client fixture는 자동으로 temp\_data\_dir를 사용합니다.*

### **2\. Fixture Scope 이해**

| Scope | 생명주기 | 사용 사례 |
| :---- | :---- | :---- |
| function | 각 테스트마다 생성/소멸 | **기본값**, 상태 격리 필수 |
| module | 모듈(파일)당 1회 | 무거운 초기화 공유 (드물게 사용) |
| session | 전체 테스트 세션당 1회 | 외부 서버 subprocess |

### **3\. 캐시 초기화**

@pytest.fixture  
def dynamic\_toolset():  
    toolset \= DynamicToolset()  
    yield toolset  
    toolset.invalidate\_cache()  \# 캐시 정리

### **4\. 환경변수 격리 (monkeypatch)**

def test\_with\_env(monkeypatch):  
    monkeypatch.setenv("API\_KEY", "test-key")  
    \# 이 테스트만 영향, 다른 테스트와 격리

## **🎭 Mock vs Fake: When to Use What**

### **Fake Adapter (권장 \- 헥사고날 아키텍처)**

Fake는 실제 동작하는 단순화된 구현체입니다.

\# ✅ Fake Adapter: Port 인터페이스 구현  
from src.domain.ports.outbound.storage\_port import ConversationStoragePort  
from src.domain.entities.conversation import Conversation

class FakeConversationStorage(ConversationStoragePort):  
    def \_\_init\_\_(self):  
        self.\_conversations \= {}  \# 인메모리

    async def save\_conversation(self, conversation: Conversation) \-\> None:  
        self.\_conversations\[conversation.id\] \= conversation

    async def get\_conversation(self, conversation\_id: str) \-\> Conversation | None:  
        return self.\_conversations.get(conversation\_id)

### **Mock (필요한 경우만)**

Mock은 호출 여부나 반환값을 제어하는 모의 객체입니다.

\# ⚠️ Mock: 외부 API 호출 등 Fake 구현이 어려운 경우  
from unittest.mock import AsyncMock, patch

@patch("httpx.AsyncClient.post")  
async def test\_external\_api\_call(mock\_post):  
    mock\_post.return\_value \= AsyncMock(status\_code=200, json=lambda: {"ok": True})

    result \= await call\_external\_api()  
    assert result\["ok"\] is True  
    mock\_post.assert\_called\_once()

**Mock 사용 시점:**

* 외부 HTTP API 호출  
* 시간 의존적 로직 (time.time, datetime.now)  
* 파일 시스템 I/O (특수한 경우)  
* 랜덤 값 생성