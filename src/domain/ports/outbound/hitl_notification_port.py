"""HITL Notification Port - HITL 요청 알림용 포트

HITL timeout 시 Extension으로 알림을 전송합니다.
Domain은 알림 메커니즘(SSE, WebSocket 등)을 알 필요 없습니다.
"""

from abc import ABC, abstractmethod

from src.domain.entities.elicitation_request import ElicitationRequest
from src.domain.entities.sampling_request import SamplingRequest


class HitlNotificationPort(ABC):
    """HITL 요청 알림 포트

    HITL timeout 시 Extension으로 알림을 전송합니다.
    Domain은 알림 메커니즘(SSE, WebSocket 등)을 알 필요 없습니다.
    """

    @abstractmethod
    async def notify_sampling_request(self, request: SamplingRequest) -> None:
        """Sampling 요청 알림

        Args:
            request: Sampling 요청 엔티티
        """
        pass

    @abstractmethod
    async def notify_elicitation_request(self, request: ElicitationRequest) -> None:
        """Elicitation 요청 알림

        Args:
            request: Elicitation 요청 엔티티
        """
        pass
