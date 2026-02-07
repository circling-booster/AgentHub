"""FakeHitlNotification 테스트 (TDD - Red Phase)

FakeHitlNotification 자체의 동작을 검증합니다.
"""

from datetime import datetime, timezone

from src.domain.entities.elicitation_request import (
    ElicitationRequest,
    ElicitationStatus,
)
from src.domain.entities.sampling_request import SamplingRequest, SamplingStatus
from tests.unit.fakes.fake_hitl_notification import FakeHitlNotification


class TestFakeHitlNotification:
    """FakeHitlNotification 자체 테스트"""

    async def test_notify_sampling_request_records_call(self):
        """Sampling 알림 호출 기록"""
        fake = FakeHitlNotification()
        request = SamplingRequest(
            id="req-123",
            endpoint_id="ep-1",
            messages=[{"role": "user", "content": "test"}],
            model_preferences=None,
            system_prompt=None,
            max_tokens=1024,
            status=SamplingStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )

        await fake.notify_sampling_request(request)

        assert len(fake.sampling_notifications) == 1
        assert fake.sampling_notifications[0].id == "req-123"

    async def test_notify_elicitation_request_records_call(self):
        """Elicitation 알림 호출 기록"""
        fake = FakeHitlNotification()
        request = ElicitationRequest(
            id="req-456",
            endpoint_id="ep-1",
            message="Enter API key",
            requested_schema={"type": "string"},
            status=ElicitationStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )

        await fake.notify_elicitation_request(request)

        assert len(fake.elicitation_notifications) == 1
        assert fake.elicitation_notifications[0].id == "req-456"

    async def test_multiple_notifications_recorded(self):
        """여러 알림이 순서대로 기록됨"""
        fake = FakeHitlNotification()

        req1 = SamplingRequest(
            id="req-1",
            endpoint_id="ep-1",
            messages=[],
            status=SamplingStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )
        req2 = SamplingRequest(
            id="req-2",
            endpoint_id="ep-2",
            messages=[],
            status=SamplingStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )

        await fake.notify_sampling_request(req1)
        await fake.notify_sampling_request(req2)

        assert len(fake.sampling_notifications) == 2
        assert fake.sampling_notifications[0].id == "req-1"
        assert fake.sampling_notifications[1].id == "req-2"

    async def test_reset_clears_all_notifications(self):
        """reset()이 모든 알림 기록 초기화"""
        fake = FakeHitlNotification()

        request = SamplingRequest(
            id="req-123",
            endpoint_id="ep-1",
            messages=[],
            status=SamplingStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )
        await fake.notify_sampling_request(request)

        fake.reset()

        assert len(fake.sampling_notifications) == 0
        assert len(fake.elicitation_notifications) == 0
