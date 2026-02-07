"""Integration tests for HitlNotificationAdapter

HitlNotificationAdapter는 HITL 요청을 SSE를 통해 브로드캐스트합니다.
"""

import pytest

from src.adapters.outbound.sse.hitl_notification_adapter import HitlNotificationAdapter
from src.domain.entities.elicitation_request import ElicitationRequest
from src.domain.entities.sampling_request import SamplingRequest
from tests.unit.fakes.fake_sse_broker import FakeSseBroker


class TestHitlNotificationAdapter:
    @pytest.fixture
    def fake_sse_broker(self):
        return FakeSseBroker()

    @pytest.fixture
    def adapter(self, fake_sse_broker):
        return HitlNotificationAdapter(sse_broker=fake_sse_broker)

    async def test_notify_sampling_request_broadcasts(self, adapter, fake_sse_broker):
        """notify_sampling_request() - SSE 브로드캐스트"""
        request = SamplingRequest(
            id="req-1",
            endpoint_id="ep-1",
            messages=[{"role": "user", "content": "test"}],
            model_preferences={"hints": ["fast"]},
            system_prompt="You are helpful",
            max_tokens=100,
        )

        await adapter.notify_sampling_request(request)

        # FakeSseBroker의 브로드캐스트 호출 확인
        assert len(fake_sse_broker.broadcasted_events) == 1
        event = fake_sse_broker.broadcasted_events[0]
        assert event["type"] == "sampling_request"
        assert event["data"]["request_id"] == "req-1"
        assert event["data"]["endpoint_id"] == "ep-1"
        assert event["data"]["messages"] == [{"role": "user", "content": "test"}]
        assert event["data"]["model_preferences"] == {"hints": ["fast"]}
        assert event["data"]["system_prompt"] == "You are helpful"
        assert event["data"]["max_tokens"] == 100

    async def test_notify_elicitation_request_broadcasts(self, adapter, fake_sse_broker):
        """notify_elicitation_request() - SSE 브로드캐스트"""
        request = ElicitationRequest(
            id="req-2",
            endpoint_id="ep-2",
            message="Please confirm",
            requested_schema={"type": "object", "properties": {"confirmed": {"type": "boolean"}}},
        )

        await adapter.notify_elicitation_request(request)

        # FakeSseBroker의 브로드캐스트 호출 확인
        assert len(fake_sse_broker.broadcasted_events) == 1
        event = fake_sse_broker.broadcasted_events[0]
        assert event["type"] == "elicitation_request"
        assert event["data"]["request_id"] == "req-2"
        assert event["data"]["endpoint_id"] == "ep-2"
        assert event["data"]["message"] == "Please confirm"
        assert event["data"]["requested_schema"] == {
            "type": "object",
            "properties": {"confirmed": {"type": "boolean"}},
        }

    async def test_multiple_notifications(self, adapter, fake_sse_broker):
        """여러 알림이 순차적으로 브로드캐스트됨"""
        sampling_req = SamplingRequest(
            id="req-1", endpoint_id="ep-1", messages=[{"role": "user", "content": "test"}]
        )
        elicitation_req = ElicitationRequest(
            id="req-2", endpoint_id="ep-2", message="Confirm", requested_schema={}
        )

        await adapter.notify_sampling_request(sampling_req)
        await adapter.notify_elicitation_request(elicitation_req)

        assert len(fake_sse_broker.broadcasted_events) == 2
        assert fake_sse_broker.broadcasted_events[0]["type"] == "sampling_request"
        assert fake_sse_broker.broadcasted_events[1]["type"] == "elicitation_request"
