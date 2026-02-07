"""HITL Notification Adapter

HITL(Human-In-The-Loop) 요청을 SSE를 통해 브로드캐스트합니다.
"""

from src.domain.entities.elicitation_request import ElicitationRequest
from src.domain.entities.sampling_request import SamplingRequest
from src.domain.ports.outbound.event_broadcast_port import EventBroadcastPort
from src.domain.ports.outbound.hitl_notification_port import HitlNotificationPort


class HitlNotificationAdapter(HitlNotificationPort):
    """HITL 요청 알림 어댑터 (SSE 브로드캐스트)

    timeout 시 SSE를 통해 Extension/Playground에 알림 전송
    """

    def __init__(self, sse_broker: EventBroadcastPort) -> None:
        """
        Args:
            sse_broker: EventBroadcastPort 구현체 (DI로 주입)
        """
        self._broker = sse_broker

    async def notify_sampling_request(self, request: SamplingRequest) -> None:
        """Sampling 요청 알림 (SSE 브로드캐스트)

        Args:
            request: SamplingRequest 엔티티
        """
        await self._broker.broadcast(
            event_type="sampling_request",
            data={
                "request_id": request.id,
                "endpoint_id": request.endpoint_id,
                "messages": request.messages,
                "model_preferences": request.model_preferences,
                "system_prompt": request.system_prompt,
                "max_tokens": request.max_tokens,
            },
        )

    async def notify_elicitation_request(self, request: ElicitationRequest) -> None:
        """Elicitation 요청 알림 (SSE 브로드캐스트)

        Args:
            request: ElicitationRequest 엔티티
        """
        await self._broker.broadcast(
            event_type="elicitation_request",
            data={
                "request_id": request.id,
                "endpoint_id": request.endpoint_id,
                "message": request.message,
                "requested_schema": request.requested_schema,
            },
        )
