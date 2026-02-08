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
        """notify_sampling_request() - SSE 브로드캐스트 (StreamChunk 기반)"""
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

        # StreamChunk 기반 검증
        assert event["type"] == "sampling_request"
        assert event["data"]["type"] == "sampling_request"
        assert event["data"]["content"] == "req-1"  # request_id
        assert event["data"]["agent_name"] == "ep-1"  # endpoint_id
        assert event["data"]["tool_arguments"]["messages"] == [{"role": "user", "content": "test"}]

    async def test_notify_elicitation_request_broadcasts(self, adapter, fake_sse_broker):
        """notify_elicitation_request() - SSE 브로드캐스트 (StreamChunk 기반)"""
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

        # StreamChunk 기반 검증
        assert event["type"] == "elicitation_request"
        assert event["data"]["type"] == "elicitation_request"
        assert event["data"]["content"] == "req-2"  # request_id
        assert event["data"]["result"] == "Please confirm"  # message
        assert event["data"]["tool_arguments"]["schema"] == {
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
