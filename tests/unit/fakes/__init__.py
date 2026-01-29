"""
Fake Adapters for Testing

헥사고날 아키텍처에서 Domain Layer를 테스트할 때 사용하는 가짜 어댑터들입니다.
실제 외부 시스템(DB, API 등)에 의존하지 않고 테스트할 수 있습니다.

사용법:
    from tests.unit.fakes import FakeConversationStorage, FakeOrchestrator
    또는 conftest.py의 fixture를 사용하세요.
"""

from tests.unit.fakes.fake_conversation_service import FakeConversationService
from tests.unit.fakes.fake_orchestrator import FakeOrchestrator
from tests.unit.fakes.fake_storage import (
    FakeConversationStorage,
    FakeEndpointStorage,
)
from tests.unit.fakes.fake_toolset import FakeToolset

__all__ = [
    "FakeConversationService",
    "FakeConversationStorage",
    "FakeEndpointStorage",
    "FakeOrchestrator",
    "FakeToolset",
]
