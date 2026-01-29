# Fake Adapter Patterns

## Why Fake over Mock

| Aspect | Fake Adapter | unittest.mock |
|--------|-------------|---------------|
| Port compliance | Implements full interface | No contract check |
| Behavior | Real logic (in-memory) | Stub returns |
| Refactor safety | Breaks if port changes | Silently passes |
| Readability | Plain Python class | Mock setup noise |

## Template: Storage Fake (dict-based)

```python
# tests/unit/fakes/fake_storage.py
from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.domain.ports.outbound.storage_port import ConversationStoragePort

class FakeConversationStorage(ConversationStoragePort):
    """In-memory dict storage. All port methods implemented."""

    def __init__(self) -> None:
        self.conversations: dict[str, Conversation] = {}
        self.messages: dict[str, list[Message]] = {}

    async def save_conversation(self, conversation: Conversation) -> None:
        self.conversations[conversation.id] = conversation
        if conversation.id not in self.messages:
            self.messages[conversation.id] = []

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        return self.conversations.get(conversation_id)

    async def list_conversations(self, limit: int = 20, offset: int = 0) -> list[Conversation]:
        sorted_convs = sorted(
            self.conversations.values(),
            key=lambda c: c.updated_at,
            reverse=True,
        )
        return sorted_convs[offset : offset + limit]

    async def delete_conversation(self, conversation_id: str) -> bool:
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            self.messages.pop(conversation_id, None)
            return True
        return False

    async def save_message(self, message: Message) -> None:
        conv_id = message.conversation_id
        if conv_id not in self.messages:
            self.messages[conv_id] = []
        self.messages[conv_id].append(message)

    async def get_messages(self, conversation_id: str, limit: int | None = None) -> list[Message]:
        messages = self.messages.get(conversation_id, [])
        if limit:
            return messages[-limit:]
        return messages

    # --- Test helpers (not part of port) ---
    def clear(self) -> None:
        self.conversations.clear()
        self.messages.clear()
```

## Template: Streaming Fake (AsyncIterator)

```python
# tests/unit/fakes/fake_orchestrator.py
from collections.abc import AsyncIterator
from src.domain.ports.outbound.orchestrator_port import OrchestratorPort

class FakeOrchestrator(OrchestratorPort):
    """Controllable orchestrator: set responses, toggle failure."""

    def __init__(
        self,
        responses: list[str] | None = None,
        should_fail: bool = False,
        error_message: str = "Orchestrator error",
    ) -> None:
        self.responses = responses or ["Hello! ", "How can I help you?"]
        self.should_fail = should_fail
        self.error_message = error_message
        self.initialized = False
        self.closed = False
        self.processed_messages: list[tuple[str, str]] = []

    async def initialize(self) -> None:
        self.initialized = True

    async def process_message(self, message: str, conversation_id: str) -> AsyncIterator[str]:
        if self.should_fail:
            raise RuntimeError(self.error_message)
        self.processed_messages.append((message, conversation_id))
        for chunk in self.responses:
            yield chunk

    async def close(self) -> None:
        self.closed = True

    # --- Test helpers ---
    def set_responses(self, responses: list[str]) -> None:
        self.responses = responses

    def set_failure(self, should_fail: bool, message: str = "error") -> None:
        self.should_fail = should_fail
        self.error_message = message

    def reset(self) -> None:
        self.initialized = False
        self.closed = False
        self.processed_messages.clear()
        self.should_fail = False
```

## Template: Toolset Fake

```python
# tests/unit/fakes/fake_toolset.py
from src.domain.entities.tool import Tool
from src.domain.ports.outbound.toolset_port import ToolsetPort

class FakeToolset(ToolsetPort):
    """In-memory toolset with controllable tools and results."""

    def __init__(self) -> None:
        self.tools: dict[str, Tool] = {}
        self.call_results: dict[str, object] = {}
        self.call_history: list[tuple[str, dict]] = []

    async def get_tools(self) -> list[Tool]:
        return list(self.tools.values())

    async def call_tool(self, tool_name: str, arguments: dict) -> object:
        self.call_history.append((tool_name, arguments))
        if tool_name in self.call_results:
            return self.call_results[tool_name]
        raise ToolNotFoundError(f"Tool not found: {tool_name}")

    # --- Test helpers ---
    def add_tool(self, tool: Tool, result: object = None) -> None:
        self.tools[tool.name] = tool
        if result is not None:
            self.call_results[tool.name] = result
```

## Fake Adapter Design Rules

1. **Implement every abstract method** - No `NotImplementedError` stubs
2. **Use simple data structures** - `dict`, `list` for storage
3. **Add test helpers** - `clear()`, `reset()`, `set_failure()` etc.
4. **Track calls** - `processed_messages`, `call_history` for assertions
5. **Support error simulation** - `should_fail` flag pattern
6. **Location** - Always in `tests/unit/fakes/fake_<name>.py`

## pytest Fixture Pattern

```python
@pytest.fixture
def fake_orchestrator():
    return FakeOrchestrator(responses=["Test"])

@pytest.fixture
def fake_storage():
    return FakeConversationStorage()

@pytest.fixture
def service(fake_orchestrator, fake_storage):
    """Compose service with fakes via constructor injection."""
    return ConversationService(
        orchestrator=fake_orchestrator,
        storage=fake_storage,
    )
```
