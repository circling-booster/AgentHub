---
name: hexagonal-patterns
description: "Hexagonal architecture patterns for AgentHub Python backend. Use when (1) creating new entities, services, or ports in src/domain/, (2) implementing adapters in src/adapters/, (3) adding dependency injection providers in src/config/container.py, (4) writing tests with Fake Adapters in tests/unit/fakes/, (5) reviewing code for domain layer purity violations (external imports in domain). Covers Domain Layer purity, Port/Adapter separation, DI container patterns, and Fake Adapter testing."
---

# Hexagonal Patterns

## Architecture Overview

```
Adapters (inbound/outbound)
    |           ^
    v           |
  Ports (interfaces)
    |           ^
    v           |
  Domain (pure Python)
```

Dependency rule: **Domain depends on nothing. Everything depends on Domain.**

## 1. Domain Layer Purity

Domain code (`src/domain/`) uses **only** Python stdlib. No external libraries.

### Allowed imports in `src/domain/`

```python
# OK - stdlib only
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING
import uuid

# OK - domain internal
from src.domain.entities.conversation import Conversation
from src.domain.exceptions import ValidationError
```

### Forbidden imports in `src/domain/`

```python
# NEVER in domain layer
from fastapi import ...        # adapter concern
from google.adk import ...     # adapter concern
import aiosqlite               # adapter concern
from dependency_injector import ...  # config concern
from pydantic import ...       # adapter/config concern
```

### Entity pattern

```python
# src/domain/entities/<name>.py
"""<Name> entity - 순수 Python, 외부 의존성 없음"""
import uuid
from dataclasses import dataclass, field

from src.domain.exceptions import ValidationError

@dataclass
class MyEntity:
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not self.name:
            raise ValidationError("Name cannot be empty")
```

### Domain exception pattern

```python
# All exceptions inherit from DomainException (src/domain/exceptions.py)
class DomainException(Exception):
    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__

class MySpecificError(DomainException):
    pass
```

## 2. Port / Adapter Separation

### Outbound Port (domain defines contract)

```python
# src/domain/ports/outbound/<name>_port.py
"""순수 Python으로 작성. 외부 라이브러리 의존 없음."""
from abc import ABC, abstractmethod

class MyPort(ABC):
    """
    Port docstring includes:
    - Purpose
    - Example implementations (real + fake)
    """

    @abstractmethod
    async def do_something(self, arg: str) -> str:
        pass
```

### Inbound Port (domain exposes use cases)

```python
# src/domain/ports/inbound/<name>_port.py
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

class ChatPort(ABC):
    @abstractmethod
    async def send_message(
        self, conversation_id: str | None, message: str,
    ) -> AsyncIterator[str]:
        pass
```

### Service implements Inbound Port, depends on Outbound Ports

```python
# src/domain/services/<name>_service.py
"""순수 Python. 외부 라이브러리 의존 없음."""
from src.domain.ports.inbound.chat_port import ChatPort
from src.domain.ports.outbound.orchestrator_port import OrchestratorPort
from src.domain.ports.outbound.storage_port import ConversationStoragePort

class ConversationService:
    """Constructor receives ports, NOT concrete adapters."""

    def __init__(
        self,
        orchestrator: OrchestratorPort,
        storage: ConversationStoragePort,
    ) -> None:
        self._orchestrator = orchestrator
        self._storage = storage
```

### Adapter implements Outbound Port (external side)

```python
# src/adapters/outbound/storage/sqlite_conversation_storage.py
import aiosqlite  # OK here - adapter layer

from src.domain.ports.outbound.storage_port import ConversationStoragePort

class SqliteConversationStorage(ConversationStoragePort):
    """Implements port with real SQLite. External imports allowed."""

    def __init__(self, db_path: str):
        self._db_path = db_path

    async def save_conversation(self, conversation) -> None:
        # aiosqlite usage OK in adapter
        ...
```

## 3. Dependency Injection

### Container pattern (dependency-injector)

```python
# src/config/container.py
from dependency_injector import containers, providers
from src.config.settings import Settings

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    settings = providers.Singleton(Settings)

    # Outbound adapters (Singleton - stateful)
    storage = providers.Singleton(
        SqliteConversationStorage,
        db_path=config.storage.database,
    )

    # Domain services (Factory - stateless, receives ports)
    conversation_service = providers.Factory(
        ConversationService,
        orchestrator=orchestrator_adapter,
        storage=storage,
    )
```

### Async Factory pattern (for adapters needing async init)

```python
class AdkOrchestratorAdapter(OrchestratorPort):
    def __init__(self, model: str):
        self._initialized = False

    async def initialize(self) -> None:
        """Called in FastAPI lifespan, not constructor."""
        if self._initialized:
            return
        # async setup here
        self._initialized = True
```

## 4. Fake Adapter Testing

**Rule: No mocking. Use Fake Adapters that implement Port interfaces.**

### Fake Adapter pattern

```python
# tests/unit/fakes/fake_<name>.py
from src.domain.ports.outbound.storage_port import ConversationStoragePort

class FakeConversationStorage(ConversationStoragePort):
    """In-memory implementation for testing."""

    def __init__(self) -> None:
        self.conversations: dict[str, Conversation] = {}

    async def save_conversation(self, conversation) -> None:
        self.conversations[conversation.id] = conversation

    async def get_conversation(self, conv_id: str):
        return self.conversations.get(conv_id)

    # Test helpers (not part of port)
    def clear(self) -> None:
        self.conversations.clear()
```

### Controllable Fake (for error simulation)

```python
# tests/unit/fakes/fake_orchestrator.py
class FakeOrchestrator(OrchestratorPort):
    def __init__(
        self,
        responses: list[str] | None = None,
        should_fail: bool = False,
        error_message: str = "Orchestrator error",
    ) -> None:
        self.responses = responses or ["Hello! ", "How can I help you?"]
        self.should_fail = should_fail
        self.processed_messages: list[tuple[str, str]] = []

    async def process_message(self, message, conversation_id):
        if self.should_fail:
            raise RuntimeError(self.error_message)
        self.processed_messages.append((message, conversation_id))
        for chunk in self.responses:
            yield chunk

    # Helpers
    def set_failure(self, fail: bool, msg: str = "error") -> None:
        self.should_fail = fail
        self.error_message = msg

    def reset(self) -> None:
        self.processed_messages.clear()
        self.should_fail = False
```

### Test using Fake Adapters

```python
# tests/unit/domain/services/test_conversation_service.py
import pytest
from tests.unit.fakes.fake_orchestrator import FakeOrchestrator
from tests.unit.fakes.fake_storage import FakeConversationStorage

@pytest.fixture
def fake_orchestrator():
    return FakeOrchestrator(responses=["Test response"])

@pytest.fixture
def fake_storage():
    return FakeConversationStorage()

@pytest.fixture
def service(fake_orchestrator, fake_storage):
    return ConversationService(
        orchestrator=fake_orchestrator,
        storage=fake_storage,
    )

@pytest.mark.asyncio
async def test_send_message_stores_and_returns(service, fake_storage):
    chunks = []
    async for chunk in service.send_message(None, "Hello"):
        chunks.append(chunk)
    assert chunks == ["Test response"]
    assert len(fake_storage.messages) > 0
```

## Quick Reference

| Layer | Location | Imports | Tests with |
|-------|----------|---------|------------|
| Domain entities | `src/domain/entities/` | stdlib only | direct instantiation |
| Domain services | `src/domain/services/` | stdlib + domain | Fake Adapters |
| Domain ports | `src/domain/ports/` | `abc`, `typing` | N/A (interfaces) |
| Domain exceptions | `src/domain/exceptions.py` | stdlib only | direct raise/catch |
| Inbound adapters | `src/adapters/inbound/` | any + domain ports | TestClient, Fake Services |
| Outbound adapters | `src/adapters/outbound/` | any + domain ports | Integration tests |
| Config/DI | `src/config/` | any | Container tests |
| Fake adapters | `tests/unit/fakes/` | domain ports | N/A (test helpers) |

For detailed reference, see:
- [Domain purity rules](references/domain-purity.md) - Allowed/forbidden imports, validation checklist
- [Fake adapter patterns](references/fake-adapter-patterns.md) - Templates for all port types
