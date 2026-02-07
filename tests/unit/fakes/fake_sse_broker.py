"""FakeSseBroker - SSE Broker Fake (테스트용)

실제 asyncio.Queue 대신 메모리에 이벤트를 저장합니다.
subscribe()는 구현하지 않습니다 (테스트 불필요).
"""

from collections.abc import AsyncIterator
from typing import Any


class FakeSseBroker:
    """SSE Broker Fake (테스트용)

    실제 asyncio.Queue 대신 메모리에 이벤트를 저장합니다.
    subscribe()는 구현하지 않습니다 (테스트 불필요).
    """

    def __init__(self):
        self.broadcasted_events: list[dict[str, Any]] = []

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """이벤트를 히스토리에 추가"""
        self.broadcasted_events.append({"type": event_type, "data": data})

    def get_events_by_type(self, event_type: str) -> list[dict[str, Any]]:
        """특정 타입의 이벤트만 필터링 (테스트용)"""
        return [e for e in self.broadcasted_events if e["type"] == event_type]

    def clear_events(self) -> None:
        """이벤트 히스토리 초기화 (테스트 간 격리)"""
        self.broadcasted_events.clear()

    async def subscribe(self) -> AsyncIterator[dict[str, Any]]:
        """구독 (Fake에서는 미사용)"""
        # Fake에서는 subscribe 불필요 (테스트 시 broadcast만 검증)
        raise NotImplementedError("FakeSseBroker does not implement subscribe")
