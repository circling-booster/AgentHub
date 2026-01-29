# Domain Layer Purity Rules

## Allowed Imports (stdlib only)

```python
# Standard library
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING
import uuid

# Domain internal cross-references
from src.domain.entities.<module> import <Entity>
from src.domain.ports.<direction>.<module> import <Port>
from src.domain.services.<module> import <Service>
from src.domain.exceptions import <Exception>
```

## Forbidden Imports

Any `pip install`-able package is forbidden inside `src/domain/`:

| Package | Layer it belongs to |
|---------|-------------------|
| `fastapi`, `starlette` | `src/adapters/inbound/` |
| `google.adk`, `litellm` | `src/adapters/outbound/` |
| `aiosqlite`, `sqlalchemy` | `src/adapters/outbound/` |
| `pydantic` | `src/adapters/` schemas or `src/config/` |
| `dependency_injector` | `src/config/` |
| `httpx`, `aiohttp` | `src/adapters/outbound/` |

## TYPE_CHECKING Guard

Use `TYPE_CHECKING` for type annotations that reference domain entities in ports, avoiding circular imports:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.entities.conversation import Conversation

class MyPort(ABC):
    @abstractmethod
    async def get(self, id: str) -> "Conversation | None":
        pass
```

## Validation Checklist

Run after any domain layer change:

```
[ ] No external library imports in src/domain/**/*.py
[ ] All exceptions inherit from DomainException
[ ] Entities use @dataclass (not pydantic BaseModel)
[ ] Services receive ports via constructor (not concrete adapters)
[ ] No file I/O, network calls, or DB access in domain
[ ] Enums use stdlib enum.Enum (not third-party)
```

## Module Docstring Convention

Every domain module starts with:

```python
"""<Module description>

순수 Python으로 작성됩니다. 외부 라이브러리에 의존하지 않습니다.
"""
```

## Entity Conventions

| Convention | Example |
|-----------|---------|
| ID field | `id: str = field(default_factory=lambda: str(uuid.uuid4()))` |
| Timestamp | `created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))` |
| Validation | `__post_init__` with `raise ValidationError(...)` |
| Immutable default | `field(default_factory=list)` not `= []` |
