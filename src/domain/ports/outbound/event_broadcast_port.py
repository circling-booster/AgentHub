"""Event Broadcasting Port (SSE 추상화)

HITL 알림을 Extension에 전달하기 위한 SSE Broker 추상화입니다.
"""

from collections.abc import AsyncIterator
from typing import Any, Protocol


class EventBroadcastPort(Protocol):
    """Event Broadcasting Port (Domain 추상화)

    SSE를 통해 클라이언트에게 이벤트를 브로드캐스트합니다.
    Adapter 레이어에서 asyncio.Queue 기반 pub/sub으로 구현됩니다.
    """

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """이벤트를 모든 구독자에게 브로드캐스트

        Args:
            event_type: 이벤트 타입 (예: "sampling_request", "elicitation_request")
            data: 이벤트 데이터
        """
        ...

    async def subscribe(self) -> AsyncIterator[dict[str, Any]]:
        """이벤트 스트림 구독

        Yields:
            이벤트 딕셔너리 {"type": str, "data": dict}
        """
        ...
