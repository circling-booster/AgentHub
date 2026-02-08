"""FakeHitlNotification - 테스트용 HITL 알림 Fake

알림 호출을 기록하여 검증할 수 있습니다.
"""

from src.domain.entities.elicitation_request import ElicitationRequest
from src.domain.entities.sampling_request import SamplingRequest
from src.domain.ports.outbound.hitl_notification_port import HitlNotificationPort


class FakeHitlNotification(HitlNotificationPort):
    """테스트용 HITL Notification Fake

    알림 호출을 기록하여 검증할 수 있습니다.
    """

    def __init__(self) -> None:
        self.sampling_notifications: list[SamplingRequest] = []
        self.elicitation_notifications: list[ElicitationRequest] = []

    async def notify_sampling_request(self, request: SamplingRequest) -> None:
        """Sampling 요청 알림 기록"""
        self.sampling_notifications.append(request)

    async def notify_elicitation_request(self, request: ElicitationRequest) -> None:
        """Elicitation 요청 알림 기록"""
        self.elicitation_notifications.append(request)

    def reset(self) -> None:
        """모든 기록 초기화 (테스트 간 격리)"""
        self.sampling_notifications.clear()
        self.elicitation_notifications.clear()
