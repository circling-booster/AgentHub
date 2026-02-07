"""Integration tests for SseBroker

SseBroker는 asyncio.Queue 기반 pub/sub 패턴으로 SSE 이벤트를 브로드캐스트합니다.
"""

import asyncio

import pytest

from src.adapters.outbound.sse.broker import SseBroker


class TestSseBroker:
    @pytest.fixture
    def broker(self):
        return SseBroker()

    async def test_broadcast_to_subscribers(self, broker):
        """broadcast가 모든 구독자에게 전달"""
        received_events = []

        async def subscriber():
            async for event in broker.subscribe():
                received_events.append(event)
                if len(received_events) >= 2:
                    break

        # 구독 시작
        task = asyncio.create_task(subscriber())
        await asyncio.sleep(0.1)  # 구독 대기

        # 이벤트 브로드캐스트
        await broker.broadcast("test_event", {"key": "value"})
        await broker.broadcast("test_event_2", {"key": "value2"})

        await task

        assert len(received_events) == 2
        assert received_events[0]["type"] == "test_event"
        assert received_events[0]["data"]["key"] == "value"
        assert received_events[1]["type"] == "test_event_2"
        assert received_events[1]["data"]["key"] == "value2"

    async def test_multiple_subscribers(self, broker):
        """여러 구독자가 동일한 이벤트 수신"""
        received_1 = []
        received_2 = []

        async def subscriber_1():
            async for event in broker.subscribe():
                received_1.append(event)
                break

        async def subscriber_2():
            async for event in broker.subscribe():
                received_2.append(event)
                break

        # 두 구독자 시작
        task1 = asyncio.create_task(subscriber_1())
        task2 = asyncio.create_task(subscriber_2())
        await asyncio.sleep(0.1)

        # 이벤트 브로드캐스트
        await broker.broadcast("shared", {"msg": "hello"})

        await asyncio.gather(task1, task2)

        assert len(received_1) == 1
        assert len(received_2) == 1
        assert received_1[0]["type"] == "shared"
        assert received_1[0]["data"]["msg"] == "hello"
        assert received_2[0]["type"] == "shared"
        assert received_2[0]["data"]["msg"] == "hello"

    async def test_subscriber_cleanup_on_exit(self, broker):
        """구독 종료 시 큐가 제거됨"""

        async def short_subscriber():
            async for _event in broker.subscribe():
                break  # 첫 이벤트 후 즉시 종료

        # 구독 시작
        task = asyncio.create_task(short_subscriber())
        await asyncio.sleep(0.1)

        # 초기 구독자 수
        initial_count = len(broker._subscribers)

        # 이벤트 브로드캐스트
        await broker.broadcast("test", {"value": 1})
        await task

        # 구독 종료 후 구독자 수 확인
        await asyncio.sleep(0.1)
        final_count = len(broker._subscribers)

        assert final_count < initial_count or final_count == 0
