"""Unit Test Fixtures - Fake Adapter 중앙 관리

모든 단위 테스트에서 공유되는 Fake Adapter fixture를 제공합니다.
tests/unit/fakes/ 디렉토리의 Fake 구현체를 사용합니다.
"""

import pytest

from tests.unit.fakes import (
    FakeConversationService,
    FakeConversationStorage,
    FakeEndpointStorage,
    FakeOrchestrator,
    FakeToolset,
)


@pytest.fixture
def fake_conversation_storage():
    """Fake ConversationStorage fixture"""
    return FakeConversationStorage()


@pytest.fixture
def fake_endpoint_storage():
    """Fake EndpointStorage fixture"""
    return FakeEndpointStorage()


@pytest.fixture
def fake_orchestrator():
    """Fake Orchestrator fixture"""
    return FakeOrchestrator()


@pytest.fixture
def fake_toolset():
    """Fake Toolset fixture"""
    return FakeToolset()


@pytest.fixture
def fake_conversation_service():
    """Fake ConversationService fixture"""
    return FakeConversationService()
