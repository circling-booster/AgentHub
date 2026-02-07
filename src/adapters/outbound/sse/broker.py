"""SSE Broker for Event Broadcasting

asyncio.Queue 기반 pub/sub 패턴으로 SSE 이벤트를 브로드캐스트합니다.
"""

import asyncio
import contextlib
from collections.abc import AsyncIterator
from typing import Any

from src.domain.ports.outbound.event_broadcast_port import EventBroadcastPort


class SseBroker(EventBroadcastPort):
    """SSE 이벤트 브로드캐스터 (Singleton)

    여러 클라이언트가 subscribe()로 이벤트 스트림을 구독하고,
    broadcast()로 모든 구독자에게 이벤트를 전송합니다.
    """

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """이벤트를 모든 구독자에게 브로드캐스트

        Args:
            event_type: 이벤트 타입
            data: 이벤트 데이터
        """
        event = {"type": event_type, "data": data}
        async with self._lock:
            # 모든 구독자의 Queue에 이벤트 전송
            for queue in self._subscribers:
                # Queue가 꽉 찼거나 취소된 경우 무시
                with contextlib.suppress(Exception):
                    await queue.put(event)

    async def subscribe(self) -> AsyncIterator[dict[str, Any]]:
        """이벤트 스트림 구독

        Yields:
            이벤트 딕셔너리 {"type": str, "data": dict}
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)

        async with self._lock:
            self._subscribers.append(queue)

        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            # 구독 종료 시 큐 제거
            async with self._lock:
                if queue in self._subscribers:
                    self._subscribers.remove(queue)
