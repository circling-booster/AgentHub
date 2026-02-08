"""FakeSseBroker 테스트 (TDD - Red Phase)

FakeSseBroker 자체의 동작을 검증합니다.
"""

import pytest

from tests.unit.fakes.fake_sse_broker import FakeSseBroker


class TestFakeSseBroker:
    """FakeSseBroker 자체 테스트"""

    @pytest.fixture
    def broker(self):
        return FakeSseBroker()

    async def test_broadcast_appends_to_history(self, broker):
        """broadcast가 이벤트를 히스토리에 추가"""
        await broker.broadcast("test_event", {"key": "value"})

        assert len(broker.broadcasted_events) == 1
        assert broker.broadcasted_events[0]["type"] == "test_event"
        assert broker.broadcasted_events[0]["data"] == {"key": "value"}

    async def test_get_events_by_type_filters(self, broker):
        """get_events_by_type이 타입별로 필터링"""
        await broker.broadcast("event_a", {"msg": "A"})
        await broker.broadcast("event_b", {"msg": "B"})
        await broker.broadcast("event_a", {"msg": "A2"})

        events_a = broker.get_events_by_type("event_a")
        assert len(events_a) == 2
        assert all(e["type"] == "event_a" for e in events_a)

    async def test_clear_events_empties_history(self, broker):
        """clear_events가 히스토리 초기화"""
        await broker.broadcast("test", {"data": 1})
        broker.clear_events()

        assert len(broker.broadcasted_events) == 0

    async def test_multiple_broadcasts_in_order(self, broker):
        """여러 이벤트가 순서대로 기록됨"""
        await broker.broadcast("event1", {"order": 1})
        await broker.broadcast("event2", {"order": 2})
        await broker.broadcast("event3", {"order": 3})

        assert len(broker.broadcasted_events) == 3
        assert broker.broadcasted_events[0]["data"]["order"] == 1
        assert broker.broadcasted_events[1]["data"]["order"] == 2
        assert broker.broadcasted_events[2]["data"]["order"] == 3
